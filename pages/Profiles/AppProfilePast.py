import datetime
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime



st.title("📘 AppProfile - Past Option Strategy")

col1, col2, col3 = st.columns(3)
with col1:
    symbol = st.text_input("Symbol", "AAPL")
with col2:
    expiration_input = st.date_input("Maturity Date", datetime(2025, 6, 20))
    expiration = expiration_input.strftime('%Y-%m-%d')
with col3:
    strike_price = st.number_input("Strike Price", value=190.0)

col4, col5 = st.columns(2)
with col4:
    call_premium = st.number_input("Call Premium", value=9.8)
    num_calls = st.slider("Number of Calls", 0, 5, 1)
    delta_call = st.number_input("Delta Call", value=0.0)
with col5:
    put_premium = st.number_input("Put Premium", value=14.5)
    num_puts = st.slider("Number of Puts", 0, 5, 1)
    delta_put = st.number_input("Delta Put", value=0.0)

type_options = ["Buy Call-Buy Put", "Buy Call-Sell Put", "Sell Call-Buy Put", "Sell Call-Sell Put"]
trade_type = st.selectbox("Trade Type", type_options)

col6, col7, col8, col9 = st.columns(4)
with col6:
    stock_price = st.number_input("Stock Price", value=150.0)
with col7:
    stock_range = st.number_input("Stock Range (%)", value=0.25)
with col8:
    y_min = st.number_input("Y Axis Min", value=-10000.0)
with col9:
    y_max = st.number_input("Y Axis Max", value=10000.0)

# --- Calculate Payoff ---
S_min = np.floor(stock_price * (1 - stock_range))
S_max = np.ceil(stock_price * (1 + stock_range))
S_grid = np.arange(S_min, S_max + 1, 0.1)
call_payoff = np.maximum(S_grid - strike_price, 0)
put_payoff = np.maximum(strike_price - S_grid, 0)
delta_put = -abs(delta_put)

if trade_type == "Buy Call-Buy Put":
    y_option = num_calls * (call_payoff - call_premium) + num_puts * (put_payoff - put_premium)
    y_stock = num_calls * delta_call * (stock_price - S_grid) + num_puts * delta_put * (stock_price - S_grid)
    effective_delta = -num_calls * delta_call - num_puts * delta_put
elif trade_type == "Buy Call-Sell Put":
    y_option = num_calls * (call_payoff - call_premium) + num_puts * (put_premium - put_payoff)
    y_stock = 0
    effective_delta = -num_calls * delta_call + num_puts * delta_put
elif trade_type == "Sell Call-Buy Put":
    y_option = num_calls * (call_premium - call_payoff) + num_puts * (put_payoff - put_premium)
    y_stock = num_calls * delta_call * (S_grid - stock_price) + num_puts * delta_put * (stock_price - S_grid)
    effective_delta = num_calls * delta_call - num_puts * delta_put
elif trade_type == "Sell Call-Sell Put":
    y_option = num_calls * (call_premium - call_payoff) + num_puts * (put_premium - put_payoff)
    y_stock = num_calls * delta_call * (S_grid - stock_price) + num_puts * delta_put * (S_grid - stock_price)
    effective_delta = num_calls * delta_call + num_puts * delta_put
else:
    y_option = y_stock = 0
    effective_delta = 0

y = 100 * (y_option + y_stock)
yp = np.maximum(y, 0)
y_neg = np.where(yp == 0)[0]
y_pos = np.where(yp > 0)[0]

if y_neg.size != 0 and y_pos.size != 0:
    if y_neg[0] > 0 and y_neg[-1] < len(S_grid) - 1:
        pos_str = f'(0, {np.ceil(S_grid[y_neg[0] - 1])}) and ({np.floor(S_grid[y_neg[-1] + 1])}, ∞)'
    else:
        pos_range = S_grid[y_pos]
        if y_pos[0] == 0:
            pos_str = f'(0, {np.ceil(pos_range[-1])})'
        else:
            pos_str = f'({np.floor(pos_range[0])}, {np.ceil(pos_range[-1])})'
elif y_neg.size == 0:
    pos_str = '(0, ∞)'
else:
    pos_str = '∞'

# --- Plot ---
title_str = f"100Δ_effective = {round(100 * effective_delta)}. Make money if S ∈ {pos_str}\n"
title_str += f"n_call = {num_calls}, n_put = {num_puts}, Δ_call = {delta_call:.2f}, Δ_put = {delta_put:.2f}"

fig, ax = plt.subplots()
ax.plot(S_grid, y, 'blue', linewidth=1.5, label='Strategy PnL')
ax.fill_between(S_grid, y, where=(y > 0), color='#bd1414', alpha=0.8, label='Profit')
ax.fill_between(S_grid, y, where=(y <= 0), color='#007560', alpha=0.8, label='Loss')
ax.set_title(title_str, fontsize=14, fontweight='bold')
ax.set_xlabel("Stock Price")
ax.set_ylabel("Payoff at Maturity")
ax.axhline(0, color='black', linewidth=1.5)
ax.set_ylim([y_min, y_max])
ax.set_xlim([S_min, S_max])
ax.grid(True)
ax.legend()
st.pyplot(fig)
