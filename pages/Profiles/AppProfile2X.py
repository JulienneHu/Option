import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf
from datetime import datetime


st.title("📘 All Call-Put SPX Visualizer")

st.subheader("Strategy 1")
col1, col2, col3 = st.columns(3)
n1_call = col1.slider("N1 Calls", 0, 10, 1)
n1_put = col2.slider("N1 Puts", 0, 10, 1)
delta1_call = col3.number_input("Delta 1 Call", value=0.0)

col4, col5, col6 = st.columns(3)
delta1_put = col4.number_input("Delta 1 Put", value=0.0)
X1 = col5.number_input("Strike Price 1", value=150.0)

st.subheader("Strategy 2")
col7, col8, col9 = st.columns(3)
n2_call = col7.slider("N2 Calls", 0, 10, 1)
n2_put = col8.slider("N2 Puts", 0, 10, 1)
delta2_call = col9.number_input("Delta 2 Call", value=0.0)

col10, col11, col12 = st.columns(3)
delta2_put = col10.number_input("Delta 2 Put", value=0.0)
X2 = col11.number_input("Strike Price 2", value=180.0)

# --- General Inputs ---
st.subheader("Stock & Global Settings")
col13, col14, col15 = st.columns(3)
symbol = col13.text_input("Symbol", "AAPL")
maturity_date_input = st.date_input("Maturity Date", datetime(2025, 7, 18))
maturity_date = maturity_date_input.strftime('%Y-%m-%d')
stock_range = col15.number_input("Stock Range (%)", value=0.2)

col16, col17 = st.columns(2)
y_min = col16.number_input("Y Axis Min", value=-5000)
y_max = col17.number_input("Y Axis Max", value=5000)

trade1_type = st.selectbox(
    "Strategy 1 Trade Type",
    ['Buy Call-Buy Put', 'Buy Call-Sell Put', 'Sell Call-Buy Put', 'Sell Call-Sell Put'],
)

trade2_type = st.selectbox(
    "Strategy 2 Trade Type",
    ['Buy Call-Buy Put', 'Buy Call-Sell Put', 'Sell Call-Buy Put', 'Sell Call-Sell Put'],
)

