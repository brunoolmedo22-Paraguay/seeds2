"""Páginas operacionais da plataforma unificada H₂V."""

from __future__ import annotations

from datetime import date, time
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from ems_app.charts import (
    battery_chart,
    fuel_cell_electrical_chart,
    fuel_cell_power_chart,
    fuel_cell_resources_chart,
    input_power_chart,
    overview_power_chart,
    pv_forecast_chart,
    source_energy_shares,
    source_share_donut,
    system_balance_chart,
)
from ems_app.data_pipeline import (
    available_observation_starts,
    build_synthetic_ems_profile,
    dataframe_to_csv_bytes,
    load_input_csv,
)
from ems_app.model_runner import SimulationBundle
from ems_app.multimodel_charts import (
    plot_comparison_efficiency,
    plot_comparison_energy,
    plot_comparison_power,
    plot_cumulative_energy,
    plot_difference_to_reference,
    plot_efficiency,
    plot_input_profile,
    plot_iv_pv_at_peak,
    plot_model_power,
    plot_temperatures,
)
from ems_app.style import CHART_CONFIG, page_header, panel_title, status_chip
from ems_core.solar.config.pv_database import MODULE_DB, get_module
from ems_core.solar.config.settings import PROFILES
from ems_core.solar.simulation.multimodel import (
    DEFAULT_EXPORT_COLUMNS,
    MODEL_LABELS,
    MODEL_NOCT,
    MODEL_ORDER,
    MODEL_SDM,
    MODEL_SHORT_LABELS,
    MODEL_SIMPLE,
    available_export_columns,
    build_export_dataframe,
    normalize_filename,
)


def _section(text: str) -> None:
    st.markdown(f'<div class="section-label">{text}</div>', unsafe_allow_html=True)


def _panel(text: str) -> None:
    st.markdown(panel_title(text), unsafe_allow_html=True)


def _chart(figure, key: str) -> None:
    st.plotly_chart(
        figure,
        width="stretch",
        config=CHART_CONFIG,
        key=key,
    )


def _download(frame: pd.DataFrame, label: str, filename: str, key: str) -> None:
    st.download_button(
        label,
        data=dataframe_to_csv_bytes(frame),
        file_name=filename,
        mime="text/csv",
        key=key,
        width="stretch",
    )


