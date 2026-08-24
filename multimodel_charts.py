"""Identidade visual madura e compacta da plataforma unificada H₂V."""

APP_CSS = r"""
<style>
:root {
  --ems-navy:#25394B;
  --ems-navy-dark:#1C2C3A;
  --ems-blue:#00699A;
  --ems-blue-light:#E9F5FB;
  --ems-green:#16A085;
  --ems-orange:#F2994A;
  --ems-yellow:#F2B84B;
  --ems-border:#D8DEE5;
  --ems-text:#17222D;
  --ems-muted:#718096;
  --ems-panel:#FFFFFF;
}

html,body,[class*="css"] { font-family:Inter,Arial,sans-serif; }
.stApp,[data-testid="stAppViewContainer"] { background:#FFFFFF; color:var(--ems-text); }
[data-testid="stHeader"] { background:transparent; }
.block-container {
  padding-top:4.55rem; padding-bottom:3rem; padding-left:1.25rem;
  padding-right:1.6rem; max-width:1780px;
}
h1,h2,h3 { letter-spacing:-.025em; color:var(--ems-text); }

[data-testid="stSidebar"] {
  background:linear-gradient(180deg,var(--ems-navy-dark) 0%,var(--ems-navy) 100%);
  border-right:1px solid #324B60;
}
[data-testid="stSidebar"] > div { padding-top:1rem; }
[data-testid="stSidebar"] p,[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label,[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3 { color:#EAF1F6 !important; }
[data-testid="stSidebar"] hr { border-color:rgba(255,255,255,.14); }

.ems-brand { text-align:center; padding:1.05rem .3rem 1.35rem; }
.ems-mark {
  width:70px; height:70px; margin:0 auto .8rem; display:grid; place-items:center;
  border-radius:50%; color:#FFFFFF; font-size:2rem;
  background:radial-gradient(circle at 42% 42%,#6DD4C1 0 12%,#1380AC 42%,transparent 44%);
  border:1px solid rgba(255,255,255,.28);
}
.ems-brand-name { color:white; font-weight:850; letter-spacing:.2em; font-size:1.02rem; }
.ems-brand-sub { color:#91A9BB; font-weight:700; letter-spacing:.12em; font-size:.62rem; margin-top:.35rem; }
.sidebar-label { color:#91A9BB; font-size:.67rem; font-weight:800; letter-spacing:.13em; margin:.25rem 0 .55rem; }
.sidebar-status {
  border:1px solid rgba(255,255,255,.12); background:rgba(255,255,255,.055);
  border-radius:9px; padding:.68rem .78rem; margin-bottom:.5rem;
}
.sidebar-status small { display:block; color:#91A9BB !important; font-size:.61rem; letter-spacing:.1em; font-weight:800; }
.sidebar-status b { display:block; color:#FFFFFF !important; font-size:.79rem; margin-top:.16rem; line-height:1.35; }

.page-head {
  border:1px solid var(--ems-border); border-radius:10px; background:#FFFFFF;
  padding:.72rem .95rem; margin-bottom:.62rem;
}
.eyebrow { color:var(--ems-blue); font-size:.68rem; font-weight:850; letter-spacing:.14em; text-transform:uppercase; }
.page-title { font-size:1.55rem; line-height:1.08; font-weight:900; color:#111A22; margin:.2rem 0 .12rem; }
.page-subtitle { color:var(--ems-muted); font-size:.75rem; line-height:1.45; margin-top:.22rem; }
.panel-title { color:var(--ems-blue); font-size:.66rem; font-weight:850; letter-spacing:.13em; text-transform:uppercase; margin-bottom:.38rem; }
.model-page-title { color:#111A22; font-size:1.42rem; line-height:1.08; font-weight:900; margin:.2rem 0 .3rem; }
.section-label { color:var(--ems-blue); font-size:.66rem; font-weight:850; letter-spacing:.13em; text-transform:uppercase; margin:.48rem 0 .34rem; }

.status-row { display:flex; gap:.42rem; flex-wrap:wrap; margin-top:.5rem; margin-bottom:.48rem; }
.chip { display:inline-flex; align-items:center; border-radius:999px; padding:.27rem .54rem; font-size:.65rem; font-weight:800; }
.chip-ok { background:#E8F7F1; color:#087A55; border:1px solid #BCE9D8; }
.chip-warn { background:#FFF4DF; color:#9A6200; border:1px solid #F3D494; }
.chip-info { background:#EAF5FB; color:#006390; border:1px solid #BBDCEC; }
.chip-off { background:#F3F5F7; color:#65717D; border:1px solid #D9DEE3; }

.notice {
  border-left:3px solid #1380AC; border-radius:0 8px 8px 0; background:#F2F8FC;
  color:#426174; font-size:.73rem; line-height:1.48; padding:.56rem .7rem; margin:.1rem 0 .45rem;
}
.notice strong { color:#21485E; }
.warning-note { border-left-color:#D28B19; background:#FFF8EA; color:#77531C; }
.formula-box {
  background:#F7FAFC; border:1px solid #E1E7ED; border-left:3px solid var(--ems-blue);
  border-radius:8px; padding:.5rem .72rem; color:#3E4C59; font-size:.74rem; margin:.16rem 0 .52rem;
}

.datasheet-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:.5rem; margin:.45rem 0 .2rem; }
.datasheet-item { border:1px solid #E1E6EB; border-radius:8px; padding:.56rem .62rem; background:#FBFCFD; }
.datasheet-item small { display:block; color:#7B8894; font-size:.59rem; letter-spacing:.08em; font-weight:800; text-transform:uppercase; }
.datasheet-item b { display:block; color:#17222D; font-size:.84rem; margin-top:.12rem; }
.config-facts { display:grid; grid-template-columns:1fr 1fr; gap:.42rem; margin:.18rem 0 .12rem; }
.config-fact { border:1px solid #E0E6EB; border-radius:7px; background:#FBFCFD; padding:.46rem .52rem; }
.config-fact small { display:block; color:#788896; font-size:.57rem; font-weight:850; letter-spacing:.09em; text-transform:uppercase; }
.config-fact b { display:block; color:#20313F; font-size:.72rem; margin-top:.12rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }

.kpi-card { min-height:76px; background:#FFFFFF; border:1px solid #DDE3E9; border-radius:9px; padding:.48rem .62rem; }
.kpi-label { color:#657484; font-size:.69rem; line-height:1.3; margin-bottom:.22rem; }
.kpi-value-line { display:flex; align-items:baseline; gap:.46rem; flex-wrap:wrap; }
.kpi-value { color:#111820; font-size:1.12rem; line-height:1.2; font-weight:850; }
.kpi-context { color:#718096; font-size:.64rem; line-height:1.2; font-weight:750; white-space:nowrap; }

.subsystem-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:.6rem; margin:.2rem 0 .55rem; }
.subsystem-card { border:1px solid #DDE3E9; border-radius:9px; padding:.68rem .72rem; background:#FFFFFF; min-height:92px; }
.subsystem-card small { display:block; color:#72808D; font-size:.59rem; font-weight:850; letter-spacing:.1em; text-transform:uppercase; }
.subsystem-card b { display:block; color:#17222D; font-size:.86rem; margin:.2rem 0 .18rem; }
.subsystem-card p { color:#718096; font-size:.68rem; line-height:1.4; margin:0; }
.subsystem-card.solar { border-left:3px solid var(--ems-yellow); }
.subsystem-card.fuel { border-left:3px solid var(--ems-green); }
.subsystem-card.battery { border-left:3px solid #5B79B7; }

.process-band {
  display:grid; grid-template-columns:1fr auto 1fr auto 1fr; gap:.55rem; align-items:stretch;
  border:1px solid #D8E2E9; border-radius:10px;
  background:linear-gradient(90deg,#F7FBFD 0%,#FFFFFF 50%,#F8FBFA 100%); padding:.72rem;
}
.process-step { min-height:72px; display:flex; flex-direction:column; justify-content:center; border-radius:8px; padding:.6rem .7rem; background:#FFFFFF; }
.process-step small { display:block; color:#08729E; font-size:.59rem; font-weight:880; letter-spacing:.11em; margin-bottom:.24rem; }
.process-step b { display:block; color:#1D303D; font-size:.79rem; line-height:1.35; }
.process-step span { display:block; color:#71818E; font-size:.67rem; line-height:1.35; margin-top:.14rem; }
.process-input { border-left:3px solid #2F80ED; }
.process-models { border-left:3px solid #16A085; }
.process-output { border-left:3px solid #F2994A; }
.process-arrow { align-self:center; color:#6E92A7; font-size:1.25rem; font-weight:900; }

.compact-note {
  min-height:220px; display:flex; flex-direction:column; justify-content:center;
  border:1px dashed #C9D9E4; border-radius:8px; background:#F7FAFC;
  padding:1rem 1.1rem; color:#536575; font-size:.78rem; line-height:1.55;
}
.compact-note b { color:#203746; font-size:.85rem; margin-bottom:.25rem; }
.construction { min-height:350px; display:grid; place-items:center; text-align:center; border:1px dashed #C9D9E4; border-radius:10px; background:#F7FAFC; padding:2rem; }
.construction .icon { font-size:2.25rem; margin-bottom:.65rem; }
.construction h3 { color:#17222D; margin:0 0 .42rem; font-size:1.25rem; }
.construction p { color:#718096; margin:0; max-width:600px; font-size:.8rem; line-height:1.55; }
.balance-note { color:#718096; font-size:.7rem; line-height:1.35; padding:.1rem .12rem 0; }
.balance-note strong { color:#243746; }
.balance-note span { color:#B0BAC2; padding:0 .2rem; }

div[data-testid="stVerticalBlockBorderWrapper"] { border-color:var(--ems-border) !important; border-radius:10px !important; box-shadow:none !important; padding-bottom:.12rem; }
div[data-testid="stVerticalBlock"] { gap:.7rem !important; }
div[data-testid="stHorizontalBlock"] { gap:.68rem !important; }
div[data-testid="stMetric"] { background:#FFFFFF; border:1px solid #DDE3E9; border-radius:9px; padding:.48rem .62rem; min-height:76px; }
div[data-testid="stMetricLabel"] { color:#657484; font-size:.69rem; }
div[data-testid="stMetricValue"] { color:#111820; font-size:1.12rem; font-weight:850; }
div[data-testid="stMetricDelta"] { font-size:.62rem; }
div[data-testid="stAlert"] { padding:.52rem .7rem; }
div[data-testid="stPlotlyChart"] { margin:0 !important; border:0; }
[data-testid="stDataFrame"] { border:1px solid #E1E6EB; border-radius:9px; overflow:hidden; }

.stButton > button,.stDownloadButton > button { border-radius:8px; font-weight:800; min-height:2.65rem; box-shadow:none; }
.stButton > button[kind="primary"],.stDownloadButton > button[kind="primary"] { background:linear-gradient(135deg,#0878A8,#00577F); border-color:#00577F; }
[data-testid="stSidebar"] .stButton { margin-bottom:.34rem; }
[data-testid="stSidebar"] .stButton > button {
  width:100%; min-height:2.5rem; border-radius:9px; background:rgba(255,255,255,.065);
  border:1px solid rgba(255,255,255,.12); color:#EAF1F6; font-size:.77rem; font-weight:760;
  box-shadow:none; transition:background .16s ease,border-color .16s ease,transform .16s ease;
}
[data-testid="stSidebar"] .stButton > button:hover { background:rgba(255,255,255,.11); border-color:rgba(255,255,255,.25); color:#FFFFFF; transform:translateY(-1px); }
[data-testid="stSidebar"] .stButton > button[kind="primary"] { background:linear-gradient(135deg,#1D496D 0%,#123B5F 100%); border:1px solid #5D86A6; color:#FFFFFF; box-shadow:inset 0 0 0 1px rgba(255,255,255,.04); }
[data-testid="stSidebar"] .stButton > button p { color:inherit !important; font-weight:inherit; }
.stTabs [data-baseweb="tab-list"] { gap:.45rem; border-bottom:1px solid #DDE3E9; }
.stTabs [data-baseweb="tab"] { padding:.48rem .72rem; font-weight:750; }
[data-baseweb="select"] > div,[data-baseweb="input"] > div { border-radius:8px; }
[data-testid="stFileUploaderDropzone"] { border-radius:9px; background:#F8FAFC; }

@media (max-width:900px) {
  .datasheet-grid,.subsystem-grid { grid-template-columns:repeat(2,minmax(0,1fr)); }
  .process-band { grid-template-columns:1fr; }
  .process-arrow { transform:rotate(90deg); justify-self:center; }
  .block-container { padding-left:1rem; padding-right:1rem; }
}
@media (max-width:620px) {
  .datasheet-grid,.subsystem-grid,.config-facts { grid-template-columns:1fr; }
}
</style>
"""


CHART_CONFIG = {
    "displaylogo": False,
    "responsive": True,
    "modeBarButtonsToRemove": ["lasso2d", "select2d"],
    "toImageButtonOptions": {"format": "svg", "filename": "h2v_ems"},
}


def page_header(eyebrow: str, title: str, subtitle: str = "") -> str:
    subtitle_html = f'<div class="page-subtitle">{subtitle}</div>' if subtitle else ""
    return f"""
    <div class="page-head">
      <div class="eyebrow">{eyebrow}</div>
      <div class="page-title">{title}</div>
      {subtitle_html}
    </div>
    """


def panel_title(text: str) -> str:
    return f'<div class="panel-title">{text}</div>'


def status_chip(text: str, kind: str = "info") -> str:
    return f'<span class="chip chip-{kind}">{text}</span>'


def sidebar_brand() -> str:
    return """
    <div class="ems-brand">
      <div class="ems-mark">⚡</div>
      <div class="ems-brand-name">H₂V · EMS</div>
      <div class="ems-brand-sub">UNIFIED MODEL PLATFORM</div>
    </div>
    """
