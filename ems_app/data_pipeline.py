"""Leitura, normalização e enriquecimento dos sinais de entrada da EMS."""

from __future__ import annotations

from io import BytesIO, StringIO
from pathlib import Path
import re
import unicodedata

import numpy as np
import pandas as pd


REQUIRED_COLUMNS = (
    "timestamp",
    "irradiancia_W_m2",
    "temperatura_ambiente_C",
    "potencia_solicitada_fc_kW",
)

OPTIONAL_COLUMNS = (
    "carga_total_kW",
    "FC_enable",
    "T_coolant_in_C",
    "V_bus_V",
)

OBSERVATION_WINDOW_MINUTES = 120


def _slug(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.strip().lower()
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_")


ALIASES = {
    "timestamp": {
        "timestamp", "data_hora", "datetime", "date_time", "tempo", "time",
        "fecha_hora",
    },
    "irradiancia_W_m2": {
        "irradiancia_w_m2", "irradiancia", "irrad", "ghi", "g", "g_w_m2",
        "irradiance", "irradiance_w_m2",
    },
    "temperatura_ambiente_C": {
        "temperatura_ambiente_c", "temperatura", "temp", "tamb", "t_ambiente_c",
        "ambient_temperature_c", "t_ambient_c",
    },
    "potencia_solicitada_fc_kW": {
        "potencia_solicitada_fc_kw", "potencia_demandada_fc_kw",
        "potencia_demandada_para_a_celula", "potencia_demandada_celula_kw",
        "p_fc_requested_kw", "pfc_requested_kw", "fc_power_request_kw",
    },
    "carga_total_kW": {
        "carga_total_kw", "carga_kw", "potencia_carga_kw", "load_kw",
        "total_load_kw",
    },
    "FC_enable": {"fc_enable", "habilitar_fc", "fc_ligada", "enable_fc"},
    "T_coolant_in_C": {
        "t_coolant_in_c", "temperatura_refrigerante_c", "coolant_temperature_c",
    },
    "V_bus_V": {"v_bus_v", "tensao_barramento_v", "bus_voltage_v"},
}


def _read_csv_payload(payload: bytes | str | Path | BytesIO) -> pd.DataFrame:
    if isinstance(payload, Path):
        raw = payload.read_bytes()
    elif isinstance(payload, str):
        candidate = Path(payload)
        raw = candidate.read_bytes() if candidate.exists() else payload.encode("utf-8")
    elif hasattr(payload, "read"):
        raw = payload.read()
    else:
        raw = payload

    if isinstance(raw, str):
        text = raw
    else:
        try:
            text = bytes(raw).decode("utf-8-sig")
        except UnicodeDecodeError:
            text = bytes(raw).decode("latin-1")

    try:
        return pd.read_csv(StringIO(text), sep=None, engine="python")
    except Exception as exc:
        raise ValueError(f"Não foi possível ler o CSV: {exc}") from exc


def _numeric(series: pd.Series, column: str) -> pd.Series:
    if series.dtype == object:
        normalized = series.astype(str).str.strip().str.replace(",", ".", regex=False)
    else:
        normalized = series
    values = pd.to_numeric(normalized, errors="coerce")
    if values.isna().any() or not np.isfinite(values.to_numpy(dtype=float)).all():
        invalid = int(values.isna().sum())
        raise ValueError(f"A coluna {column!r} contém {invalid} valor(es) inválido(s).")
    return values.astype(float)


def _boolean(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series.astype(bool)
    normalized = series.astype(str).str.strip().str.lower()
    mapping = {
        "1": True, "true": True, "sim": True, "yes": True, "on": True,
        "0": False, "false": False, "nao": False, "não": False, "no": False,
        "off": False,
    }
    result = normalized.map(mapping)
    if result.isna().any():
        raise ValueError("FC_enable deve conter somente 0/1, true/false ou sim/não.")
    return result.astype(bool)


def normalize_input_table(raw: pd.DataFrame) -> pd.DataFrame:
    """Converte nomes aceitos para o contrato canônico e valida unidades/domínios."""
    if not isinstance(raw, pd.DataFrame) or raw.empty:
        raise ValueError("O CSV de entrada está vazio.")

    slugged = {_slug(column): column for column in raw.columns}
    rename: dict[object, str] = {}
    for canonical, aliases in ALIASES.items():
        matches = [slugged[name] for name in aliases if name in slugged]
        if len(matches) > 1:
            raise ValueError(
                f"Mais de uma coluna representa {canonical}: "
                + ", ".join(map(str, matches))
            )
        if matches:
            rename[matches[0]] = canonical

    normalized = raw.rename(columns=rename).copy()
    missing = [column for column in REQUIRED_COLUMNS if column not in normalized]
    if missing:
        raise ValueError("Colunas obrigatórias ausentes: " + ", ".join(missing))

    keep = list(REQUIRED_COLUMNS) + [
        column for column in OPTIONAL_COLUMNS if column in normalized
    ]
    normalized = normalized.loc[:, keep]
    normalized["timestamp"] = pd.to_datetime(
        normalized["timestamp"], errors="coerce", format="mixed"
    )
    if normalized["timestamp"].isna().any():
        raise ValueError("A coluna timestamp contém datas ou horas inválidas.")
    if normalized["timestamp"].duplicated().any():
        raise ValueError("O CSV não pode conter timestamps duplicados.")
    if not normalized["timestamp"].is_monotonic_increasing:
        raise ValueError("Os timestamps devem estar em ordem cronológica crescente.")

    for column in (
        "irradiancia_W_m2",
        "temperatura_ambiente_C",
        "potencia_solicitada_fc_kW",
        "carga_total_kW",
        "T_coolant_in_C",
        "V_bus_V",
    ):
        if column in normalized:
            normalized[column] = _numeric(normalized[column], column)

    if (normalized["irradiancia_W_m2"] < 0.0).any():
        raise ValueError("A irradiância não pode ser negativa.")
    if (normalized["potencia_solicitada_fc_kW"] < 0.0).any():
        raise ValueError("A potência solicitada à célula não pode ser negativa.")
    if "carga_total_kW" in normalized and (normalized["carga_total_kW"] < 0.0).any():
        raise ValueError("A carga total não pode ser negativa.")
    if "V_bus_V" in normalized and (normalized["V_bus_V"] <= 0.0).any():
        raise ValueError("A tensão do barramento deve ser positiva.")

    if "FC_enable" in normalized:
        normalized["FC_enable"] = _boolean(normalized["FC_enable"])
    else:
        normalized["FC_enable"] = True

    return normalized.reset_index(drop=True)


def load_input_csv(payload: bytes | str | Path | BytesIO) -> pd.DataFrame:
    return normalize_input_table(_read_csv_payload(payload))


def load_default_profile(path: str | Path) -> pd.DataFrame:
    return load_input_csv(Path(path))


def available_observation_start_hours(
    input_data: pd.DataFrame,
    *,
    duration_minutes: int = OBSERVATION_WINDOW_MINUTES,
) -> list[int]:
    """Retorna horas inteiras com cobertura suficiente para uma janela completa."""
    if input_data.empty:
        return []
    timestamps = pd.to_datetime(input_data["timestamp"])
    first_day = timestamps.iloc[0].normalize()
    minimum = timestamps.min()
    maximum = timestamps.max()
    last_offset = pd.Timedelta(minutes=duration_minutes - 1)
    return [
        hour
        for hour in range(24)
        if first_day + pd.Timedelta(hours=hour) >= minimum
        and first_day + pd.Timedelta(hours=hour) + last_offset <= maximum
    ]


def select_observation_window(
    input_data: pd.DataFrame,
    start_hour: int,
    *,
    duration_minutes: int = OBSERVATION_WINDOW_MINUTES,
) -> pd.DataFrame:
    """Recorta e interpola uma janela exata de 120 pontos, um por minuto."""
    if duration_minutes < 1:
        raise ValueError("A duração da janela deve ser positiva.")
    available = available_observation_start_hours(
        input_data, duration_minutes=duration_minutes
    )
    if int(start_hour) not in available:
        raise ValueError(
            f"A fonte de dados não possui {duration_minutes} minutos completos "
            f"a partir de {int(start_hour):02d}:00."
        )

    source = input_data.copy()
    source["timestamp"] = pd.to_datetime(source["timestamp"])
    source = source.set_index("timestamp").sort_index()
    start = source.index[0].normalize() + pd.Timedelta(hours=int(start_hour))
    target_index = pd.date_range(start, periods=duration_minutes, freq="1min")

    expanded = source.reindex(source.index.union(target_index)).sort_index()
    numeric_columns = expanded.select_dtypes(include=[np.number]).columns
    if len(numeric_columns):
        expanded.loc[:, numeric_columns] = expanded.loc[:, numeric_columns].interpolate(
            method="time", limit_area="inside"
        )
    other_columns = [column for column in expanded.columns if column not in numeric_columns]
    if other_columns:
        expanded.loc[:, other_columns] = expanded.loc[:, other_columns].ffill().bfill()

    window = expanded.reindex(target_index)
    if window.isna().any().any():
        missing = ", ".join(window.columns[window.isna().any()].tolist())
        raise ValueError(
            "Não foi possível completar a janela minuto a minuto. "
            f"Colunas com lacunas: {missing}."
        )
    window.index.name = "timestamp"
    return window.reset_index()


def synthesize_monitoring_signals(
    aligned: pd.DataFrame,
    *,
    battery_power_limit_kW: float = 18.0,
    battery_capacity_kWh: float = 80.0,
    initial_soc_pct: float = 68.0,
) -> pd.DataFrame:
    """Cria sinais demonstrativos de carga/bateria; não é um modelo físico."""
    out = aligned.copy()
    count = len(out)
    phase = np.linspace(0.0, 2.4 * np.pi, count)
    rng = np.random.default_rng(42)

    if "carga_total_kW" not in out:
        baseline = 31.0 + 5.5 * np.sin(phase - 0.8) + 2.0 * np.sin(2.3 * phase)
        perturbation = rng.normal(0.0, 0.55, count)
        out["carga_total_kW"] = np.clip(baseline + perturbation, 20.0, None)
        out["carga_origem"] = "SINTETICA"
    else:
        out["carga_origem"] = "CSV"

    residual = (
        out["carga_total_kW"].to_numpy(dtype=float)
        - out["potencia_fv_kW"].to_numpy(dtype=float)
        - out["potencia_fc_entregue_kW"].to_numpy(dtype=float)
    )
    battery = np.clip(residual, -battery_power_limit_kW, battery_power_limit_kW)
    out["potencia_bateria_kW"] = battery

    timestamps = pd.to_datetime(out["timestamp"])
    dt_h = timestamps.diff().dt.total_seconds().fillna(0.0).to_numpy() / 3600.0
    soc = np.zeros(count, dtype=float)
    soc[0] = initial_soc_pct
    for idx in range(1, count):
        power = battery[idx - 1]
        if power >= 0.0:
            delta = -(power / 0.95) * dt_h[idx] / battery_capacity_kWh * 100.0
        else:
            delta = -(power * 0.95) * dt_h[idx] / battery_capacity_kWh * 100.0
        soc[idx] = np.clip(soc[idx - 1] + delta, 10.0, 95.0)
    out["soc_bateria_pct"] = soc
    out["bateria_origem"] = "SINTETICA_SEM_MODELO_FISICO"
    return out


def dataframe_to_csv_bytes(frame: pd.DataFrame, *, separator: str = ";") -> bytes:
    export = frame.copy()
    for column in export.select_dtypes(include=["datetime", "datetimetz"]).columns:
        export[column] = export[column].dt.strftime("%Y-%m-%d %H:%M:%S")
    return export.to_csv(index=False, sep=separator).encode("utf-8-sig")
