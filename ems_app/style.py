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
    background: #ffffff;
}
[data-testid="stHeader"] { background: transparent; }
.block-container { max-width: 1540px; padding-top: .85rem; padding-bottom: 1.6rem; }

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
    padding: .15rem .15rem .65rem;
}
.page-head h1 { color: var(--ink); font-size: 1.85rem; line-height: 1.08; margin: 0; letter-spacing: -.035em; }
.page-head p { color: var(--muted); margin: .28rem 0 0; font-size: .88rem; }
.status-pill {
    flex: none; display: inline-flex; align-items: center; gap: .45rem;
    padding: .48rem .72rem; border-radius: 999px; color: #0d6259;
    background: rgba(22,160,133,.09); border: 1px solid rgba(22,160,133,.20);
    font-size: .76rem; font-weight: 700; letter-spacing: .03em; text-transform: uppercase;
}
.status-dot { width: 7px; height: 7px; border-radius: 99px; background: #16a085; box-shadow: 0 0 0 4px rgba(22,160,133,.11); }

.section-label { color: #48647b; font-size: .68rem; font-weight: 700; letter-spacing: .085em; text-transform: uppercase; margin: .68rem 0 .34rem; }
.notice {
    padding: .52rem .78rem; border-radius: 12px; color: #496175;
    background: #f7fafb; border: 1px solid var(--line); font-size: .78rem; margin-top: .28rem;
}
.notice strong { color: var(--ink); }
.construction {
    min-height: 380px; display: grid; place-items: center; text-align: center;
    border: 1px dashed rgba(23,50,77,.24); border-radius: 20px;
    background: #fbfcfd; padding: 2rem;
}
.construction .icon { font-size: 2.4rem; margin-bottom: .7rem; }
.construction h3 { color: var(--ink); margin: 0 0 .5rem; font-size: 1.35rem; }
.construction p { color: var(--muted); margin: 0; max-width: 560px; }

[data-testid="stMetric"] {
    background: var(--panel); border: 1px solid var(--line); border-radius: 13px;
    padding: .46rem .72rem; min-height: 68px; box-shadow: 0 5px 18px rgba(23,50,77,.035);
}
[data-testid="stMetricLabel"] { color: var(--muted); }
[data-testid="stMetricLabel"] p { font-size: .68rem; line-height: 1.12; margin-bottom: .08rem; }
[data-testid="stMetricValue"] { color: var(--ink); font-size: 1.28rem; line-height: 1.05; }
[data-testid="stPlotlyChart"] {
    background: var(--panel); border: 1px solid var(--line); border-radius: 15px;
    padding: .18rem; box-shadow: 0 5px 20px rgba(23,50,77,.035);
}
.quick-read {
    min-height: 260px; box-sizing: border-box; padding: 1.05rem 1.15rem;
    background: #f8fbfa; border: 1px solid rgba(22,160,133,.16); border-radius: 18px;
    box-shadow: 0 8px 30px rgba(23,50,77,.04);
}
.quick-kicker { color: #558076; font-size: .72rem; font-weight: 700; letter-spacing: .09em; text-transform: uppercase; }
.quick-read h3 { color: var(--ink); font-size: 1.18rem; margin: .32rem 0 .14rem; }
.quick-read p { color: var(--muted); margin: 0 0 .55rem; font-size: .8rem; }
.quick-read p strong { color: var(--fuel); font-size: 1.02rem; }
.quick-read ul { list-style: none; padding: 0; margin: .4rem 0 0; }
.quick-read li { display: flex; justify-content: space-between; gap: .7rem; padding: .31rem 0; border-bottom: 1px solid var(--line); color: #48647b; font-size: .76rem; }
.quick-read li strong { color: var(--ink); }
.quick-note { color: var(--muted); font-size: .78rem; line-height: 1.5; padding-top: .2rem; }

.balance-note {
    color: var(--muted); font-size: .72rem; line-height: 1.35;
    padding: .12rem .15rem 0; white-space: normal;
}
.balance-note strong { color: var(--ink); font-weight: 650; }
.balance-note span { color: rgba(23,50,77,.34); padding: 0 .2rem; }
.quick-read-compact { min-height: 260px; }

/* Reduz o espaço vertical padrão entre blocos do Streamlit sem colapsar controles. */
[data-testid="stVerticalBlock"] { gap: .55rem; }
[data-testid="stHorizontalBlock"] { gap: .75rem; }

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
