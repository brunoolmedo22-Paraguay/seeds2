"""Gráficos Plotly padronizados para a interface de monitoramento."""

from __future__ import annotations

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


COLORS = {
    "navy": "#17324D",
    "blue": "#2878B5",
    "cyan": "#31A6B8",
    "solar": "#F2B84B",
    "fuel": "#16A085",
    "battery": "#7B61A8",
    "load": "#334E68",
    "temperature": "#D96C5F",
    "grid": "rgba(23, 50, 77, 0.10)",
    "muted": "#6B7C8F",
}


def _style(fig: go.Figure, *, height: int = 360, hovermode: str = "x unified") -> go.Figure:
    fig.update_layout(
        template="plotly_white",
        height=height,
        hovermode=hovermode,
        margin={"l": 16, "r": 16, "t": 28, "b": 16},
        font={"family": "Inter, system-ui, sans-serif", "color": COLORS["navy"]},
        legend={"orientation": "h", "y": 1.03, "yanchor": "bottom", "x": 0.0},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_xaxes(showgrid=False, title=None)
    fig.update_yaxes(gridcolor=COLORS["grid"], zeroline=False)
    return fig


def empty_chart(message: str, *, y_title: str = "Potência (kW)", height: int = 300) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        text=message,
        showarrow=False,
        font={"size": 15, "color": COLORS["muted"]},
        align="center",
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False, title=y_title)
    return _style(fig, height=height)


