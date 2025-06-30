import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from realPrice.realOption import get_realtime_option_price, calls_or_puts
from realPrice.realOptionProfile import main as get_option
from tools.APFetch import fetch_stock_price_streamlit, fetch_option_prices_streamlit

st.title("📘 AppProfile")

col1, col2, col3 = st.columns(3)
with col1:
    symbol = st.text_input("Symbol", value="AAPL")
    n_call = st.slider("Number of Calls", 0, 5, 1)
    delta_call = st.number_input("Delta Call", value=0.0)
    
with col2:
    date = st.text_input("Expiration Date (YYYY-MM-DD)", value="2025-08-15")
    n_put = st.slider("Number of Puts", 0, 5, 1)
    delta_put = st.number_input("Delta Put", value=0.0)
with col3:
    strike = st.number_input("Strike Price", value=200.0)
    trade_type = st.selectbox("Trade Type", ['Buy Call-Buy Put', 'Buy Call-Sell Put', 'Sell Call-Buy Put', 'Sell Call-Sell Put'])
    


# Additional controls
col4, col5, col6 = st.columns(3)
with col4:
    y_min = st.number_input("Y Axis Min", value=-6000)
with col5:
    y_max = st.number_input("Y Axis Max", value=6000)
with col6:
    s_range = st.number_input("Stock Range (%)", value=0.25)


if symbol and date and strike:
    option_tickers = calls_or_puts(symbol, date, strike)

    # Validate result
    if not option_tickers or len(option_tickers) < 2 or not all(option_tickers):
        st.error("❌ Unable to generate valid option tickers. Please check the symbol, date, and strike.")
        st.stop()

    try:
        call_data = get_realtime_option_price(option_tickers[0])
        put_data = get_realtime_option_price(option_tickers[1])
        stock_price, price_change, pct_change = fetch_stock_price_streamlit(symbol)
    except Exception as e:
        st.error(f"❌ Failed to fetch market data: {e}")
        st.stop()
else:
    st.warning("Please input all required parameters.")
    st.stop()


if None in [call_data, put_data, stock_price]:
    st.error("❌ Failed to retrieve data. Check ticker or internet connection.")
    st.stop()

call_price = call_data[1] if 'Buy' in trade_type else call_data[2]
put_price = put_data[1] if 'Buy' in trade_type.split('-')[1] else put_data[2]

S_min = np.floor(stock_price * (1 - s_range))
S_max = np.ceil(stock_price * (1 + s_range))
S_grid = np.arange(S_min, S_max + 1, 0.1)

call_payoff = np.maximum(S_grid - strike, 0)
put_payoff = np.maximum(strike - S_grid, 0)

if trade_type == 'Buy Call-Buy Put':
    y_option = n_call * (call_payoff - call_price) + n_put * (put_payoff - put_price)
    y_stock = n_call * delta_call * (stock_price - S_grid) + n_put * (-abs(delta_put)) * (stock_price - S_grid)
    effective_delta = -n_call * delta_call - n_put * (-abs(delta_put))
elif trade_type == 'Buy Call-Sell Put':
    y_option = n_call * (call_payoff - call_price) + n_put * (put_price - put_payoff)
    y_stock = n_call * delta_call * (stock_price - S_grid) + n_put * (-abs(delta_put)) * (S_grid - stock_price)
    effective_delta = -n_call * delta_call + n_put * (-abs(delta_put))
elif trade_type == 'Sell Call-Buy Put':
    y_option = n_call * (call_price - call_payoff) + n_put * (put_payoff - put_price)
    y_stock = n_call * delta_call * (S_grid - stock_price) + n_put * (-abs(delta_put)) * (stock_price - S_grid)
    effective_delta = n_call * delta_call - n_put * (-abs(delta_put))
elif trade_type == 'Sell Call-Sell Put':
    y_option = n_call * (call_price - call_payoff) + n_put * (put_price - put_payoff)
    y_stock = n_call * delta_call * (S_grid - stock_price) + n_put * (-abs(delta_put)) * (S_grid - stock_price)
    effective_delta = n_call * delta_call + n_put * (-abs(delta_put))

PnL = 100 * (y_option + y_stock)

# Positive payoff range
yp = np.maximum(PnL, 0)
y_neg = np.where(yp == 0)[0]
y_pos = np.where(yp > 0)[0]

if y_neg.size != 0 and y_pos.size != 0:
    if y_neg[0] > 0 and y_neg[-1] < len(S_grid) - 1:
        pos_str = f'(0, {np.ceil(S_grid[y_neg[0] - 1])}) and ({np.floor(S_grid[y_neg[-1] + 1])}, ∞)'
    else:
        pos_range = S_grid[y_pos]
        pos_str = f'({np.floor(pos_range[0])}, {np.ceil(pos_range[-1])})'
elif y_neg.size == 0:
    pos_str = '(0, ∞)'
else:
    pos_str = '∞'


# Plot
fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(S_grid, PnL, label='Strategy PnL', color='blue')
ax.fill_between(S_grid, PnL, where=(PnL > 0), color='#007560', alpha=0.7, label='Profit')
ax.fill_between(S_grid, PnL, where=(PnL <= 0), color='#bd1414', alpha=0.7, label='Loss')
ax.axhline(0, color='black', linewidth=1.5)
ax.set_xlabel("Stock Price")
ax.set_ylabel("Payoff at Maturity")
ax.set_ylim([y_min, y_max])
ax.set_title("Option Strategy Payoff")
ax.grid(True)
ax.legend()
st.pyplot(fig)

# Show fetched data
with st.expander("Option & Stock Data", expanded=False):
    st.metric(label="Stock Price", value=f"{stock_price:.2f}", delta=f"{price_change:.2f} ({pct_change:.2f}%)")
    st.write(f"Call Ticker: `{option_tickers[0]}` | Last: {call_data[0]} | Ask: {call_data[1]} | Bid: {call_data[2]}")
    st.write(f"Put Ticker: `{option_tickers[1]}` | Last: {put_data[0]} | Ask: {put_data[1]} | Bid: {put_data[2]}")