# --- Fetch, Display, and Plot ---
if st.button("Fetch Data and Plot Strategy"):

    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="2d")
        live_price = hist['Close'].iloc[-1]
        previous_price = hist['Close'].iloc[-2]
        price_change = live_price - previous_price
        pct_change = (price_change / previous_price) * 100

        # Color logic
        change_color = "green" if price_change >= 0 else "red"
        sign = "+" if price_change >= 0 else ""

        # Fetch Option Chain
        options = ticker.option_chain(maturity_date)
        calls = options.calls
        puts = options.puts

        # Strategy 1
        call1 = calls.loc[calls['strike'] == X1]
        put1 = puts.loc[puts['strike'] == X1]
        call1_price = call1.iloc[0]['lastPrice'] if not call1.empty else "NA"
        call1_bid = call1.iloc[0]['bid'] if not call1.empty else "NA"
        call1_ask = call1.iloc[0]['ask'] if not call1.empty else "NA"
        put1_price = put1.iloc[0]['lastPrice'] if not put1.empty else "NA"
        put1_bid = put1.iloc[0]['bid'] if not put1.empty else "NA"
        put1_ask = put1.iloc[0]['ask'] if not put1.empty else "NA"

        # Strategy 2
        call2 = calls.loc[calls['strike'] == X2]
        put2 = puts.loc[puts['strike'] == X2]
        call2_price = call2.iloc[0]['lastPrice'] if not call2.empty else "NA"
        call2_bid = call2.iloc[0]['bid'] if not call2.empty else "NA"
        call2_ask = call2.iloc[0]['ask'] if not call2.empty else "NA"
        put2_price = put2.iloc[0]['lastPrice'] if not put2.empty else "NA"
        put2_bid = put2.iloc[0]['bid'] if not put2.empty else "NA"
        put2_ask = put2.iloc[0]['ask'] if not put2.empty else "NA"

        # Display fetched data
        with st.expander("📈 Fetched Stock and Option Data", expanded=True):
            st.markdown(f"""
            ### Stock Price: {live_price:.2f}
            <span style='color:{change_color}; font-size: 18px;'>{sign}{price_change:.2f} ({sign}{pct_change:.2f}%)</span>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            **Strategy 1 (Strike {X1}):**
            - Call: Last {call1_price} | Bid {call1_bid} | Ask {call1_ask}
            - Put: Last {put1_price} | Bid {put1_bid} | Ask {put1_ask}

            **Strategy 2 (Strike {X2}):**
            - Call: Last {call2_price} | Bid {call2_bid} | Ask {call2_ask}
            - Put: Last {put2_price} | Bid {put2_bid} | Ask {put2_ask}
            """)

        # Payoff Calculation
        S_min = np.floor(live_price * (1 - stock_range))
        S_max = np.ceil(live_price * (1 + stock_range))
        S_grid = np.arange(S_min, S_max + 1, 1)

        def calc_strategy(n_call, n_put, delta_call, delta_put, X, call_premium, put_premium, trade_type):
            call_payoff = np.maximum(S_grid - X, 0)
            put_payoff = np.maximum(X - S_grid, 0)
            delta_put = -abs(delta_put)
            if trade_type == 'Buy Call-Buy Put':
                y_option = n_call * (call_payoff - call_premium) + n_put * (put_payoff - put_premium)
                y_stock = n_call * delta_call * (live_price - S_grid) + n_put * delta_put * (live_price - S_grid)
                eff_delta = -n_call * delta_call - n_put * delta_put
            elif trade_type == 'Buy Call-Sell Put':
                y_option = n_call * (call_payoff - call_premium) + n_put * (put_premium - put_payoff)
                y_stock = n_call * delta_call * (live_price - S_grid) + n_put * delta_put * (S_grid - live_price)
                eff_delta = -n_call * delta_call + n_put * delta_put
            elif trade_type == 'Sell Call-Buy Put':
                y_option = n_call * (call_premium - call_payoff) + n_put * (put_payoff - put_premium)
                y_stock = n_call * delta_call * (S_grid - live_price) + n_put * delta_put * (live_price - S_grid)
                eff_delta = n_call * delta_call - n_put * delta_put
            else:
                y_option = n_call * (call_premium - call_payoff) + n_put * (put_premium - put_payoff)
                y_stock = n_call * delta_call * (S_grid - live_price) + n_put * delta_put * (S_grid - live_price)
                eff_delta = n_call * delta_call + n_put * delta_put
            return 100 * (y_option + y_stock), eff_delta

        call1_premium_use = float(call1_ask) if call1_ask != "NA" else 5
        put1_premium_use = float(put1_ask) if put1_ask != "NA" else 5
        call2_premium_use = float(call2_ask) if call2_ask != "NA" else 5
        put2_premium_use = float(put2_ask) if put2_ask != "NA" else 5

        y1, eff_delta1 = calc_strategy(n1_call, n1_put, delta1_call, delta1_put, X1, call1_premium_use, put1_premium_use, trade1_type)
        y2, eff_delta2 = calc_strategy(n2_call, n2_put, delta2_call, delta2_put, X2, call2_premium_use, put2_premium_use, trade2_type)
        y_total = y1 + y2
        eff_delta_total = eff_delta1 + eff_delta2

        # Plot
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(S_grid, y1, label="Strategy 1", color="red")
        ax.plot(S_grid, y2, label="Strategy 2", color="purple")
        ax.plot(S_grid, y_total, label="Combined", color="blue")
        ax.axhline(0, color='black', linewidth=1)
        ax.set_ylim(y_min, y_max)
        ax.set_xlabel("Stock Price")
        ax.set_ylabel("Payoff at Maturity")
        ax.set_title(f"Combined Effective Delta: {eff_delta_total:.2f}")
        ax.grid(True)
        ax.legend()
        st.pyplot(fig)

    except Exception as e:
        st.error(f"Error: {e}")
