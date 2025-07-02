import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime
import hashlib
from realPrice.OptionPnl import main, calls_or_puts
from realPrice.realOption import get_realtime_option_price
from tools.pnl_tools import calculate_pnl, market_open

# --- Page Config ---
st.title("📘 Option PNL Tracker")

# --- Persistent Storage ---
def initialize_trades():
    return pd.DataFrame(columns=[
        'trade_id', 'trade_key_display', 'trade_date', 'symbol', 'strike', 'expiration', 'stock_trade_price', 'effective_delta',
        'call_trade_price', 'call_action_type', 'num_call_contracts',
        'put_trade_price', 'put_action_type', 'num_put_contracts',
        'stock_close_price', 'call_close_price', 'put_close_price',
        'daily_pnl', 'change'
    ])

if 'trades' not in st.session_state:
    st.session_state.trades = initialize_trades()

# --- Input Form ---
with st.form("Trade Input"):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        trade_date = st.text_input("Trade Date", '2025-06-01')
        symbol = st.text_input("Symbol", 'IBM')
        strike = st.number_input("Strike Price", value=280.0, step=1.0, format="%.2f")
    with col2:
        expiration = st.text_input("Expiration Date", '2025-07-18')
        stock_trade_price = st.number_input("Stock Trade Price", value=0.0, step=1.0, format="%.2f")
        effective_delta = st.number_input("Effective Delta", value=0.0, step=0.01, format="%.2f")
    with col3:
        call_action_type = st.selectbox("Call Action Type", ["buy", "sell"])
        num_call_contracts = st.number_input("Call Contracts", min_value=0, value=2)
        call_trade_price = st.number_input("Call Trade Price", value=2.79)
    with col4:
        put_action_type = st.selectbox("Put Action Type", ["buy", "sell"])
        num_put_contracts = st.number_input("Put Contracts", min_value=0, value=0)
        put_trade_price = st.number_input("Put Trade Price", value=0.0)

    submitted = st.form_submit_button("Add Trade")

# --- Logic After Submit ---
if submitted:
    with st.spinner("Fetching data and adding trade..."):
        option_data = main(symbol, expiration, strike, trade_date)

        if option_data is None or option_data.empty:
            st.warning("⚠️ No data found or unable to retrieve data.")
        else:
            # Create a deterministic unique ID for the trade
            trade_key = f"{trade_date}_{expiration}_{call_action_type}_{put_action_type}_{symbol}_{stock_trade_price}_{call_trade_price}_{put_trade_price}_{strike}_{effective_delta}_{num_call_contracts}_{num_put_contracts}"
            trade_id = hashlib.md5(trade_key.encode()).hexdigest()

            # Create a readable display string for context
            trade_key_display = (
                f"Date: {trade_date} | Exp: {expiration} | Sym: {symbol} | Strike: {strike} | "
                f"Call: {call_action_type} {num_call_contracts} @ {call_trade_price} | "
                f"Put: {put_action_type} {num_put_contracts} @ {put_trade_price} | "
                f"Stock: {stock_trade_price} | Delta: {effective_delta}"
            )

            first_row = option_data.iloc[0]
            if stock_trade_price in [0, None]:
                stock_trade_price = round(first_row['stock_close_price'], 2)
            # Use first available close prices if the originally entered ones are 0 or None
            if call_trade_price in [0, None]:
                fr_call_price = first_row['call_close_price']
                if pd.notna(fr_call_price):
                    call_trade_price = round(fr_call_price, 2)

            if put_trade_price in [0, None]:
                fr_put_price = first_row['put_close_price']
                if pd.notna(fr_put_price):
                    put_trade_price = round(fr_put_price, 2)


            if market_open():
                options = calls_or_puts(symbol, expiration, strike)
                if options and len(options) == 2:
                    call_close_price, call_ask_price, call_bid_price = get_realtime_option_price(options[0])
                    put_close_price, put_ask_price, put_bid_price = get_realtime_option_price(options[1])
                    option_data.at[option_data.index[-1], 'call_close_price'] = call_ask_price if call_action_type == "sell" else call_bid_price
                    option_data.at[option_data.index[-1], 'put_close_price'] = put_ask_price if put_action_type == "sell" else put_bid_price

            for _, row in option_data.iterrows():
                daily_pnl = calculate_pnl(
                    call_action_type, put_action_type,
                    num_call_contracts, call_trade_price, row['call_close_price'],
                    num_put_contracts, put_trade_price, row['put_close_price'],
                    effective_delta, stock_trade_price, row['stock_close_price']
                )
                investment = ((num_call_contracts * call_trade_price) + (num_put_contracts * put_trade_price)) * 100
                change = round(daily_pnl / investment * 100, 2) if investment != 0 else 0.0

                new_trade = {
                    'trade_id': trade_id,
                    'trade_key_display': trade_key_display,
                    'trade_date': row['date'].strftime('%Y-%m-%d'),
                    'symbol': symbol,
                    'strike': strike,
                    'expiration': expiration,
                    'stock_trade_price': stock_trade_price,
                    'effective_delta': effective_delta,
                    'call_trade_price': call_trade_price,
                    'call_action_type': call_action_type,
                    'num_call_contracts': num_call_contracts,
                    'put_trade_price': put_trade_price,
                    'put_action_type': put_action_type,
                    'num_put_contracts': num_put_contracts,
                    'stock_close_price': round(row['stock_close_price'], 2),
                    'call_close_price': row['call_close_price'],
                    'put_close_price': row['put_close_price'],
                    'daily_pnl': round(daily_pnl, 2),
                    'change': change
                }

                new_trade_df = pd.DataFrame([new_trade])
                # Drop duplicates if the same trade_id and trade_date already exist
                st.session_state.trades = pd.concat(
                    [st.session_state.trades, new_trade_df],
                    ignore_index=True
                ).drop_duplicates(subset=['trade_id', 'trade_date'])

            st.success("✅ Trade(s) added successfully with prices auto-filled from first day history.")

