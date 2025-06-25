# import yfinance as yf
# from datetime import datetime
# import holidays
# import pytz

# import yfinance as yf

# import os
# import sys
# import pandas as pd
# from datetime import datetime
# import psutil

# # Set environment variables for Mono
# mono_lib_path = "/opt/homebrew/Cellar/mono/6.12.0.206/lib"
# os.environ["DYLD_LIBRARY_PATH"] = f"{mono_lib_path}:{os.environ.get('DYLD_LIBRARY_PATH', '')}"
# os.environ["LD_LIBRARY_PATH"] = f"{mono_lib_path}:{os.environ.get('LD_LIBRARY_PATH', '')}"

# def initialize_clr():
#     # Print the environment variables to ensure they are set correctly
#     print(f"Python executable: {sys.executable}")
#     print(f"DYLD_LIBRARY_PATH: {os.environ.get('DYLD_LIBRARY_PATH')}")
#     print(f"LD_LIBRARY_PATH: {os.environ.get('LD_LIBRARY_PATH')}")
#     print(f"sys.path: {sys.path}")

#     # Try importing clr
#     try:
#         import clr  # This import should work after installing pythonnet
#         clr.AddReference('System.Collections')
#         from System import DateTime, TimeSpan
#         print("pythonnet is installed and clr module is available.")
#     except ImportError as e:
#         print("pythonnet is not installed or clr module is not available. Please install it using 'pip install pythonnet'.")
#         print(e)
#         sys.exit(1)

#     # Set the assembly path
#     # assembly_path = f'{os.getenv("HOME")}/Library/CloudStorage/Dropbox-UniversityofMichigan/Hu Jun/Kamaly/cSharpFeed/Feed'
#     assembly_path = '/Users/rkamaly/University of Michigan Dropbox/Reza Kamaly/Kamaly/cSharpFeed/Feed'
#     sys.path.append(assembly_path)

#     # Try adding the IQFeed.CSharpApiClient reference
#     try:
#         clr.AddReference("IQFeed.CSharpApiClient")
#     except Exception as e:
#         print(f"Failed to add reference to IQFeed.CSharpApiClient: {e}")
#         sys.exit(1)
#     return clr

# def is_iqconnect_running():
#     for proc in psutil.process_iter(attrs=['pid', 'name']):
#         if proc.info['name'] == 'IQConnect.exe':
#             return True
#     return False

# def connect_lookup_client():
#     from IQFeed.CSharpApiClient.Lookup import LookupClientFactory
#     try:
#         lookupClient = LookupClientFactory.CreateNew()
#         lookupClient.Connect()
#         return lookupClient
#     except Exception as e:
#         print(f"Failed to create or connect LookupClient: {e}")
#         sys.exit(1)



# # lookupClient = connect_lookup_client()

# def get_realtime_option_price(option_name):
#     print(f"[get_realtime_option_price] Fetching {option_name} from IQFeed")
#     try:
#         clr = initialize_clr()
#         import clr
#         assembly_path = f'{os.getenv("HOME")}/Library/CloudStorage/Dropbox-UniversityofMichigan/Hu Jun/Kamaly/cSharpFeed/Feed'
#         if assembly_path not in sys.path:
#             sys.path.append(assembly_path)
#         clr.AddReference("IQFeed.CSharpApiClient")

#         from IQFeed.CSharpApiClient.Lookup import LookupClientFactory
#         from System import DateTime

#         lookupClient = LookupClientFactory.CreateNew()
#         lookupClient.Connect()

#         try:
#             result = lookupClient.Historical.GetHistoryIntervalDatapoints(
#                 option_name,
#                 1,
#                 1
#             )
#             data = list(result)
#         finally:
#             lookupClient.Disconnect()

#         if len(data) == 0:
#             print(f"No data found for {option_name}")
#             return "NA", "NA", "NA"

#         item = data[0]
#         last = float(item.Close)
#         ask = float(item.High)
#         bid = float(item.Low)

