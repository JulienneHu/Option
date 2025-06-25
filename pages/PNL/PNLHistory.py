import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import mplcursors
from matplotlib.backends.backend_agg import RendererAgg
import plotly.graph_objects as go
from datetime import datetime

from tools.pnl_tools import calculate_pnl, get_ticker, get_pnl

# Ensure thread safety for matplotlib
# _lock = RendererAgg.lock

# st.set_page_config(page_title="Expired Option PNL Tracker", layout="wide")
st.title("📘 Expired Option PNL")

# Initialize session state
if 'trades_df' not in st.session_state:
    st.session_state.trades_df = pd.DataFrame(columns=[
        'trade_date', 'symbol', 'strike', 'expiration', 'stock_trade_price', 'effective_delta',
        'call_trade_price', 'call_action_type', 'num_call_contracts', 'put_trade_price',
        'put_action_type', 'num_put_contracts', 'stock_close_price', 'call_close_price',
        'put_close_price', 'daily_pnl', 'change'])

# Form input
with st.form("trade_form"):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        trade_date = st.text_input("Trade Date", '2025-05-08')
        symbol = st.text_input("Symbol", 'IBM')
        strike = st.number_input("Strike Price", value=280.0)
    with col2:
        expiration = st.text_input("Expiration Date", '2025-06-20')
        stock_trade_price = st.number_input("Stock Trade Price", value=178.0)
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

if submitted:
    call_ticker, put_ticker = get_ticker(strike, symbol, expiration)
    pnl_data = get_pnl(call_ticker, put_ticker, trade_date, stock_trade_price, effective_delta,
                       call_action_type, num_call_contracts, call_trade_price,
                       put_action_type, num_put_contracts, put_trade_price)

    if pnl_data is not None and not pnl_data.empty:
        for _, row in pnl_data.iterrows():
            daily_pnl = calculate_pnl(call_action_type, put_action_type,
                                       num_call_contracts, call_trade_price, row['call_close_price'],
                                       num_put_contracts, put_trade_price, row['put_close_price'],
                                       effective_delta, stock_trade_price, row['stock'])
            investment = ((num_call_contracts * call_trade_price) + (num_put_contracts * put_trade_price)) * 100
            change = round(daily_pnl / investment * 100, 2)

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
                'stock_close_price': round(row['stock'], 2),
                'call_close_price': row['call_close_price'],
                'put_close_price': row['put_close_price'],
                'daily_pnl': round(daily_pnl, 2),
                'change': change
            }

            exists = st.session_state.trades_df[
                (st.session_state.trades_df['trade_date'] == new_trade['trade_date']) &
                (st.session_state.trades_df['symbol'] == new_trade['symbol']) &
                (st.session_state.trades_df['strike'] == new_trade['strike']) &
                (st.session_state.trades_df['expiration'] == new_trade['expiration']) &
                (st.session_state.trades_df['stock_trade_price'] == new_trade['stock_trade_price']) &
                (st.session_state.trades_df['effective_delta'] == new_trade['effective_delta']) &
                (st.session_state.trades_df['call_trade_price'] == new_trade['call_trade_price']) &
                (st.session_state.trades_df['call_action_type'] == new_trade['call_action_type']) &
                (st.session_state.trades_df['num_call_contracts'] == new_trade['num_call_contracts']) &
                (st.session_state.trades_df['put_trade_price'] == new_trade['put_trade_price']) &
                (st.session_state.trades_df['put_action_type'] == new_trade['put_action_type']) &
                (st.session_state.trades_df['num_put_contracts'] == new_trade['num_put_contracts'])
            ]
            if exists.empty:
                st.session_state.trades_df = pd.concat([st.session_state.trades_df, pd.DataFrame([new_trade])], ignore_index=True)

        st.success("✅ Trade(s) added successfully!")
    else:
        st.warning("⚠️ No data found for given input.")

# Plot
if not st.session_state.trades_df.empty:
    st.subheader("📈 PNL Chart")
    df = st.session_state.trades_df.copy()
    df['trade_date'] = pd.to_datetime(df['trade_date'])
    df = df.sort_values(by='trade_date')
    df['plot_index'] = range(len(df))

    colors = ['#bd1414' if x < 0 else '#007560' for x in df['daily_pnl']]
    hover_texts = [
        f"Date: {row['trade_date'].strftime('%Y-%m-%d')}<br>"
        f"Stock: ${row['stock_close_price']:.2f}<br>"
        f"Call: ${row['call_close_price']:.2f}<br>"
        f"Put: ${row['put_close_price']:.2f}<br>"
        f"PNL: ${row['daily_pnl']:.2f}<br>"
        f"Change: {row['change']:.2f}%"
        for _, row in df.iterrows()
    ]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['plot_index'],
        y=df['daily_pnl'],
        mode='lines+markers',
        marker=dict(color=colors, size=10),
        line=dict(color='black', width=2),
        hovertext=hover_texts,
        hoverinfo='text'
    ))
    fig.update_layout(
        title="Daily PNL",
        xaxis=dict(
            tickmode='array',
            tickvals=df['plot_index'],
            ticktext=[d.strftime('%m-%d') for d in df['trade_date']],
            tickangle=45
        ),
        yaxis_title='Π',
        xaxis_title='Date',
        hovermode='closest',
        margin=dict(l=40, r=20, t=40, b=40)
    )
    st.plotly_chart(fig, use_container_width=True)
    st.subheader("📄 Trade Records")
    st.dataframe(df)
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV", csv, "trades.csv", "text/csv")
