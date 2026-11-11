import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Coin Super App", layout="wide")
st.title("📈 Coin Super App")

coin = st.selectbox("Coin eka", ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "DOGEUSDT", "XRPUSDT"])
timeframe = st.selectbox("Timeframe", ["15m", "1h", "4h", "1d"])

@st.cache_data(ttl=60)
def get_data(symbol, interval):
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": 100}
    r = requests.get(url, params=params, timeout=10)
    data = r.json()
    df = pd.DataFrame(data, columns=["time","open","high","low","close","volume","close_time","qav","trades","taker_base","taker_quote","ignore"])
    for c in ["open","high","low","close","volume"]:
        df[c] = df[c].astype(float)
    df["time"] = pd.to_datetime(df["time"], unit="ms")
    return df

try:
    df = get_data(coin, timeframe)
    last_price = df.iloc[-1]["close"]
    prev_price = df.iloc[-2]["close"]
    change = (last_price - prev_price) / prev_price * 100

    col1, col2, col3 = st.columns(3)
    col1.metric("Last Price", f"${last_price:,.2f}")
    col2.metric("Change", f"{change:.2f}%")
    col3.metric("Volume", f"{df.iloc[-1]['volume']:,.0f}")

    fig = go.Figure(data=[go.Candlestick(
        x=df["time"], open=df["open"], high=df["high"],
        low=df["low"], close=df["close"], name=coin
    )])
    fig.update_layout(height=500, xaxis_rangeslider_visible=False, template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(df.tail(10), use_container_width=True)
    st.success("Live data from Binance ✅")
except Exception as e:
    st.error(f"Data ganna baha. Tikak inna passe refresh karanna. Error: {e}")
