"""Orquestra o motor FV multimodelo, a PEMFC e os sinais de bateria da EMS."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import numpy as np
import pandas as pd

from ems_app.data_pipeline import synthesize_monitoring_signals
from ems_core.pemfc.models.equivalent_65kw_dynamic import (
    Equivalent65kWHorizonDynamicModel,
)
from ems_core.solar.config.pv_database import get_module
from ems_core.solar.models.pv_module import PVModule, SDMParams
from ems_core.solar.simulation.multimodel import (
    MODEL_NOCT,
    MODEL_ORDER,
    MODEL_SDM,
    MODEL_SIMPLE,
    ModelStatus,
    compute_model_kpis,
    run_all_models,
)
from ems_core.solar.simulation.solver import extract_sdm_params


@dataclass(frozen=True)
class SolarRunConfig:
    module_key: str = "CS7L-580MS"
    n_series: int = 2
    n_parallel: int = 3
    soiling_losses_pct: float = 0.0

    @property
    def n_modules(self) -> int:
        return int(self.n_series) * int(self.n_parallel)


@dataclass(frozen=True)
class FuelCellRunConfig:
    internal_time_step_s: float = 60.0


@dataclass(frozen=True)
class SubsystemStatus:
    available: bool
    fidelity: str
    message: str


@dataclass
class SimulationBundle:
    input_data: pd.DataFrame
    solar_input: pd.DataFrame
    solar_output: pd.DataFrame
    solar_results_by_model: dict[str, pd.DataFrame]
    solar_statuses: dict[str, ModelStatus]
    solar_kpis_by_model: dict[str, dict]
    solar_reference_model: str
    solar_module: PVModule
    fuel_cell_input: pd.DataFrame
    fuel_cell_output: pd.DataFrame
    overview: pd.DataFrame
    solar_metrics: dict[str, float]
    fuel_cell_metrics: dict[str, float]
    fuel_cell_status: SubsystemStatus
    battery_status: SubsystemStatus
    synthetic_signals_enabled: bool


def _integrate_power_kwh(timestamp: pd.Series, power_kw: pd.Series) -> float:
    if len(timestamp) < 2:
        return 0.0
    seconds = (
        pd.to_datetime(timestamp) - pd.to_datetime(timestamp).iloc[0]
    ).dt.total_seconds().to_numpy(dtype=float)
    power = pd.to_numeric(power_kw, errors="coerce").fillna(0.0).to_numpy(dtype=float)
    interval_energy_kw_s = 0.5 * (power[1:] + power[:-1]) * np.diff(seconds)
    return float(interval_energy_kw_s.sum() / 3600.0)


@lru_cache(maxsize=32)
def _extracted_sdm_parameters(module_key: str) -> tuple[dict, dict]:
    module = get_module(module_key)
    if module.sdm is not None:
        return module.sdm.to_dict(), {"success": True, "cost": 0.0}
    parameters, report = extract_sdm_params(module.stc)
    if not report.success:
        raise RuntimeError(
            f"A extração dos parâmetros SDM não convergiu para {module_key}."
        )
    return parameters.to_dict(), {
        "success": bool(report.success),
        "cost": float(report.cost),
        "message": str(report.message),
    }


def build_solar_module(module_key: str) -> PVModule:
    module = get_module(module_key)
    parameters, _ = _extracted_sdm_parameters(module_key)
    module.sdm = SDMParams(**parameters)
    return module


def _canonical_solar_output(result: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame({"timestamp": pd.DatetimeIndex(result.index)})
    mapping = {
        "G": "irradiancia_W_m2",
        "G_eff": "irradiancia_efetiva_W_m2",
        "Tamb": "temperatura_ambiente_C",
        "Tc": "temperatura_celula_C",
        "Vmp": "tensao_mpp_modulo_V",
        "Imp": "corrente_mpp_modulo_A",
        "P_module": "potencia_mpp_modulo_W",
        "eta": "eficiencia_fv_fracao",
        "P_array": "potencia_fv_W",
        "P_disp": "potencia_solar_disponivel_W",
    }
    for source, target in mapping.items():
        if source in result:
            out[target] = result[source].to_numpy()
        else:
            out[target] = np.nan
    out["potencia_fv_kW"] = out["potencia_fv_W"] / 1000.0
    out["eficiencia_fv_pct"] = out["eficiencia_fv_fracao"] * 100.0
    out.attrs.update(result.attrs)
    return out


def run_solar_model(
    input_data: pd.DataFrame,
    config: SolarRunConfig,
    module: PVModule | None = None,
) -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    dict[str, float],
    dict[str, pd.DataFrame],
    dict[str, ModelStatus],
    dict[str, dict],
    str,
    PVModule,
]:
    if config.n_series < 1 or config.n_parallel < 1:
        raise ValueError("O arranjo FV deve possuir ao menos um módulo.")
    if not 0.0 <= config.soiling_losses_pct < 100.0:
        raise ValueError("As perdas ópticas devem estar entre 0 e 100%.")

    active_module = module or build_solar_module(config.module_key)
    index = pd.DatetimeIndex(input_data["timestamp"], name="timestamp")
    temperature = (
        input_data["temperatura_ambiente_C"].to_numpy(dtype=float)
        if "temperatura_ambiente_C" in input_data
        else np.full(len(input_data), np.nan)
    )
    solar_input = pd.DataFrame(
        {
            "G": input_data["irradiancia_W_m2"].to_numpy(dtype=float),
            "Tamb": temperature,
        },
        index=index,
    )
    solar_input.attrs.update(input_data.attrs)
    results, statuses = run_all_models(
        active_module,
        solar_input,
        n_series=config.n_series,
        n_parallel=config.n_parallel,
        soiling_losses=config.soiling_losses_pct / 100.0,
        noct=active_module.stc.noct,
    )
    if not results:
        raise RuntimeError("Nenhum modelo fotovoltaico conseguiu produzir resultados.")

    preferred = (MODEL_SDM, MODEL_NOCT, MODEL_SIMPLE)
    reference_model = next(model_id for model_id in preferred if model_id in results)
    selected = results[reference_model]
    kpis = {
        model_id: compute_model_kpis(result, active_module)
        for model_id, result in results.items()
    }
    selected_kpi = kpis[reference_model]
    active = selected["G_eff"] >= 1.0
    efficiency = selected.loc[active, "eta"] * 100.0
    metrics = {
        "installed_power_kW": float(
            active_module.stc.p_nom * config.n_modules / 1000.0
        ),
        "array_area_m2": float(active_module.stc.area * config.n_modules),
        "energy_kWh": float(selected_kpi["energy_kWh"]),
        "peak_power_kW": float(selected_kpi["p_max_W"] / 1000.0),
        "mean_efficiency_pct": float(efficiency.mean() if len(efficiency) else 0.0),
        "peak_efficiency_pct": float(selected["eta"].max() * 100.0),
        "available_models": float(len(results)),
    }
    return (
        solar_input.reset_index(),
        _canonical_solar_output(selected),
        metrics,
        results,
        statuses,
        kpis,
        reference_model,
        active_module,
    )


def _fuel_cell_input_with_missing_columns(input_data: pd.DataFrame) -> pd.DataFrame:
    profile = pd.DataFrame({"timestamp": input_data["timestamp"]})
    profile["P_FC_requested_kW"] = (
        input_data["potencia_solicitada_fc_kW"]
        if "potencia_solicitada_fc_kW" in input_data
        else np.nan
    )
    profile["FC_enable"] = input_data.get("FC_enable", True)
    profile["T_ambient_C"] = (
        input_data["temperatura_ambiente_C"]
        if "temperatura_ambiente_C" in input_data
        else np.nan
    )
    if "T_coolant_in_C" in input_data:
        profile["T_coolant_in_C"] = input_data["T_coolant_in_C"]
    if "V_bus_V" in input_data:
        profile["V_bus_V"] = input_data["V_bus_V"]
    return profile


def build_fuel_cell_input(input_data: pd.DataFrame) -> pd.DataFrame:
    return _fuel_cell_input_with_missing_columns(input_data)


def _unavailable_fuel_cell_output(
    input_data: pd.DataFrame,
    reason: str,
) -> pd.DataFrame:
    count = len(input_data)
    requested = (
        pd.to_numeric(input_data["potencia_solicitada_fc_kW"], errors="coerce")
        .fillna(0.0)
        .to_numpy(dtype=float)
        if "potencia_solicitada_fc_kW" in input_data
        else np.zeros(count, dtype=float)
    )
    return pd.DataFrame(
        {
            "timestamp": pd.to_datetime(input_data["timestamp"]),
            "P_FC_requested_kW": requested,
            "P_FC_delivered_kW": np.zeros(count),
            "hydrogen_supplied_kg_h": np.zeros(count),
            "net_electrical_efficiency_LHV_percent": np.zeros(count),
            "current_A": np.zeros(count),
            "V_stack_V": np.zeros(count),
            "state": ["INDISPONIVEL"] * count,
            "limitation_flag": np.ones(count, dtype=bool),
            "status_message": [reason] * count,
        }
    )


def run_fuel_cell_model(
    input_data: pd.DataFrame,
    config: FuelCellRunConfig,
    model: Equivalent65kWHorizonDynamicModel | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, float], SubsystemStatus]:
    if config.internal_time_step_s <= 0.0:
        raise ValueError("O passo interno da PEMFC deve ser positivo.")
    fuel_cell_input = build_fuel_cell_input(input_data)
    missing: list[str] = []
    if fuel_cell_input["P_FC_requested_kW"].isna().any():
        missing.append("potência solicitada")
    if fuel_cell_input["T_ambient_C"].isna().any():
        missing.append("temperatura ambiente")
    if missing:
        reason = "Entrada incompleta: " + ", ".join(missing) + "."
        empty_metrics = {
            "energy_requested_kWh": 0.0,
            "energy_delivered_kWh": 0.0,
            "peak_delivered_kW": 0.0,
            "max_hydrogen_kg_h": 0.0,
            "mean_efficiency_pct": 0.0,
            "limited_points": float(len(input_data)),
        }
        return (
            fuel_cell_input,
            _unavailable_fuel_cell_output(input_data, reason),
            empty_metrics,
            SubsystemStatus(False, "PRELIMINAR", reason),
        )

    dynamic_model = model or Equivalent65kWHorizonDynamicModel()
    fuel_cell_output = dynamic_model.simulate_profile(
        fuel_cell_input,
        internal_time_step_s=config.internal_time_step_s,
    )
    metrics = {
        "energy_requested_kWh": _integrate_power_kwh(
            fuel_cell_output["timestamp"], fuel_cell_output["P_FC_requested_kW"]
        ),
        "energy_delivered_kWh": _integrate_power_kwh(
            fuel_cell_output["timestamp"], fuel_cell_output["P_FC_delivered_kW"]
        ),
        "peak_delivered_kW": float(fuel_cell_output["P_FC_delivered_kW"].max()),
        "max_hydrogen_kg_h": float(fuel_cell_output["hydrogen_supplied_kg_h"].max()),
        "mean_efficiency_pct": float(
            fuel_cell_output.loc[
                fuel_cell_output["P_FC_delivered_kW"] > 0.01,
                "net_electrical_efficiency_LHV_percent",
            ].mean()
        ),
        "limited_points": float(fuel_cell_output["limitation_flag"].sum()),
    }
    if not np.isfinite(metrics["mean_efficiency_pct"]):
        metrics["mean_efficiency_pct"] = 0.0
    request_origin = input_data.attrs.get("fuel_cell_request_origin", "CSV")
    fidelity = "SINTETICO" if request_origin == "SINTETICA" else "PRELIMINAR"
    message = (
        "Referência sintética; resposta PEMFC aproximada."
        if fidelity == "SINTETICO"
        else "Modelo PEMFC aproximado executado com a referência da entrada."
    )
    return (
        fuel_cell_input,
        fuel_cell_output,
        metrics,
        SubsystemStatus(True, fidelity, message),
    )


def _complete_synthetic_fuel_request(input_data: pd.DataFrame) -> pd.DataFrame:
    out = input_data.copy()
    needs_request = (
        "potencia_solicitada_fc_kW" not in out
        or out["potencia_solicitada_fc_kW"].isna().any()
    )
    if not needs_request:
        return out
    count = len(out)
    phase = np.linspace(0.0, 2.4 * np.pi, count)
    generated = np.clip(24.0 + 7.0 * np.sin(phase - 0.55), 8.0, 42.0)
    if "potencia_solicitada_fc_kW" not in out:
        out["potencia_solicitada_fc_kW"] = generated
    else:
        missing = out["potencia_solicitada_fc_kW"].isna().to_numpy()
        out.loc[missing, "potencia_solicitada_fc_kW"] = generated[missing]
    out.attrs.update(input_data.attrs)
    out.attrs["fuel_cell_request_origin"] = "SINTETICA"
    return out


def build_overview(
    input_data: pd.DataFrame,
    solar_output: pd.DataFrame,
    fuel_cell_output: pd.DataFrame,
    *,
    simulate_missing_signals: bool,
) -> pd.DataFrame:
    overview = input_data[["timestamp"]].copy()
    overview["potencia_fv_kW"] = solar_output["potencia_fv_kW"].to_numpy(dtype=float)

    fc_indexed = fuel_cell_output.set_index("timestamp")
    target_index = pd.DatetimeIndex(overview["timestamp"])
    snapshots = fc_indexed.reindex(target_index)
    if snapshots["P_FC_delivered_kW"].isna().any():
        snapshots = fc_indexed.reindex(target_index, method="ffill")
    overview["potencia_fc_solicitada_kW"] = (
        input_data["potencia_solicitada_fc_kW"].fillna(0.0).to_numpy(dtype=float)
        if "potencia_solicitada_fc_kW" in input_data
        else np.zeros(len(input_data))
    )
    overview["potencia_fc_entregue_kW"] = snapshots[
        "P_FC_delivered_kW"
    ].fillna(0.0).to_numpy(dtype=float)
    overview["consumo_h2_kg_h"] = snapshots[
        "hydrogen_supplied_kg_h"
    ].fillna(0.0).to_numpy(dtype=float)
    overview["estado_fc"] = snapshots["state"].fillna("INDISPONIVEL").astype(str).to_numpy()

    if "carga_total_kW" in input_data:
        overview["carga_total_kW"] = input_data["carga_total_kW"].to_numpy(dtype=float)
        overview["carga_origem"] = input_data.attrs.get("load_origin", "CSV")
    if simulate_missing_signals:
        overview = synthesize_monitoring_signals(overview)

    battery_power = (
        overview["potencia_bateria_kW"].to_numpy(dtype=float)
        if "potencia_bateria_kW" in overview
        else np.zeros(len(overview), dtype=float)
    )
    overview["potencia_geracao_total_kW"] = (
        overview["potencia_fv_kW"].to_numpy(dtype=float)
        + overview["potencia_fc_entregue_kW"].to_numpy(dtype=float)
        + battery_power
    )
    if "carga_total_kW" in overview:
        overview["desbalanco_potencia_kW"] = (
            overview["potencia_geracao_total_kW"].to_numpy(dtype=float)
            - overview["carga_total_kW"].to_numpy(dtype=float)
        )
    return overview


def run_complete_simulation(
    input_data: pd.DataFrame,
    solar_config: SolarRunConfig,
    fuel_cell_config: FuelCellRunConfig,
    *,
    simulate_missing_signals: bool,
    fuel_cell_model: Equivalent65kWHorizonDynamicModel | None = None,
) -> SimulationBundle:
    effective_input = input_data.copy()
    effective_input.attrs.update(input_data.attrs)
    if simulate_missing_signals:
        effective_input = _complete_synthetic_fuel_request(effective_input)

    (
        solar_input,
        solar_output,
        solar_metrics,
        solar_results,
        solar_statuses,
        solar_kpis,
        solar_reference,
        solar_module,
    ) = run_solar_model(effective_input, solar_config)
    fuel_input, fuel_output, fuel_metrics, fuel_status = run_fuel_cell_model(
        effective_input, fuel_cell_config, model=fuel_cell_model
    )
    overview = build_overview(
        effective_input,
        solar_output,
        fuel_output,
        simulate_missing_signals=simulate_missing_signals,
    )
    battery_available = "potencia_bateria_kW" in overview
    battery_status = SubsystemStatus(
        battery_available,
        "SINTETICO" if battery_available else "NAO_IMPLEMENTADO",
        (
            "Sinais demonstrativos de potência e SOC ativos; não são um modelo físico."
            if battery_available
            else "Modelo físico ainda não integrado; sinais sintéticos desativados."
        ),
    )
    return SimulationBundle(
        input_data=effective_input,
        solar_input=solar_input,
        solar_output=solar_output,
        solar_results_by_model=solar_results,
        solar_statuses=solar_statuses,
        solar_kpis_by_model=solar_kpis,
        solar_reference_model=solar_reference,
        solar_module=solar_module,
        fuel_cell_input=fuel_input,
        fuel_cell_output=fuel_output,
        overview=overview,
        solar_metrics=solar_metrics,
        fuel_cell_metrics=fuel_metrics,
        fuel_cell_status=fuel_status,
        battery_status=battery_status,
        synthetic_signals_enabled=simulate_missing_signals,
    )
