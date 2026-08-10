"""Identidade visual da aplicação Streamlit."""

APP_CSS = r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
    --ink: #0d1721;
    --muted: #78838f;
    --line: #d8dde2;
    --line-soft: #e7eaed;
    --panel: #ffffff;
    --fuel: #23856b;
    --solar: #f2b84b;
    --sidebar: #173b34;
    --sidebar-deep: #102f2a;
    --section: #0c5b55;
}

html, body, [class*="css"] { font-family: Inter, system-ui, sans-serif; color: var(--ink); }
[data-testid="stAppViewContainer"] {
    background: #ffffff;
}
[data-testid="stHeader"] { background: #ffffff; }
.block-container { max-width: 1640px; padding: 2rem 1.05rem 3rem; }

[data-testid="stSidebar"] {
    width: 286px !important;
    min-width: 286px !important;
    background: linear-gradient(180deg, var(--sidebar) 0%, var(--sidebar-deep) 100%);
    border-right: 1px solid rgba(255,255,255,.08);
}
[data-testid="stSidebar"] > div:first-child { width: 286px !important; }
[data-testid="stSidebar"] * { color: rgba(255,255,255,.94); }
[data-testid="stSidebar"] [role="radiogroup"] label {
    min-height: 42px;
    display: flex; align-items: center; justify-content: center;
    padding: .62rem .72rem;
    margin: .34rem 0;
    border-radius: 10px;
    background: rgba(255,255,255,.075);
    border: 1px solid rgba(255,255,255,.11);
    transition: background .15s ease, border-color .15s ease;
    font-size: .86rem; font-weight: 650;
}
[data-testid="stSidebar"] [role="radiogroup"] label > div:first-child { display: none; }
[data-testid="stSidebar"] [role="radiogroup"] label:hover {
    background: rgba(255,255,255,.12);
    border-color: rgba(255,255,255,.20);
}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
    background: #0c342e;
    border-color: #68a997;
    box-shadow: none;
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: rgba(255,255,255,.82); }
[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,.12); margin: 1.55rem 0; }

.sidebar-brand {
    display: flex; flex-direction: column; align-items: center; text-align: center;
    padding: 1.4rem .25rem 1.2rem;
}
.sidebar-brand .mark {
    width: 76px; height: 54px; border-radius: 10px;
    display: grid; place-items: center; font-size: 1.25rem; font-weight: 750;
    letter-spacing: .08em;
    background: rgba(255,255,255,.035); border: 1px solid rgba(196,238,226,.35);
    box-shadow: none;
}
.sidebar-brand h2 { margin: .65rem 0 .12rem; font-size: 1.1rem; letter-spacing: .20em; }
.sidebar-brand span { color: rgba(255,255,255,.58); font-size: .62rem; letter-spacing: .12em; text-transform: uppercase; }
.sidebar-section-label {
    color: #90bcae; font-size: .62rem; font-weight: 700;
    letter-spacing: .14em; text-transform: uppercase; margin: .35rem .25rem .2rem;
}

