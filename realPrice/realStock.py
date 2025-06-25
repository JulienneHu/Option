import yfinance as yf
from datetime import datetime
import holidays
import pytz
import logging

def get_realtime_stock_price(stock_name):
    try:
        stock = yf.Ticker(stock_name)

        data = stock.history(period="1d", interval="1m")
        if data.empty:
            logging.warning("Intraday data unavailable, falling back to last close.")
            data = stock.history(period="2d")
            if data.empty:
                return None, None, None
            current_price = data['Close'].iloc[-1]
            previous_close = data['Close'].iloc[-2] if len(data) > 1 else current_price
        else:
            current_price = data['Close'].iloc[-1]
            previous_close = stock.history(period="2d")['Close'].iloc[-2] if len(data) > 1 else current_price

        price_change = current_price - previous_close
        percent_change = round((price_change / previous_close) * 100, 2)
        print(f"The current price of {stock_name} is {current_price:.2f}.")

        return current_price, price_change, percent_change

    except Exception as e:
        logging.error(f"Error retrieving stock data: {e}")
        return None, None, None
