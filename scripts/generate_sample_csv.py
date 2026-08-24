"""Gera o CSV diário demonstrativo usado para selecionar janelas de 120 min."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "entrada_padrao_ems.csv"


def build_profile() -> pd.DataFrame:
    timestamp = pd.date_range("2026-08-10 00:00:00", periods=24 * 60, freq="1min")
    hour = np.arange(len(timestamp), dtype=float) / 60.0

    daylight = np.clip((hour - 6.0) / 12.0, 0.0, 1.0)
    envelope = np.where(
        (hour >= 6.0) & (hour < 18.0),
        955.0 * np.sin(np.pi * daylight) ** 1.35,
        0.0,
    )
    cloud = 1.0 - 0.13 * np.exp(-((hour - 10.7) / 0.38) ** 2)
    cloud -= 0.20 * np.exp(-((hour - 15.6) / 0.28) ** 2)
    irradiance = np.clip(envelope * cloud, 0.0, None)

    temperature = 22.0 + 7.2 * np.sin(2.0 * np.pi * (hour - 8.5) / 24.0)
    temperature += 1.1 * (irradiance / 1000.0)

    morning = 8.0 * np.exp(-((hour - 8.0) / 1.8) ** 2)
    afternoon = 22.0 * np.exp(-((hour - 16.0) / 3.0) ** 2)
    base = 10.0 + 3.0 * np.sin(2.0 * np.pi * (hour - 3.0) / 24.0)
    requested_fc = np.clip(base + morning + afternoon, 0.0, 50.0)

    return pd.DataFrame(
        {
            "timestamp": timestamp,
            "irradiancia_W_m2": np.round(irradiance, 2),
            "temperatura_ambiente_C": np.round(temperature, 2),
            "potencia_solicitada_fc_kW": np.round(requested_fc, 2),
        }
    )


if __name__ == "__main__":
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    build_profile().to_csv(OUTPUT, index=False, sep=";")
    print(f"Gerado: {OUTPUT} (1440 linhas)")