.page-head {
    display: flex; align-items: flex-end; justify-content: space-between; gap: 1rem;
    padding: 1.35rem 1.45rem;
    margin: .05rem 0 1rem;
    background: #ffffff; border: 1px solid var(--line); border-radius: 9px;
}
.page-head h1 {
    color: var(--ink); font-size: 1.68rem; line-height: 1.08; margin: 0;
    letter-spacing: -.035em; text-transform: uppercase; font-weight: 750;
}
.page-head p { color: var(--muted); margin: .30rem 0 0; font-size: .76rem; }
.status-pill {
    flex: none; display: inline-flex; align-items: center; gap: .45rem;
    padding: .38rem .62rem; border-radius: 999px; color: #176d5c;
    background: #eef8f5; border: 1px solid #b8ddd3;
    font-size: .63rem; font-weight: 700; letter-spacing: .06em; text-transform: uppercase;
}
.status-dot { width: 6px; height: 6px; border-radius: 99px; background: #23856b; box-shadow: none; }

.section-label {
    color: var(--section); font-size: .64rem; font-weight: 750;
    letter-spacing: .14em; text-transform: uppercase; margin: 1.05rem .12rem .46rem;
}
.notice {
    padding: .72rem .88rem; border-radius: 8px; color: #53616c;
    background: #f8faf9; border: 1px solid var(--line); font-size: .78rem;
}
.notice strong { color: var(--ink); }
.construction {
    min-height: 380px; display: grid; place-items: center; text-align: center;
    border: 1px dashed #cbd2d8; border-radius: 9px;
    background: #fbfcfd; padding: 2rem;
}
.construction .icon { font-size: 2.4rem; margin-bottom: .7rem; }
.construction h3 { color: var(--ink); margin: 0 0 .5rem; font-size: 1.35rem; }
.construction p { color: var(--muted); margin: 0; max-width: 560px; }

[data-testid="stMetric"] {
    min-height: 112px;
    background: var(--panel); border: 1px solid var(--line); border-radius: 10px;
    padding: .72rem .78rem; box-shadow: none;
}
[data-testid="stMetricLabel"] { color: #596671; font-size: .72rem; }
[data-testid="stMetricValue"] { color: var(--ink); font-size: 1.24rem; font-weight: 700; }
[data-testid="stPlotlyChart"] {
    background: var(--panel); border: 1px solid var(--line); border-radius: 9px;
    padding: .28rem; box-shadow: none;
}
.quick-read {
    min-height: 345px; box-sizing: border-box; padding: 1.5rem 1.6rem;
    background: #ffffff; border: 1px solid var(--line); border-radius: 9px;
    box-shadow: none;
}
.quick-kicker { color: #558076; font-size: .72rem; font-weight: 700; letter-spacing: .09em; text-transform: uppercase; }
.quick-read h3 { color: var(--ink); font-size: 1.45rem; margin: .45rem 0 .2rem; }
.quick-read p { color: var(--muted); margin: 0 0 1rem; }
.quick-read p strong { color: var(--fuel); font-size: 1.15rem; }
.quick-read ul { list-style: none; padding: 0; margin: .8rem 0 1rem; }
.quick-read li { display: flex; justify-content: space-between; gap: 1rem; padding: .48rem 0; border-bottom: 1px solid var(--line-soft); color: #48647b; }
.quick-read li strong { color: var(--ink); }
.quick-note { color: var(--muted); font-size: .78rem; line-height: 1.5; padding-top: .2rem; }
[data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 8px; overflow: hidden; }
[data-testid="stTabs"] [data-baseweb="tab-list"] { gap: .35rem; border-bottom: 1px solid var(--line); }
[data-testid="stTabs"] [data-baseweb="tab"] { border-radius: 7px 7px 0 0; padding-left: 1rem; padding-right: 1rem; }
.stButton > button, .stDownloadButton > button {
    min-height: 40px; border-radius: 8px; font-weight: 650;
    border: 1px solid var(--line); box-shadow: none;
}
[data-testid="stSelectbox"] [data-baseweb="select"] > div,
[data-testid="stFileUploaderDropzone"] {
    border-radius: 8px; border-color: var(--line); box-shadow: none;
}
[data-testid="stVerticalBlockBorderWrapper"] {
    border-color: var(--line) !important; border-radius: 9px !important; box-shadow: none !important;
}
hr { border-color: var(--line); }

@media (max-width: 800px) {
    .page-head { align-items: flex-start; flex-direction: column; }
    .page-head h1 { font-size: 1.72rem; }
}
</style>
"""


def page_header(title: str, subtitle: str, status: str = "Modelos ativos") -> str:
    return f"""
    <div class="page-head">
      <div><h1>{title}</h1><p>{subtitle}</p></div>
      <div class="status-pill"><span class="status-dot"></span>{status}</div>
    </div>
    """


def sidebar_brand() -> str:
    return """
    <div class="sidebar-brand">
      <div class="mark">H₂V</div>
      <h2>H₂V · EMS</h2>
      <span>Energy Management System</span>
    </div>
    """