def overview_power_chart(data: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    if "carga_total_kW" in data:
        fig.add_trace(
            go.Scatter(
                x=data["timestamp"], y=data["carga_total_kW"],
                mode="lines", name="Carga total", line={"color": COLORS["load"], "width": 3},
            )
        )
    fig.add_trace(
        go.Scatter(
            x=data["timestamp"], y=data["potencia_fv_kW"],
            mode="lines", name="Fotovoltaica", line={"color": COLORS["solar"], "width": 3},
            fill="tozeroy", fillcolor="rgba(242, 184, 75, 0.10)",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=data["timestamp"], y=data["potencia_fc_entregue_kW"],
            mode="lines", name="Célula a combustível",
            line={"color": COLORS["fuel"], "width": 3},
        )
    )
    if "potencia_bateria_kW" in data:
        fig.add_trace(
            go.Scatter(
                x=data["timestamp"], y=data["potencia_bateria_kW"],
                mode="lines", name="Bateria (+ descarga)",
                line={"color": COLORS["battery"], "width": 2},
            )
        )
    fig.update_yaxes(title="Potência (kW)")
    return _style(fig, height=410)


def system_balance_chart(data: pd.DataFrame) -> go.Figure:
    """Compara demanda e geração líquida total e destaca o desbalanço.

    A potência da bateria segue a convenção da EMS: positiva na descarga e
    negativa na carga. Assim, a geração líquida é FV + PEMFC + bateria.
    """
    if "carga_total_kW" not in data:
        return empty_chart(
            "Aguardando o sinal de carga para fechar o balanço do sistema.<br>"
            "Ative os sinais demonstrativos ou forneça carga_total_kW no CSV.",
            height=360,
        )

    timestamp = pd.to_datetime(data["timestamp"])
    load = pd.to_numeric(data["carga_total_kW"], errors="coerce").to_numpy(dtype=float)

    if "potencia_geracao_total_kW" in data:
        generation = pd.to_numeric(
            data["potencia_geracao_total_kW"], errors="coerce"
        ).to_numpy(dtype=float)
    else:
        battery = (
            pd.to_numeric(data["potencia_bateria_kW"], errors="coerce").to_numpy(dtype=float)
            if "potencia_bateria_kW" in data
            else np.zeros(len(data), dtype=float)
        )
        generation = (
            pd.to_numeric(data["potencia_fv_kW"], errors="coerce").to_numpy(dtype=float)
            + pd.to_numeric(data["potencia_fc_entregue_kW"], errors="coerce").to_numpy(dtype=float)
            + battery
        )

    balance = generation - load
    excess = balance > 1e-9
    deficit = balance < -1e-9

    fig = go.Figure()

    # Áreas entre as curvas. NaN quebra o preenchimento quando o sinal muda,
    # deixando excedentes e déficits visualmente independentes.
    fig.add_trace(
        go.Scatter(
            x=timestamp, y=np.where(excess, load, np.nan),
            mode="lines", line={"width": 0}, showlegend=False,
            hoverinfo="skip", connectgaps=False,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=timestamp, y=np.where(excess, generation, np.nan),
            mode="lines", line={"width": 0},
            fill="tonexty", fillcolor="rgba(22, 160, 133, 0.16)",
            name="Excedente", hoverinfo="skip", connectgaps=False,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=timestamp, y=np.where(deficit, generation, np.nan),
            mode="lines", line={"width": 0}, showlegend=False,
            hoverinfo="skip", connectgaps=False,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=timestamp, y=np.where(deficit, load, np.nan),
            mode="lines", line={"width": 0},
            fill="tonexty", fillcolor="rgba(217, 108, 95, 0.16)",
            name="Déficit", hoverinfo="skip", connectgaps=False,
        )
    )

    fig.add_trace(
        go.Scatter(
            x=timestamp, y=load, mode="lines", name="Carga",
            line={"color": COLORS["load"], "width": 3},
            customdata=balance,
            hovertemplate=(
                "Carga: %{y:.2f} kW<br>"
                "Balanço (geração − carga): %{customdata:+.2f} kW<extra></extra>"
            ),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=timestamp, y=generation, mode="lines", name="Geração total",
            line={"color": COLORS["blue"], "width": 3},
            customdata=balance,
            hovertemplate=(
                "Geração total: %{y:.2f} kW<br>"
                "Balanço (geração − carga): %{customdata:+.2f} kW<extra></extra>"
            ),
        )
    )

    fig.add_hline(
        y=0.0, line_width=1, line_dash="dot", line_color=COLORS["grid"]
    )
    fig.update_yaxes(title="Potência (kW)")
    return _style(fig, height=390)


def _series_energy_kwh(timestamp: pd.Series, power_kw: pd.Series) -> float:
    time_s = (
        pd.to_datetime(timestamp) - pd.to_datetime(timestamp).iloc[0]
    ).dt.total_seconds().to_numpy(dtype=float)
    power = np.clip(pd.to_numeric(power_kw).to_numpy(dtype=float), 0.0, None)
    if len(power) < 2:
        return 0.0
    return float((0.5 * (power[1:] + power[:-1]) * np.diff(time_s)).sum() / 3600.0)


def source_energy_shares(data: pd.DataFrame) -> dict[str, float]:
    """Participação na energia positiva fornecida durante a janela ativa."""
    energy = {
        "Solar fotovoltaica": _series_energy_kwh(
            data["timestamp"], data["potencia_fv_kW"]
        ),
        "Célula a combustível": _series_energy_kwh(
            data["timestamp"], data["potencia_fc_entregue_kW"]
        ),
    }
    if "potencia_bateria_kW" in data:
        energy["Bateria"] = _series_energy_kwh(
            data["timestamp"], data["potencia_bateria_kW"]
        )
    total = sum(energy.values())
    if total <= 0.0:
        return {name: 0.0 for name in energy}
    return {name: value / total * 100.0 for name, value in energy.items()}


def source_share_donut(data: pd.DataFrame) -> go.Figure:
    shares = source_energy_shares(data)
    labels = list(shares)
    values = list(shares.values())
    color_map = {
        "Solar fotovoltaica": COLORS["solar"],
        "Célula a combustível": COLORS["fuel"],
        "Bateria": COLORS["battery"],
    }
    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.62,
            sort=False,
            textinfo="percent",
            textposition="inside",
            hovertemplate="%{label}<br>%{value:.1f}%<extra></extra>",
            marker={"colors": [color_map[label] for label in labels], "line": {"color": "white", "width": 3}},
        )
    )
    fig.add_annotation(
        x=0.5,
        y=0.5,
        text="ORIGEM<br><b>DA ENERGIA</b>",
        showarrow=False,
        align="center",
        font={"size": 12, "color": COLORS["muted"]},
    )
    return _style(fig, height=345, hovermode="closest")


def pv_forecast_chart(solar_output: pd.DataFrame) -> go.Figure:
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Scatter(
            x=solar_output["timestamp"], y=solar_output["potencia_fv_kW"],
            name="Potência FV", mode="lines", line={"color": COLORS["solar"], "width": 3},
            fill="tozeroy", fillcolor="rgba(242,184,75,0.12)",
        ), secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=solar_output["timestamp"], y=solar_output["irradiancia_W_m2"],
            name="Irradiância", mode="lines", line={"color": COLORS["blue"], "width": 1.5, "dash": "dot"},
        ), secondary_y=True,
    )
    fig.update_yaxes(title="Potência (kW)", secondary_y=False)
    fig.update_yaxes(title="Irradiância (W/m²)", secondary_y=True, gridcolor="rgba(0,0,0,0)")
    return _style(fig, height=330)


def fuel_cell_power_chart(fuel_output: pd.DataFrame, *, height: int = 330) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=fuel_output["timestamp"], y=fuel_output["P_FC_requested_kW"],
            name="Solicitada", mode="lines", line={"color": COLORS["muted"], "dash": "dash"},
        )
    )
    fig.add_trace(
        go.Scatter(
            x=fuel_output["timestamp"], y=fuel_output["P_FC_delivered_kW"],
            name="Entregue", mode="lines", line={"color": COLORS["fuel"], "width": 3},
        )
    )
    fig.update_yaxes(title="Potência (kW)")
    return _style(fig, height=height)