#         print(f"Fetched prices: Last={last}, Approx Ask={ask}, Approx Bid={bid}")
#         return float(last), float(ask), float(bid)

#     except Exception as e:
#         print(f"[get_realtime_option_price] Exception for {option_name}: {e}")
#         return "NA", "NA", "NA"

# def build_occ_symbol(company, date, strike, option_type):
#     yy = date[2:4]     # e.g. "25"
#     mm = date[5:7]     # e.g. "08"
#     dd = date[8:10]    # e.g. "15"
#     cp = "C" if option_type.lower() == "call" else "P"
#     strike_int = int(round(strike * 1000))  # e.g. 300.0 -> 300000
#     strike_str = f"{strike_int:08d}"        # zero-padded to 8 digits
#     return f"{company.upper()}{yy}{mm}{dd}{cp}{strike_str}"


# def calls_or_puts(company, date, strike):
#     call_symbol = None
#     put_symbol = None
#     ticker = yf.Ticker(company)
#     expiration_dates = ticker.options

#     if date in expiration_dates:
#         opts = ticker.option_chain(date)
#         call = opts.calls[opts.calls['strike'] == strike]
#         put = opts.puts[opts.puts['strike'] == strike]

#         strike = int(strike) if strike.is_integer() else strike
#         if not call.empty:
#             # call_symbol = call['contractSymbol'].iloc[0]
#             call_symbol = company + date[2:4] + date[8:10] +  chr(65+ int(date[5:7])-1) + str(strike)
#             print(f"Call option for strike {strike} on {date}: {call_symbol}")
#         if not put.empty:
#             # put_symbol = put['contractSymbol'].iloc[0]
#             put_symbol = company + date[2:4] + date[8:10] +  chr(65+ int(date[5:7])-1+12) + str(strike)
#             print(f"Put option for strike {strike} on {date}: {put_symbol}")
#     return [call_symbol, put_symbol]


# def main(company, date, strike):
#     options = calls_or_puts(company, date, strike)
#     res = []
#     if options:
#         for option in options:
#             print(f"Current Option is {option}")
#             opt = get_realtime_option_price(option)
#             res.append(opt[0])
#     return res

# def getIndexOption(symbol, ticker):
#     info = yf.Ticker(symbol)
#     option_syb = ticker[:next((i for i, char in enumerate(ticker) if char.isdigit()), None)]
#     length = len(option_syb)
#     date = ticker[length:length + 6]
#     option_date = f"20{date[:2]}-{date[2:4]}-{date[4:]}"
#     opt = info.option_chain(option_date)
#     optionType = ticker[length + 6]
#     if optionType.upper() == "C":
#         calls = opt.calls
#         res = calls[calls['contractSymbol'] == ticker]
#     else:
#         puts = opt.puts
#         res = puts[puts['contractSymbol'] == ticker]
    
#     if res.empty:
#         print(f"No specific option found for {ticker}.")
#         return None
#     today = datetime.today()
    
#     if today.weekday() > 4 or today in holidays.UnitedStates(years=today.year):
#         market_status = "weekend" if today.weekday() > 4 else "a holiday"
#         last_price = res["lastPrice"].iloc[0] if not res.empty else "N/A"
#         print(f"Today is {market_status}, the market is closed. The last recorded transaction price of {option_name} was {last_price}.")
#     else:
#         last = res['lastPrice'].values[0]
#         bid = res['bid'].values[0]
#         ask = res['ask'].values[0]
#         print(f"Last price: {last}, Ask: {ask}, Bid: {bid}.")
#     return last, bid, ask
# # calls_or_puts('AAPL', '2025-07-18', 190)
# # get_realtime_option_price('AAPL2518G190')
# # get_realtime_option_price('AAPL2518S190')

import yfinance as yf
from datetime import datetime
import holidays
import pytz

