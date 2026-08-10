from __future__ import annotations

from io import BytesIO
from pathlib import Path
import unittest

import numpy as np

from ems_app.data_pipeline import (
    available_observation_start_hours,
    load_default_profile,
    load_input_csv,
    select_observation_window,
)
from ems_app.model_runner import (
    FuelCellRunConfig,
    SolarRunConfig,
    run_complete_simulation,
)


class InputContractTests(unittest.TestCase):
    def test_aliases_and_semicolon_are_accepted(self):
        payload = (
            "timestamp;irrad;temp;potencia demandada para a celula\n"
            "2026-08-10 10:00:00;500;26,5;12\n"
            "2026-08-10 10:01:00;520;26,7;14\n"
        ).encode("utf-8")
        frame = load_input_csv(BytesIO(payload))
        self.assertEqual(len(frame), 2)
        self.assertEqual(float(frame.loc[0, "temperatura_ambiente_C"]), 26.5)
        self.assertTrue(frame["FC_enable"].all())

    def test_duplicate_timestamps_are_rejected(self):
        payload = (
            "timestamp,irradiancia_W_m2,temperatura_ambiente_C,potencia_solicitada_fc_kW\n"
            "2026-08-10 10:00:00,500,26,12\n"
            "2026-08-10 10:00:00,520,27,14\n"
        ).encode("utf-8")
        with self.assertRaisesRegex(ValueError, "duplicados"):
            load_input_csv(payload)

    def test_default_source_builds_exact_120_minute_window(self):
        root = Path(__file__).resolve().parents[1]
        source = load_default_profile(root / "data" / "entrada_padrao_ems.csv")
        self.assertEqual(available_observation_start_hours(source), list(range(23)))
        window = select_observation_window(source, 15)
        self.assertEqual(len(window), 120)
        self.assertEqual(str(window["timestamp"].iloc[0]), "2026-08-10 15:00:00")
        self.assertEqual(str(window["timestamp"].iloc[-1]), "2026-08-10 16:59:00")
        step = window["timestamp"].diff().dropna().dt.total_seconds()
        self.assertTrue((step == 60.0).all())

    def test_operational_defaults_match_the_unified_app(self):
        solar = SolarRunConfig()
        fuel_cell = FuelCellRunConfig()
        self.assertEqual((solar.n_series, solar.n_parallel), (2, 3))
        self.assertEqual(fuel_cell.internal_time_step_s, 60.0)


class ModelIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        payload = (
            "timestamp;irradiancia_W_m2;temperatura_ambiente_C;potencia_solicitada_fc_kW\n"
            "2026-08-10 10:00:00;500;26;0\n"
            "2026-08-10 10:01:00;650;27;18\n"
            "2026-08-10 10:02:00;700;28;24\n"
        ).encode("utf-8")
        profile = load_input_csv(payload)
        cls.bundle = run_complete_simulation(
            profile,
            SolarRunConfig(n_series=3, n_parallel=2),
            FuelCellRunConfig(internal_time_step_s=30.0),
            simulate_missing_signals=True,
        )

    def test_solar_output_is_finite_and_nonnegative(self):
        power = self.bundle.solar_output["potencia_fv_kW"].to_numpy(dtype=float)
        self.assertTrue(np.isfinite(power).all())
        self.assertTrue((power >= 0.0).all())

    def test_pemfc_output_contains_ems_contract(self):
        required = {
            "P_FC_delivered_kW",
            "hydrogen_supplied_kg_h",
            "net_electrical_efficiency_LHV_percent",
            "state",
        }
        self.assertTrue(required.issubset(self.bundle.fuel_cell_output.columns))
        self.assertTrue(
            np.isfinite(
                self.bundle.fuel_cell_output["P_FC_delivered_kW"].to_numpy(dtype=float)
            ).all()
        )

    def test_synthetic_signals_fill_reserved_dashboard_fields(self):
        required = {"carga_total_kW", "potencia_bateria_kW", "soc_bateria_pct"}
        self.assertTrue(required.issubset(self.bundle.overview.columns))
        soc = self.bundle.overview["soc_bateria_pct"]
        self.assertTrue(soc.between(0.0, 100.0).all())


if __name__ == "__main__":
    unittest.main()