def battery_chart(data: pd.DataFrame) -> go.Figure:
    if "potencia_bateria_kW" not in data:
        return empty_chart(
            "Espaço reservado para potência e estado de carga da bateria.<br>Ative os sinais sintéticos na aba Entradas para visualizar o layout.",
            height=315,
        )
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Bar(
            x=data["timestamp"], y=data["potencia_bateria_kW"], name="Potência",
            marker_color=COLORS["battery"], opacity=0.70,
        ), secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=data["timestamp"], y=data["soc_bateria_pct"], name="SOC",
            mode="lines", line={"color": COLORS["navy"], "width": 2.5},
        ), secondary_y=True,
    )
    fig.update_yaxes(title="Potência (kW)", secondary_y=False)
    fig.update_yaxes(title="SOC (%)", range=[0, 100], secondary_y=True, gridcolor="rgba(0,0,0,0)")
    return _style(fig, height=315)


def input_weather_chart(data: pd.DataFrame) -> go.Figure:
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Scatter(
            x=data["timestamp"], y=data["irradiancia_W_m2"], name="Irradiância",
            mode="lines", line={"color": COLORS["solar"], "width": 2.5},
            fill="tozeroy", fillcolor="rgba(242,184,75,0.10)",
        ), secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=data["timestamp"], y=data["temperatura_ambiente_C"], name="Temperatura",
            mode="lines", line={"color": COLORS["temperature"], "width": 2.5},
        ), secondary_y=True,
    )
    fig.update_yaxes(title="Irradiância (W/m²)", secondary_y=False)
    fig.update_yaxes(title="Temperatura (°C)", secondary_y=True, gridcolor="rgba(0,0,0,0)")
    return _style(fig, height=335)


def input_power_chart(data: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=data["timestamp"], y=data["potencia_solicitada_fc_kW"],
            name="Solicitação PEMFC", mode="lines",
            line={"color": COLORS["fuel"], "width": 2.5},
        )
    )
    if "carga_total_kW" in data:
        fig.add_trace(
            go.Scatter(
                x=data["timestamp"], y=data["carga_total_kW"],
                name="Carga total", mode="lines", line={"color": COLORS["load"], "width": 2.5},
            )
        )
    fig.update_yaxes(title="Potência (kW)")
    return _style(fig, height=335)


def solar_efficiency_chart(solar_output: pd.DataFrame) -> go.Figure:
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Scatter(
            x=solar_output["timestamp"], y=solar_output["eficiencia_fv_pct"],
            name="Eficiência FV", mode="lines", line={"color": COLORS["blue"], "width": 2.5},
        ), secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=solar_output["timestamp"], y=solar_output["temperatura_celula_C"],
            name="Temperatura da célula", mode="lines",
            line={"color": COLORS["temperature"], "width": 2},
        ), secondary_y=True,
    )
    fig.update_yaxes(title="Eficiência (%)", secondary_y=False)
    fig.update_yaxes(title="Temperatura (°C)", secondary_y=True, gridcolor="rgba(0,0,0,0)")
    return _style(fig, height=335)


def fuel_cell_electrical_chart(fuel_output: pd.DataFrame) -> go.Figure:
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Scatter(
            x=fuel_output["timestamp"], y=fuel_output["current_A"],
            name="Corrente", mode="lines", line={"color": COLORS["blue"], "width": 2.5},
        ), secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=fuel_output["timestamp"], y=fuel_output["V_stack_V"],
            name="Tensão do stack", mode="lines", line={"color": COLORS["fuel"], "width": 2.5},
        ), secondary_y=True,
    )
    fig.update_yaxes(title="Corrente (A)", secondary_y=False)
    fig.update_yaxes(title="Tensão (V)", secondary_y=True, gridcolor="rgba(0,0,0,0)")
    return _style(fig, height=335)


def fuel_cell_resources_chart(fuel_output: pd.DataFrame) -> go.Figure:
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Scatter(
            x=fuel_output["timestamp"], y=fuel_output["hydrogen_supplied_kg_h"],
            name="H₂", mode="lines", line={"color": COLORS["cyan"], "width": 2.5},
        ), secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=fuel_output["timestamp"],
            y=fuel_output["net_electrical_efficiency_LHV_percent"],
            name="Eficiência líquida", mode="lines",
            line={"color": COLORS["fuel"], "width": 2.5},
        ), secondary_y=True,
    )
    fig.update_yaxes(title="H₂ (kg/h)", secondary_y=False)
    fig.update_yaxes(title="Eficiência PCI (%)", secondary_y=True, gridcolor="rgba(0,0,0,0)")
    return _style(fig, height=335)
