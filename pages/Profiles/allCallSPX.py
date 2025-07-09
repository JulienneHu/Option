import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf

st.title("📘 All Call SPX Visualizer")

# ----------------- Input Layout (AppProfile style) -----------------

col1, col2, col3 = st.columns(3)
symbol = col1.text_input("Symbol", value="^SPX")
maturity_date = col2.text_input("Maturity Date (YYYY-MM-DD)", value="2025-07-18")
Ax = col3.number_input("Strike A", value=6175.0)

col4, col5, col6 = st.columns(3)
Bx = col4.number_input("Strike B", value=6230.0)
n_A = col5.slider("Number of A", 0, 5, 1)
n_B = col6.slider("Number of B", 0, 5, 2)

col7, col8, col9 = st.columns(3)
delta_A = col7.number_input("Delta A", value=0.0)
delta_B = col8.number_input("Delta B", value=0.0)
stock_range = col9.number_input("Stock Range (%)", value=0.25, step=0.01)

col10, col11, col12 = st.columns(3)
y_min = col10.number_input("Y Axis Min", value=-1000)
y_max = col11.number_input("Y Axis Max", value=1000)
trade_type = col12.selectbox(
    "Trade Type",
    ['Buy A - Buy B', 'Buy A - Sell B', 'Sell A - Buy B', 'Sell A - Sell B']
)

# ----------------- Fetch Data & Calculate -----------------

if st.button("Fetch Data and Plot Strategy"):

    try:
        ticker = yf.Ticker(symbol)
        live_price = ticker.history(period="1d")['Close'].iloc[-1]
        S_min = np.floor(live_price * (1 - stock_range))
        S_max = np.ceil(live_price * (1 + stock_range))
        S_grid = np.arange(S_min, S_max, 0.1)

        A_at_maturity = np.maximum(S_grid - Ax, 0)
        B_at_maturity = np.maximum(S_grid - Bx, 0)

        # Using fixed premiums for illustration; replace with fetched values if integrated with your FetchOptionThread
        A_ask = 5
        A_bid = 4.5
        B_ask = 5
        B_bid = 4.5

        if trade_type == 'Buy A - Buy B':
            A_premium = A_ask
            B_premium = B_ask
            y_option = n_A * (A_at_maturity - A_premium) + n_B * (B_at_maturity - B_premium)
            y_stock = n_A * delta_A * (live_price - S_grid) + n_B * delta_B * (live_price - S_grid)
            effective_delta = - n_A * delta_A - n_B * delta_B
        elif trade_type == 'Buy A - Sell B':
            A_premium = A_ask
            B_premium = B_bid
            y_option = n_A * (A_at_maturity - A_premium) + n_B * (B_premium - B_at_maturity)
            y_stock = n_A * delta_A * (live_price - S_grid) + n_B * delta_B * (S_grid - live_price)
            effective_delta = - n_A * delta_A + n_B * delta_B
        elif trade_type == 'Sell A - Buy B':
            A_premium = A_bid
            B_premium = B_ask
            y_option = n_A * (A_premium - A_at_maturity) + n_B * (B_at_maturity - B_premium)
            y_stock = n_A * delta_A * (S_grid - live_price) + n_B * delta_B * (live_price - S_grid)
            effective_delta = n_A * delta_A - n_B * delta_B
        else:  # Sell A - Sell B
            A_premium = A_bid
            B_premium = B_bid
            y_option = n_A * (A_premium - A_at_maturity) + n_B * (B_premium - B_at_maturity)
            y_stock = n_A * delta_A * (S_grid - live_price) + n_B * delta_B * (S_grid - live_price)
            effective_delta = n_A * delta_A + n_B * delta_B

        y = 100 * (y_option + y_stock)

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(S_grid, y, label="Strategy P/L", color="blue")
        ax.fill_between(S_grid, y, where=y > 0, color="#007560", alpha=0.6, label="Profit")
        ax.fill_between(S_grid, y, where=y <= 0, color="#bd1414", alpha=0.6, label="Loss")
        ax.axhline(0, color='black', linewidth=1)
        ax.set_xlabel("Stock Price")
        ax.set_ylabel("Payoff at Maturity")
        ax.set_ylim(y_min, y_max)
        ax.set_title(
            f"Strategy: {trade_type} | 100Δ_effective = {round(100 * effective_delta, 2)}\n"
            f"n_A={n_A}, n_B={n_B}, Δ_A={delta_A}, Δ_B={delta_B}, S={live_price:.2f}"
        )
        ax.legend()
        ax.grid(True)

        st.pyplot(fig)

    except Exception as e:
        st.error(f"Error during calculation or plotting: {e}")

# --- Display fetched stock and option data ---
with st.expander("Option & Stock Data", expanded=True):
    if 'live_price' in locals():
        price_change = ticker.history(period="2d")['Close'].iloc[-1] - ticker.history(period="2d")['Close'].iloc[-2]
        pct_change = (price_change / ticker.history(period="2d")['Close'].iloc[-2]) * 100

        change_color = "green" if price_change >= 0 else "red"
        change_sign = "+" if price_change >= 0 else ""

        st.markdown(f"""
        ### Stock Price
        <div style="font-size: 48px; font-weight: bold;">{live_price:.2f}</div>
        <div style="color: {change_color}; font-size: 20px;">{change_sign}{price_change:.2f} ({change_sign}{pct_change:.2f}%)</div>
        """, unsafe_allow_html=True)

        # Fetch call and put tickers
        options = ticker.option_chain(maturity_date)
        calls = options.calls
        puts = options.puts

        call_row = calls.loc[calls['strike'] == Ax].iloc[0] if not calls.loc[calls['strike'] == Ax].empty else None
        put_row = puts.loc[puts['strike'] == Bx].iloc[0] if not puts.loc[puts['strike'] == Bx].empty else None

        if call_row is not None:
            st.markdown(f"""
            **Call Ticker:** <span style='background-color:#e8f5e9; color:#1b5e20; padding:2px 6px; border-radius:4px; font-family: monospace;'>{call_row['contractSymbol']}</span> |
            Last: {call_row['lastPrice']} | Ask: {call_row['ask']} | Bid: {call_row['bid']}
            """, unsafe_allow_html=True)
        else:
            st.warning("Call option data not found for the specified strike.")

        if put_row is not None:
            st.markdown(f"""
            **Put Ticker:** <span style='background-color:#e8f5e9; color:#1b5e20; padding:2px 6px; border-radius:4px; font-family: monospace;'>{put_row['contractSymbol']}</span> |
            Last: {put_row['lastPrice']} | Ask: {put_row['ask']} | Bid: {put_row['bid']}
            """, unsafe_allow_html=True)
        else:
            st.warning("Put option data not found for the specified strike.")
    else:
        st.info("No data fetched yet. Click 'Fetch Data and Plot Strategy' to retrieve.")