def get_realtime_option_price(option_name):
    '''
    This function gets the real-time option price in the US stock market.
    It considers the market closed during weekends, US public holidays, and off-hours.
    '''
    last_price = None
    ask_price = None
    bid_price = None
    today = datetime.today()
    company = option_name[:next((i for i, char in enumerate(option_name) if char.isdigit()), None)]
    comp_info = yf.Ticker(company)
    
    length = len(company)
    date = option_name[length:length + 6]
    option_date = f"20{date[:2]}-{date[2:4]}-{date[4:]}"
    
    optionType = option_name[length + 6]
    opt = comp_info.option_chain(option_date)  

    if optionType.upper() == "C":
        specific_opt = opt.calls[opt.calls.contractSymbol == option_name] 
    else:
        specific_opt = opt.puts[opt.puts.contractSymbol == option_name]

    if specific_opt.empty:
        print(f"No specific option found for {option_name}.")
        return None

    if today.weekday() > 4 or today in holidays.UnitedStates(years=today.year):
        market_status = "weekend" if today.weekday() > 4 else "a holiday"
        last_price = specific_opt["lastPrice"].iloc[0] if not specific_opt.empty else "N/A"
        print(f"Today is {market_status}, the market is closed. The last recorded transaction price of {option_name} was {last_price}.")
    else:
        last_price = specific_opt["lastPrice"].iloc[0]
        ask_price = specific_opt["ask"].iloc[0]
        bid_price = specific_opt["bid"].iloc[0]
        print(f"Last price: {last_price}, Ask: {ask_price}, Bid: {bid_price}.")
        
    return last_price, ask_price, bid_price

def calls_or_puts(company, date, strike):
    options = [] 
    ticker = yf.Ticker(company)
    expiration_dates = ticker.options

    if date in expiration_dates:
        opts = ticker.option_chain(date)
        
        call_option = opts.calls[opts.calls['strike'] == strike]
        put_option = opts.puts[opts.puts['strike'] == strike]
        
        if not call_option.empty:
            call_option_names = call_option['contractSymbol'].tolist()
            options.extend(call_option_names)
            print(f"Call option(s) for strike price {strike} on {date}: {', '.join(call_option_names)}")
        else:
            print(f"No call option with a strike price of {strike} for {date}.")
            
        if not put_option.empty:
            put_option_names = put_option['contractSymbol'].tolist()
            options.extend(put_option_names)
            print(f"Put option(s) for strike price {strike} on {date}: {', '.join(put_option_names)}")
        else:
            print(f"No put option with a strike price of {strike} for {date}.")
    else:
        print(f"No options available for {date}.")
    return options

def main(company, date, strike):
    options = calls_or_puts(company, date, strike)
    res = []
    if options:
        for option in options:
            print(f"Current Option is {option}")
            opt = get_realtime_option_price(option)
            res.append(opt[0])
    return res

def getIndexOption(symbol, ticker):
    info = yf.Ticker(symbol)
    option_syb = ticker[:next((i for i, char in enumerate(ticker) if char.isdigit()), None)]
    length = len(option_syb)
    date = ticker[length:length + 6]
    option_date = f"20{date[:2]}-{date[2:4]}-{date[4:]}"
    opt = info.option_chain(option_date)
    optionType = ticker[length + 6]
    if optionType.upper() == "C":
        calls = opt.calls
        res = calls[calls['contractSymbol'] == ticker]
    else:
        puts = opt.puts
        res = puts[puts['contractSymbol'] == ticker]
    
    if res.empty:
        print(f"No specific option found for {ticker}.")
        return None
    today = datetime.today()
    
    if today.weekday() > 4 or today in holidays.UnitedStates(years=today.year):
        market_status = "weekend" if today.weekday() > 4 else "a holiday"
        last_price = res["lastPrice"].iloc[0] if not res.empty else "N/A"
        print(f"Today is {market_status}, the market is closed. The last recorded transaction price of {option_name} was {last_price}.")
    else:
        last = res['lastPrice'].values[0]
        bid = res['bid'].values[0]
        ask = res['ask'].values[0]
        print(f"Last price: {last}, Ask: {ask}, Bid: {bid}.")
    return last, bid, ask
