"""SEED2 · plataforma unificada de gestão dos modelos energéticos H₂V."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from ems_app.data_pipeline import (
    available_observation_starts,
    load_default_profile,
    select_observation_window,
)
from ems_app.model_runner import FuelCellRunConfig, SolarRunConfig, run_complete_simulation
from ems_app.pages import (
    render_export,
    render_inputs,
    render_models,
    render_optimizer,
    render_overview,
    render_settings,
    render_solar_comparison,
)
from ems_app.style import APP_CSS, sidebar_brand, status_chip
from ems_core.pemfc.models.equivalent_65kw_dynamic import (
    Equivalent65kWHorizonDynamicModel,
)
from ems_core.solar.simulation.multimodel import MODEL_ORDER, MODEL_SHORT_LABELS


BASE_DIR = Path(__file__).resolve().parent
SAMPLE_PATH = BASE_DIR / "data" / "entrada_padrao_ems.csv"
SIMULATION_CACHE_SCHEMA = "seed2-multimodel-v1-2026-08-24"

NAV_OVERVIEW = "Visão geral"
NAV_INPUT = "Entrada comum"
NAV_MODELS = "Modelos"
NAV_COMPARISON = "Comparação solar"
NAV_EXPORT = "Exportação"
NAV_OPTIMIZER = "Otimizador"
NAV_SETTINGS = "Configurações"
NAV_OPTIONS = (
    NAV_OVERVIEW,
    NAV_INPUT,
    NAV_MODELS,
    NAV_COMPARISON,
    NAV_EXPORT,
    NAV_OPTIMIZER,
    NAV_SETTINGS,
)
NAV_KEYS = {
    NAV_OVERVIEW: "overview",
    NAV_INPUT: "input",
    NAV_MODELS: "models",
    NAV_COMPARISON: "comparison",
    NAV_EXPORT: "export",
    NAV_OPTIMIZER: "optimizer",
    NAV_SETTINGS: "settings",
}


st.set_page_config(
    page_title="SEED2 · H₂V Energy Management System",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(APP_CSS, unsafe_allow_html=True)


def _initialize_state() -> None:
    if "input_dataframe" not in st.session_state:
        default_source = load_default_profile(SAMPLE_PATH)
        default_starts = available_observation_starts(default_source)
        preferred = next((start for start in default_starts if start.hour == 15), default_starts[0])
        st.session_state["input_dataframe"] = default_source
        st.session_state["observation_start"] = preferred
    defaults = {
        "active_input_hash": "DEFAULT",
        "input_source_label": SAMPLE_PATH.name,
        "input_mode": "CSV",
        "simulate_missing_signals": False,
        "solar_module_key": "CS7L-580MS",
        "solar_n_series": 2,
        "solar_n_parallel": 3,
        "solar_soiling_pct": 0.0,
        "fc_internal_step_s": 60.0,
        "input_uploader_generation": 0,
        "current_page": NAV_OVERVIEW,
        "selected_solar_model": "sdm",
        "comparison_reference_model": "sdm",
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


@st.cache_resource(show_spinner=False)
def get_fuel_cell_model() -> Equivalent65kWHorizonDynamicModel:
    return Equivalent65kWHorizonDynamicModel()


@st.cache_data(show_spinner=False, max_entries=16)
def simulate_cached(
    input_data: pd.DataFrame,
    module_key: str,
    n_series: int,
    n_parallel: int,
    soiling_pct: float,
    internal_step_s: float,
    simulate_missing_signals: bool,
    cache_schema: str,
):
    _ = cache_schema
    return run_complete_simulation(
        input_data=input_data,
        solar_config=SolarRunConfig(
            module_key=str(module_key),
            n_series=int(n_series),
            n_parallel=int(n_parallel),
            soiling_losses_pct=float(soiling_pct),
        ),
        fuel_cell_config=FuelCellRunConfig(internal_time_step_s=float(internal_step_s)),
        simulate_missing_signals=bool(simulate_missing_signals),
        fuel_cell_model=get_fuel_cell_model(),
    )


def _sidebar(bundle, available_starts: list[pd.Timestamp]) -> str:
    with st.sidebar:
        st.markdown(sidebar_brand(), unsafe_allow_html=True)
        st.markdown('<div class="sidebar-label">NAVEGAÇÃO</div>', unsafe_allow_html=True)
        navigation = st.session_state["current_page"]
        for option in NAV_OPTIONS:
            clicked = st.button(
                option,
                key=f"nav_{NAV_KEYS[option]}",
                type="primary" if option == navigation else "secondary",
                width="stretch",
            )
            if clicked and option != navigation:
                st.session_state["current_page"] = option
                st.rerun()

        st.divider()
        st.markdown('<div class="sidebar-label">EXECUÇÃO AUTOMÁTICA</div>', unsafe_allow_html=True)
        start = pd.Timestamp(bundle.input_data["timestamp"].iloc[0])
        end = start + pd.Timedelta(minutes=120)
        st.markdown(
            f"""
            <div class="sidebar-status"><small>FONTE</small><b>{st.session_state.get('input_source_label', 'Entrada comum')}</b></div>
            <div class="sidebar-status"><small>JANELA ATIVA</small><b>{start:%d/%m/%Y · %H:%M}–{end:%H:%M}</b></div>
            <div class="sidebar-status"><small>MÓDULO FV</small><b>{bundle.solar_module.stc.model}</b></div>
            <div class="sidebar-status"><small>SUBSISTEMAS</small><b>FV automático · PEMFC {'ativa' if bundle.fuel_cell_status.available else 'indisponível'} · bateria {'sintética' if bundle.battery_status.available else 'off'}</b></div>
            """,
            unsafe_allow_html=True,
        )
        chips = []
        for model_id in MODEL_ORDER:
            available = model_id in bundle.solar_results_by_model
            chips.append(
                status_chip(
                    ("● " if available else "○ ") + MODEL_SHORT_LABELS[model_id],
                    "ok" if available else "warn",
                )
            )
        st.markdown('<div class="status-row">' + "".join(chips) + "</div>", unsafe_allow_html=True)
        st.caption(
            "Uma entrada · 120 min · passo de 1 min. O motor FV mantém até três estimadores em paralelo."
        )
        return st.session_state["current_page"]


_initialize_state()

source_data = st.session_state["input_dataframe"]
available_starts = available_observation_starts(source_data)
if not available_starts:
    st.error("A fonte de dados não contém uma janela completa de 120 minutos.")
    st.stop()

try:
    current_start = pd.Timestamp(st.session_state["observation_start"])
except (TypeError, ValueError):
    current_start = available_starts[0]
if current_start not in available_starts:
    current_start = available_starts[0]
    st.session_state["observation_start"] = current_start

active_input_data = select_observation_window(source_data, current_start)

try:
    with st.spinner("Atualizando automaticamente os modelos do sistema…"):
        bundle = simulate_cached(
            active_input_data,
            st.session_state["solar_module_key"],
            st.session_state["solar_n_series"],
            st.session_state["solar_n_parallel"],
            st.session_state["solar_soiling_pct"],
            st.session_state["fc_internal_step_s"],
            st.session_state["simulate_missing_signals"],
            SIMULATION_CACHE_SCHEMA,
        )
except (TypeError, ValueError, RuntimeError, KeyError) as exc:
    st.error(f"Não foi possível executar a simulação integrada: {exc}")
    st.info("Revise a fonte na página Entrada comum ou restaure o arquivo padrão.")
    st.stop()

navigation = _sidebar(bundle, available_starts)

if navigation == NAV_OVERVIEW:
    render_overview(bundle)
elif navigation == NAV_INPUT:
    render_inputs(bundle, SAMPLE_PATH, available_starts)
elif navigation == NAV_MODELS:
    render_models(bundle, get_fuel_cell_model())
elif navigation == NAV_COMPARISON:
    render_solar_comparison(bundle)
elif navigation == NAV_EXPORT:
    render_export(bundle)
elif navigation == NAV_OPTIMIZER:
    render_optimizer()
else:
    render_settings(bundle)
