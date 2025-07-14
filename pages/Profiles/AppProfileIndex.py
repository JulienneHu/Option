import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from datetime import datetime
from realPrice.realStock import get_realtime_stock_price
from realPrice.realOptionIndex import main as get_realtime_option_price, get_option_chain

st.title("📘 AppProfile Index")

col1, col2, col3 = st.columns(3)
with col1:
    symbol = st.text_input("Symbol", value="^SPX")
with col2:
    expiration_date_input = st.date_input("Maturity Date", datetime(2025, 8, 15))
    expiration_date = expiration_date_input.strftime('%Y-%m-%d')
with col3:
    strike_price = st.number_input("Strike Price", value=5900.0)

col1, col2, col3 = st.columns(3)
with col1:
    n_calls = st.slider("Number of Calls", 0, 5, 1)
with col2:
    n_puts = st.slider("Number of Puts", 0, 5, 1)
with col3:
    trade_type = st.selectbox("Trade Type", ['Buy Call-Buy Put', 'Buy Call-Sell Put', 'Sell Call-Buy Put', 'Sell Call-Sell Put'])

col1, col2, col3 = st.columns(3)
with col1:
    delta_call = st.number_input("Delta Call", value=0.0)
with col2:
    delta_put = st.number_input("Delta Put", value=0.0)

col1, col2, col3 = st.columns(3)
with col1:
    y_min = st.number_input("Y Axis Min", value=-6000)
with col2:
    y_max = st.number_input("Y Axis Max", value=6000)
with col3:
    stock_range = st.number_input("Stock Range (%)", value=0.25)

# --- Fetch Stock & Option Data ---
def fetch_data():
    stock_price, price_change, percent_change = get_realtime_stock_price(symbol)
    option_data = get_realtime_option_price(symbol, expiration_date, strike_price)
    option_symbol = get_option_chain(symbol, expiration_date, strike_price)

    if option_data is None or stock_price is None:
        st.error("Failed to fetch data. Please check inputs.")
        return None, None, None, None

    prices, open_interests, volumes = option_data
    return stock_price, price_change, percent_change, prices, open_interests, volumes, option_symbol

# --- Plot Payoff Function ---
def plot_payoff(S, y):
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(S, y, 'b', linewidth=1.5, label='Strategy PnL')
    ax.fill_between(S, y, where=(y > 0), color='#007560', alpha=0.8, label='Profit')
    ax.fill_between(S, y, where=(y <= 0), color='#bd1414', alpha=0.8, label='Loss')
    ax.axhline(0, color='black', linewidth=1.0)
    ax.set_title("Option Strategy Payoff", fontsize=16)
    ax.set_xlabel("Stock Price")
    ax.set_ylabel("Payoff at Maturity")
    ax.set_ylim([y_min, y_max])
    ax.grid(True)
    ax.legend()
    st.pyplot(fig)

# --- Run Main Logic ---
if st.button("Fetch Data & Plot"):
    result = fetch_data()
    if result:
        stock_price, price_change, percent_change, prices, open_interests, volumes, option_symbol = result

        # Compute payoff
        S_min = np.floor(stock_price * (1 - stock_range))
        S_max = np.ceil(stock_price * (1 + stock_range))
        S_grid = np.arange(S_min, S_max, 0.5)
        X = strike_price
        call_price, put_price = prices if prices else (0, 0)
        call_price = 0 if call_price == 'NA' else call_price
        put_price = 0 if put_price == 'NA' else put_price

        call_payoff = np.maximum(S_grid - X, 0)
        put_payoff = np.maximum(X - S_grid, 0)

        delta_put = -abs(delta_put)

        if trade_type == 'Buy Call-Buy Put':
            y = n_calls * (call_payoff - call_price) + n_puts * (put_payoff - put_price)
            y_stock = n_calls * delta_call * (stock_price - S_grid) + n_puts * delta_put * (stock_price - S_grid)
        elif trade_type == 'Buy Call-Sell Put':
            y = n_calls * (call_payoff - call_price) + n_puts * (put_price - put_payoff)
            y_stock = n_calls * delta_call * (stock_price - S_grid) + n_puts * (-delta_put) * (stock_price - S_grid)
        elif trade_type == 'Sell Call-Buy Put':
            y = n_calls * (call_price - call_payoff) + n_puts * (put_payoff - put_price)
            y_stock = n_calls * delta_call * (S_grid - stock_price) + n_puts * delta_put * (stock_price - S_grid)
        elif trade_type == 'Sell Call-Sell Put':
            y = n_calls * (call_price - call_payoff) + n_puts * (put_price - put_payoff)
            y_stock = n_calls * delta_call * (S_grid - stock_price) + n_puts * delta_put * (S_grid - stock_price)

        total_y = 100 * (y + y_stock)
        plot_payoff(S_grid, total_y)

        # --- Option & Stock Info Display ---
        with st.expander("Option & Stock Data"):
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Stock Price", f"{stock_price:.2f}", f"{price_change:.2f} ({percent_change:.2f}%)",
                          delta_color="inverse" if price_change < 0 else "normal")
            with col2:
                st.markdown(f"**Option Chain Prefix**: `{option_symbol}`")
                st.markdown(f"**Call Price**: {call_price} | OI: {open_interests[0]} | Vol: {volumes[0]}")
                st.markdown(f"**Put Price**: {put_price} | OI: {open_interests[1]} | Vol: {volumes[1]}")
