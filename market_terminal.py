"""
QUANTUM MARKET TERMINAL v5.0
Live Indian & Global Market Data — NSE, BSE, MCX (INR), Forex, Crypto

FIXES v5:
  1. Heatmap colorbar: titlefont → title=dict(font=dict(...))
  2. Chart Studio: cs_sym always defined, selectbox keys unique
  3. Live clock: JavaScript updates every second without rerun
  4. Auto-refresh: time.sleep(n)+rerun at end of script
  5. MCX prices converted to Indian Rupees (₹) via live USD/INR
  6. Focus Stock: wired to mini chart + live card in overview

Install:  pip install streamlit yfinance plotly pandas numpy
Run:      streamlit run market_terminal.py
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import time
import warnings
warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SIVA MARKET TERMINAL",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────────────────
# CSS — safe selectors only, no [class*="css"] which breaks Streamlit tabs
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Orbitron:wght@700;900&family=Exo+2:wght@400;600&display=swap');
:root{
  --bg:#040c04;--bg2:#080f08;--card:#0d1a0d;--border:#1a3a1a;
  --green:#00ff41;--green2:#00cc33;--amber:#ffb300;--red:#ff3d3d;
  --blue:#00b4ff;--cyan:#00fff7;
  --t1:#c8ffc8;--t2:#6a9a6a;--t3:#2d5a2d;
  --mono:'Share Tech Mono',monospace;
  --disp:'Orbitron',sans-serif;
  --body:'Exo 2',sans-serif;
}
body,.main,.stApp{background:var(--bg)!important;color:var(--t1);font-family:var(--body)}
.main .block-container{padding:.5rem 1.2rem 2rem!important;max-width:100%!important}
#MainMenu,footer,header{visibility:hidden}
::-webkit-scrollbar{width:4px;height:4px}
::-webkit-scrollbar-track{background:var(--bg)}
::-webkit-scrollbar-thumb{background:var(--green2);border-radius:2px}

/* HEADER */
.qmt-header{background:linear-gradient(135deg,#020802,#041204,#061806);border:1px solid var(--green2);border-top:3px solid var(--green);border-radius:6px;padding:12px 20px;margin-bottom:8px;position:relative;overflow:hidden}
.qmt-header::before{content:'';position:absolute;top:0;left:-100%;width:60%;height:100%;background:linear-gradient(90deg,transparent,rgba(0,255,65,.04),transparent);animation:scan 5s linear infinite}
@keyframes scan{0%{left:-100%}100%{left:200%}}
.qmt-title{font-family:var(--disp);font-size:22px;font-weight:900;color:var(--green);letter-spacing:4px;margin:0;animation:glow 3s ease-in-out infinite}
@keyframes glow{0%,100%{text-shadow:0 0 20px rgba(0,255,65,.6),0 0 40px rgba(0,255,65,.3)}50%{text-shadow:0 0 30px rgba(0,255,65,.9),0 0 60px rgba(0,255,65,.5)}}
.qmt-sub{font-family:var(--mono);font-size:11px;color:var(--t2);letter-spacing:2px;margin:2px 0 0}
.live-dot{display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--green);box-shadow:0 0 8px var(--green);animation:blink 1.2s ease-in-out infinite;margin-right:6px}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.3}}
/* JS clock target */
#qmt-clock{font-family:var(--disp);font-size:20px;color:var(--amber);letter-spacing:3px;font-weight:700}
.mkt-open{color:var(--green);font-size:11px;font-family:var(--mono)}
.mkt-close{color:var(--red);font-size:11px;font-family:var(--mono)}
.mkt-preopen{color:var(--amber);font-size:11px;font-family:var(--mono)}

/* TICKER */
.ticker-wrap{background:#020802;border:1px solid var(--border);border-left:3px solid var(--amber);padding:6px 0;overflow:hidden;margin-bottom:10px}
.ticker-tape{display:flex;gap:40px;white-space:nowrap;animation:tape 50s linear infinite;font-family:var(--mono);font-size:12px}
@keyframes tape{0%{transform:translateX(0)}100%{transform:translateX(-50%)}}
.tn{color:var(--cyan);font-weight:600}.tp{color:var(--t1)}.tu{color:var(--green)}.td{color:var(--red)}.ts{color:var(--border)}

/* INDEX CARD */
.idx-card{background:var(--card);border:1px solid var(--border);border-radius:6px;padding:14px 16px;position:relative;overflow:hidden;transition:border-color .3s,box-shadow .3s;margin-bottom:6px}
.idx-card::after{content:'';position:absolute;bottom:0;left:0;right:0;height:2px}
.idx-card.up::after{background:linear-gradient(90deg,transparent,var(--green),transparent)}
.idx-card.down::after{background:linear-gradient(90deg,transparent,var(--red),transparent)}
.idx-card:hover{border-color:var(--green2);box-shadow:0 0 20px rgba(0,255,65,.08)}
.idx-name{font-family:var(--disp);font-size:10px;color:var(--t2);letter-spacing:2px;margin-bottom:4px}
.idx-price{font-family:var(--mono);font-size:22px;font-weight:700;color:var(--t1);line-height:1}
.idx-chg{font-family:var(--mono);font-size:13px;margin-top:4px}
.idx-meta{font-family:var(--mono);font-size:10px;color:var(--t3);margin-top:6px;display:flex;justify-content:space-between}
.c-up{color:var(--green)}.c-dn{color:var(--red)}.c-amb{color:var(--amber)}

/* COMMODITY CARD */
.comm-card{background:var(--card);border:1px solid var(--border);border-left:3px solid var(--amber);border-radius:4px;padding:10px 14px;margin-bottom:4px}
.comm-name{font-family:var(--disp);font-size:9px;color:var(--amber);letter-spacing:2px}
.comm-price{font-family:var(--mono);font-size:18px;color:var(--t1)}
.comm-unit{font-size:10px;color:var(--t3)}

/* SECTION HEADER */
.sec-hdr{font-family:var(--disp);font-size:11px;font-weight:700;color:var(--green);letter-spacing:3px;text-transform:uppercase;border-bottom:1px solid var(--border);padding-bottom:6px;margin:16px 0 10px}

/* MARKET TABLE */
.mkt-table{width:100%;border-collapse:collapse;font-family:var(--mono);font-size:12px}
.mkt-table th{background:#050d05;color:var(--green);padding:6px 10px;text-align:right;border-bottom:1px solid var(--border);font-size:10px;letter-spacing:1px;font-family:var(--disp)}
.mkt-table th:first-child{text-align:left}
.mkt-table td{padding:5px 10px;text-align:right;border-bottom:1px solid #0a160a;color:var(--t1)}
.mkt-table td:first-child{text-align:left;color:var(--cyan)}
.mkt-table tr:hover td{background:#0d1e0d}
.tg{color:var(--green);font-weight:600}.tl{color:var(--red);font-weight:600}.tv{color:var(--amber)}
.vb-wrap{width:55px;display:inline-block;background:#0a140a;border-radius:1px;height:4px;vertical-align:middle}
.vb{height:4px;border-radius:1px;background:var(--amber)}

/* BREADTH */
.breadth-panel{background:var(--card);border:1px solid var(--border);border-radius:6px;padding:14px}
.b-title{font-family:var(--disp);font-size:9px;color:var(--t2);letter-spacing:2px;margin-bottom:8px}
.b-num{font-family:var(--mono);font-size:26px;font-weight:700}
.chart-box{background:var(--card);border:1px solid var(--border);border-radius:6px;padding:4px;margin:4px 0}

/* TABS — cursor and pointer-events left untouched */
.stTabs [data-baseweb="tab-list"]{background:var(--bg2)!important;border-bottom:1px solid var(--border)!important}
.stTabs [data-baseweb="tab"]{font-family:var(--disp)!important;font-size:10px!important;font-weight:700!important;letter-spacing:2px!important;color:var(--t2)!important;background:transparent!important;border:none!important;padding:10px 16px!important}
.stTabs [data-baseweb="tab"]:hover{color:var(--t1)!important;background:rgba(0,255,65,.04)!important}
.stTabs [aria-selected="true"]{color:var(--green)!important;border-bottom:2px solid var(--green)!important;background:rgba(0,255,65,.05)!important}
.stTabs [data-baseweb="tab-panel"]{background:var(--bg)!important;padding-top:8px!important}

/* WIDGETS */
.stSelectbox>label{color:var(--t2)!important;font-family:var(--mono)!important;font-size:10px!important}
.stSelectbox>div>div{background:var(--card)!important;border:1px solid var(--border)!important;color:var(--t1)!important}
.stButton>button{background:transparent!important;border:1px solid var(--green2)!important;color:var(--green)!important;font-family:var(--disp)!important;font-size:10px!important;letter-spacing:2px!important;padding:6px 16px!important}
.stButton>button:hover{background:rgba(0,255,65,.06)!important}
div[data-testid="stMetric"]{background:var(--card);border:1px solid var(--border);border-radius:6px;padding:10px 14px}
div[data-testid="stMetric"] label{font-family:var(--disp)!important;font-size:10px!important;color:var(--t2)!important}
div[data-testid="stMetricValue"]{font-family:var(--mono)!important;font-size:22px!important;color:var(--t1)!important}
.stCheckbox label,.stRadio label{color:var(--t2)!important;font-family:var(--mono)!important}
div[data-testid="column"]{padding:2px 4px!important}
div[data-testid="stSidebar"]{background:var(--bg2)!important}
.stSlider label{color:var(--t2)!important;font-family:var(--mono)!important;font-size:10px!important}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# PLOTLY LAYOUT HELPER
# ─────────────────────────────────────────────────────────────────────────────
_PAPER  = "rgba(13,26,13,0.0)"
_PLOT   = "rgba(4,12,4,0.0)"
_FONT   = dict(family="Share Tech Mono, monospace", color="#c8ffc8", size=11)
_HOVER  = dict(bgcolor="#0d1a0d", font_color="#00ff41", bordercolor="#1a3a1a",
               font_family="Share Tech Mono, monospace")
_LEG    = dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#6a9a6a", size=10),
               bordercolor="#1a3a1a")
_MARGIN = dict(l=50, r=20, t=40, b=40)
_AX     = dict(gridcolor="#0d1e0d", showgrid=True, color="#2d5a2d",
               tickfont=dict(color="#6a9a6a", size=10),
               linecolor="#1a3a1a", zeroline=False)
COLORS  = ["#00ff41","#ffb300","#00b4ff","#ff3d3d","#00fff7","#ff6b6b","#c8b96e","#a8ff78"]


def make_layout(height=360, title="", tc="#00ff41", xa=None, ya=None, **kw):
    """Build Plotly layout. xa/ya are override-only — _AX merged here, never in callers."""
    d = dict(
        paper_bgcolor=_PAPER, plot_bgcolor=_PLOT,
        font=_FONT, hoverlabel=_HOVER, legend=_LEG, margin=_MARGIN,
        height=height,
        xaxis=dict(**_AX, **(xa or {})),
        yaxis=dict(**_AX, **(ya or {})),
    )
    if title:
        d["title"] = dict(text=title,
                          font=dict(family="Orbitron", size=11, color=tc), x=0.01)
    d.update(kw)
    return d


# ─────────────────────────────────────────────────────────────────────────────
# SYMBOLS
# ─────────────────────────────────────────────────────────────────────────────
INDIAN_INDICES = {
    "NIFTY 50":     "^NSEI",
    "SENSEX":       "^BSESN",
    "BANK NIFTY":   "^NSEBANK",
    "NIFTY IT":     "^CNXIT",
    "NIFTY FMCG":   "^CNXFMCG",
    "NIFTY AUTO":   "^CNXAUTO",
    "NIFTY PHARMA": "^CNXPHARMA",
    "NIFTY METAL":  "^CNXMETAL",
}
GLOBAL_INDICES = {
    "S&P 500":    "^GSPC",
    "DOW JONES":  "^DJI",
    "NASDAQ":     "^IXIC",
    "FTSE 100":   "^FTSE",
    "DAX":        "^GDAXI",
    "NIKKEI 225": "^N225",
    "HANG SENG":  "^HSI",
    "CAC 40":     "^FCHI",
    "SGX":        "^STI",
    "ASX 200":    "^AXJO",
}
# MCX: (yfinance_symbol, unit_label)
# MCX_SYMBOLS:
#   key → (yf_symbol, base_unit_label, unit_breakdowns)
#   unit_breakdowns: list of (display_label, multiplier)
#   multiplier is applied to ₹/base_unit price to get ₹/display_unit
# Conversion factors:
#   1 troy oz = 31.1035 grams
#   1 barrel  = 158.987 litres
#   1 lb      = 0.453592 kg
#   1 metric ton = 1000 kg
MCX_SYMBOLS = {
    "GOLD":      ("GC=F",  "troy oz",   [("1 gm",   1/31.1035),
                                          ("10 gm",  10/31.1035),
                                          ("100 gm", 100/31.1035)]),
    "SILVER":    ("SI=F",  "troy oz",   [("1 gm",   1/31.1035),
                                          ("100 gm", 100/31.1035),
                                          ("1 kg",   1000/31.1035)]),
    "CRUDE":     ("CL=F",  "barrel",    [("1 bbl",  1),
                                          ("1 litre",1/158.987)]),
    "NAT GAS":   ("NG=F",  "MMBtu",     [("1 MMBtu",1)]),
    "COPPER":    ("HG=F",  "lb",        [("100 gm", 0.1/0.453592),
                                          ("1 kg",   1/0.453592)]),
    "ALUMINIUM": ("ALI=F", "metric ton",[("100 gm", 0.1/1000),
                                          ("1 kg",   1/1000)]),
}
FOREX_SYMBOLS = {
    "USD/INR": "USDINR=X",
    "EUR/INR": "EURINR=X",
    "GBP/INR": "GBPINR=X",
    "JPY/INR": "JPYINR=X",
}
NIFTY50 = {
    "RELIANCE":   "RELIANCE.NS",  "TCS":        "TCS.NS",
    "HDFCBANK":   "HDFCBANK.NS",  "INFY":       "INFY.NS",
    "ICICIBANK":  "ICICIBANK.NS", "KOTAKBANK":  "KOTAKBANK.NS",
    "LT":         "LT.NS",        "HINDUNILVR": "HINDUNILVR.NS",
    "AXISBANK":   "AXISBANK.NS",  "SBIN":       "SBIN.NS",
    "BHARTIARTL": "BHARTIARTL.NS","ITC":        "ITC.NS",
    "BAJFINANCE": "BAJFINANCE.NS","MARUTI":     "MARUTI.NS",
    "SUNPHARMA":  "SUNPHARMA.NS", "TITAN":      "TITAN.NS",
    "WIPRO":      "WIPRO.NS",     "ULTRACEMCO": "ULTRACEMCO.NS",
    "NESTLEIND":  "NESTLEIND.NS", "TECHM":      "TECHM.NS",
    "POWERGRID":  "POWERGRID.NS", "NTPC":       "NTPC.NS",
    "ONGC":       "ONGC.NS",      "JSWSTEEL":   "JSWSTEEL.NS",
    "TATAMOTORS": "TATAMOTORS.NS","TATASTEEL":  "TATASTEEL.NS",
    "HCLTECH":    "HCLTECH.NS",   "DRREDDY":    "DRREDDY.NS",
    "CIPLA":      "CIPLA.NS",     "EICHERMOT":  "EICHERMOT.NS",
    "BPCL":       "BPCL.NS",      "HEROMOTOCO": "HEROMOTOCO.NS",
    "GRASIM":     "GRASIM.NS",    "ADANIPORTS": "ADANIPORTS.NS",
    "COALINDIA":  "COALINDIA.NS", "HINDALCO":   "HINDALCO.NS",
    "INDUSINDBK": "INDUSINDBK.NS","BRITANNIA":  "BRITANNIA.NS",
    "BAJAJFINSV": "BAJAJFINSV.NS","APOLLOHOSP": "APOLLOHOSP.NS",
    "ASIANPAINT": "ASIANPAINT.NS","MM":         "M&M.NS",
    "BAJAJ-AUTO": "BAJAJ-AUTO.NS","DIVISLAB":   "DIVISLAB.NS",
    "SHREECEM":   "SHREECEM.NS",
}
SECTORS = {
    "IT":      ["TCS","INFY","WIPRO","HCLTECH","TECHM"],
    "BANKING": ["HDFCBANK","ICICIBANK","KOTAKBANK","AXISBANK","SBIN","INDUSINDBK"],
    "OIL GAS": ["RELIANCE","ONGC","BPCL"],
    "PHARMA":  ["SUNPHARMA","DRREDDY","CIPLA","DIVISLAB","APOLLOHOSP"],
    "AUTO":    ["MARUTI","TATAMOTORS","BAJAJ-AUTO","HEROMOTOCO","MM","EICHERMOT"],
    "METALS":  ["TATASTEEL","JSWSTEEL","HINDALCO","COALINDIA"],
    "FMCG":    ["HINDUNILVR","ITC","NESTLEIND","BRITANNIA"],
    "INFRA":   ["LT","ADANIPORTS","POWERGRID","NTPC","GRASIM"],
    "FINANCE": ["BAJFINANCE","BAJAJFINSV"],
}
CRYPTO = {
    "BITCOIN":  "BTC-USD",
    "ETHEREUM": "ETH-USD",
    "BNB":      "BNB-USD",
    "SOLANA":   "SOL-USD",
}
PERIOD_IV = {
    "1d":"5m","5d":"30m","1mo":"1d","3mo":"1d",
    "6mo":"1d","1y":"1wk","2y":"1wk","5y":"1mo",
}

# ─────────────────────────────────────────────────────────────────────────────
# DATA FETCHING
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=5, show_spinner=False)
def get_quote(symbol):
    try:
        df = yf.Ticker(symbol).history(period="2d", interval="1d", auto_adjust=True)
        df = df.dropna(subset=["Close"])
        if df.empty:
            return {}
        prev = float(df["Close"].iloc[-2]) if len(df) >= 2 else float(df["Open"].iloc[-1])
        curr = float(df["Close"].iloc[-1])
        chg  = curr - prev
        pct  = (chg / prev * 100) if prev != 0 else 0.0
        vol  = int(df["Volume"].iloc[-1]) if "Volume" in df.columns else 0
        return {
            "price": round(curr, 3), "prev":  round(prev, 3),
            "chg":   round(chg, 3),  "pct":   round(pct, 2),
            "high":  round(float(df["High"].iloc[-1]), 3),
            "low":   round(float(df["Low"].iloc[-1]),  3),
            "open":  round(float(df["Open"].iloc[-1]), 3),
            "vol":   vol,
        }
    except Exception:
        return {}


@st.cache_data(ttl=5, show_spinner=False)
def get_usdinr():
    """Fetch live USD/INR rate for MCX conversion."""
    d = get_quote("USDINR=X")
    return d.get("price", 84.0) if d else 84.0


@st.cache_data(ttl=5, show_spinner=False)
def get_bulk(symbols):
    if not symbols:
        return {}
    try:
        raw = yf.download(symbols, period="2d", interval="1d",
                          group_by="ticker", progress=False, auto_adjust=True)
        out = {}
        for sym in symbols:
            try:
                if len(symbols) > 1:
                    if sym not in raw.columns.get_level_values(0):
                        continue
                    df = raw[sym].copy()
                else:
                    df = raw.copy()
                df = df.dropna(subset=["Close"])
                if df.empty:
                    continue
                prev = float(df["Close"].iloc[-2]) if len(df) >= 2 else float(df["Open"].iloc[-1])
                curr = float(df["Close"].iloc[-1])
                chg  = curr - prev
                pct  = (chg / prev * 100) if prev != 0 else 0.0
                vol  = int(df["Volume"].iloc[-1]) if "Volume" in df.columns else 0
                out[sym] = {
                    "price": round(curr, 3), "prev":  round(prev, 3),
                    "chg":   round(chg, 3),  "pct":   round(pct, 2),
                    "high":  round(float(df["High"].iloc[-1]), 3),
                    "low":   round(float(df["Low"].iloc[-1]),  3),
                    "open":  round(float(df["Open"].iloc[-1]), 3),
                    "vol":   vol,
                }
            except Exception:
                pass
        return out
    except Exception:
        return {}


@st.cache_data(ttl=5, show_spinner=False)
def get_ohlcv(symbol, period="1d", interval="5m"):
    try:
        df = yf.Ticker(symbol).history(period=period, interval=interval, auto_adjust=True)
        df.index = pd.to_datetime(df.index)
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=60, show_spinner=False)
def fetch_all_n50():
    syms = list(NIFTY50.values())
    bulk = get_bulk(syms)
    result = {}
    for name, sym in NIFTY50.items():
        d = bulk.get(sym) or get_quote(sym)
        if d:
            d = dict(d)
            d["name"] = name
            result[name] = d
    return result


def get_movers(n50_data):
    stocks  = [v for v in n50_data.values() if v and "pct" in v]
    gainers = sorted([s for s in stocks if s["pct"] > 0],  key=lambda x: -x["pct"])
    losers  = sorted([s for s in stocks if s["pct"] < 0],  key=lambda x:  x["pct"])
    by_vol  = sorted(stocks, key=lambda x: -x.get("vol", 0))
    return gainers, losers, by_vol


def convert_mcx_to_inr(d, rate):
    """Return a new quote dict with prices multiplied by USD/INR rate."""
    if not d:
        return {}
    m = rate
    return {
        "price": round(d["price"] * m, 2),
        "prev":  round(d["prev"]  * m, 2),
        "chg":   round(d["chg"]   * m, 2),
        "pct":   d["pct"],
        "high":  round(d["high"]  * m, 2),
        "low":   round(d["low"]   * m, 2),
        "open":  round(d["open"]  * m, 2),
        "vol":   d.get("vol", 0),
    }


# ─────────────────────────────────────────────────────────────────────────────
# CHART BUILDERS
# ─────────────────────────────────────────────────────────────────────────────

def chart_line(df, title, color="#00ff41", height=260, show_vwap=False):
    if df.empty:
        return go.Figure()
    r, g, b = int(color[1:3],16), int(color[3:5],16), int(color[5:7],16)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df.index, y=df["Close"], mode="lines",
        line=dict(color=color, width=2),
        fill="tozeroy",
        fillcolor="rgba({},{},{},0.07)".format(r, g, b),
        name="Price",
    ))
    if show_vwap and "Volume" in df.columns and len(df) > 1:
        cvol = df["Volume"].cumsum().replace(0, 1)
        vwap = (df["Close"] * df["Volume"]).cumsum() / cvol
        fig.add_trace(go.Scatter(x=df.index, y=vwap, mode="lines", name="VWAP",
                                  line=dict(color="#ffb300", width=1.2, dash="dash")))
    fig.update_layout(**make_layout(height=height, title=title))
    fig.update_xaxes(rangeslider_visible=False)
    return fig


def chart_candle(df, title, height=380, show_vol=True):
    if df.empty:
        return go.Figure()
    rows = 2 if show_vol else 1
    fig  = make_subplots(rows=rows, cols=1, shared_xaxes=True,
                          vertical_spacing=0.03,
                          row_heights=[0.75, 0.25] if show_vol else [1.0])
    bc = ["#00ff41" if c >= o else "#ff3d3d"
          for c, o in zip(df["Close"].tolist(), df["Open"].tolist())]
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"],
        increasing=dict(line=dict(color="#00ff41",width=1),fillcolor="rgba(0,255,65,0.4)"),
        decreasing=dict(line=dict(color="#ff3d3d",width=1),fillcolor="rgba(255,61,61,0.4)"),
        name="OHLC"), row=1, col=1)
    if len(df) >= 9:
        fig.add_trace(go.Scatter(x=df.index,y=df["Close"].ewm(span=9).mean(),
                                  mode="lines",name="EMA9",
                                  line=dict(color="#ffb300",width=1,dash="dot")),row=1,col=1)
    if len(df) >= 21:
        fig.add_trace(go.Scatter(x=df.index,y=df["Close"].ewm(span=21).mean(),
                                  mode="lines",name="EMA21",
                                  line=dict(color="#00b4ff",width=1,dash="dot")),row=1,col=1)
    if show_vol and "Volume" in df.columns:
        fig.add_trace(go.Bar(x=df.index,y=df["Volume"],marker_color=bc,
                              opacity=0.5,name="Vol"),row=2,col=1)
    fig.update_layout(**make_layout(height=height, title=title))
    fig.update_xaxes(rangeslider_visible=False)
    for rn in range(1, rows+1):
        fig.update_xaxes(gridcolor="#0d1e0d",linecolor="#1a3a1a",
                         tickfont=dict(color="#6a9a6a",size=10),row=rn,col=1)
        fig.update_yaxes(gridcolor="#0d1e0d",linecolor="#1a3a1a",
                         tickfont=dict(color="#6a9a6a",size=10),row=rn,col=1)
    return fig


def chart_multi_line(series_dict, title, height=320, y_suffix=""):
    fig = go.Figure()
    for i, (label, s) in enumerate(series_dict.items()):
        fig.add_trace(go.Scatter(x=s.index, y=s.values, mode="lines", name=label,
                                  line=dict(color=COLORS[i % len(COLORS)], width=1.5)))
    fig.add_hline(y=0, line=dict(color="#2d5a2d", width=1, dash="dot"))
    fig.update_layout(**make_layout(height=height, title=title,
                                     ya=dict(ticksuffix=y_suffix)))
    fig.update_xaxes(rangeslider_visible=False)
    return fig


def chart_bar_v(names, values, title="", tc="#00ff41", height=280, texts=None, y_suffix=""):
    colors = ["#00ff41" if v >= 0 else "#ff3d3d" for v in values]
    kw = dict(marker_color=colors, opacity=0.85)
    if texts:
        kw["text"] = texts
        kw["textposition"] = "outside"
        kw["textfont"] = dict(family="Share Tech Mono", size=9, color="#c8ffc8")
    fig = go.Figure(go.Bar(x=names, y=values, **kw))
    fig.add_hline(y=0, line=dict(color="#2d5a2d", width=1))
    fig.update_layout(**make_layout(height=height, title=title, tc=tc,
                                     ya=dict(ticksuffix=y_suffix)))
    return fig


def chart_bar_h(names, values, title="", tc="#00ff41", height=400, texts=None, x_suffix=""):
    colors = ["#00ff41" if v >= 0 else "#ff3d3d" for v in values]
    kw = dict(marker_color=colors, opacity=0.85)
    if texts:
        kw["text"] = texts
        kw["textposition"] = "outside"
        kw["textfont"] = dict(family="Share Tech Mono", size=9, color="#c8ffc8")
    fig = go.Figure(go.Bar(x=values, y=names, orientation="h", **kw))
    fig.add_vline(x=0, line=dict(color="#2d5a2d", width=1))
    fig.update_layout(**make_layout(height=height, title=title, tc=tc,
                                     xa=dict(ticksuffix=x_suffix),
                                     margin=dict(l=140,r=60,t=40,b=30)))
    return fig


def chart_heatmap(names, pcts, ncols=10, height=260):
    n      = len(names)
    nrows  = (n + ncols - 1) // ncols
    pad    = nrows * ncols - n
    names2 = list(names) + [""] * pad
    pcts2  = list(pcts)  + [0.0] * pad
    z      = np.array(pcts2, dtype=float).reshape(nrows, ncols)
    text   = np.array(
        ["{}\n{:+.2f}%".format(names2[i], pcts2[i]) for i in range(len(names2))]
    ).reshape(nrows, ncols)
    cscale = [[0.0,"#8b0000"],[0.35,"#cc0000"],[0.45,"#2d1a1a"],
               [0.5,"#0d1a0d"],[0.55,"#1a2d1a"],[0.65,"#004d00"],[1.0,"#00cc44"]]
    # FIX: titlefont is invalid — use title=dict(text=..., font=dict(...))
    fig = go.Figure(go.Heatmap(
        z=z, text=text, texttemplate="%{text}",
        colorscale=cscale, zmid=0, zmin=-4, zmax=4,
        textfont=dict(family="Share Tech Mono", size=9, color="white"),
        showscale=True,
        colorbar=dict(
            title=dict(
                text="% CHG",
                font=dict(color="#6a9a6a", family="Orbitron", size=9),
            ),
            tickfont=dict(color="#6a9a6a", size=9),
            outlinecolor="#1a3a1a",
            bgcolor="rgba(0,0,0,0)",
        ),
    ))
    fig.update_layout(**make_layout(
        height=height, title="NIFTY 50 — PERFORMANCE GRID",
        xa=dict(visible=False),
        ya=dict(visible=False),
        margin=dict(l=10,r=70,t=40,b=10),
    ))
    return fig


def chart_treemap(sector_data):
    labels, values, parents, colors = [], [], [], []
    for sec, stocks in sector_data.items():
        pcts = [d["pct"] for d in stocks.values() if d and "pct" in d]
        avg  = float(np.mean(pcts)) if pcts else 0.0
        labels.append(sec); values.append(abs(avg)+0.5); parents.append("")
        colors.append("#00c853" if avg>1 else "#1b5e20" if avg>0 else "#b71c1c" if avg>-1 else "#ff1744")
        for stk, d in stocks.items():
            if d and "pct" in d:
                p = d["pct"]
                labels.append(stk); values.append(abs(p)+0.1); parents.append(sec)
                colors.append("#00c853" if p>2 else "#1b5e20" if p>0 else "#b71c1c" if p>-2 else "#ff1744")
    fig = go.Figure(go.Treemap(
        labels=labels, values=values, parents=parents,
        marker=dict(colors=colors, line=dict(color="#040c04", width=2)),
        textfont=dict(family="Share Tech Mono", color="white", size=11),
        hovertemplate="<b>%{label}</b><extra></extra>",
    ))
    fig.update_layout(**make_layout(height=340, title="SECTOR PERFORMANCE — TREEMAP",
                                     margin=dict(l=0,r=0,t=36,b=0)))
    return fig


def chart_advanced(df, title, chart_type="Candlestick", height=680):
    if df.empty:
        return go.Figure()
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True,
                         vertical_spacing=0.03, row_heights=[0.60,0.20,0.20])
    bc = ["#00ff41" if c >= o else "#ff3d3d"
          for c, o in zip(df["Close"].tolist(), df["Open"].tolist())]
    if chart_type == "Candlestick":
        fig.add_trace(go.Candlestick(
            x=df.index, open=df["Open"], high=df["High"],
            low=df["Low"], close=df["Close"],
            increasing=dict(line=dict(color="#00ff41",width=1),fillcolor="rgba(0,255,65,0.4)"),
            decreasing=dict(line=dict(color="#ff3d3d",width=1),fillcolor="rgba(255,61,61,0.4)"),
            name="OHLC"), row=1, col=1)
    elif chart_type == "OHLC":
        fig.add_trace(go.Ohlc(
            x=df.index, open=df["Open"], high=df["High"],
            low=df["Low"], close=df["Close"],
            increasing_line_color="#00ff41", decreasing_line_color="#ff3d3d",
            name="OHLC"), row=1, col=1)
    else:
        cl = "#00ff41" if float(df["Close"].iloc[-1]) >= float(df["Close"].iloc[0]) else "#ff3d3d"
        r2,g2,b2 = int(cl[1:3],16),int(cl[3:5],16),int(cl[5:7],16)
        fig.add_trace(go.Scatter(
            x=df.index, y=df["Close"], mode="lines",
            line=dict(color=cl, width=2), fill="tozeroy",
            fillcolor="rgba({},{},{},0.06)".format(r2,g2,b2),
            name="Price"), row=1, col=1)
    if len(df) >= 20:
        ema20 = df["Close"].ewm(span=20).mean()
        sma20 = df["Close"].rolling(20).mean()
        std20 = df["Close"].rolling(20).std()
        fig.add_trace(go.Scatter(x=df.index,y=ema20,mode="lines",name="EMA20",
                                  line=dict(color="#ffb300",width=1,dash="dot")),row=1,col=1)
        fig.add_trace(go.Scatter(x=df.index,y=sma20+2*std20,mode="lines",name="BB+",
                                  showlegend=False,
                                  line=dict(color="#2d5a2d",width=1,dash="dot")),row=1,col=1)
        fig.add_trace(go.Scatter(x=df.index,y=sma20-2*std20,mode="lines",name="BB-",
                                  showlegend=False,fill="tonexty",
                                  fillcolor="rgba(0,255,65,0.03)",
                                  line=dict(color="#2d5a2d",width=1,dash="dot")),row=1,col=1)
    if len(df) >= 50:
        fig.add_trace(go.Scatter(x=df.index,y=df["Close"].ewm(span=50).mean(),
                                  mode="lines",name="EMA50",
                                  line=dict(color="#00b4ff",width=1,dash="dot")),row=1,col=1)
    if "Volume" in df.columns:
        fig.add_trace(go.Bar(x=df.index,y=df["Volume"],marker_color=bc,
                              opacity=0.6,name="Vol"),row=2,col=1)
    if len(df) >= 26:
        macd   = df["Close"].ewm(span=12).mean() - df["Close"].ewm(span=26).mean()
        signal = macd.ewm(span=9).mean()
        hist   = macd - signal
        hc = ["#00ff41" if float(v) >= 0 else "#ff3d3d" for v in hist.tolist()]
        fig.add_trace(go.Bar(x=df.index,y=hist,marker_color=hc,
                              opacity=0.7,name="MACD Hist"),row=3,col=1)
        fig.add_trace(go.Scatter(x=df.index,y=macd,mode="lines",name="MACD",
                                  line=dict(color="#00fff7",width=1.5)),row=3,col=1)
        fig.add_trace(go.Scatter(x=df.index,y=signal,mode="lines",name="Signal",
                                  line=dict(color="#ffb300",width=1)),row=3,col=1)
    fig.update_layout(
        paper_bgcolor=_PAPER, plot_bgcolor=_PLOT,
        font=_FONT, hoverlabel=_HOVER, legend=_LEG,
        margin=dict(l=50,r=20,t=40,b=40), height=height,
        title=dict(text=title,font=dict(family="Orbitron",size=12,color="#00ff41"),x=0.01),
        xaxis_rangeslider_visible=False,
    )
    for rn in [1,2,3]:
        fig.update_xaxes(gridcolor="#0d1e0d",linecolor="#1a3a1a",
                         tickfont=dict(color="#6a9a6a",size=10),row=rn,col=1)
        fig.update_yaxes(gridcolor="#0d1e0d",linecolor="#1a3a1a",
                         tickfont=dict(color="#6a9a6a",size=10),row=rn,col=1)
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# HTML HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def fmt_vol(v):
    v = int(v)
    if v >= 10_000_000: return "{:.2f}Cr".format(v/10_000_000)
    if v >= 100_000:    return "{:.2f}L".format(v/100_000)
    if v >= 1_000:      return "{:.1f}K".format(v/1_000)
    return str(v)


def market_status():
    now = datetime.now()
    wd  = now.weekday()
    hr  = now.hour + now.minute/60.0
    if wd < 5 and 9.25 <= hr < 15.5:  return "MARKET OPEN",   "mkt-open"
    if wd < 5 and 9.0  <= hr < 9.25:  return "PRE-OPEN",      "mkt-preopen"
    return "MARKET CLOSED", "mkt-close"


def render_header():
    """
    Entire header rendered inside st.components.v1.html() so the
    clock JS and the #qmt-clock element live in the SAME document —
    no cross-iframe/parent-DOM issues.
    """
    import streamlit.components.v1 as components
    st_txt, st_cls = market_status()

    now  = datetime.now()
    date = now.strftime("%d %b %Y")

    STATUS_COLOR = {"mkt-open": "#00ff41", "mkt-preopen": "#ffb300", "mkt-close": "#ff3d3d"}
    st_color = STATUS_COLOR.get(st_cls, "#ff3d3d")

    header_html = """
