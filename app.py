"""
Real-Time Stock Market Dashboard
Tech: Python (Pandas, Plotly, Requests API) + Streamlit
Data: Yahoo Finance public chart API (no API key needed)
"""
import time

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
from plotly.subplots import make_subplots

# ----------------------------------------------------------------- config
st.set_page_config(page_title="Real-Time Stock Dashboard", page_icon="📈", layout="wide")

API_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
HEADERS = {"User-Agent": "Mozilla/5.0"}

PERIODS = {  # label: (interval, range)
    "1 Day (1m candles)": ("1m", "1d"),
    "5 Days (5m candles)": ("5m", "5d"),
    "1 Month (30m candles)": ("30m", "1mo"),
    "6 Months (daily)": ("1d", "6mo"),
    "1 Year (daily)": ("1d", "1y"),
}
DEFAULT_SYMBOLS = ["AAPL", "MSFT", "TSLA", "RELIANCE.NS", "TCS.NS"]


# ------------------------------------------------------------- data layer
@st.cache_data(ttl=30, show_spinner=False)
def fetch_history(symbol: str, interval: str, rng: str) -> pd.DataFrame:
    """Fetch OHLCV data for one symbol using the Requests library."""
    resp = requests.get(
        API_URL.format(symbol=symbol),
        params={"interval": interval, "range": rng},
        headers=HEADERS,
        timeout=10,
    )
    resp.raise_for_status()
    chart = resp.json()["chart"]
    if chart.get("error") or not chart.get("result"):
        raise ValueError(f"No data for '{symbol}'")

    result = chart["result"][0]
    quote = result["indicators"]["quote"][0]
    index = pd.to_datetime(result["timestamp"], unit="s", utc=True)
    tz = result["meta"].get("exchangeTimezoneName", "UTC")

    df = pd.DataFrame(
        {
            "Open": quote["open"],
            "High": quote["high"],
            "Low": quote["low"],
            "Close": quote["close"],
            "Volume": quote["volume"],
        },
        index=index.tz_convert(tz).tz_localize(None),
    ).dropna(subset=["Close"])
    df.attrs["currency"] = result["meta"].get("currency", "")
    return df


# ------------------------------------------------------------- indicators
def add_indicators(df: pd.DataFrame, sma_n=20, ema_n=50, rsi_n=14) -> pd.DataFrame:
    df = df.copy()
    close = df["Close"]

    df["SMA"] = close.rolling(sma_n).mean()
    df["EMA"] = close.ewm(span=ema_n, adjust=False).mean()

    std = close.rolling(sma_n).std()
    df["BB_up"] = df["SMA"] + 2 * std
    df["BB_low"] = df["SMA"] - 2 * std

    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / rsi_n, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / rsi_n, adjust=False).mean()
    df["RSI"] = 100 - 100 / (1 + gain / loss)

    macd = close.ewm(span=12, adjust=False).mean() - close.ewm(span=26, adjust=False).mean()
    df["MACD"] = macd
    df["MACD_signal"] = macd.ewm(span=9, adjust=False).mean()
    df["MACD_hist"] = df["MACD"] - df["MACD_signal"]
    return df


# ----------------------------------------------------------------- charts
def build_chart(df: pd.DataFrame, symbol: str, show: dict) -> go.Figure:
    rows = ["price", "volume"] + [k for k in ("RSI", "MACD") if show[k]]
    heights = {"price": 0.5, "volume": 0.12, "RSI": 0.19, "MACD": 0.19}
    fig = make_subplots(
        rows=len(rows), cols=1, shared_xaxes=True, vertical_spacing=0.03,
        row_heights=[heights[r] for r in rows],
    )
    r = {name: i + 1 for i, name in enumerate(rows)}

    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
        name=symbol), row=r["price"], col=1)

    if show["SMA"]:
        fig.add_trace(go.Scatter(x=df.index, y=df["SMA"], name="SMA 20",
                                 line=dict(width=1.5, color="orange")), row=r["price"], col=1)
    if show["EMA"]:
        fig.add_trace(go.Scatter(x=df.index, y=df["EMA"], name="EMA 50",
                                 line=dict(width=1.5, color="purple")), row=r["price"], col=1)
    if show["BB"]:
        for col, name in (("BB_up", "BB upper"), ("BB_low", "BB lower")):
            fig.add_trace(go.Scatter(x=df.index, y=df[col], name=name,
                                     line=dict(width=1, dash="dot", color="gray")),
                          row=r["price"], col=1)

    colors = ["#26a69a" if c >= o else "#ef5350" for o, c in zip(df["Open"], df["Close"])]
    fig.add_trace(go.Bar(x=df.index, y=df["Volume"], marker_color=colors, name="Volume",
                         showlegend=False), row=r["volume"], col=1)

    if show["RSI"]:
        fig.add_trace(go.Scatter(x=df.index, y=df["RSI"], name="RSI 14",
                                 line=dict(color="#1f77b4")), row=r["RSI"], col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=r["RSI"], col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=r["RSI"], col=1)
        fig.update_yaxes(range=[0, 100], row=r["RSI"], col=1)

    if show["MACD"]:
        fig.add_trace(go.Scatter(x=df.index, y=df["MACD"], name="MACD",
                                 line=dict(color="#1f77b4")), row=r["MACD"], col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["MACD_signal"], name="Signal",
                                 line=dict(color="orange")), row=r["MACD"], col=1)
        fig.add_trace(go.Bar(x=df.index, y=df["MACD_hist"], name="Histogram",
                             marker_color="gray"), row=r["MACD"], col=1)

    fig.update_layout(height=250 + 160 * len(rows), xaxis_rangeslider_visible=False,
                      margin=dict(l=10, r=10, t=30, b=10),
                      legend=dict(orientation="h", y=1.04), hovermode="x unified")
    fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])
    return fig


