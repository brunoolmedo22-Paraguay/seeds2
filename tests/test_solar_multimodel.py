from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from ems_core.solar.config.pv_database import MODULE_DB, get_module
from ems_core.solar.simulation.multimodel import (
    MODEL_NOCT,
    MODEL_SDM,
    MODEL_SIMPLE,
    build_synthetic_profile,
    compute_model_kpis,
    run_all_models,
    simulate_irradiance_model,
    simulate_noct_efficiency_model,
    simulate_sdm_model,
)
from ems_core.solar.simulation.solver import extract_sdm_params


def constant_profile(g: float = 1000.0, tamb: float | None = 25.0) -> pd.DataFrame:
    index = pd.date_range("2026-03-21 12:00:00", periods=120, freq="1min", name="timestamp")
    return pd.DataFrame(
        {
            "G": np.full(120, g, dtype=float),
            "Tamb": np.full(120, np.nan if tamb is None else tamb, dtype=float),
        },
        index=index,
    )


class SolarMultiModelPhysicsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = get_module("CS7L-580MS")
        cls.module.sdm, cls.report = extract_sdm_params(cls.module.stc)

    def test_sdm_extraction_converges(self):
        self.assertTrue(self.report.success)
        self.assertLess(self.report.cost, 1e-6)

    def test_linear_model_matches_nameplate_at_stc(self):
        result = simulate_irradiance_model(
            self.module, constant_profile(), n_series=2, n_parallel=3
        )
        np.testing.assert_allclose(
            result["P_array"], self.module.stc.p_nom * 6, rtol=0, atol=1e-10
        )

    def test_noct_model_applies_thermal_derating(self):
        result = simulate_noct_efficiency_model(
            self.module, constant_profile(), n_series=2, n_parallel=3
        )
        expected_tc = 25.0 + (self.module.stc.noct - 20.0) / 800.0 * 1000.0
        self.assertAlmostEqual(float(result["Tc"].iloc[0]), expected_tc, places=10)
        self.assertLess(float(result["P_array"].iloc[0]), self.module.stc.p_nom * 6)

    def test_sdm_runs_complete_window(self):
        result = simulate_sdm_model(
            self.module, constant_profile(g=800.0, tamb=28.0), n_series=2, n_parallel=3
        )
        self.assertEqual(len(result), 120)
        self.assertTrue((result["P_array"] > 0).all())
        self.assertIn("Vmp_array", result)
        self.assertIn("Imp_array", result)

    def test_missing_temperature_keeps_only_continuity_model(self):
        results, statuses = run_all_models(
            self.module, constant_profile(g=700.0, tamb=None), n_series=2, n_parallel=3
        )
        self.assertEqual(set(results), {MODEL_SIMPLE})
        self.assertTrue(statuses[MODEL_SIMPLE].available)
        self.assertFalse(statuses[MODEL_NOCT].available)
        self.assertFalse(statuses[MODEL_SDM].available)

    def test_kpis_are_consistent(self):
        result = simulate_irradiance_model(
            self.module, constant_profile(g=500.0), n_series=2, n_parallel=3
        )
        kpi = compute_model_kpis(result, self.module)
        expected_power = self.module.stc.p_nom * 0.5 * 6
        expected_energy = expected_power * 2.0 / 1000.0
        self.assertAlmostEqual(kpi["energy_kWh"], expected_energy, places=10)


class SolarSyntheticProfileTests(unittest.TestCase):
    def test_perfect_irradiance_is_smooth_and_single_peak(self):
        profile = build_synthetic_profile(
            start="2026-03-21 00:00:00",
            irradiance_profile="Irradiância perfeita",
            season="Verano",
            duration_minutes=1440,
            g_peak=1000.0,
        )
        daylight = profile.loc[profile["G"] > 0, "G"].to_numpy(dtype=float)
        peak = int(np.argmax(daylight))
        self.assertGreater(len(daylight), 600)
        self.assertTrue((np.diff(daylight[: peak + 1]) >= -1e-9).all())
        self.assertTrue((np.diff(daylight[peak:]) <= 1e-9).all())
        self.assertAlmostEqual(float(daylight.max()), 1000.0, places=8)

    def test_all_catalog_modules_expose_shared_datasheet_inputs(self):
        for key in MODULE_DB:
            with self.subTest(module=key):
                module = get_module(key)
                self.assertGreater(module.stc.p_nom, 0)
                self.assertGreater(module.stc.area, 0)
                self.assertGreater(module.stc.noct, 20)
                self.assertLess(module.stc.gamma_pmax_pct, 0)


if __name__ == "__main__":
    unittest.main()
