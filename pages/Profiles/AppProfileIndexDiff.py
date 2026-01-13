from datetime import datetime
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from realPrice.realStock import get_realtime_stock_price
from realPrice.realOptionIndexDiff import main as get_realtime_option_price
from realPrice.realOptionIndex import get_option_chain
from datetime import datetime


st.markdown("📘  AppProfile Diff")

# --- Input Fields ---
col1, col2, col3 = st.columns(3)
with col1:
    symbol = st.text_input("Symbol", "^SPX")
    n_call = st.slider("Number of Calls", 0, 5, 1)
    delta_call = st.number_input("Delta Call", value=0.0)
    y_min = st.number_input("Y Axis Min", value=-6000.0)
with col2:
    date_input = st.date_input("Maturity Date", datetime(2026, 8, 21))
    date = date_input.strftime('%Y-%m-%d')
    n_put = st.slider("Number of Puts", 0, 5, 1)
    delta_put = st.number_input("Delta Put", value=0.0)
    y_max = st.number_input("Y Axis Max", value=6000.0)
with col3:
    Cx = st.number_input("Call Strike", value=6000.0)
    Px = st.number_input("Put Strike", value=5900.0)
    stock_range = st.number_input("Stock Range (%)", value=0.25)
    trade_type = st.selectbox("Trade Type", ["Buy Call-Buy Put", "Buy Call-Sell Put", "Sell Call-Buy Put", "Sell Call-Sell Put"])

# --- Fetch Data Button ---
fetch = st.button("Fetch Data")

stock_price, price_change, pct_change = get_realtime_stock_price(symbol) if fetch else (None, None, None)
option_data_call = get_realtime_option_price(symbol, date, Cx) if fetch else (None, None, None)
option_data_put = get_realtime_option_price(symbol, date, Px) if fetch else (None, None, None)
call_chain = get_option_chain(symbol, date, Cx) if fetch else None
put_chain = get_option_chain(symbol, date, Px) if fetch else None

if fetch:
    
    try:
        stock_price = float(stock_price)
        call_ask = float(option_data_call[2][0])
        call_bid = float(option_data_call[1][0])
        put_ask = float(option_data_put[2][1])
        put_bid = float(option_data_put[1][1])

        S_min = np.floor(stock_price * (1 - stock_range))
        S_max = np.ceil(stock_price * (1 + stock_range))
        S_grid = np.arange(S_min, S_max + 1, 0.1)
        call_at_maturity = np.maximum(S_grid - Cx, 0)
        put_at_maturity = np.maximum(Px - S_grid, 0)

        if trade_type == 'Buy Call-Buy Put':
            call_premium = call_ask
            put_premium = put_ask
            y_option = n_call * (call_at_maturity - call_premium) + n_put * (put_at_maturity - put_premium)
            y_stock = n_call * delta_call * (stock_price - S_grid) + n_put * (-abs(delta_put)) * (stock_price - S_grid)
            effective_delta = -n_call * delta_call - n_put * (-abs(delta_put))
        elif trade_type == 'Buy Call-Sell Put':
            call_premium = call_ask
            put_premium = put_bid
            y_option = n_call * (call_at_maturity - call_premium) + n_put * (put_premium - put_at_maturity)
            effective_delta = -n_call * delta_call + n_put * (-abs(delta_put))
        elif trade_type == 'Sell Call-Buy Put':
            call_premium = call_bid
            put_premium = put_ask
            y_option = n_call * (call_premium - call_at_maturity) + n_put * (put_at_maturity - put_premium)
            y_stock = n_call * delta_call * (S_grid - stock_price) + n_put * (-abs(delta_put)) * (stock_price - S_grid)
            effective_delta = n_call * delta_call - n_put * (-abs(delta_put))
        elif trade_type == 'Sell Call-Sell Put':
            call_premium = call_bid
            put_premium = put_bid
            y_option = n_call * (call_premium - call_at_maturity) + n_put * (put_premium - put_at_maturity)
            y_stock = n_call * delta_call * (S_grid - stock_price) + n_put * (-abs(delta_put)) * (S_grid - stock_price)
            effective_delta = n_call * delta_call + n_put * (-abs(delta_put))

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


        fig, ax = plt.subplots()
        ax.plot(S_grid, y, 'blue', label='Strategy PnL')
        ax.fill_between(S_grid, y, where=(y > 0), color='#007560', alpha=0.8, label='Profit')
        ax.fill_between(S_grid, y, where=(y <= 0), color='#bd1414', alpha=0.8, label='Loss')
        ax.set_title(
            f'100Δ_effective = {round(100 * effective_delta)}. Make money if S ∈ {pos_str}\n' \
            f'n_call = {n_call}, n_put = {n_put}, Δ_call = {delta_call:.2f}, Δ_put = {delta_put:.2f}'
        )
        ax.set_xlabel("Stock Price")
        ax.set_ylabel("Payoff at Maturity")
        ax.axhline(0, color='black')
        ax.set_ylim([y_min, y_max])
        ax.set_xlim([S_min, S_max])
        ax.grid(True)
        ax.legend()
        st.pyplot(fig)
        with st.expander("Option & Stock Data", expanded=True):
            if stock_price != 'NA':
                price_color = "green" if price_change > 0 else ("red" if price_change < 0 else "black")
                st.markdown(f"### Stock Price\n**<span style='font-size:36px'>{stock_price:.2f}</span>**  ", unsafe_allow_html=True)
                st.markdown(f"<span style='color:{price_color}; font-size:20px'> {price_change:+.2f} ({pct_change:+.2f}%) </span>", unsafe_allow_html=True)
            
            st.markdown(f"**Call Ticker:** `{call_chain}` | Last: {option_data_call[0][0]} | Ask: {option_data_call[2][0]} | Bid: {option_data_call[1][0]}")
            st.markdown(f"**Put Ticker:** `{put_chain}` | Last: {option_data_put[0][1]} | Ask: {option_data_put[2][1]} | Bid: {option_data_put[1][1]}")

    except Exception as e:
        st.error(f"Error in plotting: {e}")
