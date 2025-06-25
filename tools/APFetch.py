# tools/APFetchStreamlit.py
import streamlit as st
from realPrice.realStock import get_realtime_stock_price
from realPrice.realOptionProfile import main as get_option

def fetch_stock_price_streamlit(symbol):
    try:
        price, price_change, pct_change = get_realtime_stock_price(symbol)
        if None in (price, price_change, pct_change):
            raise ValueError("Missing price data")
        return round(price, 2), round(price_change, 2), round(pct_change, 2)
    except Exception as e:
        st.warning(f"⚠️ Failed to fetch stock price: {e}")
        return None, None, None

def fetch_option_prices_streamlit(symbol, date, strike):
    try:
        prices, open_interests, volumes = get_option(symbol, date, strike)
        return prices, open_interests, volumes
    except Exception as e:
        st.warning(f"⚠️ Failed to fetch option data: {e}")
        return [], [], []
