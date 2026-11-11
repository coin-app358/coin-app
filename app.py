import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
from binance.client import Client
from ta.momentum import RSIIndicator
from ta.trend import MACD, EMAIndicator
from sklearn.linear_model import LinearRegression
import numpy as np

# ========== SETTINGS - MEWA OYAGE DEWAL DAA GANNA ==========
TELEGRAM_BOT_TOKEN = "OYAGE_BOT_TOKEN_METHANA_DANNA"
TELEGRAM_CHAT_ID = "OYAGE_CHAT_ID_METHANA_DANNA"
# Chat ID ganna widiya: @userinfobot ta /start kiyala message ekak yawanna
# ============================================================

st.set_page_config(page_title="Coin Super App", layout="centered", initial_sidebar_state="collapsed")

# --- Phone App CSS ---
st.markdown("""
<style>
    .block-container { padding-top: 10px; padding-bottom: 90px; max-width: 430px; }
    .price-card { background: linear-gradient(135deg, #1e1e2e, #2d2d44); padding: 20px; border-radius: 20px; color: white; text-align: center; }
    .ai-card { background: linear-gradient(135deg, #6a11cb, #2575fc); padding: 16px; border-radius: 18px; color: white; text-align: center; margin-top: 12px; }
    .signal-buy { background: #00c853; color: white; padding: 15px; border-radius: 15px; text-align: center; font-size: 22px; font-weight: bold; }
    .signal-sell { background: #d50000; color: white; padding: 15px; border-radius: 15px; text-align: center; font-size: 22px; font-weight: bold; }
    .signal-wait { background: #ff9100; color: white; padding: 15px; border-radius: 15px; text-align: center; font-size: 22px; font-weight: bold; }
    .reason-box { background: #f1f1f1; padding: 10px 14px; border-radius: 12px; margin-bottom: 8px; font-size: 14px; }
    .stButton>button { width: 100%; border-radius: 15px; height: 50px; font-size: 18px; font-weight: bold; background: #FFD700; color: black; }
    .bottom-nav { position: fixed; bottom: 0; left: 0; right: 0; background: white; display: flex; justify-content: space-around; padding: 12px; border-top: 1px solid #ddd; z-index: 999; }
</style>
""", unsafe_allow_html=True)

st.markdown("<h2 style='text-align:center;'>📈 Coin Super App</h2>", unsafe_allow_html=True)

def send_telegram(msg):
    if "OYAGE" in TELEGRAM_BOT_TOKEN:
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"})
        return True
    except:
        return False

