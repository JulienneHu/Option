import yfinance as yf
from realPrice.realStock import get_realtime_stock_price
import requests
import pandas as pd
from datetime import datetime, timedelta
import time
import numpy as np
import holidays


def get_option_chain(company='SPX', date='2024-05-02', strike=4500):
    ticker = yf.Ticker(company)
    option_chain = ticker.option_chain(date)
   
    call_data = option_chain.calls[option_chain.calls['strike'] == strike]
    
    if not call_data.empty:
        call_symbol = call_data['contractSymbol'].values[0]
        call_symbol = call_symbol[:next((i for i, char in enumerate(call_symbol) if char.isdigit()), None)]
        return call_symbol
    else:
        return None
    
def get_historical_data(ticker, start_date):
    api_key = 'C6ig1sXku2yKl_XEIvSvc_OWCwB8ILLn'
    base_url = 'https://api.polygon.io/v2/aggs/ticker/'
    end_date = datetime.now()  

    ticker = f'O:{ticker}'
    if isinstance(start_date, datetime):
        start_date = start_date.strftime('%Y-%m-%d')

    url = f"{base_url}{ticker}/range/1/day/{start_date}/{end_date.strftime('%Y-%m-%d')}?apiKey={api_key}"

    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if 'results' in data:
            df = pd.DataFrame(data['results'])
            df['t'] = pd.to_datetime(df['t'], unit='ms')
            df['date'] = df['t'].dt.date  
            return df[['date','c',]]
        else:
            print("No results found in the data.")
            return pd.DataFrame()  
    else:
        print(f"Failed to retrieve data: {response.status_code}")
        return None

def get_stock_price(symbol, start_date, end_date):
    stock = yf.Ticker(symbol)
    hist = stock.history(start=start_date, end=end_date)
    hist.reset_index(inplace=True)
    hist['date'] = hist['Date'].dt.date
    hist.rename(columns={'Close': 'stock_close_price'}, inplace=True)
    hist['stock_close_price'] = hist['stock_close_price'].round(2)
    return hist[['date', 'stock_close_price']]

def calls_and_puts(company='SPX', date='2024-05-02', strike=4500):
    ticker = yf.Ticker(company)
    option_chain = ticker.option_chain(date)
  
    
    calls = option_chain.calls
    puts = option_chain.puts
    call_data = calls[calls['strike'] == strike]
    put_data = puts[puts['strike'] == strike]
    options = []
    call_symbol = call_data['contractSymbol'].values[0]
    options.append(call_symbol)
    put_symbol = put_data['contractSymbol'].values[0]
    options.append(put_symbol) 
    return options 
    
def main(company='^SPX', date='2024-08-16', strike=4700, trade_date='2024-07-01'):
    # Fetch ticker information
    ticker = yf.Ticker(company)
    option_chain = ticker.option_chain(date)
  
    
    calls = option_chain.calls
    puts = option_chain.puts
    call_data = calls[calls['strike'] == strike]
    put_data = puts[puts['strike'] == strike]

    if call_data.empty and put_data.empty:
        print("No call or put options available for the specified strike price.")
        return None
    
    options = []
    realPrices = []
    
    if not call_data.empty:
        call_symbol = call_data['contractSymbol'].values[0]
        options.append(call_symbol)
        call_price = call_data['lastPrice'].values[0]
        realPrices.append(call_price)
    
    if not put_data.empty:
        put_symbol = put_data['contractSymbol'].values[0]
        options.append(put_symbol)
        put_price = put_data['lastPrice'].values[0]
        realPrices.append(put_price)

    # Get historical data for the options
    data_frames = []
    for i, option in enumerate(options):
        price_data = get_historical_data(option, trade_date)
        time.sleep(1)
        if price_data is not None:
            if i == 0:
                price_data.rename(columns={'c': 'call_close_price'}, inplace=True)
            else:    
                price_data.rename(columns={'c': 'put_close_price'}, inplace=True)
            data_frames.append(price_data)
        else:
            print(f"Failed to retrieve data for option: {option}")
    
    # Merge the dataframes
    if len(data_frames) == 2:
        df = pd.merge(data_frames[0], data_frames[1], on='date')
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values(by='date')
        
        today = datetime.now().date()-timedelta(days=1)
        us_holidays = holidays.US(years=[2024])
        allday = pd.date_range(trade_date, today).strftime('%Y-%m-%d')
        allday = [day for day in allday if pd.to_datetime(day).weekday() < 5 and day not in us_holidays ]

        # add dates that are not in the df but in the allday list
        missing_dates = [day for day in allday if day not in df['date'].dt.strftime('%Y-%m-%d').values]
        missing_df = pd.DataFrame(missing_dates, columns=['date'])
        missing_df['date'] = pd.to_datetime(missing_df['date'])
        missing_df['call_close_price'] = np.nan
        missing_df['put_close_price'] = np.nan
        df = pd.concat([df, missing_df], ignore_index=True)
        df = df.sort_values(by='date')
        
        # Get the stock price data
        start_date = datetime.strptime(trade_date, '%Y-%m-%d')
        end_date = datetime.now()
        stock_prices = get_stock_price(company, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        stock_prices['date'] = pd.to_datetime(stock_prices['date'])
        df = pd.merge(df, stock_prices, on='date', how='left')
        df['date'] = df['date'].dt.date
            
        # add real time stock price, call price as realPrices[0], put price as realPrices[1]
        current_price = get_realtime_stock_price(company)[0]
        call_price = realPrices[0]
        put_price = realPrices[1]
        
        df.loc[len(df)] = [datetime.now().date(), call_price, put_price, current_price]
        df = df.fillna(method='ffill')
        # round the stock price to two digits
        df['stock_close_price'] = df['stock_close_price'].round(2)
        print(df)
        return df
    else:
        print("Could not retrieve data for one or more options.")
        return None
    
# main()


