"""Orquestra os modelos solar e PEMFC sem alterar seus núcleos científicos."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from ems_app.data_pipeline import synthesize_monitoring_signals
from ems_core.solar.simulation.automation import build_fixed_automation_module
from ems_core.solar.simulation.mpp import simulate_timeseries
from ems_core.pemfc.models.equivalent_65kw_dynamic import (
    Equivalent65kWHorizonDynamicModel,
)


@dataclass(frozen=True)
class SolarRunConfig:
    n_series: int = 3
    n_parallel: int = 2
    soiling_losses_pct: float = 0.0

    @property
    def n_modules(self) -> int:
        return int(self.n_series) * int(self.n_parallel)


@dataclass(frozen=True)
class FuelCellRunConfig:
    internal_time_step_s: float = 10.0


@dataclass
class SimulationBundle:
    input_data: pd.DataFrame
    solar_input: pd.DataFrame
    solar_output: pd.DataFrame
    fuel_cell_input: pd.DataFrame
    fuel_cell_output: pd.DataFrame
    overview: pd.DataFrame
    solar_metrics: dict[str, float]
    fuel_cell_metrics: dict[str, float]
    synthetic_signals_enabled: bool


def _integrate_power_kwh(timestamp: pd.Series, power_kw: pd.Series) -> float:
    if len(timestamp) < 2:
        return 0.0
    seconds = (
        pd.to_datetime(timestamp) - pd.to_datetime(timestamp).iloc[0]
    ).dt.total_seconds().to_numpy(dtype=float)
    power = pd.to_numeric(power_kw).to_numpy(dtype=float)
    interval_energy_kw_s = 0.5 * (power[1:] + power[:-1]) * np.diff(seconds)
    return float(interval_energy_kw_s.sum() / 3600.0)


def run_solar_model(
    input_data: pd.DataFrame,
    config: SolarRunConfig,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, float]]:
    if config.n_series < 1 or config.n_parallel < 1:
        raise ValueError("O arranjo FV deve possuir ao menos um módulo.")
    if not 0.0 <= config.soiling_losses_pct < 100.0:
        raise ValueError("As perdas por sujidade devem estar entre 0 e 100%.")

    module = build_fixed_automation_module()
    solar_input = pd.DataFrame(
        {
            "G": input_data["irradiancia_W_m2"].to_numpy(dtype=float),
            "Tamb": input_data["temperatura_ambiente_C"].to_numpy(dtype=float),
        },
        index=pd.DatetimeIndex(input_data["timestamp"], name="timestamp"),
    )
    raw = simulate_timeseries(
        module,
        solar_input,
        n_series=config.n_series,
        n_parallel=config.n_parallel,
        soiling_losses=config.soiling_losses_pct / 100.0,
    ).reset_index()
    solar_output = raw.rename(
        columns={
            "G": "irradiancia_W_m2",
            "G_eff": "irradiancia_efetiva_W_m2",
            "Tamb": "temperatura_ambiente_C",
            "Tc": "temperatura_celula_C",
            "Vmp": "tensao_mpp_modulo_V",
            "Imp": "corrente_mpp_modulo_A",
            "Pmp": "potencia_mpp_modulo_W",
            "eta": "eficiencia_fv_fracao",
            "P_array": "potencia_fv_W",
            "P_disp": "potencia_solar_disponivel_W",
        }
    )
    solar_output["potencia_fv_kW"] = solar_output["potencia_fv_W"] / 1000.0
    solar_output["eficiencia_fv_pct"] = (
        solar_output["eficiencia_fv_fracao"] * 100.0
    )

    installed_kw = module.stc.p_nom * config.n_modules / 1000.0
    active = solar_output["irradiancia_efetiva_W_m2"] >= 1.0
    metrics = {
        "installed_power_kW": float(installed_kw),
        "array_area_m2": float(module.stc.area * config.n_modules),
        "energy_kWh": _integrate_power_kwh(
            solar_output["timestamp"], solar_output["potencia_fv_kW"]
        ),
        "peak_power_kW": float(solar_output["potencia_fv_kW"].max()),
        "mean_efficiency_pct": float(
            solar_output.loc[active, "eficiencia_fv_pct"].mean() if active.any() else 0.0
        ),
        "peak_efficiency_pct": float(solar_output["eficiencia_fv_pct"].max()),
    }
    return solar_input.reset_index(), solar_output, metrics


def build_fuel_cell_input(input_data: pd.DataFrame) -> pd.DataFrame:
    profile = pd.DataFrame(
        {
            "timestamp": input_data["timestamp"],
            "P_FC_requested_kW": input_data["potencia_solicitada_fc_kW"],
            "FC_enable": input_data.get("FC_enable", True),
            "T_ambient_C": input_data["temperatura_ambiente_C"],
        }
    )
    if "T_coolant_in_C" in input_data:
        profile["T_coolant_in_C"] = input_data["T_coolant_in_C"]
    if "V_bus_V" in input_data:
        profile["V_bus_V"] = input_data["V_bus_V"]
    return profile


def run_fuel_cell_model(
    input_data: pd.DataFrame,
    config: FuelCellRunConfig,
    model: Equivalent65kWHorizonDynamicModel | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, float]]:
    if config.internal_time_step_s <= 0.0:
        raise ValueError("O passo interno da PEMFC deve ser positivo.")
    fuel_cell_input = build_fuel_cell_input(input_data)
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
    return fuel_cell_input, fuel_cell_output, metrics


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
    snapshots = fc_indexed.reindex(pd.DatetimeIndex(overview["timestamp"]))
    if snapshots["P_FC_delivered_kW"].isna().any():
        snapshots = fc_indexed.reindex(
            pd.DatetimeIndex(overview["timestamp"]), method="ffill"
        )
    overview["potencia_fc_solicitada_kW"] = input_data[
        "potencia_solicitada_fc_kW"
    ].to_numpy(dtype=float)
    overview["potencia_fc_entregue_kW"] = snapshots[
        "P_FC_delivered_kW"
    ].to_numpy(dtype=float)
    overview["estado_fc"] = snapshots["state"].astype(str).to_numpy()

    if "carga_total_kW" in input_data:
        overview["carga_total_kW"] = input_data["carga_total_kW"].to_numpy(dtype=float)
        overview["carga_origem"] = "CSV"
    if simulate_missing_signals:
        overview = synthesize_monitoring_signals(overview)
    return overview


def run_complete_simulation(
    input_data: pd.DataFrame,
    solar_config: SolarRunConfig,
    fuel_cell_config: FuelCellRunConfig,
    *,
    simulate_missing_signals: bool,
    fuel_cell_model: Equivalent65kWHorizonDynamicModel | None = None,
) -> SimulationBundle:
    solar_input, solar_output, solar_metrics = run_solar_model(input_data, solar_config)
    fuel_input, fuel_output, fuel_metrics = run_fuel_cell_model(
        input_data, fuel_cell_config, model=fuel_cell_model
    )
    overview = build_overview(
        input_data,
        solar_output,
        fuel_output,
        simulate_missing_signals=simulate_missing_signals,
    )
    return SimulationBundle(
        input_data=input_data,
        solar_input=solar_input,
        solar_output=solar_output,
        fuel_cell_input=fuel_input,
        fuel_cell_output=fuel_output,
        overview=overview,
        solar_metrics=solar_metrics,
        fuel_cell_metrics=fuel_metrics,
        synthetic_signals_enabled=simulate_missing_signals,
    )
