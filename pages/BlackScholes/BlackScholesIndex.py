from time import sleep
import streamlit as st
from datetime import datetime, date
import yfinance as yf
from realPrice.realStock import get_realtime_stock_price
from tools.BsCal import BlackScholes

# st.set_page_config(page_title="📘 Black-Scholes Index", layout="wide")
st.title("📘 Black-Scholes Index Options (^SPX / ^NDX)")

# --- Date Handling ---
today = datetime.now()
maturity_date = st.date_input("📅 Maturity Date", value=date(2025, 8, 15))
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

# --- Inputs ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    index_symbol = st.selectbox("📈 Index", ["^SPX", "^NDX"])
with col2:
    strike = st.number_input("💥 Strike Price", value=6000.0 if index_symbol == "^SPX" else 21600.0)
with col3:
    volatility = st.number_input("📊 Volatility (σ)", value=0.2, step=0.01)
with col4:
    interest_rate = st.number_input("💰 Interest Rate (r)", value=0.03, step=0.005)

# --- Utility: Ticker Generation ---
def generate_option_ticker(base, expiry_date, cp_flag, strike):
    yy = str(expiry_date.year)[2:]
    mm = f"{expiry_date.month:02d}"
    dd = f"{expiry_date.day:02d}"
    strike_str = f"{int(strike * 1000):08d}"
    return f"{base}{yy}{mm}{dd}{cp_flag}{strike_str}"

# --- Utility: Verify Existence ---
def verify_ticker_exists(ticker):
    try:
        info = yf.Ticker(ticker).info
        # Some tickers may return {'quoteType': 'OPTION'} even if valid
        return 'regularMarketPrice' in info or 'lastPrice' in info or 'openInterest' in info
    except Exception:
        return False

# --- Fetch and Compute Button ---
fetch_btn = st.button("🚀 Fetch and Compute", use_container_width=True)

if fetch_btn:
    current_price, price_change, pct_change = get_realtime_stock_price(index_symbol)

    st.markdown(
        f"<div style='font-size: 28px; font-weight: bold;'>📈 {index_symbol} Current Price: {current_price:.2f} | Δ: {price_change:.2f} ({pct_change:.2f}%)</div>",
        unsafe_allow_html=True
    )

    expiry_date = maturity_date
    call_ticker, put_ticker = None, None

    if index_symbol == "^SPX":
        # Try SPX first
        call_ticker_candidate = generate_option_ticker("SPX", expiry_date, "C", strike)
        put_ticker_candidate = generate_option_ticker("SPX", expiry_date, "P", strike)
        print(f"Generated Call Ticker: {call_ticker_candidate}, Put Ticker: {put_ticker_candidate}")

        if verify_ticker_exists(call_ticker_candidate) and verify_ticker_exists(put_ticker_candidate):
            call_ticker, put_ticker = call_ticker_candidate, put_ticker_candidate
        else:
            st.warning("⚠️ 'SPX' ticker not found, trying 'SPXW'.")
            call_ticker_candidate = generate_option_ticker("SPXW", expiry_date, "C", strike)
            put_ticker_candidate = generate_option_ticker("SPXW", expiry_date, "P", strike)
            print(f"Generated Call Ticker: {call_ticker_candidate}, Put Ticker: {put_ticker_candidate}")
            
            call_ticker, put_ticker = call_ticker_candidate, put_ticker_candidate

    elif index_symbol == "^NDX":
        call_ticker_candidate = generate_option_ticker("NDX", expiry_date, "C", strike)
        put_ticker_candidate = generate_option_ticker("NDX", expiry_date, "P", strike)
        print(f"Generated Call Ticker: {call_ticker_candidate}, Put Ticker: {put_ticker_candidate}")
        if verify_ticker_exists(call_ticker_candidate) and verify_ticker_exists(put_ticker_candidate):
            call_ticker, put_ticker = call_ticker_candidate, put_ticker_candidate
        else:
            st.warning("⚠️ 'NDX' ticker not found, trying 'NDXP'.")
            call_ticker_candidate = generate_option_ticker("NDXP", expiry_date, "C", strike)
            put_ticker_candidate = generate_option_ticker("NDXP", expiry_date, "P", strike)
            print(f"Generated Call Ticker: {call_ticker_candidate}, Put Ticker: {put_ticker_candidate}")
            call_ticker, put_ticker = call_ticker_candidate, put_ticker_candidate

    # If tickers found, fetch and display
    if call_ticker and put_ticker:
        call_data = yf.Ticker(call_ticker).history(period="30d")
        print(call_data.tail(1))
        sleep(1)  # To avoid hitting API limits
        put_data = yf.Ticker(put_ticker).history(period="30d")

        col_call, col_put = st.columns(2)
        with col_call:
            st.success(f"📈 Call Option: {call_ticker}")
            st.write(call_data.tail(1))

        with col_put:
            st.info(f"📉 Put Option: {put_ticker}")
            st.write(put_data.tail(1))

        # Black-Scholes Pricing
        if current_price and T > 0:
            bs = BlackScholes()
            col_c, col_p = st.columns(2)

            with col_c:
                st.subheader("📊 Call Option (Black-Scholes)")
                st.write(f"Price: {bs.blsprice('c', current_price, strike, T, interest_rate, volatility):.2f}")
                st.write(f"Delta: {bs.blsdelta('c', current_price, strike, T, interest_rate, volatility):.2f}")
                st.write(f"Theta: {bs.blstheta('c', current_price, strike, T, interest_rate, volatility):.2f}")
                st.write(f"Rho: {bs.blsrho('c', current_price, strike, T, interest_rate, volatility):.2f}")

            with col_p:
                st.subheader("📊 Put Option (Black-Scholes)")
                st.write(f"Price: {bs.blsprice('p', current_price, strike, T, interest_rate, volatility):.2f}")
                st.write(f"Delta: {bs.blsdelta('p', current_price, strike, T, interest_rate, volatility):.2f}")
                st.write(f"Theta: {bs.blstheta('p', current_price, strike, T, interest_rate, volatility):.2f}")
                st.write(f"Rho: {bs.blsrho('p', current_price, strike, T, interest_rate, volatility):.2f}")

            st.markdown(f"**Gamma:** {bs.blsgamma(current_price, strike, T, interest_rate, volatility):.4f}")
            st.markdown(f"**Vega:** {bs.blsvega(current_price, strike, T, interest_rate, volatility):.4f}")
