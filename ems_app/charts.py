"""Gráficos Plotly padronizados para a interface de monitoramento."""

from __future__ import annotations

import pandas as pd
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