def signal_text(df: pd.DataFrame) -> str:
    """Very simple, educational signal summary (not financial advice)."""
    last = df.iloc[-1]
    notes = []
    if pd.notna(last["RSI"]):
        if last["RSI"] > 70:
            notes.append("RSI > 70: possibly **overbought**")
        elif last["RSI"] < 30:
            notes.append("RSI < 30: possibly **oversold**")
        else:
            notes.append(f"RSI {last['RSI']:.0f}: neutral")
    if pd.notna(last["MACD"]):
        notes.append("MACD above signal line: **bullish momentum**"
                     if last["MACD"] > last["MACD_signal"]
                     else "MACD below signal line: **bearish momentum**")
    if pd.notna(last["SMA"]):
        notes.append("Price above SMA 20: **uptrend**" if last["Close"] > last["SMA"]
                     else "Price below SMA 20: **downtrend**")
    return "  \n".join(f"- {n}" for n in notes)


# ------------------------------------------------------------------- UI
st.title("📈 Real-Time Stock Market Dashboard")
st.caption("Live prices and technical indicators • Data: Yahoo Finance API • Educational use only")

with st.sidebar:
    st.header("⚙️ Settings")
    symbols = st.multiselect("Stocks (type to add, e.g. INFY.NS)", DEFAULT_SYMBOLS,
                             default=DEFAULT_SYMBOLS[:3], accept_new_options=True)
    period = st.selectbox("Time period", list(PERIODS), index=1)
    st.subheader("Indicators")
    show = {
        "SMA": st.checkbox("SMA (20)", True),
        "EMA": st.checkbox("EMA (50)", False),
        "BB": st.checkbox("Bollinger Bands", False),
        "RSI": st.checkbox("RSI (14)", True),
        "MACD": st.checkbox("MACD", True),
    }
    st.subheader("Live updates")
    auto = st.checkbox("Auto-refresh", True)
    every = st.slider("Refresh every (seconds)", 15, 120, 30, step=5)
    st.caption("Tip: NSE stocks end with .NS, BSE with .BO")

if not symbols:
    st.info("Select at least one stock in the sidebar.")
    st.stop()

interval, rng = PERIODS[period]
data, errors = {}, []
for sym in symbols:
    try:
        data[sym.upper()] = add_indicators(fetch_history(sym.upper(), interval, rng))
    except Exception as e:  # network error, bad ticker, etc.
        errors.append(f"{sym}: {e}")
for err in errors:
    st.warning(err)
if not data:
    st.stop()

# ---- summary metrics
cols = st.columns(len(data))
for col, (sym, df) in zip(cols, data.items()):
    first, last = df["Close"].iloc[0], df["Close"].iloc[-1]
    chg = (last / first - 1) * 100
    col.metric(sym, f"{last:,.2f} {df.attrs.get('currency', '')}", f"{chg:+.2f}%")

# ---- tabs
tab_names = list(data) + ["Compare"]
for tab, name in zip(st.tabs(tab_names), tab_names):
    with tab:
        if name == "Compare":
            fig = go.Figure()
            for sym, df in data.items():
                fig.add_trace(go.Scatter(x=df.index, y=(df["Close"] / df["Close"].iloc[0] - 1) * 100,
                                         name=sym))
            fig.update_layout(title="Performance comparison (% change from start)",
                              yaxis_title="% change", height=500, hovermode="x unified")
            fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])
            st.plotly_chart(fig, use_container_width=True)
            continue

        df = data[name]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("High", f"{df['High'].max():,.2f}")
        c2.metric("Low", f"{df['Low'].min():,.2f}")
        c3.metric("Avg volume", f"{df['Volume'].mean():,.0f}")
        c4.metric("Latest RSI", f"{df['RSI'].iloc[-1]:.1f}" if pd.notna(df["RSI"].iloc[-1]) else "–")
        st.plotly_chart(build_chart(df, name, show), use_container_width=True)
        with st.expander("📊 Indicator summary"):
            st.markdown(signal_text(df))
        with st.expander("🗂️ Raw data"):
            st.dataframe(df.tail(100).round(2), use_container_width=True)
            st.download_button("Download CSV", df.to_csv().encode(), f"{name}.csv", "text/csv")

st.caption(f"Last updated: {time.strftime('%d %b %Y, %H:%M:%S')} • Disclaimer: not financial advice.")

if auto:
    time.sleep(every)
    st.cache_data.clear()
    st.rerun()
