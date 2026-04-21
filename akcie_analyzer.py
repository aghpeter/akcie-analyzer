import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import json
import re
import anthropic
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Akcie Analyzer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CUSTOM CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
}

.stApp {
    background: #0a0e1a;
    color: #e0e6f0;
}

.main-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 2rem;
    font-weight: 600;
    color: #00d4aa;
    letter-spacing: -1px;
    margin-bottom: 0.2rem;
}

.sub-title {
    font-family: 'IBM Plex Sans', sans-serif;
    font-weight: 300;
    color: #6b7fa3;
    font-size: 0.95rem;
    margin-bottom: 2rem;
}

.metric-card {
    background: #111827;
    border: 1px solid #1e2d47;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.5rem;
}

.metric-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    color: #4a5a7a;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.metric-value {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.6rem;
    font-weight: 600;
    color: #e0e6f0;
}

.metric-value.green { color: #00d4aa; }
.metric-value.red { color: #ff4d6a; }
.metric-value.yellow { color: #f5c518; }

.analysis-box {
    background: #111827;
    border: 1px solid #1e2d47;
    border-left: 3px solid #00d4aa;
    border-radius: 8px;
    padding: 1.5rem;
    font-size: 0.95rem;
    line-height: 1.7;
    color: #c8d4e8;
    margin-top: 1rem;
}

.ticker-badge {
    display: inline-block;
    background: #00d4aa22;
    border: 1px solid #00d4aa44;
    color: #00d4aa;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.8rem;
    padding: 0.2rem 0.6rem;
    border-radius: 4px;
    margin-right: 0.4rem;
}

.stTextInput > div > div > input {
    background: #111827 !important;
    border: 1px solid #1e2d47 !important;
    color: #e0e6f0 !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
    border-radius: 6px !important;
}

.stTextInput > div > div > input:focus {
    border-color: #00d4aa !important;
    box-shadow: 0 0 0 1px #00d4aa44 !important;
}

.stButton > button {
    background: #00d4aa !important;
    color: #0a0e1a !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-weight: 600 !important;
    border: none !important;
    border-radius: 6px !important;
    padding: 0.5rem 1.5rem !important;
    letter-spacing: 0.5px !important;
}

.stButton > button:hover {
    background: #00b894 !important;
}

[data-testid="stSidebar"] {
    background: #0d1221 !important;
    border-right: 1px solid #1e2d47 !important;
}

.stSelectbox > div > div {
    background: #111827 !important;
    border: 1px solid #1e2d47 !important;
    color: #e0e6f0 !important;
}

hr {
    border-color: #1e2d47 !important;
}

.example-query {
    background: #0d1221;
    border: 1px solid #1e2d47;
    border-radius: 6px;
    padding: 0.5rem 0.8rem;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.8rem;
    color: #6b7fa3;
    margin-bottom: 0.3rem;
    cursor: pointer;
}
</style>
""", unsafe_allow_html=True)


# ── HELPERS ───────────────────────────────────────────────────────────────────

TICKER_ALIASES = {
    "gold miners": "GDX", "zlato miners": "GDX", "gdx": "GDX",
    "apple": "AAPL", "tesla": "TSLA", "microsoft": "MSFT",
    "google": "GOOGL", "alphabet": "GOOGL", "amazon": "AMZN",
    "nvidia": "NVDA", "meta": "META", "sp500": "SPY", "s&p": "SPY",
    "nasdaq": "QQQ", "dow": "DIA", "oil": "USO", "silver": "SLV",
    "gold": "GLD", "bitcoin etf": "IBIT", "cez": "CEZ.PR",
}

def extract_ticker_and_days(query: str) -> tuple[str, int]:
    """Extract ticker symbol and number of days from natural language query."""
    q = query.lower()

    # Days extraction
    days = 200  # default
    patterns = [
        r'(\d+)\s*d[ní][íu]?', r'(\d+)\s*day', r'(\d+)\s*den',
        r'posledn[íi][ch]?\s*(\d+)', r'last\s*(\d+)',
        r'(\d+)\s*t[ýy]dn[ůu]',  # weeks
        r'(\d+)\s*m[eě]s[íi]c',   # months
    ]
    for p in patterns:
        m = re.search(p, q)
        if m:
            val = int(m.group(1))
            if 't' in p or 'week' in p:
                val *= 7
            elif 'm' in p and 'ě' in p or 'mes' in p:
                val *= 30
            days = min(max(val, 5), 1000)
            break

    # Ticker extraction – first check aliases
    ticker = None
    for alias, sym in TICKER_ALIASES.items():
        if alias in q:
            ticker = sym
            break

    # Then look for explicit uppercase tickers like GDX, AAPL etc.
    if not ticker:
        m = re.search(r'\b([A-Z]{1,5}(?:\.[A-Z]{1,3})?)\b', query)
        if m:
            ticker = m.group(1)

    if not ticker:
        # Try to find known words
        words = query.upper().split()
        for w in words:
            if 2 <= len(w) <= 5 and w.isalpha():
                ticker = w
                break

    return ticker or "GDX", days


def download_data(ticker: str, days: int) -> pd.DataFrame:
    """Download OHLCV data via yfinance."""
    end = datetime.today()
    # Add buffer for weekends/holidays
    start = end - timedelta(days=int(days * 1.45) + 10)
    df = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)
    if df.empty:
        raise ValueError(f"Žádná data pro ticker '{ticker}'. Zkontroluj symbol.")
    df = df.tail(days).copy()
    df.index = pd.to_datetime(df.index)
    return df


def compute_metrics(df: pd.DataFrame) -> dict:
    """Compute key technical metrics."""
    close = df["Close"].squeeze()
    volume = df["Volume"].squeeze() if "Volume" in df.columns else None

    returns = close.pct_change().dropna()
    vol_ann = returns.std() * np.sqrt(252) * 100

    # Trend – linear regression slope
    x = np.arange(len(close))
    slope, intercept = np.polyfit(x, close.values, 1)
    trend_pct = (slope * len(close)) / close.iloc[0] * 100

    # Moving averages
    ma20 = close.rolling(20).mean().iloc[-1]
    ma50 = close.rolling(50).mean().iloc[-1] if len(close) >= 50 else None
    ma200 = close.rolling(200).mean().iloc[-1] if len(close) >= 200 else None

    # RSI
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss
    rsi = (100 - 100 / (1 + rs)).iloc[-1]

    # Max drawdown
    peak = close.cummax()
    drawdown = ((close - peak) / peak * 100).min()

    price_now = float(close.iloc[-1])
    price_start = float(close.iloc[0])
    change_pct = (price_now - price_start) / price_start * 100

    avg_vol = float(volume.mean()) if volume is not None else None
    last_vol = float(volume.iloc[-1]) if volume is not None else None

    return {
        "ticker": df.columns.get_level_values(1)[0] if isinstance(df.columns, pd.MultiIndex) else "N/A",
        "days": len(close),
        "price_now": round(price_now, 2),
        "price_start": round(price_start, 2),
        "change_pct": round(change_pct, 2),
        "volatility_ann": round(float(vol_ann), 2),
        "trend_direction": "UP" if slope > 0 else "DOWN",
        "trend_strength_pct": round(float(trend_pct), 2),
        "ma20": round(float(ma20), 2),
        "ma50": round(float(ma50), 2) if ma50 is not None else None,
        "ma200": round(float(ma200), 2) if ma200 is not None else None,
        "rsi_14": round(float(rsi), 1),
        "max_drawdown_pct": round(float(drawdown), 2),
        "avg_volume": int(avg_vol) if avg_vol else None,
        "last_volume": int(last_vol) if last_vol else None,
    }


def build_ohlcv_summary(df: pd.DataFrame, max_rows: int = 60) -> list[dict]:
    """Build a compact OHLCV list for the AI prompt."""
    step = max(1, len(df) // max_rows)
    subset = df.iloc[::step].tail(max_rows)
    rows = []
    for date, row in subset.iterrows():
        r = {"date": date.strftime("%Y-%m-%d")}
        for col in ["Open", "High", "Low", "Close", "Volume"]:
            if col in df.columns:
                val = row[col]
                if hasattr(val, 'item'):
                    val = val.item()
                r[col.lower()] = round(float(val), 2) if col != "Volume" else int(val)
        rows.append(r)
    return rows


def call_claude(api_key: str, ticker: str, metrics: dict, ohlcv: list, user_prompt: str, model: str) -> str:
    """Send data + prompt to Claude API and return analysis."""
    client = anthropic.Anthropic(api_key=api_key)

    system = """Jsi expert na technickou a fundamentální analýzu finančních trhů.
Dostaneš JSON s historickými cenovými daty a předpočítanými metrikami pro konkrétní ticker.
Proveď podrobnou analýzu v češtině. Strukturuj odpověď takto:
1. **Shrnutí cenového vývoje** – co se dělo s cenou
2. **Volatilita a riziko** – interpretace volatility, max drawdown
3. **Trendová analýza** – směr, síla, klouzavé průměry
4. **Momentum (RSI)** – je trh překoupený/přeprodaný?
5. **Objem** – potvrzuje objem trend?
6. **Závěr a výhled** – celkové hodnocení, na co si dát pozor

Buď konkrétní, uváděj čísla z dat. Vyhni se obecným frázím."""

    payload = {
        "ticker": ticker,
        "metrics": metrics,
        "ohlcv_sample": ohlcv,
        "user_question": user_prompt,
    }

    message = client.messages.create(
        model=model,
        max_tokens=2000,
        system=system,
        messages=[{
            "role": "user",
            "content": f"Zde jsou data pro analýzu:\n\n```json\n{json.dumps(payload, ensure_ascii=False, indent=2)}\n```\n\nPrověď analýzu."
        }]
    )
    return message.content[0].text


def make_chart(df: pd.DataFrame, ticker: str, metrics: dict) -> go.Figure:
    """Create interactive Plotly chart with price + volume + MAs."""
    close = df["Close"].squeeze()
    
    has_volume = "Volume" in df.columns
    rows = 2 if has_volume else 1
    row_heights = [0.75, 0.25] if has_volume else [1.0]

    fig = make_subplots(
        rows=rows, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=row_heights,
    )

    # Candlestick
    if all(c in df.columns for c in ["Open", "High", "Low", "Close"]):
        fig.add_trace(go.Candlestick(
            x=df.index,
            open=df["Open"].squeeze(),
            high=df["High"].squeeze(),
            low=df["Low"].squeeze(),
            close=close,
            name=ticker,
            increasing_fillcolor="#00d4aa",
            increasing_line_color="#00d4aa",
            decreasing_fillcolor="#ff4d6a",
            decreasing_line_color="#ff4d6a",
        ), row=1, col=1)
    else:
        fig.add_trace(go.Scatter(x=df.index, y=close, name=ticker,
                                  line=dict(color="#00d4aa", width=1.5)), row=1, col=1)

    # Moving averages
    colors_ma = {"ma20": "#f5c518", "ma50": "#a78bfa", "ma200": "#60a5fa"}
    for key, color in colors_ma.items():
        val = metrics.get(key)
        if val and len(close) >= int(key[2:]):
            window = int(key[2:])
            ma_series = close.rolling(window).mean()
            fig.add_trace(go.Scatter(
                x=df.index, y=ma_series,
                name=f"MA{window}", line=dict(color=color, width=1.2, dash="dot"),
                opacity=0.8,
            ), row=1, col=1)

    # Volume
    if has_volume:
        vol = df["Volume"].squeeze()
        colors = ["#ff4d6a" if close.iloc[i] < close.iloc[i-1] else "#00d4aa"
                  for i in range(len(close))]
        fig.add_trace(go.Bar(x=df.index, y=vol, name="Volume",
                              marker_color=colors, opacity=0.6), row=2, col=1)

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0a0e1a",
        plot_bgcolor="#0a0e1a",
        font=dict(family="IBM Plex Mono", color="#6b7fa3", size=11),
        xaxis_rangeslider_visible=False,
        legend=dict(orientation="h", y=1.02, bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=0, r=0, t=30, b=0),
        height=480,
    )
    fig.update_xaxes(gridcolor="#1e2d47", zeroline=False)
    fig.update_yaxes(gridcolor="#1e2d47", zeroline=False)

    return fig


# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="main-title">⚙ Nastavení</div>', unsafe_allow_html=True)
    st.markdown("---")

    api_key = st.text_input(
        "Claude API klíč",
        type="password",
        placeholder="sk-ant-...",
        help="Získej na console.anthropic.com",
    )

    model = st.selectbox(
        "Model",
        ["claude-sonnet-4-20250514", "claude-haiku-4-5-20251001"],
        index=0,
        help="Sonnet = lepší analýza, Haiku = rychlejší a levnější",
    )

    st.markdown("---")
    st.markdown("**Příklady dotazů:**")
    examples = [
        "Analyzuj GDX za posledních 200 dní",
        "Jak si vede NVDA za 100 dní?",
        "Volatilita a trend SPY 150 dní",
        "Analýza TSLA za poslední rok",
        "Zhodnoť vývoj GLD 60 dní",
    ]
    for ex in examples:
        st.markdown(f'<div class="example-query">→ {ex}</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<span style="font-size:0.75rem;color:#4a5a7a;">Data: Yahoo Finance · 15min zpoždění<br>AI: Claude API (Anthropic)</span>', unsafe_allow_html=True)


# ── MAIN ──────────────────────────────────────────────────────────────────────
st.markdown('<div class="main-title">📈 AI Akcie Analyzer</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Zadej ticker a časový horizont přirozeným jazykem → automatická analýza dat + AI komentář</div>', unsafe_allow_html=True)

col_input, col_btn = st.columns([5, 1])
with col_input:
    query = st.text_input(
        "",
        placeholder='Např.: "Analyzuj GDX za posledních 200 dní, volatilitu a trend"',
        label_visibility="collapsed",
    )
with col_btn:
    run = st.button("▶ Analyzovat", use_container_width=True)

if run and query:
    if not api_key:
        st.error("⚠️ Zadej Claude API klíč v levém panelu.")
        st.stop()

    ticker, days = extract_ticker_and_days(query)

    with st.spinner(f"Stahuji data pro {ticker} ({days} dní)..."):
        try:
            df = download_data(ticker, days)
        except Exception as e:
            st.error(f"❌ Chyba při stahování dat: {e}")
            st.stop()

    metrics = compute_metrics(df)
    ohlcv = build_ohlcv_summary(df)

    # ── HEADER INFO ──
    st.markdown("---")
    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown(f'<span class="ticker-badge">{ticker}</span>'
                    f'<span class="ticker-badge">{days} dní</span>'
                    f'<span class="ticker-badge">{df.index[0].strftime("%d.%m.%Y")} – {df.index[-1].strftime("%d.%m.%Y")}</span>',
                    unsafe_allow_html=True)

    # ── CHART ──
    fig = make_chart(df, ticker, metrics)
    st.plotly_chart(fig, use_container_width=True)

    # ── METRICS GRID ──
    m1, m2, m3, m4, m5 = st.columns(5)

    chg_cls = "green" if metrics["change_pct"] >= 0 else "red"
    trend_cls = "green" if metrics["trend_direction"] == "UP" else "red"
    rsi = metrics["rsi_14"]
    rsi_cls = "red" if rsi > 70 else ("green" if rsi < 30 else "yellow")

    with m1:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Cena nyní</div>'
                    f'<div class="metric-value">${metrics["price_now"]}</div></div>', unsafe_allow_html=True)
    with m2:
        sign = "+" if metrics["change_pct"] >= 0 else ""
        st.markdown(f'<div class="metric-card"><div class="metric-label">Změna období</div>'
                    f'<div class="metric-value {chg_cls}">{sign}{metrics["change_pct"]}%</div></div>', unsafe_allow_html=True)
    with m3:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Volatilita (ann.)</div>'
                    f'<div class="metric-value yellow">{metrics["volatility_ann"]}%</div></div>', unsafe_allow_html=True)
    with m4:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Trend</div>'
                    f'<div class="metric-value {trend_cls}">{metrics["trend_direction"]} {abs(metrics["trend_strength_pct"]):.1f}%</div></div>', unsafe_allow_html=True)
    with m5:
        st.markdown(f'<div class="metric-card"><div class="metric-label">RSI (14)</div>'
                    f'<div class="metric-value {rsi_cls}">{rsi}</div></div>', unsafe_allow_html=True)

    # ── AI ANALYSIS ──
    st.markdown("---")
    st.markdown("#### 🤖 AI Analýza")

    with st.spinner("Claude analyzuje data..."):
        try:
            analysis = call_claude(api_key, ticker, metrics, ohlcv, query, model)
            st.markdown(f'<div class="analysis-box">{analysis}</div>', unsafe_allow_html=True)
        except anthropic.AuthenticationError:
            st.error("❌ Neplatný API klíč. Zkontroluj ho v nastavení.")
        except Exception as e:
            st.error(f"❌ Chyba Claude API: {e}")

    # ── RAW DATA EXPANDER ──
    with st.expander("📋 Zobrazit raw data (JSON odeslaný do AI)"):
        st.json({"metrics": metrics, "ohlcv_sample_rows": len(ohlcv)})

elif run and not query:
    st.warning("Zadej dotaz do pole výše.")
else:
    st.markdown("""
    <div style="margin-top:3rem;text-align:center;color:#2a3a5a;">
        <div style="font-size:3rem;margin-bottom:1rem;">📊</div>
        <div style="font-family:'IBM Plex Mono',monospace;font-size:1rem;">
            Zadej dotaz a klikni na Analyzovat
        </div>
    </div>
    """, unsafe_allow_html=True)
