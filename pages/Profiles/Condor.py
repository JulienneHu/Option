import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from realPrice.realOption import calls_or_puts
from tools.CondorFetch import fetch_stock_price_streamlit, fetch_option_prices_streamlit
from datetime import datetime

# st.set_page_config(page_title="🦅 Condor Option Strategy Visualizer", layout="wide")
st.title("🦅 Condor Option Strategy Visualizer")

# ---------------------- Inputs ----------------------
col1, col2, col3, col4 = st.columns(4)

with col1:
    symbol = st.text_input("Symbol", value="AAPL")
    x1 = st.number_input("Strike X1", value=180.0)
    c1 = st.number_input("Call Premium C1", value=9.8)
    p1 = st.number_input("Put Premium P1", value=14.5)
    delta1 = st.number_input("Delta 1", value=0.0)
    s_range = st.number_input("Stock Range (%)", value=0.25)

with col2:
    condor_type = st.selectbox("Condor Type", ['Long Call', 'Short Call', 'Long Put', 'Short Put'])
    x2 = st.number_input("Strike X2", value=185.0)
    c2 = st.number_input("Call Premium C2", value=7.0)
    p2 = st.number_input("Put Premium P2", value=12.0)
    delta2 = st.number_input("Delta 2", value=0.0)
    y_min = st.number_input("Y Axis Min", value=-1500)

with col3:
    maturity_date_input = st.date_input("Maturity Date", datetime(2026, 8, 21))
    maturity_date = maturity_date_input.strftime('%Y-%m-%d')
    x3 = st.number_input("Strike X3", value=190.0)
    c3 = st.number_input("Call Premium C3", value=5.5)
    p3 = st.number_input("Put Premium P3", value=10.0)
    delta3 = st.number_input("Delta 3", value=0.0)
    y_max = st.number_input("Y Axis Max", value=1500)
with col4:
    stock_price = st.number_input("Stock Price", value=150.0)
    x4 = st.number_input("Strike X4", value=195.0)
    c4 = st.number_input("Call Premium C4", value=4.0)
    p4 = st.number_input("Put Premium P4", value=8.0)
    delta4 = st.number_input("Delta 4", value=0.0)
   


# ---------------------- Fetch Data & Update Button ----------------------
if st.button("🚀 Fetch Live Data & Update Plot"):
    fetched_price, price_change, pct_change = fetch_stock_price_streamlit(symbol)
    if fetched_price != 'NA':
        stock_price = fetched_price
        st.success(f"✅ Stock Price Updated: {fetched_price} | Δ: {price_change} ({pct_change}%)")
    else:
        st.warning("⚠️ Failed to fetch stock price. Using manual input.")

    strikes = [x1, x2, x3, x4]
    call_prices = []
    put_prices = []
    for strike in strikes:
        option_tickers = calls_or_puts(symbol, maturity_date, strike)
        option_prices = fetch_option_prices_streamlit(symbol, maturity_date, strike)
        st.write(f"Call Ticker: `{option_tickers[0]}`, Price: {option_prices[0]} | Put Ticker: `{option_tickers[1]}`, Price: {option_prices[1]}")
        call_prices.append(option_prices[0])
        put_prices.append(option_prices[1])

    def safe_update(val, default):
        try:
            return float(val) if val != 'NA' else default
        except:
            return default

    c1 = safe_update(call_prices[0], c1)
    c2 = safe_update(call_prices[1], c2)
    c3 = safe_update(call_prices[2], c3)
    c4 = safe_update(call_prices[3], c4)
    p1 = safe_update(put_prices[0], p1)
    p2 = safe_update(put_prices[1], p2)
    p3 = safe_update(put_prices[2], p3)
    p4 = safe_update(put_prices[3], p4)

# ---------------------- Calculation ----------------------
S_min = np.floor(stock_price * (1 - s_range))
S_max = np.ceil(stock_price * (1 + s_range))
S_grid = np.arange(S_min, S_max + 0.1, 0.1)

C_at_maturity = [np.maximum(S_grid - x, 0) for x in [x1, x2, x3, x4]]
P_at_maturity = [np.maximum(x - S_grid, 0) for x in [x1, x2, x3, x4]]

Deltas = [delta1, delta2, delta3, delta4]

if condor_type == 'Long Call':
    y_option = (C_at_maturity[0] - c1) + (c2 - C_at_maturity[1]) + (c3 - C_at_maturity[2]) + (C_at_maturity[3] - c4)
    Effective_Delta = (delta2 + delta3) - (delta1 + delta4)
elif condor_type == 'Short Call':
    y_option = (c1 - C_at_maturity[0]) + (C_at_maturity[1] - c2) + (C_at_maturity[2] - c3) + (c4 - C_at_maturity[3])
    Effective_Delta = (delta1 + delta4) - (delta2 + delta3)
elif condor_type == 'Long Put':
    y_option = (P_at_maturity[0] - p1) + (p2 - P_at_maturity[1]) + (p3 - P_at_maturity[2]) + (P_at_maturity[3] - p4)
    Effective_Delta = -(delta1 + delta4) + (delta2 + delta3)
elif condor_type == 'Short Put':
    y_option = (p1 - P_at_maturity[0]) + (P_at_maturity[1] - p2) + (P_at_maturity[2] - p3) + (p4 - P_at_maturity[3])
    Effective_Delta = -(delta2 + delta3) + (delta1 + delta4)
else:
    y_option = np.zeros_like(S_grid)
    Effective_Delta = 0

y_stock = Effective_Delta * (S_grid - stock_price)
PnL = 100 * (y_option + y_stock)

yp = np.clip(PnL, 0, None)
y_neg = np.where(yp == 0)[0]
y_pos = np.where(yp > 0)[0]

if y_neg.size > 0 and y_pos.size > 0:
    if S_grid[y_neg[0]] > S_min and S_grid[y_neg[-1]] < S_max:
        pos_str = f'(0, {np.ceil(S_grid[y_neg[0] - 1])}) and ({np.floor(S_grid[y_neg[-1] + 1])}, ∞)'
    else:
        pos_range = S_grid[y_pos]
        pos_str = f'({np.floor(pos_range[0])}, {np.ceil(pos_range[-1])})'
elif y_neg.size == 0:
    pos_str = "(0, ∞)"
else:
    pos_str = "∞"


# ---------------------- Plot ----------------------
fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(S_grid, PnL, label='Strategy PnL', color='blue')
ax.fill_between(S_grid, PnL, where=(PnL > 0), color='#007560', alpha=0.7, label='Profit')
ax.fill_between(S_grid, PnL, where=(PnL <= 0), color='#bd1414', alpha=0.7, label='Loss')
ax.axhline(0, color='black', linewidth=1)
ax.set_xlabel("Stock Price at Maturity")
ax.set_ylabel("PnL at Maturity")
ax.set_ylim([y_min, y_max])
ax.grid(True, linestyle='--')
ax.legend()
ax.set_title(f"{condor_type} Condor Strategy PnL\nEffective Δ: {Effective_Delta:.2f} | Profit Region: {pos_str}")

st.pyplot(fig)
