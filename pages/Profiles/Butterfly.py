import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from realPrice.realOption import get_realtime_option_price, calls_or_puts
from realPrice.realOptionProfile import main as get_option
from tools.ButterflyFetch import fetch_stock_price_streamlit, fetch_option_prices_streamlit

st.title("🦋 Butterfly Option Strategy Visualizer")

# ---------------------- Inputs ----------------------
col1, col2, col3 = st.columns(3)

with col1:
    symbol = st.text_input("Symbol", value="AAPL")
    x1 = st.number_input("Strike X1", value=185.0)
    c1 = st.number_input("Call Premium C1", value=9.8)
    p1 = st.number_input("Put Premium P1", value=14.5)
    delta1 = st.number_input("Delta 1", value=0.0)
    s_range = st.number_input("Stock Range (%)", value=0.25)

with col2:
    butterfly_type = st.selectbox("Butterfly Type", ['Call', 'Put'])
    x2 = st.number_input("Strike X2", value=190.0)
    c2 = st.number_input("Call Premium C2", value=7.0)
    p2 = st.number_input("Put Premium P2", value=12.0)
    delta2 = st.number_input("Delta 2", value=0.0)
    y_min = st.number_input("Y Axis Min", value=-2000)

with col3:
    maturity_date = st.text_input("Maturity Date (YYYY-MM-DD)", value="2025-08-15")
    x3 = st.number_input("Strike X3", value=195.0)
    c3 = st.number_input("Call Premium C3", value=5.5)
    p3 = st.number_input("Put Premium P3", value=10.0)
    delta3 = st.number_input("Delta 3", value=0.0)
    y_max = st.number_input("Y Axis Max", value=2000)

stock_price = st.number_input("Stock Price", value=150.0)

# ---------------------- Fetch Data and Update Button ----------------------
if st.button("🚀 Fetch All Data & Update Plot"):
    fetched_price, price_change, pct_change = fetch_stock_price_streamlit(symbol)
    if fetched_price != 'NA':
        stock_price = fetched_price
        st.success(f"✅ Stock Price Updated: {fetched_price} | Δ: {price_change} ({pct_change}%)")
    else:
        st.warning("⚠️ Failed to fetch stock price. Using manual input.")

    call_prices = []
    put_prices = []

    for idx, strike in enumerate([x1, x2, x3]):
        option_tickers = calls_or_puts(symbol, maturity_date, strike)
        option_prices = fetch_option_prices_streamlit(symbol, maturity_date, strike)
        st.write(f"Call: `{option_tickers[0]}`, Price: {option_prices[0]}| Put:`{option_tickers[1]}`, Price: {option_prices[1]}")
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
    p1 = safe_update(put_prices[0], p1)
    p2 = safe_update(put_prices[1], p2)
    p3 = safe_update(put_prices[2], p3)

else:
    st.stop()

# ---------------------- Core Calculation ----------------------
S_min = np.floor(stock_price * (1 - s_range))
S_max = np.ceil(stock_price * (1 + s_range))
S_grid = np.arange(S_min, S_max + 0.1, 0.1)

C_at_maturity = [np.maximum(S_grid - x, 0) for x in [x1, x2, x3]]
P_at_maturity = [np.maximum(x - S_grid, 0) for x in [x1, x2, x3]]

Deltas = [delta1, delta2, delta3]

if butterfly_type == 'Call':
    y_option_1 = C_at_maturity[0] - c1
    y_option_2 = c2 - C_at_maturity[1]
    y_option_3 = C_at_maturity[2] - c3
    Effective_Delta = 2 * delta2 - delta1 - delta3
elif butterfly_type == 'Put':
    y_option_1 = P_at_maturity[0] - p1
    y_option_2 = p2 - P_at_maturity[1]
    y_option_3 = P_at_maturity[2] - p3
    Effective_Delta = -2 * delta2 + delta1 + delta3

y_stock = Effective_Delta * (S_grid - stock_price)
PnL = 100 * (y_option_1 + 2 * y_option_2 + y_option_3 + y_stock)

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
ax.set_title(f"{butterfly_type} Butterfly Strategy PnL\nEffective Δ: {Effective_Delta:.2f} | Profit Region: {pos_str}")

st.pyplot(fig)
