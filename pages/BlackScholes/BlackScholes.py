import streamlit as st
import yfinance as yf
from datetime import datetime, date
from realPrice.realOption import calls_or_puts, get_realtime_option_price
from realPrice.realStock import get_realtime_stock_price
from tools.BsCal import BlackScholes

# st.set_page_config(page_title="Option Pricing Tool", layout="wide")

st.title("📘 Black-Scholes")

# --- Compact Date Row ---
today = datetime.now()
maturity_date = st.date_input("📅 Maturity Date", value=date(2026, 8, 21))
calcT_days = (maturity_date - today.date()).days
if today.hour >= 14:
    calcT_days -= 1

col_date1, col_date2, col_date3, col_date4 = st.columns(4)
with col_date1:
    st.markdown(f"**📅 Today:** {today.strftime('%Y-%m-%d %H:%M')}")
with col_date2:
    st.markdown(f"**📆 CalcT (days to maturity):** :green[{calcT_days}]")
with col_date3:
    T_input_method = st.radio("T input method", ["Auto (from CalcT)", "Manual (input days)"])
with col_date4:
    if T_input_method == "Auto (from CalcT)":
        T = calcT_days / 365
    else:
        manual_days = st.number_input("Manual T (days to maturity)", min_value=0, value=50)
        T = manual_days / 365
    st.markdown(f"**📅 Final T (years):** :green[{T:.4f}]")

# --- 2x2 Input Grid ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    symbol = st.text_input("🏢 Stock Symbol", "IBM")
with col2:
    strike = st.number_input("💥 Strike Price", value=300.0)
with col3:
    volatility = st.number_input("📊 Volatility (σ)", value=0.2, step=0.01)
with col4:
    interest_rate = st.number_input("💰 Interest Rate (r)", value=0.07, step=0.01)

# --- Fetch Button and Current Price in One Row ---
col_fetch, col_price = st.columns([1, 3])
with col_fetch:
    fetch_btn = st.button("🚀 Fetch Prices", use_container_width=True)

# --- Fetch Data and Display ---
if fetch_btn:
    current_price, price_change, pct_change = get_realtime_stock_price(symbol)
    with col_price:
        st.markdown(f"""
            <div style='display: flex; align-items: center;'>
                <div style='font-size: 32px; font-weight: bold;'>📈 Current Price: {round(current_price, 2)}</div>
                <div style='color: green; font-size: 24px; margin-left: 20px;'>↑ {price_change:.2f} ({pct_change:.2f}%)</div>
            </div>
        """, unsafe_allow_html=True)

    call_sym, put_sym = calls_or_puts(symbol, str(maturity_date), strike)

    col_call, col_put = st.columns(2)
    if call_sym:
        with col_call:
            st.success(f"📈 Call Option ({call_sym})")
            c_last, c_ask, c_bid = get_realtime_option_price(call_sym)
            st.write(f"Last: {c_last} | Ask: {c_ask} | Bid: {c_bid}")
    else:
        st.warning("Call option not found.")

    if put_sym:
        with col_put:
            st.info(f"📉 Put Option ({put_sym})")
            p_last, p_ask, p_bid = get_realtime_option_price(put_sym)
            st.write(f"Last: {p_last} | Ask: {p_ask} | Bid: {p_bid}")
    else:
        st.warning("Put option not found.")

    if current_price and T > 0:
        bs = BlackScholes()
        col4, col5 = st.columns(2)
        with col4:
            st.subheader("📊 Call Option")
            st.write(f"Price: {bs.blsprice('c', current_price, strike, T, interest_rate, volatility):.2f}")
            st.write(f"Delta: {bs.blsdelta('c', current_price, strike, T, interest_rate, volatility):.2f}")
            st.write(f"Theta: {bs.blstheta('c', current_price, strike, T, interest_rate, volatility):.2f}")
            st.write(f"Rho: {bs.blsrho('c', current_price, strike, T, interest_rate, volatility):.2f}")
        with col5:
            st.subheader("📊 Put Option")
            st.write(f"Price: {bs.blsprice('p', current_price, strike, T, interest_rate, volatility):.2f}")
            st.write(f"Delta: {bs.blsdelta('p', current_price, strike, T, interest_rate, volatility):.2f}")
            st.write(f"Theta: {bs.blstheta('p', current_price, strike, T, interest_rate, volatility):.2f}")
            st.write(f"Rho: {bs.blsrho('p', current_price, strike, T, interest_rate, volatility):.2f}")
        st.markdown(f"**Gamma:** {bs.blsgamma(current_price, strike, T, interest_rate, volatility):.2f}")
        st.markdown(f"**Vega:** {bs.blsvega(current_price, strike, T, interest_rate, volatility):.2f}")
