from realPrice.realStock import get_realtime_stock_price
from realPrice.realOption import main as get_realtime_option_price

def fetch_stock_price_streamlit(stock_name):
    """
    Fetches real-time stock price, price change, and percentage change.
    Returns (price, price_change, pct_change) as floats or 'NA' on failure.
    """
    try:
        price, price_change, pct_change = get_realtime_stock_price(stock_name)
        if price is not None and price_change is not None and pct_change is not None:
            return round(price, 2), round(price_change, 2), round(pct_change, 2)
        else:
            return 'NA', 'NA', 'NA'
    except Exception:
        return 'NA', 'NA', 'NA'

def fetch_option_prices_streamlit(company, date, strike):
    """
    Fetches real-time option prices for a specific strike.
    Returns [call_price, put_price] as floats or 'NA' on failure.
    """
    try:
        prices = get_realtime_option_price(company, date, strike)
        if prices and all(p is not None for p in prices):
            return [round(float(prices[0]), 2), round(float(prices[1]), 2)]
        else:
            return ['NA', 'NA']
    except Exception:
        return ['NA', 'NA']