def _kpi_card(label: str, value: str, context: str | None = None) -> None:
    context_html = f'<span class="kpi-context">// {context}</span>' if context else ""
    st.markdown(
        f"""
        <div class="kpi-card">
          <div class="kpi-label">{label}</div>
          <div class="kpi-value-line"><span class="kpi-value">{value}</span>{context_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _window_label(frame: pd.DataFrame) -> str:
    start = pd.Timestamp(frame["timestamp"].iloc[0])
    end = pd.Timestamp(frame["timestamp"].iloc[-1]) + pd.Timedelta(minutes=1)
    return f"{start:%H:%M}–{end:%H:%M} · {len(frame)} min"


def _model_formula(model_id: str) -> None:
    if model_id == MODEL_SIMPLE:
        formula = (
            "<b>Modelo 1:</b> P = P<sub>STC</sub> · G<sub>ef</sub>/1000. "
            "Usa irradiância, potência nominal e quantidade de módulos."
        )
    elif model_id == MODEL_NOCT:
        formula = (
            "<b>Modelo 2:</b> Tc = Tamb + (NOCT − 20)·G<sub>ef</sub>/800; "
            "η(Tc) = η<sub>STC</sub>[1 + γ(Tc − 25)]; P = η·G<sub>ef</sub>·A."
        )
    else:
        formula = (
            "<b>Modelo 3:</b> resolve o circuito equivalente de um diodo, "
            "translada os cinco parâmetros para (G,Tc) e encontra o MPP minuto a minuto."
        )
    st.markdown(f'<div class="formula-box">{formula}</div>', unsafe_allow_html=True)


def _solar_status_chips(bundle: SimulationBundle) -> str:
    chips = []
    for model_id in MODEL_ORDER:
        available = model_id in bundle.solar_results_by_model
        chips.append(
            status_chip(
                ("● " if available else "○ ") + MODEL_SHORT_LABELS[model_id],
                "ok" if available else "warn",
            )
        )
    return '<div class="status-row">' + "".join(chips) + "</div>"


def _input_as_solar_profile(data: pd.DataFrame) -> pd.DataFrame:
    profile = pd.DataFrame(
        {"G": data["irradiancia_W_m2"].to_numpy(dtype=float)},
        index=pd.DatetimeIndex(data["timestamp"], name="timestamp"),
    )
    profile["Tamb"] = (
        data["temperatura_ambiente_C"].to_numpy(dtype=float)
        if "temperatura_ambiente_C" in data
        else np.nan
    )
    return profile


def render_overview(bundle: SimulationBundle) -> None:
    st.markdown(
        page_header(
            "Visão geral · Execução integrada",
            "PLATAFORMA DE GESTÃO DOS MODELOS H₂V",
            f"Uma entrada comum · {_window_label(bundle.input_data)} · atualização automática.",
        ),
        unsafe_allow_html=True,
    )
    data = bundle.overview
    has_load = "carga_total_kW" in data
    has_battery = bundle.battery_status.available
    solar_count = len(bundle.solar_results_by_model)

    st.markdown(
        f"""
        <div class="subsystem-grid">
          <div class="subsystem-card solar">
            <small>Fotovoltaico · Físico</small><b>{solar_count} de 3 estimadores disponíveis</b>
            <p>Curva operacional: {MODEL_SHORT_LABELS[bundle.solar_reference_model]}. Comparação completa preservada.</p>
          </div>
          <div class="subsystem-card fuel">
            <small>PEMFC / H₂ · {bundle.fuel_cell_status.fidelity}</small><b>{'Executado' if bundle.fuel_cell_status.available else 'Indisponível'}</b>
            <p>{bundle.fuel_cell_status.message}</p>
          </div>
          <div class="subsystem-card battery">
            <small>Bateria · {bundle.battery_status.fidelity}</small><b>{'Sinais ativos' if has_battery else 'Aguardando modelo'}</b>
            <p>{bundle.battery_status.message}</p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4, c5, c6 = st.columns(6, gap="small")
    c1.metric("Carga · pico", f"{data['carga_total_kW'].max():.1f} kW" if has_load else "Sem sinal")
    c2.metric("FV · energia", f"{bundle.solar_metrics['energy_kWh']:.3f} kWh")
    c3.metric("FV · pico", f"{bundle.solar_metrics['peak_power_kW']:.2f} kW")
    c4.metric("PEMFC · energia", f"{bundle.fuel_cell_metrics['energy_delivered_kWh']:.2f} kWh")
    c5.metric("H₂ · vazão máx.", f"{bundle.fuel_cell_metrics['max_hydrogen_kg_h']:.3f} kg/h")
    c6.metric("Bateria · SOC final", f"{data['soc_bateria_pct'].iloc[-1]:.1f}%" if has_battery else "Sintético off")

    if bundle.synthetic_signals_enabled:
        st.markdown(
            '<div class="notice warning-note"><strong>Camada demonstrativa ativa.</strong> '
            'A bateria, a carga ausente e a referência PEMFC ausente podem ser completadas com sinais sintéticos. '
            'Esses sinais não constituem modelos físicos validados.</div>',
            unsafe_allow_html=True,
        )

    power_col, balance_col = st.columns(2, gap="small")
    with power_col:
        with st.container(border=True, height="stretch"):
            _panel("Potências · Fontes, bateria e carga")
            _chart(overview_power_chart(data, height=285), "overview_power")
    with balance_col:
        with st.container(border=True, height="stretch"):
            _panel("Fechamento · Geração total x carga")
            _chart(system_balance_chart(data, height=285), "overview_balance")
            if has_load:
                imbalance = data["desbalanco_potencia_kW"]
                st.markdown(
                    f'<div class="balance-note"><strong>|ΔP| máx.</strong> {imbalance.abs().max():.2f} kW '
                    f'<span>·</span><strong>|ΔP| médio</strong> {imbalance.abs().mean():.2f} kW '
                    '<span>·</span>bateria: + descarga / − carga</div>',
                    unsafe_allow_html=True,
                )

    solar_col, share_col, battery_col = st.columns([1.45, .78, 1.1], gap="small")
    with solar_col:
        with st.container(border=True, height="stretch"):
            _panel("Solar · Três estimadores em paralelo")
            _chart(plot_comparison_power(bundle.solar_results_by_model, height=245), "overview_solar_models")
    with share_col:
        with st.container(border=True, height="stretch"):
            _panel("Participação · Energia")
            _chart(source_share_donut(data, height=245), "overview_share")
    with battery_col:
        with st.container(border=True, height="stretch"):
            _panel("Bateria · Potência e SOC")
            _chart(battery_chart(data, height=245), "overview_battery")

    st.markdown(
        """
        <div class="process-band">
          <div class="process-step process-input"><small>01 · ENTRADA COMUM</small><b>Uma janela para toda a EMS</b><span>timestamp · GHI · Tamb · demanda</span></div>
          <div class="process-arrow">→</div>
          <div class="process-step process-models"><small>02 · EXECUÇÃO AUTOMÁTICA</small><b>FV + PEMFC/H₂ + bateria</b><span>três estimadores internos no bloco solar</span></div>
          <div class="process-arrow">→</div>
          <div class="process-step process-output"><small>03 · SAÍDA INTEGRADA</small><b>Balanço e exportação rastreáveis</b><span>modelo, origem e maturidade explícitos</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.expander("Entenda o motor fotovoltaico e seus três níveis de cálculo"):
        visual, explanation = st.columns([.9, 1.1], gap="medium")
        with visual:
            st.image("assets/fluxo_fotovoltaico.jpg", width="stretch")
        with explanation:
            st.markdown(
                """
                **Modelo 1 · Irradiância**  
                Linha de continuidade: escala a potência STC pela irradiância efetiva.

                **Modelo 2 · NOCT + eficiência**  
                Acrescenta temperatura de célula e derating térmico do datasheet.

                **Modelo 3 · SDM**  
                Resolve o circuito equivalente de um diodo e o MPP em cada minuto.

                Os três usam exatamente o mesmo módulo, arranjo, perdas e janela. Se Tamb falhar,
                o Modelo 1 continua e os demais são marcados como indisponíveis.
                """
            )


def render_inputs(
    bundle: SimulationBundle,
    sample_path: Path,
    available_starts: list[pd.Timestamp],
) -> None:
    st.markdown(
        page_header(
            "Entrada · Configuração comum",
            "UMA ENTRADA PARA OS TRÊS SUBSISTEMAS",
            "Qualquer alteração válida recalcula automaticamente FV, PEMFC/H₂ e a camada sintética da bateria.",
        ),
        unsafe_allow_html=True,
    )

    title_col, system_col = st.columns([.43, 1.57], gap="small")
    with title_col:
        with st.container(border=True):
            _panel("Execução · Estado")
            st.markdown('<div class="model-page-title">ENTRADA<br>COMUM</div>', unsafe_allow_html=True)
            st.markdown(
                '<div class="notice"><strong>Automático.</strong> Não existe um botão separado por modelo. '
                'A janela ativa é enviada a todos no mesmo rerun.</div>',
                unsafe_allow_html=True,
            )
            st.markdown(_solar_status_chips(bundle), unsafe_allow_html=True)

    with system_col:
        with st.container(border=True):
            _panel("Sistema fotovoltaico · Datasheet compartilhado")
            module_keys = list(MODULE_DB.keys())
            st.selectbox(
                "Módulo fotovoltaico",
                module_keys,
                key="solar_module_key",
                help="Os três estimadores FV usam o mesmo datasheet.",
            )
            module = get_module(st.session_state["solar_module_key"])
            a1, a2, a3 = st.columns([.8, .8, 1.4])
            a1.number_input("Módulos em série", min_value=1, max_value=30, step=1, key="solar_n_series")
            a2.number_input("Strings em paralelo", min_value=1, max_value=30, step=1, key="solar_n_parallel")
            a3.slider("Perdas ópticas / sujeira [%]", 0.0, 20.0, step=.5, key="solar_soiling_pct")
            n_modules = int(st.session_state["solar_n_series"]) * int(st.session_state["solar_n_parallel"])
            installed_kwp = module.stc.p_nom * n_modules / 1000.0
            st.markdown(
                f"""
                <div class="datasheet-grid">
                  <div class="datasheet-item"><small>Potência STC</small><b>{module.stc.p_nom:.0f} W</b></div>
                  <div class="datasheet-item"><small>Eficiência STC</small><b>{module.stc.efficiency_stc*100:.2f} %</b></div>
                  <div class="datasheet-item"><small>Área</small><b>{module.stc.area:.3f} m²</b></div>
                  <div class="datasheet-item"><small>NOCT</small><b>{module.stc.noct:.1f} °C</b></div>
                  <div class="datasheet-item"><small>Arranjo</small><b>{st.session_state['solar_n_series']}S × {st.session_state['solar_n_parallel']}P</b></div>
                  <div class="datasheet-item"><small>Potência instalada</small><b>{installed_kwp:.3f} kWp</b></div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    source_col, contract_col = st.columns([1.2, .8], gap="small")
    with source_col:
        with st.container(border=True):
            _panel("Fonte dos dados · Janela temporal")
            source_mode = st.radio(
                "Fonte",
                ("CSV", "Perfil sintético"),
                horizontal=True,
                key="input_mode",
            )
            if source_mode == "CSV":
                uploaded = st.file_uploader(
                    "Carregar CSV comum",
                    type=["csv", "txt"],
                    help="Aceita vírgula ou ponto e vírgula e detecta aliases usuais.",
                    key=f"ems_csv_uploader_{st.session_state.get('input_uploader_generation', 0)}",
                )
                if uploaded is not None:
                    payload = uploaded.getvalue()
                    digest = hashlib.sha256(payload).hexdigest()
                    if digest != st.session_state.get("active_input_hash"):
                        try:
                            parsed = load_input_csv(payload)
                            starts = available_observation_starts(parsed)
                            if not starts:
                                raise ValueError("O arquivo não contém uma janela válida de 120 minutos.")
                        except ValueError as exc:
                            st.error(str(exc))
                        else:
                            st.session_state["input_dataframe"] = parsed
                            st.session_state["active_input_hash"] = digest
                            st.session_state["input_source_label"] = uploaded.name
                            st.session_state["observation_start"] = starts[0]
                            st.rerun()

                b1, b2 = st.columns(2)
                with b1:
                    st.download_button(
                        "Baixar exemplo EMS",
                        data=sample_path.read_bytes(),
                        file_name="entrada_padrao_ems.csv",
                        mime="text/csv",
                        width="stretch",
                    )
                with b2:
                    if st.button("Restaurar exemplo", width="stretch"):
                        restored = load_input_csv(sample_path)
                        starts = available_observation_starts(restored)
                        st.session_state["input_dataframe"] = restored
                        st.session_state["active_input_hash"] = "DEFAULT"
                        st.session_state["input_source_label"] = sample_path.name
                        st.session_state["observation_start"] = next(
                            (start for start in starts if start.hour == 15), starts[0]
                        )
                        st.session_state["input_uploader_generation"] += 1
                        st.rerun()
            else:
                d1, d2, d3 = st.columns(3)
                synthetic_date = d1.date_input("Data", value=date.today(), key="synthetic_date")
                duration = d2.selectbox(
                    "Fonte sintética",
                    (1440, 120),
                    format_func=lambda value: "24 h · selecionar janela" if value == 1440 else "120 min · janela direta",
                    key="synthetic_duration",
                )
                synthetic_time = d3.time_input(
                    "Hora inicial",
                    value=time(12, 0),
                    key="synthetic_time",
                    disabled=duration == 1440,
                )
                p1, p2 = st.columns(2)
                profile_options = ["Irradiância perfeita", "Día soleado", "Día nublado", "Día lluvioso"]
                profile_display = {
                    "Irradiância perfeita": "Irradiância perfeita · curva suave",
                    "Día soleado": "Dia ensolarado",
                    "Día nublado": "Dia nublado",
                    "Día lluvioso": "Dia chuvoso",
                }
                condition = p1.selectbox("Condição solar", profile_options, format_func=profile_display.get, key="synthetic_condition")
                season = p2.selectbox("Estação", list(PROFILES["seasons"]), key="synthetic_season")
                defaults = {
                    "Irradiância perfeita": PROFILES["g_peak_clear"],
                    "Día soleado": PROFILES["g_peak_clear"],
                    "Día nublado": PROFILES["g_peak_cloudy"],
                    "Día lluvioso": PROFILES["g_peak_rainy"],
                }
                season_cfg = PROFILES["seasons"][season]
                q1, q2, q3 = st.columns(3)
                g_peak = q1.number_input("GHI pico [W/m²]", 0.0, 1400.0, float(defaults[condition]), 10.0)
                t_min = q2.number_input("Temperatura mínima [°C]", value=float(season_cfg["t_min"]), step=.5)
                t_max = q3.number_input("Temperatura máxima [°C]", value=float(season_cfg["t_max"]), step=.5)
                if st.button("APLICAR PERFIL À ENTRADA COMUM", type="primary", width="stretch"):
                    if t_max < t_min:
                        st.error("A temperatura máxima deve ser maior ou igual à mínima.")
                    else:
                        start_time = time(0, 0) if duration == 1440 else synthetic_time
                        generated = build_synthetic_ems_profile(
                            start=pd.Timestamp.combine(synthetic_date, start_time),
                            irradiance_profile=condition,
                            season=season,
                            duration_minutes=int(duration),
                            g_peak=float(g_peak),
                            t_min=float(t_min),
                            t_max=float(t_max),
                        )
                        starts = available_observation_starts(generated)
                        st.session_state["input_dataframe"] = generated
                        st.session_state["active_input_hash"] = f"SYNTHETIC-{pd.Timestamp.now().value}"
                        st.session_state["input_source_label"] = f"Sintético · {profile_display[condition]}"
                        st.session_state["observation_start"] = starts[0]
                        st.rerun()

            st.selectbox(
                "Início da janela operacional",
                options=available_starts,
                key="observation_start",
                format_func=lambda ts: pd.Timestamp(ts).strftime("%d/%m/%Y · %H:%M → ")
                + (pd.Timestamp(ts) + pd.Timedelta(minutes=120)).strftime("%H:%M"),
            )
            st.toggle(
                "Ativar sinais sintéticos de carga, bateria e referência H₂ ausente",
                key="simulate_missing_signals",
                help="Não substitui os futuros modelos físicos. A origem permanece identificada.",
            )
            st.caption(
                f"Fonte ativa: {st.session_state.get('input_source_label', 'CSV padrão')} · "
                f"{len(st.session_state['input_dataframe']):,} registros disponíveis"
            )

    with contract_col:
        with st.container(border=True, height="stretch"):
            _panel("Contrato · O que cada subsistema recebe")
            schema = pd.DataFrame(
                [
                    ("timestamp", "Obrigatória", "Todos"),
                    ("irradiancia_W_m2", "Obrigatória", "FV · 3 estimadores"),
                    ("temperatura_ambiente_C", "Recomendada", "FV térmico + PEMFC"),
                    ("potencia_solicitada_fc_kW", "Opcional", "PEMFC/H₂"),
                    ("carga_total_kW", "Opcional", "Balanço + bateria"),
                ],
                columns=["Sinal", "Contrato", "Destino"],
            )
            st.dataframe(schema, hide_index=True, width="stretch", height=214)
            st.markdown(
                '<div class="notice"><strong>Modo degradado:</strong> sem Tamb, o estimador por irradiância continua; '
                'NOCT, SDM e PEMFC ficam explicitamente indisponíveis. Sem referência PEMFC, ela só é criada quando '
                'a camada sintética está ativada.</div>',
                unsafe_allow_html=True,
            )

    with st.container(border=True):
        _panel("Pré-visualização · Dados realmente enviados aos modelos")
        profile = _input_as_solar_profile(bundle.input_data)
        q1, q2, q3, q4 = st.columns(4)
        q1.metric("Linhas", len(profile))
        q2.metric("Passo", "1 min")
        q3.metric("GHI máxima", f"{profile['G'].max():.1f} W/m²")
        q4.metric("Temperatura", "Completa" if profile["Tamb"].notna().all() else "Ausente / parcial")
        _chart(plot_input_profile(profile), "input_profile")
        st.dataframe(bundle.input_data, hide_index=True, width="stretch", height=220)


def _render_solar_model(bundle: SimulationBundle) -> None:
    available = [model_id for model_id in MODEL_ORDER if model_id in bundle.solar_results_by_model]
    if st.session_state.get("selected_solar_model") not in available:
        st.session_state["selected_solar_model"] = bundle.solar_reference_model
    controls, main = st.columns([.62, 1.78], gap="small")
    with controls:
        with st.container(border=True):
            _panel("Solar · Resultados individuais")
            st.markdown('<div class="model-page-title">MOTOR FOTOVOLTAICO</div>', unsafe_allow_html=True)
        with st.container(border=True, height="stretch"):
            _panel("Configuração · Modelo analisado")
            selected = st.selectbox(
                "Modelo analisado",
                available,
                format_func=MODEL_LABELS.get,
                key="selected_solar_model",
            )
            st.markdown(
                f"""
                <div class="config-facts">
                  <div class="config-fact"><small>Módulo</small><b>{bundle.solar_module.stc.model}</b></div>
                  <div class="config-fact"><small>Janela</small><b>{_window_label(bundle.input_data)}</b></div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(_solar_status_chips(bundle), unsafe_allow_html=True)
            _model_formula(selected)

    result = bundle.solar_results_by_model[selected]
    kpi = bundle.solar_kpis_by_model[selected]
    with main:
        with st.container(border=True, height="stretch"):
            _panel("Síntese · Indicadores e curva principal")
            m1, m2, m3, m4, m5 = st.columns(5)
            with m1: _kpi_card("Energia", f"{kpi['energy_kWh']:.4f} kWh")
            with m2: _kpi_card("Potência máxima", f"{kpi['p_max_W']:.1f} W", f"{kpi['t_peak']:%H:%M}")
            with m3: _kpi_card("Potência média", f"{kpi['p_mean_W']:.1f} W")
            with m4: _kpi_card("Eficiência energética", f"{kpi['eta_energy']*100:.2f} %")
            tc = "Não utilizada" if np.isnan(kpi["tc_max_C"]) else f"{kpi['tc_max_C']:.2f} °C"
            with m5: _kpi_card("Tc máxima", tc)
            _chart(plot_model_power(result, selected, height=250), f"solar_power_{selected}")

    energy_col, thermal_col, efficiency_col = st.columns(3, gap="small")
    with energy_col:
        with st.container(border=True, height="stretch"):
            _panel("Energia · Acumulada")
            _chart(plot_cumulative_energy(result, selected), f"solar_energy_{selected}")
    with thermal_col:
        with st.container(border=True, height="stretch"):
            _panel("Comportamento térmico")
            if selected == MODEL_SIMPLE:
                st.markdown(
                    '<div class="compact-note"><b>Independente de temperatura</b>Este estimador não calcula Tc e '
                    'permanece disponível quando Tamb deixa de chegar.</div>',
                    unsafe_allow_html=True,
                )
            else:
                _chart(plot_temperatures(result), f"solar_temp_{selected}")
    with efficiency_col:
        with st.container(border=True, height="stretch"):
            _panel("Eficiência · Evolução")
            _chart(plot_efficiency(result, selected), f"solar_eff_{selected}")

    if selected == MODEL_SDM:
        peak_ts = result["P_array"].idxmax()
        peak = result.loc[peak_ts]
        with st.expander(f"Diagnóstico elétrico avançado do SDM · pico às {peak_ts:%H:%M}"):
            e1, e2, e3, e4 = st.columns(4)
            e1.metric("Vmp do arranjo", f"{peak['Vmp_array']:.2f} V")
            e2.metric("Imp do arranjo", f"{peak['Imp_array']:.3f} A")
            e3.metric("Voc do arranjo", f"{peak['Voc_array']:.2f} V")
            e4.metric("Fator de forma", f"{peak['FF']:.4f}")
            if peak["G_eff"] > 0:
                _chart(plot_iv_pv_at_peak(bundle.solar_module, result), "solar_iv_pv_peak")

    with st.expander(f"Ver tabela completa do estimador ({len(result)} linhas)"):
        preferred = ["G", "G_eff", "Tamb", "Tc", "P_module", "P_array", "eta", "Vmp", "Imp", "Voc", "Isc", "FF"]
        columns = [column for column in preferred if column in result]
        display = result[columns].copy()
        display.index = display.index.strftime("%Y-%m-%d %H:%M:%S")
        st.dataframe(display, width="stretch", height=310)


def render_models(bundle: SimulationBundle, fuel_cell_model) -> None:
    st.markdown(
        page_header(
            "Modelos · Resultados individuais",
            "BLOCOS CONECTADOS À EMS",
            "O motor solar é físico e multimodelo; PEMFC/H₂ permanece preliminar e a bateria permanece sintética.",
        ),
        unsafe_allow_html=True,
    )
    solar_tab, fuel_tab, battery_tab = st.tabs(["☀️ Solar · 3 estimadores", "💧 PEMFC / H₂", "🔋 Bateria"])
    with solar_tab:
        _render_solar_model(bundle)
    with fuel_tab:
        st.markdown(
            f'<div class="notice"><strong>Maturidade: {bundle.fuel_cell_status.fidelity}.</strong> '
            f'{bundle.fuel_cell_status.message} Não representa validação experimental da embarcação.</div>',
            unsafe_allow_html=True,
        )
        if not bundle.fuel_cell_status.available:
            st.markdown(
                '<div class="construction"><div><div class="icon">💧</div><h3>PEMFC indisponível nesta janela</h3>'
                f'<p>{bundle.fuel_cell_status.message}</p></div></div>',
                unsafe_allow_html=True,
            )
        else:
            f1, f2, f3, f4 = st.columns(4)
            f1.metric("Pico entregue", f"{bundle.fuel_cell_metrics['peak_delivered_kW']:.2f} kW")
            f2.metric("Energia entregue", f"{bundle.fuel_cell_metrics['energy_delivered_kWh']:.2f} kWh")
            f3.metric("Eficiência média", f"{bundle.fuel_cell_metrics['mean_efficiency_pct']:.2f}%")
            f4.metric("Vazão H₂ máxima", f"{bundle.fuel_cell_metrics['max_hydrogen_kg_h']:.3f} kg/h")
            with st.container(border=True):
                _panel("Potência · Solicitação e entrega")
                _chart(fuel_cell_power_chart(bundle.fuel_cell_output, height=300), "fuel_power")
            c1, c2 = st.columns(2, gap="small")
            with c1:
                with st.container(border=True):
                    _panel("Elétrico · Corrente e tensão")
                    _chart(fuel_cell_electrical_chart(bundle.fuel_cell_output), "fuel_electrical")
            with c2:
                with st.container(border=True):
                    _panel("Recursos · H₂ e eficiência")
                    _chart(fuel_cell_resources_chart(bundle.fuel_cell_output), "fuel_resources")
            d1, d2 = st.columns(2)
            with d1: _download(bundle.fuel_cell_input, "Baixar entrada PEMFC", "entrada_pemfc.csv", "fuel_input_download")
            with d2: _download(bundle.fuel_cell_output, "Baixar saída PEMFC", "saida_pemfc.csv", "fuel_output_download")
            with st.expander("Parâmetros dinâmicos e limites operacionais"):
                p1, p2 = st.tabs(["Dinâmica", "Limites"])
                with p1:
                    table = fuel_cell_model.dynamic_parameters_table().copy()
                    table["value"] = table["value"].map(str)
                    st.dataframe(table, hide_index=True, width="stretch")
                with p2:
                    st.dataframe(fuel_cell_model.static_model.operating_limits_table(), hide_index=True, width="stretch")
    with battery_tab:
        if bundle.battery_status.available:
            st.markdown(
                '<div class="notice warning-note"><strong>Sinais sintéticos.</strong> Potência e SOC servem somente '
                'para validar o fluxo da EMS; não há modelo eletroquímico de bateria nesta versão.</div>',
                unsafe_allow_html=True,
            )
            data = bundle.overview
            b1, b2, b3, b4 = st.columns(4)
            b1.metric("SOC inicial", f"{data['soc_bateria_pct'].iloc[0]:.1f}%")
            b2.metric("SOC final", f"{data['soc_bateria_pct'].iloc[-1]:.1f}%")
            b3.metric("Descarga máxima", f"{data['potencia_bateria_kW'].max():.2f} kW")
            b4.metric("Carga máxima", f"{abs(data['potencia_bateria_kW'].min()):.2f} kW")
            _chart(battery_chart(data, height=330), "battery_model")
            _download(data[["timestamp", "potencia_bateria_kW", "soc_bateria_pct"]], "Baixar sinais sintéticos", "bateria_sintetica.csv", "battery_download")
        else:
            st.markdown(
                '<div class="construction"><div><div class="icon">🔋</div><h3>Modelo físico em construção</h3>'
                '<p>Ative a camada sintética na Entrada para validar potência, SOC e o balanço sem confundir esses sinais com um modelo real.</p></div></div>',
                unsafe_allow_html=True,
            )


def _comparison_table(bundle: SimulationBundle) -> pd.DataFrame:
    rows = []
    for model_id in MODEL_ORDER:
        if model_id not in bundle.solar_results_by_model:
            continue
        kpi = bundle.solar_kpis_by_model[model_id]
        rows.append(
            {
                "Modelo": MODEL_LABELS[model_id],
                "Energia [kWh]": kpi["energy_kWh"],
                "Pico [W]": kpi["p_max_W"],
                "Média [W]": kpi["p_mean_W"],
                "Eficiência [%]": kpi["eta_energy"] * 100.0,
                "PR [-]": kpi["PR"],
                "Tc máxima [°C]": kpi["tc_max_C"],
            }
        )
    return pd.DataFrame(rows)


def render_solar_comparison(bundle: SimulationBundle) -> None:
    st.markdown(
        page_header(
            "Comparação solar · Consistência multimodelo",
            "TRÊS FORMULAÇÕES · UMA MESMA ENTRADA",
            "As diferenças vêm do modelo matemático; datasheet, arranjo e janela permanecem idênticos.",
        ),
        unsafe_allow_html=True,
    )
    results = bundle.solar_results_by_model
    available = [model_id for model_id in MODEL_ORDER if model_id in results]
    if st.session_state.get("comparison_reference_model") not in available:
        st.session_state["comparison_reference_model"] = bundle.solar_reference_model
    energies = [bundle.solar_kpis_by_model[mid]["energy_kWh"] for mid in available]
    peaks = [bundle.solar_kpis_by_model[mid]["p_max_W"] for mid in available]
    energy_spread = max(energies) - min(energies)
    energy_spread_pct = energy_spread / np.mean(energies) * 100.0 if np.mean(energies) else 0.0

    controls, main = st.columns([.62, 1.78], gap="small")
    with controls:
        with st.container(border=True):
            _panel("Comparação · Referência")
            st.markdown('<div class="model-page-title">COMPARAÇÃO FV</div>', unsafe_allow_html=True)
        with st.container(border=True, height="stretch"):
            reference = st.selectbox("Modelo de referência", available, format_func=MODEL_LABELS.get, key="comparison_reference_model")
            st.markdown(_solar_status_chips(bundle), unsafe_allow_html=True)
            st.markdown(
                f'<div class="formula-box"><b>Referência: {MODEL_SHORT_LABELS[reference]}.</b><br>'
                'ΔP = (P<sub>modelo</sub> − P<sub>referência</sub>) / P<sub>referência</sub> × 100.</div>',
                unsafe_allow_html=True,
            )
    with main:
        with st.container(border=True, height="stretch"):
            _panel("Síntese · Indicadores e potência")
            q1, q2, q3, q4 = st.columns(4)
            with q1: _kpi_card("Modelos comparados", str(len(available)))
            with q2: _kpi_card("Dispersão de energia", f"{energy_spread:.4f} kWh", f"{energy_spread_pct:.2f}%")
            with q3: _kpi_card("Dispersão de pico", f"{max(peaks)-min(peaks):.1f} W")
            with q4: _kpi_card("Janela", "120 min", "passo 1 min")
            _chart(plot_comparison_power(results, height=250), "comparison_power")

    difference = plot_difference_to_reference(results, reference)
    c1, c2, c3 = st.columns(3, gap="small")
    with c1:
        with st.container(border=True, height="stretch"):
            _panel("Energia · Acumulada")
            _chart(plot_comparison_energy(results), "comparison_energy")
    with c2:
        with st.container(border=True, height="stretch"):
            _panel("Eficiência · Sobreposição")
            _chart(plot_comparison_efficiency(results), "comparison_efficiency")
    with c3:
        with st.container(border=True, height="stretch"):
            _panel(f"Diferença vs {MODEL_SHORT_LABELS[reference]}")
            if difference is None:
                st.info("É necessário haver pelo menos dois estimadores disponíveis.")
            else:
                _chart(difference, f"comparison_difference_{reference}")
    with st.expander("Síntese numérica · Indicadores comparáveis"):
        st.dataframe(_comparison_table(bundle), hide_index=True, width="stretch")
        st.caption("A comparação ajuda a detectar divergências; a exatidão final deve ser validada contra potência medida.")


def render_export(bundle: SimulationBundle) -> None:
    st.markdown(
        page_header(
            "Exportação · Saída configurável",
            "CSV PARA O OTIMIZADOR E O GÊMEO DIGITAL",
            "Exporte o EMS integrado, qualquer estimador solar, a PEMFC ou os sinais sintéticos de bateria.",
        ),
        unsafe_allow_html=True,
    )
    source_options = ["EMS integrado"]
    source_options += [f"Solar · {MODEL_SHORT_LABELS[mid]}" for mid in MODEL_ORDER if mid in bundle.solar_results_by_model]
    if bundle.fuel_cell_status.available:
        source_options.append("PEMFC / H₂")
    if bundle.battery_status.available:
        source_options.append("Bateria sintética")

    left, right = st.columns([.78, 1.42], gap="small")
    with left:
        with st.container(border=True):
            _panel("Configuração do arquivo")
            source = st.selectbox("Fonte exportada", source_options, key="export_source")
            solar_id = None
            if source.startswith("Solar ·"):
                short = source.split("·", 1)[1].strip()
                solar_id = next(mid for mid in MODEL_ORDER if MODEL_SHORT_LABELS[mid] == short)
                result = bundle.solar_results_by_model[solar_id]
                available_columns = available_export_columns(result)
                defaults = [column for column in DEFAULT_EXPORT_COLUMNS if column in available_columns]
                selected_columns = st.multiselect("Colunas incluídas", available_columns, default=defaults, key=f"solar_export_cols_{solar_id}")
                export_df = build_export_dataframe(result, selected_columns) if selected_columns else pd.DataFrame()
                default_name = f"modelo_solar_{solar_id}_120min"
            else:
                if source == "EMS integrado":
                    base = bundle.overview.copy()
                    default_name = "ems_integrado_120min"
                elif source == "PEMFC / H₂":
                    base = bundle.fuel_cell_output.copy()
                    default_name = "pemfc_h2_120min"
                else:
                    base = bundle.overview[["timestamp", "potencia_bateria_kW", "soc_bateria_pct"]].copy()
                    default_name = "bateria_sintetica_120min"
                selected_columns = st.multiselect("Colunas incluídas", list(base.columns), default=list(base.columns), key=f"generic_export_cols_{source}")
                export_df = base[selected_columns].copy() if selected_columns else pd.DataFrame()

            file_name = st.text_input("Nome do arquivo", value=default_name, key=f"export_name_{source}")
            separator_label = st.selectbox("Separador", ("Vírgula (,)", "Ponto e vírgula (;)") )
            decimal_label = st.selectbox("Separador decimal", ("Ponto (.)", "Vírgula (,)") )
            separator = ";" if ";" in separator_label else ","
            decimal = "," if "Vírgula" in decimal_label else "."
            final_name = normalize_filename(file_name, default_name)
            st.markdown(
                '<div class="status-row">'
                + status_chip(f"{len(export_df)} linhas", "ok")
                + status_chip(f"{len(export_df.columns)} colunas", "info")
                + "</div>",
                unsafe_allow_html=True,
            )
    with right:
        with st.container(border=True):
            _panel("Pré-visualização · Arquivo final")
            if export_df.empty or not len(export_df.columns):
                st.warning("Selecione pelo menos uma coluna para gerar o arquivo.")
                return
            st.dataframe(export_df, hide_index=not isinstance(export_df.index, pd.DatetimeIndex), width="stretch", height=340)
            csv_bytes = export_df.to_csv(index=False, sep=separator, decimal=decimal, float_format="%.6f").encode("utf-8-sig")
            st.download_button("⬇️ BAIXAR CSV", data=csv_bytes, file_name=final_name, mime="text/csv", type="primary", width="stretch")


def render_optimizer() -> None:
    st.markdown(
        page_header(
            "Otimizador · Camada de despacho",
            "CONEXÃO PREPARADA PARA O MODELO DA MARÍLIA",
            "Receberá a mesma janela integrada e devolverá referências ótimas para cada fonte.",
        ),
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="construction"><div><div class="icon">🧭</div><h3>Otimizador em implementação</h3>'
        '<p>A interface já organiza previsão FV, carga, estado sintético da bateria e restrições preliminares da PEMFC. '
        'A saída futura substituirá as referências demonstrativas sem alterar o contrato da entrada.</p></div></div>',
        unsafe_allow_html=True,
    )


def render_settings(bundle: SimulationBundle) -> None:
    st.markdown(
        page_header(
            "Configurações · Diagnóstico",
            "MATURIDADE, CONTRATOS E ESTADO DOS MODELOS",
            "Nenhum sinal sintético é apresentado como modelo físico concluído.",
        ),
        unsafe_allow_html=True,
    )
    with st.container(border=True):
        _panel("Estado atual · Camadas do sistema")
        table = pd.DataFrame(
            [
                ("Solar · Irradiância", "Físico simplificado", "Disponível" if MODEL_SIMPLE in bundle.solar_results_by_model else "Indisponível"),
                ("Solar · NOCT + eficiência", "Físico térmico", "Disponível" if MODEL_NOCT in bundle.solar_results_by_model else "Indisponível"),
                ("Solar · SDM", "Físico elétrico", "Disponível" if MODEL_SDM in bundle.solar_results_by_model else "Indisponível"),
                ("PEMFC / H₂", bundle.fuel_cell_status.fidelity.title(), "Disponível" if bundle.fuel_cell_status.available else "Indisponível"),
                ("Bateria", bundle.battery_status.fidelity.title(), "Sinais ativos" if bundle.battery_status.available else "Não implementado"),
                ("Otimizador", "Em implementação", "Aguardando integração"),
            ],
            columns=["Bloco", "Maturidade", "Estado"],
        )
        st.dataframe(table, hide_index=True, width="stretch")
    c1, c2 = st.columns(2, gap="small")
    with c1:
        with st.container(border=True, height="stretch"):
            _panel("Hipóteses operacionais")
            st.markdown(
                """
                - Janela ativa fixa de 120 minutos, passo de 1 minuto.
                - Arranjo padrão 2S × 3P, módulo CS7L-580MS.
                - SDM com MPPT ideal; inversor e conversor ainda fora do bloco FV.
                - PEMFC Horizon equivalente indicada somente para estudos preliminares.
                """
            )
    with c2:
        with st.container(border=True, height="stretch"):
            _panel("Próximas substituições")
            st.markdown(
                """
                - Modelo eletroquímico definitivo da bateria.
                - Estado físico do tanque e cadeia completa de H₂.
                - Otimizador de despacho da Marília.
                - Modelo de propulsão, velocidade e consumo da embarcação.
                """
            )