# --- Display and Plot Trades ---
if not st.session_state.trades.empty:
    st.subheader("📈 Trade PNL Chart")

    trade_ids = st.session_state.trades['trade_id'].unique()
    trade_info_mapping = {
        f"{row['trade_key_display']} [{row['trade_id'][:8]}]": row['trade_id']
        for _, row in st.session_state.trades.drop_duplicates('trade_id').iterrows()
    }
    options_list = list(trade_info_mapping.keys())

    # Find the latest trade_id from the most recent appended record
    latest_trade_id = st.session_state.trades.iloc[-1]['trade_id']
    # Find its display label in the options list
    latest_index = next((i for i, label in enumerate(options_list) if trade_info_mapping[label] == latest_trade_id), 0)

    selected_label = st.selectbox("Select Trade to View", options=options_list, index=latest_index)

    selected_trade_id = trade_info_mapping[selected_label]


    selected_trade_info = st.session_state.trades[
        st.session_state.trades['trade_id'] == selected_trade_id
    ]['trade_key_display'].iloc[0]
    st.info(f"**Trade Info:** {selected_trade_info}")

    chart_data = st.session_state.trades[st.session_state.trades['trade_id'] == selected_trade_id].copy()
    chart_data['trade_date'] = pd.to_datetime(chart_data['trade_date'])
    chart_data = chart_data.sort_values(by='trade_date')
    first_available_date = chart_data['trade_date'].min()
    chart_data = chart_data[chart_data['trade_date'] >= first_available_date]
    chart_data = chart_data.reset_index(drop=True)
    chart_data['plot_index'] = range(len(chart_data))

    colors = ['#bd1414' if x < 0 else '#007560' for x in chart_data['daily_pnl']]
    hover_texts = [
        f"Date: {row['trade_date'].strftime('%Y-%m-%d')}<br>"
        f"Stock: ${row['stock_close_price']:.2f}<br>"
        f"Call: ${row['call_close_price']:.2f}<br>"
        f"Put: ${row['put_close_price']:.2f}<br>"
        f"PNL: ${row['daily_pnl']:.2f}<br>"
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

        xaxis=dict(
            tickmode='array',
            tickvals=chart_data['plot_index'],
            ticktext=[d.strftime('%m-%d') for d in chart_data['trade_date']],
            tickangle=45
        ),
        yaxis_title='PnL ($)',
        xaxis_title='Date',
        hovermode='closest',
        margin=dict(l=40, r=20, t=40, b=40)
    )

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📄 Trade Records")
    st.dataframe(chart_data)
    csv = chart_data.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV", csv, "trades.csv", "text/csv")