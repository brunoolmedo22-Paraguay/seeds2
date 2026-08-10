"""Páginas da aplicação EMS."""

from __future__ import annotations

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
    input_weather_chart,
    overview_power_chart,
    system_balance_chart,
    pv_forecast_chart,
    solar_efficiency_chart,
    source_energy_shares,
    source_share_donut,
)
from ems_app.data_pipeline import (
    available_observation_start_hours,
    dataframe_to_csv_bytes,
    load_input_csv,
)
from ems_app.model_runner import SimulationBundle
from ems_app.style import page_header
from ems_core.solar.simulation.automation import build_fixed_automation_module


def _section(text: str) -> None:
    st.markdown(f'<div class="section-label">{text}</div>', unsafe_allow_html=True)


def _download(frame: pd.DataFrame, label: str, filename: str, key: str) -> None:
    st.download_button(
        label,
        data=dataframe_to_csv_bytes(frame),
        file_name=filename,
        mime="text/csv",
        key=key,
        width="stretch",
    )


def render_overview(bundle: SimulationBundle) -> None:
    window_start = pd.Timestamp(bundle.input_data["timestamp"].iloc[0])
    window_end = window_start + pd.Timedelta(minutes=120)
    st.markdown(
        page_header(
            "Visão geral do sistema",
            "Monitoramento integrado · "
            f"{window_start:%H:%M} → {window_end:%H:%M} · 120 minutos, ponto a ponto.",
        ),
        unsafe_allow_html=True,
    )
    data = bundle.overview
    has_load = "carga_total_kW" in data
    has_battery = "potencia_bateria_kW" in data

    # KPIs compactos: mantemos a leitura instantânea sem consumir uma faixa alta
    # do dashboard.
    c1, c2, c3, c4, c5 = st.columns(5, gap="small")
    c1.metric(
        "Carga · pico",
        f"{data['carga_total_kW'].max():.1f} kW" if has_load else "Aguardando",
    )
    c2.metric("FV · energia", f"{bundle.solar_metrics['energy_kWh']:.2f} kWh")
    c3.metric("FV · pico", f"{bundle.solar_metrics['peak_power_kW']:.2f} kW")
    c4.metric("PEMFC · energia", f"{bundle.fuel_cell_metrics['energy_delivered_kWh']:.2f} kWh")
    c5.metric(
        "Bateria · SOC final",
        f"{data['soc_bateria_pct'].iloc[-1]:.1f}%" if has_battery else "Em integração",
    )

    if bundle.synthetic_signals_enabled:
        st.markdown(
            '<div class="notice"><strong>Modo demonstrativo.</strong> '
            'Carga e bateria são sinais sintéticos para validar o fechamento do EMS; FV e PEMFC continuam vindo dos modelos.</div>',
            unsafe_allow_html=True,
        )

    # Os dois gráficos que explicam o sistema ficam lado a lado para reduzir
    # drasticamente a verticalidade da página.
    power_col, balance_col = st.columns(2, gap="medium")
    with power_col:
        _section("Potências do sistema · fontes, bateria e carga")
        st.plotly_chart(
            overview_power_chart(data, height=300),
            width="stretch",
            key="overview_power",
        )

    with balance_col:
        _section("Fechamento do balanço · geração total x carga")
        st.plotly_chart(
            system_balance_chart(data, height=300),
            width="stretch",
            key="overview_balance",
        )
        if has_load:
            # Calcula localmente para manter compatibilidade com bundles antigos
            # eventualmente preservados pelo cache do Streamlit Cloud.
            battery_power = (
                pd.to_numeric(data["potencia_bateria_kW"], errors="coerce").fillna(0.0)
                if "potencia_bateria_kW" in data
                else pd.Series(0.0, index=data.index)
            )
            generation_total = (
                pd.to_numeric(data["potencia_fv_kW"], errors="coerce").fillna(0.0)
                + pd.to_numeric(data["potencia_fc_entregue_kW"], errors="coerce").fillna(0.0)
                + battery_power
            )
            imbalance = generation_total - pd.to_numeric(
                data["carga_total_kW"], errors="coerce"
            ).fillna(0.0)
            max_abs_imbalance = float(imbalance.abs().max())
            mean_abs_imbalance = float(imbalance.abs().mean())
            st.markdown(
                f'<div class="balance-note"><strong>|ΔP| máx.</strong> {max_abs_imbalance:.2f} kW '
                f'<span>·</span> <strong>|ΔP| médio</strong> {mean_abs_imbalance:.2f} kW '
                f'<span>·</span> bateria: + descarga / − carga</div>',
                unsafe_allow_html=True,
            )

    shares = source_energy_shares(data)
    dominant_source = max(shares, key=shares.get)
    dominant_share = shares[dominant_source]
    share_items = "".join(
        f"<li><span>{name}</span><strong>{value:.1f}%</strong></li>"
        for name, value in shares.items()
    )

    # Segunda faixa compacta: participação, leitura e bateria na mesma linha.
    donut_col, reading_col, battery_col = st.columns([0.85, 1.0, 1.45], gap="medium")
    with donut_col:
        _section("Participação · energia")
        st.plotly_chart(
            source_share_donut(data, height=260),
            width="stretch",
            key="overview_share",
        )
    with reading_col:
        _section("Leitura rápida")
        st.markdown(
            f"""
            <div class="quick-read quick-read-compact">
              <span class="quick-kicker">Fonte principal</span>
              <h3>{dominant_source}</h3>
              <p><strong>{dominant_share:.1f}%</strong> da energia positiva fornecida.</p>
              <ul>{share_items}</ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with battery_col:
        _section("Bateria · potência e SOC")
        st.plotly_chart(
            battery_chart(data, height=260),
            width="stretch",
            key="overview_battery",
        )

    # Detalhe dos dois modelos ativos, também lado a lado e com menor altura.
    left, right = st.columns(2, gap="medium")
    with left:
        _section("Fotovoltaica · previsão de geração")
        st.plotly_chart(
            pv_forecast_chart(bundle.solar_output, height=285),
            width="stretch",
            key="overview_pv",
        )
    with right:
        _section("PEMFC · solicitação e potência entregue")
        st.plotly_chart(
            fuel_cell_power_chart(bundle.fuel_cell_output, height=285),
            width="stretch",
            key="overview_fc",
        )


def render_inputs(
    bundle: SimulationBundle,
    sample_path: Path,
    available_hours: list[int],
) -> None:
    st.markdown(
        page_header(
            "Entradas",
            "Leitura por CSV nesta etapa; o mesmo contrato poderá ser alimentado pela API futuramente.",
            "CSV conectado",
        ),
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.05, 1.35])
    with left:
        _section("Fonte de dados")
        st.selectbox(
            "Hora inicial da janela",
            options=available_hours,
            format_func=lambda hour: f"{hour:02d}:00 → {hour + 2:02d}:00",
            key="observation_start_hour",
            help="A app sempre processa os 120 minutos seguintes, com resolução de 1 minuto.",
        )
        uploaded = st.file_uploader(
            "Carregar CSV da EMS",
            type=["csv", "txt"],
            help="Aceita separador vírgula ou ponto e vírgula.",
            key=f"ems_csv_uploader_{st.session_state.get('input_uploader_generation', 0)}",
        )
        if uploaded is not None:
            payload = uploaded.getvalue()
            digest = hashlib.sha256(payload).hexdigest()
            if digest != st.session_state.get("active_input_hash"):
                try:
                    parsed = load_input_csv(payload)
                except ValueError as exc:
                    st.error(str(exc))
                else:
                    uploaded_hours = available_observation_start_hours(parsed)
                    if not uploaded_hours:
                        st.error("O CSV precisa cobrir pelo menos 120 minutos consecutivos.")
                        return
                    st.session_state["input_dataframe"] = parsed
                    st.session_state["active_input_hash"] = digest
                    st.session_state["input_source_label"] = uploaded.name
                    if st.session_state["observation_start_hour"] not in uploaded_hours:
                        st.session_state["observation_start_hour"] = uploaded_hours[0]
                    st.rerun()

        b1, b2 = st.columns(2)
        with b1:
            st.download_button(
                "Baixar janela ativa",
                data=dataframe_to_csv_bytes(bundle.input_data),
                file_name=(
                    f"entrada_ems_{st.session_state['observation_start_hour']:02d}h_120min.csv"
                ),
                mime="text/csv",
                width="stretch",
            )
        with b2:
            if st.button("Restaurar exemplo", width="stretch"):
                st.session_state["input_dataframe"] = load_input_csv(sample_path)
                st.session_state["active_input_hash"] = "DEFAULT"
                st.session_state["input_source_label"] = "entrada_padrao_ems.csv"
                st.session_state["observation_start_hour"] = 15
                st.session_state["input_uploader_generation"] = (
                    int(st.session_state.get("input_uploader_generation", 0)) + 1
                )
                st.rerun()

        st.checkbox(
            "Simular carga e bateria ainda indisponíveis",
            key="simulate_missing_signals",
            help="Gera sinais demonstrativos para completar o dashboard. Não substitui o futuro modelo de bateria.",
        )
        st.caption(
            f"Fonte ativa: {st.session_state.get('input_source_label', 'CSV padrão')} · "
            f"{len(st.session_state['input_dataframe']):,} registros disponíveis"
        )

    with right:
        _section("Contrato mínimo do CSV")
        schema = pd.DataFrame(
            [
                ("timestamp", "data/hora", "2026-08-10 09:00:00"),
                ("irradiancia_W_m2", "W/m²", "650"),
                ("temperatura_ambiente_C", "°C", "27.5"),
                ("potencia_solicitada_fc_kW", "kW", "24.0"),
            ],
            columns=["Coluna", "Unidade", "Exemplo"],
        )
        st.dataframe(schema, hide_index=True, width="stretch")
        st.caption(
            "Opcional: carga_total_kW, FC_enable, T_coolant_in_C e V_bus_V. "
            "Também são aceitos aliases simples como irrad, temp e P_FC_requested_kW."
        )

    _section("Pré-visualização dos dados normalizados")
    start = pd.Timestamp(bundle.input_data["timestamp"].iloc[0])
    end = start + pd.Timedelta(minutes=120)
    st.markdown(
        f'<div class="notice"><strong>Janela ativa: {start:%H:%M} → {end:%H:%M}.</strong> '
        f'Os dois modelos receberam exatamente {len(bundle.input_data)} pontos, um por minuto.</div>',
        unsafe_allow_html=True,
    )
    st.dataframe(bundle.input_data, hide_index=True, width="stretch", height=250)
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(input_weather_chart(bundle.input_data), width="stretch", key="input_weather")
    with c2:
        display = bundle.input_data.copy()
        if "carga_total_kW" not in display and "carga_total_kW" in bundle.overview:
            display["carga_total_kW"] = bundle.overview["carga_total_kW"]
        st.plotly_chart(input_power_chart(display), width="stretch", key="input_power")


def _solar_parameters_table() -> pd.DataFrame:
    module = build_fixed_automation_module()
    stc = module.stc
    sdm = module.sdm
    rows = [
        ("Fabricante / modelo", f"{stc.manufacturer} · {stc.model}", "-"),
        ("Potência nominal do módulo", stc.p_nom, "W"),
        ("Tensão MPP em STC", stc.v_mp, "V"),
        ("Corrente MPP em STC", stc.i_mp, "A"),
        ("NOCT", stc.noct, "°C"),
        ("IL de referência", sdm.IL_ref, "A"),
        ("I0 de referência", sdm.I0_ref, "A"),
        ("Resistência série", sdm.Rs, "Ω"),
        ("Resistência shunt", sdm.Rsh_ref, "Ω"),
        ("Fator de idealidade", sdm.n, "-"),
    ]
    frame = pd.DataFrame(rows, columns=["Parâmetro", "Valor", "Unidade"])
    frame["Valor"] = frame["Valor"].map(str)
    return frame


def render_models(bundle: SimulationBundle, fuel_cell_model) -> None:
    st.markdown(
        page_header(
            "Modelos",
            "Entradas, saídas, curvas e parâmetros dos modelos conectados à EMS.",
        ),
        unsafe_allow_html=True,
    )
    solar_tab, fc_tab, battery_tab = st.tabs(
        ["☀️ Solar", "💧 Célula a combustível", "🔋 Bateria"]
    )

    with solar_tab:
        st.markdown(
            '<div class="notice"><strong>Modelo ativo:</strong> Single Diode Model (SDM), '
            'operação no MPP e temperatura de célula pelo método NOCT. Configuração padrão '
            'Canadian Solar CS7L-580MS.</div>',
            unsafe_allow_html=True,
        )
        _section("Configuração do arranjo")
        a, b, c = st.columns(3)
        a.number_input("Módulos em série", min_value=1, max_value=100, step=1, key="solar_n_series")
        b.number_input("Strings em paralelo", min_value=1, max_value=200, step=1, key="solar_n_parallel")
        c.number_input(
            "Perdas por sujidade (%)", min_value=0.0, max_value=30.0, step=0.5,
            key="solar_soiling_pct",
        )

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Potência instalada", f"{bundle.solar_metrics['installed_power_kW']:.2f} kWp")
        m2.metric("Energia prevista", f"{bundle.solar_metrics['energy_kWh']:.2f} kWh")
        m3.metric("Eficiência média ativa", f"{bundle.solar_metrics['mean_efficiency_pct']:.2f}%")
        m4.metric("Área do arranjo", f"{bundle.solar_metrics['array_area_m2']:.1f} m²")

        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(pv_forecast_chart(bundle.solar_output), width="stretch", key="model_solar_power")
        with c2:
            st.plotly_chart(solar_efficiency_chart(bundle.solar_output), width="stretch", key="model_solar_efficiency")

        d1, d2 = st.columns(2)
        with d1:
            _download(bundle.solar_input, "Baixar entrada do modelo solar", "entrada_modelo_solar.csv", "solar_input_download")
        with d2:
            _download(bundle.solar_output, "Baixar saída do modelo solar", "saida_modelo_solar.csv", "solar_output_download")

        with st.expander("Ver parâmetros técnicos do modelo solar"):
            st.dataframe(_solar_parameters_table(), hide_index=True, width="stretch")

    with fc_tab:
        st.markdown(
            '<div class="notice"><strong>Modelo ativo:</strong> sistema Horizon VLIIPro50-22 aproximado '
            '(stack equivalente ≈65–66 kW), com balance of plant, inversão de potência, estados, rampas '
            'e consumo de H₂. Uso indicado para estudos preliminares de EMS.</div>',
            unsafe_allow_html=True,
        )
        _section("Configuração temporal")
        st.metric("Resolução de integração nesta app", "60 s · 1 ponto/min")
        f1, f2, f3, f4 = st.columns(4)
        f1.metric("Potência entregue · pico", f"{bundle.fuel_cell_metrics['peak_delivered_kW']:.2f} kW")
        f2.metric("Energia entregue", f"{bundle.fuel_cell_metrics['energy_delivered_kWh']:.2f} kWh")
        f3.metric("Eficiência líquida média", f"{bundle.fuel_cell_metrics['mean_efficiency_pct']:.2f}%")
        f4.metric("Vazão H₂ · máxima", f"{bundle.fuel_cell_metrics['max_hydrogen_kg_h']:.3f} kg/h")

        st.plotly_chart(fuel_cell_power_chart(bundle.fuel_cell_output, height=360), width="stretch", key="model_fc_power")
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(fuel_cell_electrical_chart(bundle.fuel_cell_output), width="stretch", key="model_fc_electrical")
        with c2:
            st.plotly_chart(fuel_cell_resources_chart(bundle.fuel_cell_output), width="stretch", key="model_fc_resources")

        d1, d2 = st.columns(2)
        with d1:
            _download(bundle.fuel_cell_input, "Baixar entrada do modelo PEMFC", "entrada_modelo_pemfc.csv", "fc_input_download")
        with d2:
            _download(bundle.fuel_cell_output, "Baixar saída completa do modelo PEMFC", "saida_modelo_pemfc.csv", "fc_output_download")

        with st.expander("Ver parâmetros dinâmicos e limites operacionais"):
            p1, p2 = st.tabs(["Dinâmica", "Limites"])
            with p1:
                dynamic_parameters = fuel_cell_model.dynamic_parameters_table().copy()
                dynamic_parameters["value"] = dynamic_parameters["value"].map(str)
                st.dataframe(dynamic_parameters, hide_index=True, width="stretch")
            with p2:
                st.dataframe(
                    fuel_cell_model.static_model.operating_limits_table(),
                    hide_index=True,
                    width="stretch",
                )

    with battery_tab:
        st.markdown(
            '<div class="construction"><div><div class="icon">🔋</div>'
            '<h3>Modelo de bateria em construção</h3>'
            '<p>A interface já reserva potência, SOC, energia e limites operacionais. '
            'Até a implementação do modelo físico, os sinais sintéticos servem apenas para validar o monitoramento.</p>'
            '</div></div>',
            unsafe_allow_html=True,
        )


def render_optimizer() -> None:
    st.markdown(
        page_header(
            "Otimizador",
            "Camada de despacho ótimo desenvolvida pela Marília e preparada para conexão aos modelos.",
            "Em implementação",
        ),
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="construction"><div><div class="icon">🧭</div>'
        '<h3>Otimizador em implementação</h3>'
        '<p>Esta página receberá carga total, previsão FV, estado da bateria e restrições da PEMFC; '
        'devolverá as referências ótimas de potência para cada fonte.</p>'
        '</div></div>',
        unsafe_allow_html=True,
    )


def render_settings() -> None:
    st.markdown(
        page_header(
            "Configurações",
            "Cenários, cargas, ativos e contratos de comunicação da aplicação.",
            "Em construção",
        ),
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="construction"><div><div class="icon">⚙️</div>'
        '<h3>Configurações em construção</h3>'
        '<p>A estrutura será usada para transformar a mesma EMS em uma aplicação configurável '
        'para diferentes embarcações, cargas, arranjos FV, stacks PEMFC e bancos de baterias.</p>'
        '</div></div>',
        unsafe_allow_html=True,
    )
