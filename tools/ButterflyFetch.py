from realPrice.realStock import get_realtime_stock_price
from realPrice.realOption import main as get_realtime_option_price

def fetch_stock_price_streamlit(stock_name):
    """
    Fetch stock price, price change, and percentage change in Streamlit.
    Returns (price, price_change, percentage_change) as floats or 'NA' if fails.
    """
    try:
        price, price_change, percentage_change = get_realtime_stock_price(stock_name)
        if price is not None and price_change is not None and percentage_change is not None:
            return round(price, 2), round(price_change, 2), round(percentage_change, 2)
        else:
            return 'NA', 'NA', 'NA'
    except Exception as e:
        return 'NA', 'NA', 'NA'

def fetch_option_prices_streamlit(company, date, strike):
    """
    Fetch option prices (call, put) for a single strike in Streamlit.
    Returns [call_price, put_price] as floats or 'NA' if fails.
    """
    try:
        prices = get_realtime_option_price(company, date, strike)
        if prices and all(p is not None for p in prices):
            return [round(float(p), 2) for p in prices]
        else:
            return ['NA', 'NA']
    except Exception as e:
        return ['NA', 'NA']

def fetch_multiple_option_prices_streamlit(company, date, strikes):
    """
    Fetch option prices for multiple strikes in Streamlit.
    Returns two lists:
        call_prices: [call_price_1, call_price_2, call_price_3]
        put_prices: [put_price_1, put_price_2, put_price_3]
    Each value is a float or 'NA' if unavailable.
    """
    call_prices = []
    put_prices = []

    for strike in strikes:
        prices = fetch_option_prices_streamlit(company, date, strike)
        call_prices.append(prices[0])
        put_prices.append(prices[1])

    return call_prices, put_prices
