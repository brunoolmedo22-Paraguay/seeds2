"""Identidade visual da aplicação Streamlit."""

APP_CSS = r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
    --ink: #17324d;
    --muted: #6b7c8f;
    --line: rgba(23, 50, 77, .11);
    --panel: rgba(255, 255, 255, .92);
    --fuel: #16a085;
    --solar: #f2b84b;
}

html, body, [class*="css"] { font-family: Inter, system-ui, sans-serif; }
[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(circle at 92% 3%, rgba(49,166,184,.10), transparent 30rem),
        linear-gradient(180deg, #f5f9fb 0%, #eef4f7 100%);
}
[data-testid="stHeader"] { background: transparent; }
.block-container { max-width: 1480px; padding-top: 1.35rem; padding-bottom: 3rem; }

[data-testid="stSidebar"] {
    background: linear-gradient(165deg, #17324d 0%, #1d4960 58%, #146c6b 100%);
    border-right: 0;
}
[data-testid="stSidebar"] * { color: rgba(255,255,255,.94); }
[data-testid="stSidebar"] [role="radiogroup"] label {
    padding: .72rem .78rem;
    margin: .22rem 0;
    border-radius: 12px;
    border: 1px solid rgba(255,255,255,.08);
    transition: all .18s ease;
}
[data-testid="stSidebar"] [role="radiogroup"] label:hover {
    background: rgba(255,255,255,.08);
    border-color: rgba(255,255,255,.16);
}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
    background: rgba(255,255,255,.16);
    border-color: rgba(255,255,255,.30);
    box-shadow: 0 8px 24px rgba(0,0,0,.12);
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: rgba(255,255,255,.82); }

.sidebar-brand { padding: .35rem .25rem 1.35rem; }
.sidebar-brand .mark {
    width: 46px; height: 46px; border-radius: 14px;
    display: grid; place-items: center; font-size: 1.45rem;
    background: rgba(255,255,255,.14); border: 1px solid rgba(255,255,255,.22);
    box-shadow: 0 10px 30px rgba(0,0,0,.12);
}
.sidebar-brand h2 { margin: .8rem 0 .12rem; font-size: 1.35rem; letter-spacing: .04em; }
.sidebar-brand span { color: rgba(255,255,255,.64); font-size: .76rem; letter-spacing: .08em; text-transform: uppercase; }

.page-head {
    display: flex; align-items: flex-end; justify-content: space-between; gap: 1rem;
    padding: .25rem .15rem 1.1rem;
}
.page-head h1 { color: var(--ink); font-size: 2.05rem; line-height: 1.1; margin: 0; letter-spacing: -.035em; }
.page-head p { color: var(--muted); margin: .42rem 0 0; font-size: .95rem; }
.status-pill {
    flex: none; display: inline-flex; align-items: center; gap: .45rem;
    padding: .48rem .72rem; border-radius: 999px; color: #0d6259;
    background: rgba(22,160,133,.09); border: 1px solid rgba(22,160,133,.20);
    font-size: .76rem; font-weight: 700; letter-spacing: .03em; text-transform: uppercase;
}
.status-dot { width: 7px; height: 7px; border-radius: 99px; background: #16a085; box-shadow: 0 0 0 4px rgba(22,160,133,.11); }

.section-label { color: #48647b; font-size: .72rem; font-weight: 700; letter-spacing: .09em; text-transform: uppercase; margin: 1.1rem 0 .5rem; }
.notice {
    padding: .85rem 1rem; border-radius: 14px; color: #496175;
    background: rgba(255,255,255,.68); border: 1px solid var(--line); font-size: .88rem;
}
.notice strong { color: var(--ink); }
.construction {
    min-height: 380px; display: grid; place-items: center; text-align: center;
    border: 1px dashed rgba(23,50,77,.24); border-radius: 20px;
    background: rgba(255,255,255,.55); padding: 2rem;
}
.construction .icon { font-size: 2.4rem; margin-bottom: .7rem; }
.construction h3 { color: var(--ink); margin: 0 0 .5rem; font-size: 1.35rem; }
.construction p { color: var(--muted); margin: 0; max-width: 560px; }

[data-testid="stMetric"] {
    background: var(--panel); border: 1px solid var(--line); border-radius: 16px;
    padding: .82rem 1rem; box-shadow: 0 8px 28px rgba(23,50,77,.045);
}
[data-testid="stMetricLabel"] { color: var(--muted); }
[data-testid="stMetricValue"] { color: var(--ink); }
[data-testid="stPlotlyChart"] {
    background: var(--panel); border: 1px solid var(--line); border-radius: 18px;
    padding: .35rem; box-shadow: 0 8px 30px rgba(23,50,77,.04);
}
[data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 14px; overflow: hidden; }
[data-testid="stTabs"] [data-baseweb="tab-list"] { gap: .35rem; }
[data-testid="stTabs"] [data-baseweb="tab"] { border-radius: 10px; padding-left: 1rem; padding-right: 1rem; }
.stButton > button, .stDownloadButton > button { border-radius: 11px; font-weight: 650; }
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
      <div class="mark">⚡</div>
      <h2>H₂V · EMS</h2>
      <span>Energy Management System</span>
    </div>
    """