<!DOCTYPE html>
<html>
<head>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Share+Tech+Mono&family=Exo+2:wght@400;600&display=swap');
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{
    background: linear-gradient(135deg,#020802,#041204,#061806);
    border: 1px solid #00cc33;
    border-top: 3px solid #00ff41;
    border-radius: 6px;
    padding: 12px 20px;
    font-family: 'Exo 2', sans-serif;
    overflow: hidden;
  }}
  body::before {{
    content: '';
    position: fixed;
    top: 0; left: -100%;
    width: 60%; height: 100%;
    background: linear-gradient(90deg,transparent,rgba(0,255,65,.04),transparent);
    animation: scan 5s linear infinite;
  }}
  @keyframes scan {{ 0%{{left:-100%}} 100%{{left:200%}} }}
  .wrap {{ display:flex; justify-content:space-between; align-items:center; }}
  .title {{
    font-family: 'Orbitron', sans-serif;
    font-size: 20px; font-weight: 900;
    color: #00ff41; letter-spacing: 4px;
    text-shadow: 0 0 20px rgba(0,255,65,.6), 0 0 40px rgba(0,255,65,.3);
    animation: glow 3s ease-in-out infinite;
  }}
  @keyframes glow {{
    0%,100% {{ text-shadow: 0 0 20px rgba(0,255,65,.6),0 0 40px rgba(0,255,65,.3); }}
    50%      {{ text-shadow: 0 0 30px rgba(0,255,65,.9),0 0 60px rgba(0,255,65,.5); }}
  }}
  .dot {{
    display:inline-block; width:8px; height:8px;
    border-radius:50%; background:#00ff41;
    box-shadow: 0 0 8px #00ff41;
    animation: blink 1.2s ease-in-out infinite;
    margin-right: 6px;
  }}
  @keyframes blink {{ 0%,100%{{opacity:1}} 50%{{opacity:.3}} }}
  .sub  {{ font-family:'Share Tech Mono',monospace; font-size:11px; color:#6a9a6a; letter-spacing:2px; margin-top:2px; }}
  .clock {{ font-family:'Orbitron',sans-serif; font-size:22px; font-weight:700; color:#ffb300; letter-spacing:3px; text-align:right; }}
  .status {{ font-size:11px; font-family:'Share Tech Mono',monospace; color:{st_color}; text-align:right; }}
  .date  {{ font-size:10px; font-family:'Share Tech Mono',monospace; color:#2d5a2d; text-align:right; }}
</style>
</head>
<body>
  <div class="wrap">
    <div>
      <div class="title"><span class="dot"></span>MARKET TERMINAL By C.V.Siva Vara Prasad</div>
      <div class="sub">LIVE &bull; NSE &bull; BSE &bull; MCX (INR) &bull; GLOBAL &bull; FOREX &bull; CRYPTO</div>
    </div>
    <div>
      <div class="clock" id="clk">--:--:--</div>
      <div class="status">&bull; {st_txt}</div>
      <div class="date">{date}</div>
    </div>
  </div>
  <script>
    function pad(n){{ return n<10?'0'+n:''+n; }}
    function tick(){{
      var d=new Date();
      document.getElementById('clk').textContent =
        pad(d.getHours())+':'+pad(d.getMinutes())+':'+pad(d.getSeconds());
    }}
    tick();
    setInterval(tick, 1000);
  </script>
</body>
</html>
""".format(st_color=st_color, st_txt=st_txt, date=date)

    components.html(header_html, height=75)


def render_ticker(data_dict):
    items = []
    for name, d in data_dict.items():
        if not d: continue
        arrow = "&#9650;" if d["chg"] >= 0 else "&#9660;"
        cls   = "tu" if d["chg"] >= 0 else "td"
        items.append(
            "<span style='display:inline-flex;gap:6px;align-items:center'>"
            "<span class='tn'>{nm}</span>"
            "<span class='tp'>{price}</span>"
            "<span class='{cls}'>{arrow}{pct}%</span>"
            "<span class='ts'>|</span></span>".format(
                nm=name, price="{:,.2f}".format(d["price"]),
                cls=cls, arrow=arrow, pct="{:+.2f}".format(d["pct"]),
            )
        )
    tape = "".join(items * 2)
    st.markdown(
        "<div class='ticker-wrap'><div class='ticker-tape'>{}</div></div>".format(tape),
        unsafe_allow_html=True)


def idx_card(name, d):
    if not d:
        return ("<div class='idx-card'><div class='idx-name'>{}</div>"
                "<div class='idx-price' style='color:#2d5a2d'>N/A</div></div>").format(name)
    up  = d["chg"] >= 0
    cc  = "#00ff41" if up else "#ff3d3d"
    arr = "&#9650;" if up else "&#9660;"
    cls = "up" if up else "down"
    return (
        "<div class='idx-card {cls}'>"
        "<div class='idx-name'>{name}</div>"
        "<div class='idx-price'>{price}</div>"
        "<div class='idx-chg' style='color:{cc}'>{arr} {chg} ({pct}%)</div>"
        "<div class='idx-meta'>"
        "<span>H:{high}</span><span>L:{low}</span><span>O:{open}</span>"
        "</div></div>"
    ).format(
        cls=cls, name=name,
        price="{:,.2f}".format(d["price"]), cc=cc, arr=arr,
        chg="{:+,.2f}".format(d["chg"]),   pct="{:+.2f}".format(d["pct"]),
        high="{:,.2f}".format(d["high"]),  low="{:,.2f}".format(d["low"]),
        open="{:,.2f}".format(d["open"]),
    )


def fmt_inr(v):
    """Format an INR price nicely — auto-selects decimal places."""
    if v >= 1000:  return "{:,.0f}".format(v)
    if v >= 10:    return "{:,.1f}".format(v)
    return "{:,.2f}".format(v)


def mcx_inr_card(nm, d_inr):
    """
    MCX card showing price in Indian Rupees with per-unit breakdown.
    unit_breakdowns from MCX_SYMBOLS[nm][2]: [(label, multiplier), ...]
    multiplier is applied to d_inr["price"] (₹/base_unit) to get ₹/display_unit.
    """
    if not d_inr:
        return ("<div class='idx-card'><div class='idx-name' style='color:#ffb300'>{}</div>"
                "<div class='idx-price' style='color:#2d5a2d'>N/A</div></div>").format(nm)

    cc  = "#00ff41" if d_inr["chg"] >= 0 else "#ff3d3d"
    arr = "&#9650;" if d_inr["chg"] >= 0 else "&#9660;"
    cls = "up" if d_inr["chg"] >= 0 else "down"

    # Get unit breakdowns from MCX_SYMBOLS
    breakdowns = MCX_SYMBOLS.get(nm, (None, None, []))[2]
    base_price = d_inr["price"]

    # Build unit rows — each breakdown shown as "label: ₹X"
    unit_rows = ""
    for label, mult in breakdowns:
        unit_val = base_price * mult
        unit_rows += (
            "<div style='display:flex;justify-content:space-between;"
            "font-family:Share Tech Mono,monospace;font-size:10px;"
            "color:#c8ffc8;border-top:1px solid #0d1e0d;padding-top:3px;margin-top:3px'>"
            "<span style='color:#6a9a6a'>{label}</span>"
            "<span>&#8377;{val}</span>"
            "</div>"
        ).format(label=label, val=fmt_inr(unit_val))

    return (
        "<div class='idx-card {cls}'>"
        "<div class='idx-name' style='color:#ffb300'>{nm}</div>"
        "<div class='idx-price' style='font-size:16px'>&#8377;{price} "
        "<span style='font-size:10px;color:#2d5a2d'>/base</span></div>"
        "<div class='idx-chg' style='color:{cc}'>{arr} {pct}% "
        "<span style='font-size:10px;color:{cc}'>({chg})</span></div>"
        "{unit_rows}"
        "<div class='idx-meta' style='margin-top:4px'>"
        "<span>H:&#8377;{hi}</span><span>L:&#8377;{lo}</span>"
        "</div></div>"
    ).format(
        cls=cls, nm=nm,
        price=fmt_inr(base_price), cc=cc, arr=arr,
        pct="{:+.2f}".format(d_inr["pct"]),
        chg="&#8377;{:+,.0f}".format(d_inr["chg"]),
        unit_rows=unit_rows,
        hi=fmt_inr(d_inr["high"]), lo=fmt_inr(d_inr["low"]),
    )


def stock_table(stocks, max_vol):
    rows = []
    for i, s in enumerate(stocks[:15], 1):
        up  = s["pct"] >= 0
        cc  = "#00ff41" if up else "#ff3d3d"
        arr = "&#9650;" if up else "&#9660;"
        vp  = int((s["vol"] / max_vol) * 100) if max_vol > 0 else 0
        rows.append(
            "<tr>"
            "<td><span style='color:#2d5a2d;font-size:10px'>{rank:02d}</span> {nm}</td>"
            "<td>{price}</td>"
            "<td style='color:{cc}'>{arr}{chg}</td>"
            "<td style='color:{cc}'>{pct}%</td>"
            "<td class='tv'>{vol}"
            "<div class='vb-wrap'><div class='vb' style='width:{vp}%'></div></div></td>"
            "<td style='color:#2d5a2d;font-size:10px'>{hi}/{lo}</td>"
            "</tr>".format(
                rank=i, nm=s["name"],
                price="{:,.2f}".format(s["price"]), cc=cc, arr=arr,
                chg="{:+.2f}".format(s["chg"]),    pct="{:+.2f}".format(s["pct"]),
                vol=fmt_vol(s["vol"]), vp=vp,
                hi="{:,.2f}".format(s.get("high",0)),
                lo="{:,.2f}".format(s.get("low",0)),
            )
        )
    return (
        "<table class='mkt-table'><thead><tr>"
        "<th>SYMBOL</th><th>PRICE</th><th>CHG</th>"
        "<th>%CHG</th><th>VOLUME</th><th>H/L</th>"
        "</tr></thead><tbody>{}</tbody></table>"
    ).format("".join(rows))


def shdr(label, color=None):
    sty = "style='color:{}'".format(color) if color else ""
    return "<div class='sec-hdr' {s}>{l}</div>".format(s=sty, l=label)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN APP
# ─────────────────────────────────────────────────────────────────────────────

def main():
    render_header()

    # ── Controls ──────────────────────────────────────────────────────────────
    c1, c2, c3 = st.columns([3, 3, 1])
    with c1:
        auto_rf = st.checkbox("AUTO REFRESH", value=False)
    with c2:
        rf_sec = 5
        if auto_rf:
            rf_sec = st.select_slider(
                "REFRESH EVERY",
                options=[1, 5, 15, 30, 60, 120, 300], value=5,
                format_func=lambda x: "{}s".format(x))
    with c3:
        if st.button("REFRESH NOW"):
            st.cache_data.clear()
            st.rerun()

    # chart_period fixed to 1mo (DEFAULT PERIOD removed from UI)
    chart_period = "1mo"

    # ── Fetch data ────────────────────────────────────────────────────────────
    with st.spinner("Fetching live market data..."):
        usd_inr   = get_usdinr()
        idx_data  = {n: get_quote(s) for n, s in INDIAN_INDICES.items()}
        glo_data  = {n: get_quote(s) for n, s in GLOBAL_INDICES.items()}
        mcx_usd   = {n: get_quote(vals[0]) for n, vals in MCX_SYMBOLS.items()}
        # FIX: convert ALL MCX quotes to INR
        mcx_data  = {n: convert_mcx_to_inr(d, usd_inr) for n, d in mcx_usd.items()}
        fx_data   = {n: get_quote(s) for n, s in FOREX_SYMBOLS.items()}


    # Ticker tape (show MCX in INR)
    tick_src = dict(idx_data)
    for k, v in mcx_data.items():
        tick_src["MCX-"+k] = v
    for k in ["S&P 500","NASDAQ","DOW JONES","NIKKEI 225"]:
        if glo_data.get(k):
            tick_src[k] = glo_data[k]
    render_ticker(tick_src)

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab1,tab2,tab3,tab4,tab5,tab6,tab7,tab8 = st.tabs([
        "LIVE OVERVIEW", "INDIAN INDICES", "MCX COMMODITIES",
        "GLOBAL INDICES", "MOVERS & VOLUME", "SECTOR HEATMAP",
        "CHART STUDIO",   "FOREX & CRYPTO",
    ])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 1 — LIVE OVERVIEW
    # ══════════════════════════════════════════════════════════════════════════
    with tab1:
        st.markdown(shdr("KEY BENCHMARKS"), unsafe_allow_html=True)
        idx_list = list(INDIAN_INDICES.keys())
        for rs in range(0, len(idx_list), 4):
            chunk = idx_list[rs:rs+4]
            cols  = st.columns(len(chunk))
            for j, nm in enumerate(chunk):
                cols[j].markdown(idx_card(nm, idx_data.get(nm,{})), unsafe_allow_html=True)

        # MCX strip + forex — show primary per-unit price
        st.markdown(shdr("MCX COMMODITIES — LIVE (INR)"), unsafe_allow_html=True)
        sc = st.columns(6)
        for i, nm in enumerate(list(MCX_SYMBOLS.keys())[:5]):
            d = mcx_data.get(nm, {})
            with sc[i]:
                if d:
                    cc  = "#00ff41" if d["chg"] >= 0 else "#ff3d3d"
                    arr = "&#9650;" if d["chg"] >= 0 else "&#9660;"
                    # Show primary unit (first breakdown entry)
                    bk = MCX_SYMBOLS[nm][2]
                    if bk:
                        pri_label, pri_mult = bk[0]
                        pri_val = d["price"] * pri_mult
                        unit_line = "&#8377;{} / {}".format(fmt_inr(pri_val), pri_label)
                        # second breakdown if exists
                        if len(bk) > 1:
                            sec_label, sec_mult = bk[1]
                            sec_val = d["price"] * sec_mult
                            unit_line += "<br><span style='font-size:10px;color:#6a9a6a'>&#8377;{} / {}</span>".format(fmt_inr(sec_val), sec_label)
                    else:
                        unit_line = "&#8377;{:,.0f}".format(d["price"])
                    st.markdown(
                        "<div class='comm-card'>"
                        "<div class='comm-name'>{nm}</div>"
                        "<div class='comm-price' style='font-size:14px'>{unit}</div>"
                        "<div style='color:{cc};font-family:var(--mono);font-size:11px'>"
                        "{arr} {pct}%</div></div>".format(
                            nm=nm, unit=unit_line,
                            cc=cc, arr=arr, pct="{:+.2f}".format(d["pct"]),
                        ), unsafe_allow_html=True)
        with sc[5]:
            usd = fx_data.get("USD/INR", {})
            if usd:
                cc  = "#00ff41" if usd["chg"] >= 0 else "#ff3d3d"
                arr = "&#9650;" if usd["chg"] >= 0 else "&#9660;"
                st.markdown(
                    "<div class='comm-card' style='border-left-color:#00b4ff'>"
                    "<div class='comm-name' style='color:#00b4ff'>USD/INR</div>"
                    "<div class='comm-price'>&#8377;{price}</div>"
                    "<div style='color:{cc};font-family:var(--mono);font-size:11px'>"
                    "{arr} {pct}%</div></div>".format(
                        price="{:.4f}".format(usd["price"]), cc=cc, arr=arr,
                        pct="{:+.2f}".format(usd["pct"]),
                    ), unsafe_allow_html=True)

        # Nifty 5-min + breadth
        st.markdown(shdr("NIFTY 50 — 5-MIN INTRADAY"), unsafe_allow_html=True)
        lc1, lc2 = st.columns([3, 1])
        with lc1:
            df_n = get_ohlcv("^NSEI", "1d", "5m")
            if not df_n.empty:
                cn = "#00ff41" if float(df_n["Close"].iloc[-1]) >= float(df_n["Open"].iloc[0]) else "#ff3d3d"
                st.markdown("<div class='chart-box'>", unsafe_allow_html=True)
                st.plotly_chart(chart_line(df_n, "NIFTY 50  5-MIN  VWAP",
                                            color=cn, height=280, show_vwap=True),
                                use_container_width=True, config={"displayModeBar": False})
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.info("Nifty data unavailable.")
        with lc2:
            n50d = fetch_all_n50()
            adv  = sum(1 for v in n50d.values() if v and v["pct"] > 0)
            dec  = sum(1 for v in n50d.values() if v and v["pct"] < 0)
            unch = max(0, len(n50d) - adv - dec)
            tot  = max(adv + dec + unch, 1)
            ap   = adv / tot * 100
            dp   = (adv + unch) / tot * 100
            st.markdown(
                "<div class='breadth-panel'>"
                "<div class='b-title'>MARKET BREADTH N50</div>"
                "<div style='display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;text-align:center'>"
                "<div><div class='b-num c-up'>{adv}</div>"
                "<div style='font-family:var(--mono);font-size:9px;color:#6a9a6a'>ADV</div></div>"
                "<div><div class='b-num c-amb'>{unch}</div>"
                "<div style='font-family:var(--mono);font-size:9px;color:#6a9a6a'>UNCH</div></div>"
                "<div><div class='b-num c-dn'>{dec}</div>"
                "<div style='font-family:var(--mono);font-size:9px;color:#6a9a6a'>DEC</div></div>"
                "</div>"
                "<div style='margin-top:10px;height:6px;border-radius:3px;"
                "background:#0a140a;overflow:hidden'>"
                "<div style='height:6px;background:linear-gradient(90deg,"
                "#00ff41 {ap:.0f}%,#ffb300 {dp:.0f}%,#ff3d3d 100%)'></div></div>"
                "<div style='font-family:var(--mono);font-size:10px;color:#2d5a2d;"
                "margin-top:6px;text-align:center'>A/D = {adv}/{dec}</div>"
                "</div>".format(adv=adv,unch=unch,dec=dec,ap=ap,dp=dp),
                unsafe_allow_html=True)

        st.markdown(shdr("SENSEX — 5-MIN"), unsafe_allow_html=True)
        df_s = get_ohlcv("^BSESN", "1d", "5m")
        if not df_s.empty:
            cs = "#00ff41" if float(df_s["Close"].iloc[-1]) >= float(df_s["Open"].iloc[0]) else "#ff3d3d"
            st.plotly_chart(chart_line(df_s, "BSE SENSEX  5-MIN", color=cs, height=220),
                            use_container_width=True, config={"displayModeBar": False})

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 2 — INDIAN INDICES
    # ══════════════════════════════════════════════════════════════════════════
    with tab2:
        st.markdown(shdr("ALL INDIAN INDICES"), unsafe_allow_html=True)
        idx_list2 = list(INDIAN_INDICES.keys())
        for rs in range(0, len(idx_list2), 4):
            chunk = idx_list2[rs:rs+4]
            cols  = st.columns(len(chunk))
            for j, nm in enumerate(chunk):
                cols[j].markdown(idx_card(nm, idx_data.get(nm,{})), unsafe_allow_html=True)

        st.markdown(shdr("RELATIVE PERFORMANCE"), unsafe_allow_html=True)
        iv = PERIOD_IV.get(chart_period, "1d")
        series = {}
        for nm, sym in list(INDIAN_INDICES.items())[:6]:
            dfi = get_ohlcv(sym, period=chart_period, interval=iv)
            if not dfi.empty and float(dfi["Close"].iloc[0]) != 0:
                series[nm] = (dfi["Close"] / dfi["Close"].iloc[0] - 1) * 100
        if series:
            st.plotly_chart(
                chart_multi_line(series,
                                  "RELATIVE PERFORMANCE  " + chart_period.upper(),
                                  height=320, y_suffix="%"),
                use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Loading chart data...")

        st.markdown(shdr("NIFTY 50 CONSTITUENTS"), unsafe_allow_html=True)
        n50d = fetch_all_n50()
        rows_list = [
            {"Symbol": nm, "Price": d["price"], "Change": d["chg"],
             "Pct Change": d["pct"], "Volume": d["vol"],
             "High": d["high"], "Low": d["low"]}
            for nm, d in n50d.items() if d
        ]
        if rows_list:
            df_tbl = pd.DataFrame(rows_list).sort_values("Pct Change", ascending=False)
            def cv(val):
                if isinstance(val,(int,float)):
                    if val > 0: return "color:#00ff41"
                    if val < 0: return "color:#ff3d3d"
                return ""
            st.dataframe(
                df_tbl.style.applymap(cv, subset=["Pct Change","Change"])
                .format({"Price":"{:,.2f}","Change":"{:+.2f}","Pct Change":"{:+.2f}%",
                         "Volume":"{:,}","High":"{:,.2f}","Low":"{:,.2f}"}),
                use_container_width=True, hide_index=True, height=450)
        else:
            st.info("Loading stock data...")

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 3 — MCX COMMODITIES (prices in INR)
    # ══════════════════════════════════════════════════════════════════════════
    with tab3:
        st.markdown(
            shdr("MCX COMMODITY FUTURES — PRICES IN INDIAN RUPEES (&#8377;)"),
            unsafe_allow_html=True)
        st.markdown(
            "<div style='font-family:Share Tech Mono,monospace;font-size:10px;"
            "color:#2d5a2d;margin-bottom:8px'>USD/INR rate: &#8377;{:.4f} &bull; "
            "All prices converted from USD to INR</div>".format(usd_inr),
            unsafe_allow_html=True)
        mcx_list = list(MCX_SYMBOLS.keys())
        for rs in range(0, len(mcx_list), 3):
            chunk = mcx_list[rs:rs+3]
            cols  = st.columns(len(chunk))
            for j, nm in enumerate(chunk):
                cols[j].markdown(
                    mcx_inr_card(nm, mcx_data.get(nm,{})),
                    unsafe_allow_html=True)

        st.markdown(shdr("COMMODITY CHART (INR)"), unsafe_allow_html=True)
        cc1, cc2 = st.columns([1, 3])
        with cc1:
            sel_c = st.selectbox("COMMODITY", list(MCX_SYMBOLS.keys()),
                                  index=0, key="mcx_sel_tab3")
            ch_p  = st.select_slider("PERIOD",
                                      options=["1d","5d","1mo","3mo","6mo","1y"],
                                      value="1mo", key="mcx_per_tab3")
        df_c = get_ohlcv(MCX_SYMBOLS[sel_c][0], period=ch_p,
                          interval=PERIOD_IV.get(ch_p,"1d"))
        # Convert OHLCV to INR
        if not df_c.empty:
            df_c_inr = df_c.copy()
            for col in ["Open","High","Low","Close"]:
                df_c_inr[col] = df_c_inr[col] * usd_inr
            with cc2:
                st.plotly_chart(
                    chart_candle(df_c_inr,
                                  sel_c + " (INR)  " + ch_p.upper(), height=340),
                    use_container_width=True, config={"displayModeBar": False})
        else:
            with cc2:
                st.info("No chart data available.")

        st.markdown(shdr("DAILY % CHANGE"), unsafe_allow_html=True)
        cn = [n for n, d in mcx_data.items() if d]
        cp = [mcx_data[n]["pct"] for n in cn]
        if cn:
            st.plotly_chart(
                chart_bar_v(cn, cp, title="MCX DAILY % CHANGE", tc="#ffb300",
                             height=260,
                             texts=["{:+.2f}%".format(p) for p in cp],
                             y_suffix="%"),
                use_container_width=True, config={"displayModeBar": False})

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 4 — GLOBAL INDICES
    # ══════════════════════════════════════════════════════════════════════════
    with tab4:
        st.markdown(shdr("GLOBAL MARKETS"), unsafe_allow_html=True)
        glo_list = list(GLOBAL_INDICES.keys())
        for rs in range(0, len(glo_list), 5):
            chunk = glo_list[rs:rs+5]
            cols  = st.columns(len(chunk))
            for j, nm in enumerate(chunk):
                cols[j].markdown(idx_card(nm, glo_data.get(nm,{})), unsafe_allow_html=True)

        st.markdown(shdr("GLOBAL BUBBLE MAP"), unsafe_allow_html=True)
        gn  = [n for n, d in glo_data.items() if d]
        gp  = [glo_data[n]["pct"]   for n in gn]
        gpr = [glo_data[n]["price"] for n in gn]
        regions = (["Americas","Americas","Americas","Europe","Europe",
                     "Asia","Asia","Europe","Asia","Asia"])[:len(gn)]
        if gn:
            fig_bub = go.Figure()
            for region in sorted(set(regions)):
                ri = [i for i, r in enumerate(regions) if r == region]
                fig_bub.add_trace(go.Scatter(
                    x=[gp[i] for i in ri], y=[gpr[i] for i in ri],
                    mode="markers+text", name=region,
                    text=[gn[i] for i in ri], textposition="top center",
                    textfont=dict(size=9, family="Share Tech Mono", color="#c8ffc8"),
                    marker=dict(
                        size=[abs(gp[i])*12+12 for i in ri],
                        color=["#00ff41" if gp[i]>=0 else "#ff3d3d" for i in ri],
                        opacity=0.8, line=dict(color="#1a3a1a", width=1))))
            fig_bub.add_vline(x=0, line=dict(color="#2d5a2d", width=1, dash="dot"))
            fig_bub.update_layout(**make_layout(
                height=380, title="GLOBAL INDICES BUBBLE MAP", tc="#00fff7",
                xa=dict(title="% Change", ticksuffix="%"),
                ya=dict(title="Price Level")))
            st.plotly_chart(fig_bub, use_container_width=True,
                            config={"displayModeBar": False})

        st.markdown(shdr("ALL INDICES DAILY % CHANGE"), unsafe_allow_html=True)
        all_c = {}
        all_c.update(idx_data)
        all_c.update(glo_data)
        an = [n for n, d in all_c.items() if d and "pct" in d]
        ap2 = [all_c[n]["pct"] for n in an]
        if an:
            st.plotly_chart(
                chart_bar_h(an, ap2, title="INDIA + GLOBAL DAILY % CHANGE",
                             tc="#00fff7", height=520,
                             texts=["{:+.2f}%".format(p) for p in ap2],
                             x_suffix="%"),
                use_container_width=True, config={"displayModeBar": False})

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 5 — MOVERS & VOLUME
    # ══════════════════════════════════════════════════════════════════════════
    with tab5:
        n50d = fetch_all_n50()
        gainers, losers, by_vol = get_movers(n50d)
        max_v = max((s.get("vol",0) for s in by_vol), default=1)

        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown(shdr("TOP GAINERS", "#00ff41"), unsafe_allow_html=True)
            st.markdown(stock_table(gainers, max_v) if gainers else "<p style='color:#2d5a2d;font-family:var(--mono)'>No data</p>",
                        unsafe_allow_html=True)
        with m2:
            st.markdown(shdr("TOP LOSERS", "#ff3d3d"), unsafe_allow_html=True)
            st.markdown(stock_table(losers, max_v) if losers else "<p style='color:#2d5a2d;font-family:var(--mono)'>No data</p>",
                        unsafe_allow_html=True)
        with m3:
            st.markdown(shdr("TOP VOLUME", "#ffb300"), unsafe_allow_html=True)
            st.markdown(stock_table(by_vol, max_v) if by_vol else "<p style='color:#2d5a2d;font-family:var(--mono)'>No data</p>",
                        unsafe_allow_html=True)

        st.markdown(shdr("NIFTY 50 — PERFORMANCE GRID"), unsafe_allow_html=True)
        all_s = sorted([(nm,d) for nm,d in n50d.items() if d], key=lambda x:-x[1]["pct"])
        if all_s:
            st.plotly_chart(
                chart_heatmap([s[0] for s in all_s],[s[1]["pct"] for s in all_s]),
                use_container_width=True, config={"displayModeBar": False})

        st.markdown(shdr("VOLUME LEADERS — TOP 15"), unsafe_allow_html=True)
        t15 = sorted([(nm,d) for nm,d in n50d.items() if d],
                      key=lambda x:-x[1].get("vol",0))[:15]
        if t15:
            vn = [s[0] for s in t15]
            vv = [s[1]["vol"] for s in t15]
            vc = ["#00ff41" if s[1]["pct"]>=0 else "#ff3d3d" for s in t15]
            fv = go.Figure(go.Bar(
                x=vn, y=vv, marker_color=vc,
                text=[fmt_vol(v) for v in vv], textposition="outside",
                textfont=dict(family="Share Tech Mono", size=9, color="#c8ffc8")))
            fv.update_layout(**make_layout(height=280, title="TOP 15 BY VOLUME", tc="#ffb300"))
            st.plotly_chart(fv, use_container_width=True, config={"displayModeBar": False})

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 6 — SECTOR HEATMAP
    # ══════════════════════════════════════════════════════════════════════════
    with tab6:
        n50d = fetch_all_n50()
        sec_data = {sec: {stk: n50d.get(stk,{}) for stk in lst}
                    for sec, lst in SECTORS.items()}
        st.plotly_chart(chart_treemap(sec_data),
                        use_container_width=True, config={"displayModeBar": False})

        st.markdown(shdr("SECTOR AVERAGE RETURNS"), unsafe_allow_html=True)
        sp_rows = []
        for sec, stocks in sec_data.items():
            pcts = [d["pct"] for d in stocks.values() if d and "pct" in d]
            if pcts:
                sp_rows.append({
                    "Sector": sec,
                    "Avg Pct": round(float(np.mean(pcts)),2),
                    "Up":     sum(1 for p in pcts if p > 0),
                    "Down":   sum(1 for p in pcts if p < 0),
                })
        if sp_rows:
            df_sp = pd.DataFrame(sp_rows).sort_values("Avg Pct", ascending=False)
            st.plotly_chart(
                chart_bar_v(df_sp["Sector"].tolist(), df_sp["Avg Pct"].tolist(),
                             title="SECTOR AVG % CHANGE", height=300,
                             texts=["{:+.2f}%".format(p) for p in df_sp["Avg Pct"]],
                             y_suffix="%"),
                use_container_width=True, config={"displayModeBar": False})
            st.dataframe(df_sp, use_container_width=True, hide_index=True)
        else:
            st.info("Loading sector data...")

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 7 — CHART STUDIO  (FIX: cs_sym always defined before use)
    # ══════════════════════════════════════════════════════════════════════════
    with tab7:
        st.markdown(shdr("ADVANCED CHART STUDIO"), unsafe_allow_html=True)
        cs1, cs2, cs3, cs4 = st.columns(4)

        # FIX: read asset_type from session_state with a default
        with cs1:
            at = st.selectbox(
                "ASSET TYPE",
                ["Nifty 50 Stock","Indian Index","MCX Commodity","Global Index"],
                key="cs_asset_type")

        # FIX: define cs_sym / cs_lbl BEFORE the with-block to avoid UnboundLocalError
        cs_sym = NIFTY50["RELIANCE"]
        cs_lbl = "RELIANCE"

        with cs2:
            if at == "Nifty 50 Stock":
                sel    = st.selectbox("SYMBOL", list(NIFTY50.keys()), key="cs_sym_n50")
                cs_sym = NIFTY50[sel]
                cs_lbl = sel
            elif at == "Indian Index":
                sel    = st.selectbox("SYMBOL", list(INDIAN_INDICES.keys()), key="cs_sym_idx")
                cs_sym = INDIAN_INDICES[sel]
                cs_lbl = sel
            elif at == "MCX Commodity":
                sel    = st.selectbox("SYMBOL", list(MCX_SYMBOLS.keys()), key="cs_sym_mcx")
                cs_sym = MCX_SYMBOLS[sel][0]
                cs_lbl = sel + " (USD)"
            else:
                sel    = st.selectbox("SYMBOL", list(GLOBAL_INDICES.keys()), key="cs_sym_glo")
                cs_sym = GLOBAL_INDICES[sel]
                cs_lbl = sel

        with cs3:
            cs_per = st.selectbox(
                "PERIOD",
                ["1d","5d","1mo","3mo","6mo","1y","2y","5y"],
                index=5, key="cs_period")

        with cs4:
            cs_type = st.radio(
                "CHART TYPE",
                ["Candlestick","Line","OHLC"],
                horizontal=True, key="cs_chart_type")

        # Now cs_sym is always defined
        df_cs = get_ohlcv(cs_sym, period=cs_per, interval=PERIOD_IV.get(cs_per,"1d"))
        if not df_cs.empty:
            st.markdown("<div class='chart-box'>", unsafe_allow_html=True)
            st.plotly_chart(
                chart_advanced(
                    df_cs,
                    "{} — {} — {} — EMA + BB + MACD".format(
                        cs_lbl, cs_per.upper(), cs_type.upper()),
                    chart_type=cs_type, height=680),
                use_container_width=True,
                config={"displayModeBar": True,
                        "modeBarButtonsToRemove": ["lasso2d","select2d"]})
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown(shdr("STATISTICS"), unsafe_allow_html=True)
            closes  = df_cs["Close"].dropna()
            rets    = closes.pct_change().dropna()
            curr_p  = float(closes.iloc[-1])
            prev_p  = float(closes.iloc[-2]) if len(closes) >= 2 else curr_p
            dlt_p   = (curr_p/prev_p-1)*100 if prev_p != 0 else 0.0
            p_ret   = (curr_p/float(closes.iloc[0])-1)*100 if float(closes.iloc[0]) != 0 else 0.0
            vol30   = float(rets.rolling(30).std().iloc[-1])*100 if len(rets) >= 30 else 0.0
            vol_avg = int(df_cs["Volume"].mean()) if "Volume" in df_cs.columns else 0

            s1,s2,s3,s4,s5,s6 = st.columns(6)
            s1.metric("52W HIGH",      "{:,.2f}".format(float(closes.max())))
            s2.metric("52W LOW",       "{:,.2f}".format(float(closes.min())))
            s3.metric("CURRENT",       "{:,.2f}".format(curr_p),
                       delta="{:+.2f}%".format(dlt_p))
            s4.metric("VOLATILITY",    "{:.2f}%".format(vol30))
            s5.metric("AVG VOLUME",    fmt_vol(vol_avg) if vol_avg else "N/A")
            s6.metric("PERIOD RETURN", "{:+.2f}%".format(p_ret))
        else:
            st.warning("No data for **{}** with period **{}**. Try another symbol or period.".format(
                cs_lbl, cs_per))

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 8 — FOREX & CRYPTO
    # ══════════════════════════════════════════════════════════════════════════
    with tab8:
        st.markdown(shdr("INR FOREX PAIRS"), unsafe_allow_html=True)
        fx_cols = st.columns(4)
        for i, nm in enumerate(list(FOREX_SYMBOLS.keys())):
            d = fx_data.get(nm, {})
            with fx_cols[i]:
                if d:
                    cc  = "#00ff41" if d["chg"] >= 0 else "#ff3d3d"
                    arr = "&#9650;" if d["chg"] >= 0 else "&#9660;"
                    cls = "up" if d["chg"] >= 0 else "down"
                    st.markdown(
                        "<div class='idx-card {cls}' style='border-top-color:#00b4ff'>"
                        "<div class='idx-name' style='color:#00b4ff'>{nm}</div>"
                        "<div class='idx-price'>&#8377;{price}</div>"
                        "<div class='idx-chg' style='color:{cc}'>"
                        "{arr} {chg} ({pct}%)</div>"
                        "<div class='idx-meta'><span>H:&#8377;{hi}</span>"
                        "<span>L:&#8377;{lo}</span></div>"
                        "</div>".format(
                            cls=cls, nm=nm,
                            price="{:.4f}".format(d["price"]), cc=cc, arr=arr,
                            chg="{:+.4f}".format(d["chg"]),
                            pct="{:+.2f}".format(d["pct"]),
                            hi="{:.4f}".format(d["high"]),
                            lo="{:.4f}".format(d["low"]),
                        ), unsafe_allow_html=True)

        st.markdown(shdr("USD/INR — 3-MONTH TREND"), unsafe_allow_html=True)
        df_fx = get_ohlcv("USDINR=X", "3mo", "1d")
        if not df_fx.empty:
            st.plotly_chart(
                chart_line(df_fx, "USD/INR  3 MONTH", color="#00b4ff", height=280),
                use_container_width=True, config={"displayModeBar": False})

        st.markdown(shdr("CRYPTOCURRENCY"), unsafe_allow_html=True)
        cr_cols = st.columns(4)
        for i, (nm, sym) in enumerate(CRYPTO.items()):
            d = get_quote(sym)
            with cr_cols[i]:
                if d:
                    cc  = "#00ff41" if d["chg"] >= 0 else "#ff3d3d"
                    arr = "&#9650;" if d["chg"] >= 0 else "&#9660;"
                    cls = "up" if d["chg"] >= 0 else "down"
                    st.markdown(
                        "<div class='idx-card {cls}' style='border-top-color:#00fff7'>"
                        "<div class='idx-name' style='color:#00fff7'>{nm}</div>"
                        "<div class='idx-price'>${price}</div>"
                        "<div class='idx-chg' style='color:{cc}'>"
                        "{arr} {pct}%</div></div>".format(
                            cls=cls, nm=nm,
                            price="{:,.2f}".format(d["price"]),
                            cc=cc, arr=arr, pct="{:+.2f}".format(d["pct"]),
                        ), unsafe_allow_html=True)
                else:
                    st.markdown(
                        "<div class='idx-card'>"
                        "<div class='idx-name' style='color:#00fff7'>{}</div>"
                        "<div class='idx-price' style='color:#2d5a2d'>N/A</div>"
                        "</div>".format(nm), unsafe_allow_html=True)

    # ── Footer ────────────────────────────────────────────────────────────────
    st.markdown(
        "<div style='text-align:center;padding:14px 0 4px;font-family:Share Tech Mono,monospace;"
        "font-size:10px;color:#2d5a2d;border-top:1px solid #0d1e0d;margin-top:16px'>"
        "QUANTUM MARKET TERMINAL v5.0 &nbsp;&bull;&nbsp; DATA: YAHOO FINANCE"
        " &nbsp;&bull;&nbsp; USD/INR: &#8377;{rate:.2f}"
        " &nbsp;&bull;&nbsp; &#9888; INFORMATIONAL ONLY"
        "</div>".format(rate=usd_inr),
        unsafe_allow_html=True)

    # ── AUTO REFRESH — at end of script so full UI renders first ──────────────
    # FIX: time.sleep(n) + st.rerun() is the standard Streamlit pattern.
    # Page is fully visible during sleep; Streamlit shows a subtle spinner.
    if auto_rf:
        time.sleep(rf_sec)
        st.cache_data.clear()
        st.rerun()


if __name__ == "__main__":
    main()
