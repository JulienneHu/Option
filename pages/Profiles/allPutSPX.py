import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf
from datetime import datetime


st.title("📘 All Put SPX Visualizer")

# --- Input Block ---
col1, col2, col3 = st.columns(3)
symbol = col1.text_input("Symbol", value="^SPX")
with col2:
    maturity_date_input = st.date_input("Maturity Date", datetime(2025, 7, 18))
    maturity_date = maturity_date_input.strftime('%Y-%m-%d')
trade_type = col3.selectbox(
    "Trade Type",
    ['Buy A - Buy B', 'Buy A - Sell B', 'Sell A - Buy B', 'Sell A - Sell B']
)

col4, col5, col6 = st.columns(3)
n_A = col4.slider("Number of A Puts", 0, 10, 1)
Ax = col5.number_input("Strike A", value=6175.0)
delta_A = col6.number_input("Delta A", value=0.0)

col7, col8, col9 = st.columns(3)
n_B = col7.slider("Number of B Puts", 0, 10, 2)
Bx = col8.number_input("Strike B", value=6230.0)
delta_B = col9.number_input("Delta B", value=0.0)

col10, col11, col12 = st.columns(3)
y_min = col10.number_input("Y Axis Min", value=-1000)
y_max = col11.number_input("Y Axis Max", value=1000)
stock_range = col12.number_input("Stock Range (%)", value=0.25)

# --- Fetch Data & Display ---
if st.button("Fetch Data & Plot"):
    try:
        ticker = yf.Ticker(symbol)
        live_price = ticker.history(period="1d")['Close'].iloc[-1]

        # Fetch put options
        options = ticker.option_chain(maturity_date)
        puts = options.puts
        A_put = puts[puts['strike'] == Ax]
        B_put = puts[puts['strike'] == Bx]

        if not A_put.empty:
            A_last = A_put.iloc[0]['lastPrice']
            A_bid = A_put.iloc[0]['bid']
            A_ask = A_put.iloc[0]['ask']
            A_symbol = A_put.iloc[0]['contractSymbol']
        else:
            A_last = A_bid = A_ask = A_symbol = "NA"

        if not B_put.empty:
            B_last = B_put.iloc[0]['lastPrice']
            B_bid = B_put.iloc[0]['bid']
            B_ask = B_put.iloc[0]['ask']
            B_symbol = B_put.iloc[0]['contractSymbol']
        else:
            B_last = B_bid = B_ask = B_symbol = "NA"


        # --- Payoff Calculation ---
        S_min = np.floor(live_price * (1 - stock_range))
        S_max = np.ceil(live_price * (1 + stock_range))
        S_grid = np.arange(S_min, S_max, 0.1)

        A_at_maturity = np.maximum(Ax - S_grid, 0)
        B_at_maturity = np.maximum(Bx - S_grid, 0)

        # Use bid/ask logic
        A_premium = float(A_ask) if A_ask != "NA" else 5
        B_premium = float(B_ask) if B_ask != "NA" else 5

        if trade_type == 'Buy A - Buy B':
            y_option = n_A * (A_at_maturity - A_premium) + n_B * (B_at_maturity - B_premium)
            y_stock = n_A * delta_A * (live_price - S_grid) + n_B * delta_B * (live_price - S_grid)
            effective_delta = - n_A * delta_A - n_B * delta_B
        elif trade_type == 'Buy A - Sell B':
            B_premium = float(B_bid) if B_bid != "NA" else 5
            y_option = n_A * (A_at_maturity - A_premium) + n_B * (B_premium - B_at_maturity)
            y_stock = n_A * delta_A * (live_price - S_grid) + n_B * delta_B * (S_grid - live_price)
            effective_delta = - n_A * delta_A + n_B * delta_B
        elif trade_type == 'Sell A - Buy B':
            A_premium = float(A_bid) if A_bid != "NA" else 5
            y_option = n_A * (A_premium - A_at_maturity) + n_B * (B_at_maturity - B_premium)
            y_stock = n_A * delta_A * (S_grid - live_price) + n_B * delta_B * (live_price - S_grid)
            effective_delta = n_A * delta_A - n_B * delta_B
        else:  # Sell A - Sell B
            A_premium = float(A_bid) if A_bid != "NA" else 5
            B_premium = float(B_bid) if B_bid != "NA" else 5
            y_option = n_A * (A_premium - A_at_maturity) + n_B * (B_premium - B_at_maturity)
            y_stock = n_A * delta_A * (S_grid - live_price) + n_B * delta_B * (S_grid - live_price)
            effective_delta = n_A * delta_A + n_B * delta_B

        y = 100 * (y_option + y_stock)
        # --- Calculate Profit Range (pos_str) ---
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
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(S_grid, y, label="Strategy P/L", color="blue")
        ax.fill_between(S_grid, y, where=(y > 0), color="#007560", alpha=0.6, label="Profit")
        ax.fill_between(S_grid, y, where=(y <= 0), color="#bd1414", alpha=0.6, label="Loss")
        ax.axhline(0, color='black', linewidth=1)
        ax.set_xlabel("Stock Price")
        ax.set_ylabel("Payoff at Maturity")
        ax.set_ylim(y_min, y_max)
        ax.set_title(
            f"Trade: {trade_type} | 100Δ_effective = {round(100 * effective_delta, 2)}\n"
            f"Make $ if S ∈ {pos_str}\n"
            f"n_A={n_A}, n_B={n_B}, Δ_A={delta_A}, Δ_B={delta_B}, S={live_price:.2f}"
        )
        ax.legend()
        ax.grid(True)

        st.pyplot(fig)
        
        # --- Expand Block for fetched data ---
        with st.expander("Fetched Stock & Option Data", expanded=True):
            price_change = ticker.history(period="2d")['Close'].iloc[-1] - ticker.history(period="2d")['Close'].iloc[-2]
            pct_change = (price_change / ticker.history(period="2d")['Close'].iloc[-2]) * 100
            color = "green" if price_change >= 0 else "red"

            st.markdown(f"""
            ### Stock Price
            <div style="font-size: 48px; font-weight: bold;">{live_price:.2f}</div>
            <div style="color: {color}; font-size: 20px;">{price_change:+.2f} ({pct_change:+.2f}%)</div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            **Put A Ticker:** <code>{A_symbol}</code> | Last: {A_last} | Ask: {A_ask} | Bid: {A_bid}
            """, unsafe_allow_html=True)

            st.markdown(f"""
            **Put B Ticker:** <code>{B_symbol}</code> | Last: {B_last} | Ask: {B_ask} | Bid: {B_bid}
            """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error during calculation or plotting: {e}")