# --- Select ---
coin = st.selectbox("Coin eka", ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT", "PEPEUSDT"])
interval = st.selectbox("Timeframe", ["15m", "1h", "4h", "1d"], index=1)

client = Client()

@st.cache_data(ttl=60)
def get_data(symbol, interval):
    klines = client.get_klines(symbol=symbol, interval=interval, limit=200)
    df = pd.DataFrame(klines, columns=['time','open','high','low','close','volume','close_time','qav','trades','taker_base','taker_quote','ignore'])
    df['time'] = pd.to_datetime(df['time'], unit='ms')
    for col in ['open','high','low','close','volume']:
        df[col] = df[col].astype(float)
    return df

df = get_data(coin, interval)
df['EMA50'] = EMAIndicator(df['close'], 50).ema_indicator()
df['EMA200'] = EMAIndicator(df['close'], 200).ema_indicator()
df['RSI'] = RSIIndicator(df['close'], 14).rsi()
macd = MACD(df['close'])
df['MACD'] = macd.macd()
df['MACD_Signal'] = macd.macd_signal()

last = df.iloc[-1]
prev = df.iloc[-2]
price = last['close']
change = ((price - prev['close'])/prev['close']*100)

# ===== A. AI PREDICTION =====
# Last 50 candles walin next price eka predict karanawa
X = np.array(range(len(df[-50:]))).reshape(-1, 1)
y = df[-50:]['close'].values
model = LinearRegression()
model.fit(X, y)
next_price = model.predict([[50]])[0]
next_price_5 = model.predict([[55]])[0]
ai_up = next_price > price
ai_percent = ((next_price - price)/price*100)

# --- Price Card ---
st.markdown(f"""
<div class="price-card">
    <div style="font-size:16px; opacity:0.7;">{coin}</div>
    <div style="font-size:36px; font-weight:bold;">${price:,.2f}</div>
    <div style="font-size:16px; color:{'lightgreen' if change>=0 else '#ff8a80'};">{'▲' if change>=0 else '▼'} {change:.2f}%</div>
    <div style="margin-top:10px; font-size:13px;">RSI: {last['RSI']:.1f} | Support: ${df['low'].min():,.2f} | Resistance: ${df['high'].max():,.2f}</div>
</div>
""", unsafe_allow_html=True)

# --- AI Card ---
st.markdown(f"""
<div class="ai-card">
    <div style="font-size:15px;">🤖 AI Prediction (Next Candle)</div>
    <div style="font-size:28px; font-weight:bold;">${next_price:,.2f}</div>
    <div style="font-size:15px;">{'📈 Uda yanna {0:.2f}% chance'.format(abs(ai_percent)) if ai_up else '📉 Pahala yanna {0:.2f}% chance'.format(abs(ai_percent))}</div>
    <div style="font-size:12px; opacity:0.8; margin-top:5px;">5 Candle walin passe: ${next_price_5:,.2f}</div>
</div>
""", unsafe_allow_html=True)
st.write("")

# --- Signal Logic ---
score = 0
reasons = []
if last['RSI'] < 30:
    score+=2; reasons.append("🟢 RSI 30 ta adui - Oversold, price wadi wenna puluwan")
elif last['RSI'] > 70:
    score-=2; reasons.append("🔴 RSI 70 ta wadi - Overbought, price adu wenna puluwan")
else:
    reasons.append(f"⚪ RSI {last['RSI']:.1f} - Neutral")

if price > last['EMA50'] > last['EMA200']:
    score+=2; reasons.append("🟢 EMA udin - Uptrend ekak")
elif price < last['EMA50'] < last['EMA200']:
    score-=2; reasons.append("🔴 EMA yatin - Downtrend ekak")
else:
    reasons.append("⚪ EMA mixed - Sideways")

if last['MACD'] > last['MACD_Signal']:
    score+=1; reasons.append("🟢 MACD Bullish")
else:
    score-=1; reasons.append("🔴 MACD Bearish")

if ai_up:
    score+=1; reasons.append(f"🤖 AI kiyanawa price ${next_price:,.2f} ta yai")
else:
    score-=1; reasons.append(f"🤖 AI kiyanawa price ${next_price:,.2f} ta bahai")

if score >= 4:
    signal, css = "STRONG BUY 🚀", "signal-buy"
elif score >= 2:
    signal, css = "BUY ✅", "signal-buy"
elif score <= -4:
    signal, css = "STRONG SELL 📉", "signal-sell"
elif score <= -2:
    signal, css = "SELL ❌", "signal-sell"
else:
    signal, css = "WAIT ⏳", "signal-wait"

st.markdown(f"<div class='{css}'>{signal}</div>", unsafe_allow_html=True)
st.write("")
st.markdown("**Ai me signal eka awe?**")
for r in reasons:
    st.markdown(f"<div class='reason-box'>{r}</div>", unsafe_allow_html=True)

# --- Chart ---
st.markdown("**Chart eka**")
fig = go.Figure(data=[go.Candlestick(x=df['time'], open=df['open'], high=df['high'], low=df['low'], close=df['close'])])
fig.add_trace(go.Scatter(x=df['time'], y=df['EMA50'], line=dict(color='blue', width=1), name='EMA 50'))
fig.add_trace(go.Scatter(x=df['time'], y=df['EMA200'], line=dict(color='orange', width=1), name='EMA 200'))
# AI Prediction line
fig.add_trace(go.Scatter(x=[df['time'].iloc[-1], df['time'].iloc[-1] + pd.Timedelta(hours=1)], y=[price, next_price], line=dict(color='#6a11cb', width=3, dash='dash'), name='AI Predict'))
fig.update_layout(height=320, margin=dict(l=0,r=0,t=10,b=0), xaxis_rangeslider_visible=False, showlegend=False)
st.plotly_chart(fig, use_container_width=True)

# ===== B. TELEGRAM ALERT =====
st.markdown("**📲 Telegram Alert**")
col1, col2 = st.columns(2)
with col1:
    if st.button("📩 Alert Yawanna"):
        msg = f"🚨 <b>{coin} Signal</b>\nPrice: ${price:,.2f}\nSignal: {signal}\nRSI: {last['RSI']:.1f}\nAI Predict: ${next_price:,.2f}\nSupport: ${df['low'].min():,.2f}\nResistance: ${df['high'].max():,.2f}"
        if send_telegram(msg):
            st.success("Telegram giya! ✅")
        else:
            st.error("Token / Chat ID danna one. Uda balanna.")

with col2:
    if st.button("🔄 Refresh"):
        st.cache_data.clear()
        st.rerun()

# Auto Alert - STRONG BUY/SELL nam auto yawanna
if "STRONG" in signal:
    if st.checkbox("Auto Alert ON karanna (STRONG signal awama Telegram yanna)"):
        send_telegram(f"🚨 AUTO ALERT: {coin} {signal} Price ${price:,.2f}")

st.markdown("""
<div class="bottom-nav">
    <span>🏠 Home</span><span>📊 Chart</span><span>🤖 AI</span><span>📲 Alert</span>
</div>
""", unsafe_allow_html=True)
