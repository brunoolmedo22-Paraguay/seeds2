"""Aplicação Streamlit unificada para monitoramento da EMS H₂V."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from ems_app.data_pipeline import load_default_profile
from ems_app.model_runner import (
    FuelCellRunConfig,
    SolarRunConfig,
    run_complete_simulation,
)
from ems_app.pages import (
    render_inputs,
    render_models,
    render_optimizer,
    render_overview,
    render_settings,
)
from ems_app.style import APP_CSS, sidebar_brand
from ems_core.pemfc.models.equivalent_65kw_dynamic import (
    Equivalent65kWHorizonDynamicModel,
)


BASE_DIR = Path(__file__).resolve().parent
SAMPLE_PATH = BASE_DIR / "data" / "entrada_padrao_ems.csv"

st.set_page_config(
    page_title="H₂V · Energy Management System",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(APP_CSS, unsafe_allow_html=True)


def _initialize_state() -> None:
    defaults = {
        "input_dataframe": load_default_profile(SAMPLE_PATH),
        "active_input_hash": "DEFAULT",
        "input_source_label": SAMPLE_PATH.name,
        "simulate_missing_signals": True,
        "solar_n_series": 3,
        "solar_n_parallel": 2,
        "solar_soiling_pct": 0.0,
        "fc_internal_step_s": 10.0,
        "input_uploader_generation": 0,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


@st.cache_resource(show_spinner=False)
def get_fuel_cell_model() -> Equivalent65kWHorizonDynamicModel:
    return Equivalent65kWHorizonDynamicModel()


@st.cache_data(show_spinner=False, max_entries=12)
def simulate_cached(
    input_data: pd.DataFrame,
    n_series: int,
    n_parallel: int,
    soiling_pct: float,
    internal_step_s: float,
    simulate_missing_signals: bool,
):
    return run_complete_simulation(
        input_data=input_data,
        solar_config=SolarRunConfig(
            n_series=int(n_series),
            n_parallel=int(n_parallel),
            soiling_losses_pct=float(soiling_pct),
        ),
        fuel_cell_config=FuelCellRunConfig(
            internal_time_step_s=float(internal_step_s),
        ),
        simulate_missing_signals=bool(simulate_missing_signals),
        fuel_cell_model=get_fuel_cell_model(),
    )


_initialize_state()

with st.sidebar:
    st.markdown(sidebar_brand(), unsafe_allow_html=True)
    navigation = st.radio(
        "Navegação",
        (
            "1. Visão geral",
            "2. Entradas",
            "3. Modelos",
            "4. Otimizador",
            "5. Configurações",
        ),
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.caption(
        "Integração atual\n\n"
        "● Modelo FV · ativo  \n"
        "● Modelo PEMFC · ativo  \n"
        "○ Bateria · próxima etapa  \n"
        "○ Otimizador · próxima etapa"
    )

try:
    with st.spinner("Atualizando os modelos do sistema…"):
        bundle = simulate_cached(
            st.session_state["input_dataframe"],
            st.session_state["solar_n_series"],
            st.session_state["solar_n_parallel"],
            st.session_state["solar_soiling_pct"],
            st.session_state["fc_internal_step_s"],
            st.session_state["simulate_missing_signals"],
        )
except (TypeError, ValueError, RuntimeError, KeyError) as exc:
    st.error(f"Não foi possível executar a simulação integrada: {exc}")
    st.info("Revise o CSV na aba Entradas ou restaure o arquivo padrão.")
    st.stop()

if navigation == "1. Visão geral":
    render_overview(bundle)
elif navigation == "2. Entradas":
    render_inputs(bundle, SAMPLE_PATH)
elif navigation == "3. Modelos":
    render_models(bundle, get_fuel_cell_model())
elif navigation == "4. Otimizador":
    render_optimizer()
else:
    render_settings()
