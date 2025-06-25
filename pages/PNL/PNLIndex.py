import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime
from realPrice.IndexPnl import main, get_option_chain, calls_and_puts
from realPrice.realOption import getIndexOption
from tools.pnl_tools import calculate_pnl, market_open

# Page config
# st.set_page_config(page_title="Index Option PNL Tracker", layout="wide")
st.title("📘 Index Option PNL")

# Initialize session state for trades and status
if 'trades' not in st.session_state:
    st.session_state.trades = pd.DataFrame(columns=[
        'trade_date', 'symbol', 'strike', 'expiration', 'stock_trade_price', 'effective_delta',
        'call_trade_price', 'call_action_type', 'num_call_contracts', 'put_trade_price',
        'put_action_type', 'num_put_contracts', 'stock_close_price', 'call_close_price',
        'put_close_price', 'daily_pnl', 'change'])
if 'last_success' not in st.session_state:
    st.session_state.last_success = False

# Input form
with st.form("Trade Input"):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        trade_date = st.text_input("Trade Date", '2025-05-02')
        symbol = st.text_input("Symbol", '^SPX')
        strike = st.number_input("Strike Price", value=5900.0)
    with col2:
        expiration = st.text_input("Expiration Date", '2025-07-18')
        stock_trade_price = st.number_input("Stock Trade Price", value=412.0)
        effective_delta = st.number_input("Effective Delta", value=0.0)
    with col3:
        call_action_type = st.selectbox("Call Action Type", ["buy", "sell"])
        num_call_contracts = st.number_input("# Call Contracts", min_value=0, value=1)
        call_trade_price = st.number_input("Call Trade Price", value=11.0)
    with col4:
        put_action_type = st.selectbox("Put Action Type", ["buy", "sell"])       
        num_put_contracts = st.number_input("# Put Contracts", min_value=0, value=1)
        put_trade_price = st.number_input("Put Trade Price", value=12.0)

    submitted = st.form_submit_button("Add Trade")

# Process submission
if submitted:
    st.session_state.last_success = False
    trade_added = False
    with st.spinner("Fetching data and adding trade..."):
        option_data = main(symbol, expiration, strike, trade_date)
        option_chain = get_option_chain(symbol, expiration, strike)
        st.info(f"Option Chain Symbol: {option_chain}")

        if option_data is not None and not option_data.empty:
            if market_open():
                options = calls_and_puts(symbol, expiration, strike)
                if options and len(options) == 2:
                    call_close_price, call_ask, call_bid = getIndexOption(symbol, options[0])
                    put_close_price, put_ask, put_bid = getIndexOption(symbol, options[1])
                    option_data.at[option_data.index[-1], 'call_close_price'] = call_ask if call_action_type == "sell" else call_bid
                    option_data.at[option_data.index[-1], 'put_close_price'] = put_ask if put_action_type == "sell" else put_bid

            for _, row in option_data.iterrows():
                daily_pnl = calculate_pnl(call_action_type, put_action_type,
                                           num_call_contracts, call_trade_price, row['call_close_price'],
                                           num_put_contracts, put_trade_price, row['put_close_price'],
                                           effective_delta, stock_trade_price, row['stock_close_price'])
                investment = ((num_call_contracts * call_trade_price) + (num_put_contracts * put_trade_price)) * 100
                change = round(daily_pnl / investment * 100, 2) if investment != 0 else 0.0

                new_trade = {
                    'trade_date': row['date'].strftime('%Y-%m-%d'),
                    'symbol': symbol,
                    'strike': strike,
                    'expiration': expiration,
                    'stock_trade_price': stock_trade_price,
                    'effective_delta': effective_delta,
                    'call_trade_price': row['call_close_price'],
                    'call_action_type': call_action_type,
                    'num_call_contracts': num_call_contracts,
                    'put_trade_price': row['put_close_price'],
                    'put_action_type': put_action_type,
                    'num_put_contracts': num_put_contracts,
                    'stock_close_price': round(row['stock_close_price'], 2),
                    'call_close_price': row['call_close_price'],
                    'put_close_price': row['put_close_price'],
                    'daily_pnl': round(daily_pnl, 2),
                    'change': change
                }

                exists = st.session_state.trades[
                    (st.session_state.trades['trade_date'] == new_trade['trade_date']) &
                    (st.session_state.trades['symbol'] == new_trade['symbol']) &
                    (st.session_state.trades['strike'] == new_trade['strike']) &
                    (st.session_state.trades['expiration'] == new_trade['expiration']) &
                    (st.session_state.trades['stock_trade_price'] == new_trade['stock_trade_price']) &
                    (st.session_state.trades['effective_delta'] == new_trade['effective_delta']) &
                    (st.session_state.trades['call_trade_price'] == new_trade['call_trade_price']) &
                    (st.session_state.trades['call_action_type'] == new_trade['call_action_type']) &
                    (st.session_state.trades['num_call_contracts'] == new_trade['num_call_contracts']) &
                    (st.session_state.trades['put_trade_price'] == new_trade['put_trade_price']) &
                    (st.session_state.trades['put_action_type'] == new_trade['put_action_type']) &
                    (st.session_state.trades['num_put_contracts'] == new_trade['num_put_contracts'])
                ]

                if exists.empty:
                    st.session_state.trades = pd.concat([st.session_state.trades, pd.DataFrame([new_trade])], ignore_index=True)
                    trade_added = True

    if trade_added:
        st.success("Trade(s) added successfully!")

# Plot if data exists
if not st.session_state.trades.empty:
    st.subheader("📈 Index PNL Chart")
    chart_data = st.session_state.trades.copy()
    chart_data['trade_date'] = pd.to_datetime(chart_data['trade_date'])
    chart_data = chart_data.sort_values(by='trade_date')
    chart_data['plot_index'] = range(len(chart_data))

    colors = ['#bd1414' if x < 0 else '#007560' for x in chart_data['daily_pnl']]
    hover_texts = [
        f"Date: {row['trade_date'].strftime('%Y-%m-%d')}<br>"
        f"Stock: ${row['stock_close_price']:.2f}<br>"
        f"Call: ${row['call_close_price']:.2f}<br>"
        f"Put: ${row['put_close_price']:.2f}<br>"
        f"Current PNL: ${row['daily_pnl']:.2f}<br>"
        f"Change: {row['change']:.2f}%"
        for _, row in chart_data.iterrows()
    ]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=chart_data['plot_index'],
        y=chart_data['daily_pnl'],
        mode='lines+markers',
        marker=dict(color=colors, size=10),
        line=dict(color='black', width=2),
        hovertext=hover_texts,
        hoverinfo='text'
    ))

    fig.update_layout(
        title="Profit & Loss",
        xaxis=dict(
            tickmode='array',
            tickvals=chart_data['plot_index'],
            ticktext=[d.strftime('%m-%d') for d in chart_data['trade_date']],
            tickangle=45
        ),
        yaxis_title='Π',
        xaxis_title='Date',
        hovermode='closest',
        margin=dict(l=40, r=20, t=40, b=40)
    )

    st.plotly_chart(fig, use_container_width=True)
    st.subheader("📄 Trade Records")
    st.dataframe(chart_data)
    csv = chart_data.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV", csv, "trades.csv", "text/csv")