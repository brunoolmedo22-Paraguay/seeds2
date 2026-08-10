"""Aplicação Streamlit unificada para monitoramento da EMS H₂V."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from ems_app.data_pipeline import (
    available_observation_start_hours,
    load_default_profile,
    select_observation_window,
)
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
        "simulate_missing_signals": False,
        "observation_start_hour": 15,
        "solar_n_series": 2,
        "solar_n_parallel": 3,
        "solar_soiling_pct": 0.0,
        "fc_internal_step_s": 60.0,
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

source_data = st.session_state["input_dataframe"]
available_hours = available_observation_start_hours(source_data)
if not available_hours:
    st.error("A fonte de dados não contém uma janela completa de 120 minutos.")
    st.stop()
if st.session_state["observation_start_hour"] not in available_hours:
    st.session_state["observation_start_hour"] = available_hours[0]
active_input_data = select_observation_window(
    source_data,
    st.session_state["observation_start_hour"],
)

with st.sidebar:
    st.markdown(sidebar_brand(), unsafe_allow_html=True)
    st.markdown('<div class="sidebar-section-label">Navegação</div>', unsafe_allow_html=True)
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
        "○ Otimizador · próxima etapa  \n\n"
        f"Janela ativa · {st.session_state['observation_start_hour']:02d}:00 → "
        f"{(st.session_state['observation_start_hour'] + 2):02d}:00"
    )

try:
    with st.spinner("Atualizando os modelos do sistema…"):
        bundle = simulate_cached(
            active_input_data,
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
    render_inputs(bundle, SAMPLE_PATH, available_hours)
elif navigation == "3. Modelos":
    render_models(bundle, get_fuel_cell_model())
elif navigation == "4. Otimizador":
    render_optimizer()
else:
    render_settings()
