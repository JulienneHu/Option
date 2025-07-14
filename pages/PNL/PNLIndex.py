import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import hashlib
import yfinance as yf
from realPrice.IndexPnl import main, get_option_chain, calls_and_puts
from realPrice.realOption import getIndexOption
from tools.pnl_tools import calculate_pnl, market_open

# Page config
st.title("📘 Index Option PNL")

# Initialize session state for trades
if 'trades' not in st.session_state:
    st.session_state.trades = pd.DataFrame(columns=[
        'trade_id', 'trade_key_display', 'actual_trade_date', 'trade_date', 'symbol', 'strike', 'expiration', 'stock_trade_price',
        'effective_delta', 'call_trade_price', 'call_action_type', 'num_call_contracts',
        'put_trade_price', 'put_action_type', 'num_put_contracts', 'stock_close_price',
        'call_close_price', 'put_close_price', 'daily_pnl', 'change'
    ])

# Input form
with st.form("Trade Input"):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        trade_date_input = st.date_input("Trade Date", datetime(2025, 5, 2))
        trade_date = trade_date_input.strftime('%Y-%m-%d')
        symbol = st.text_input("Symbol", '^SPX')
        strike = st.number_input("Strike Price", value=5900.0, step=1.0, format="%.2f")
    with col2:
        expiration_input = st.date_input("Expiration Date", datetime(2025, 7, 18))
        expiration = expiration_input.strftime('%Y-%m-%d')
        stock_trade_price = st.number_input("Stock Trade Price", value=0.0, step=1.0, format="%.2f")
        effective_delta = st.number_input("Effective Delta", value=0.0, step=0.01, format="%.2f")
    with col3:
        call_action_type = st.selectbox("Call Action Type", ['sell', 'buy'])
        num_call_contracts = st.number_input("# Call Contracts", min_value=0, value=1)
        call_trade_price = st.number_input("Call Trade Price", value=0.0)
    with col4:
        put_action_type = st.selectbox("Put Action Type", ['sell', 'buy'])
        num_put_contracts = st.number_input("# Put Contracts", min_value=0, value=1)
        put_trade_price = st.number_input("Put Trade Price", value=0.0)

    col_submit, col_clear = st.columns([3, 1])
    submitted = col_submit.form_submit_button("Add Trade")
    clear_clicked = col_clear.form_submit_button("🗑️ Clear History")

if clear_clicked:
    st.session_state.trades = st.session_state.trades.iloc[0:0]
    st.success("🗑️ Trade history cleared.")
    st.stop()

if submitted:
    with st.spinner("Fetching data and adding trade..."):

        option_data = main(symbol, expiration, strike, trade_date)
        get_option_chain(symbol, expiration, strike)

        if option_data is not None and not option_data.empty:
            valid_rows = option_data.dropna(subset=['call_close_price', 'put_close_price'])
            if not valid_rows.empty:
                first_valid_row = valid_rows.iloc[0]
                first_valid_date = first_valid_row['date']
                first_valid_call_close = first_valid_row['call_close_price']
                first_valid_put_close = first_valid_row['put_close_price']
                first_valid_stock_close = first_valid_row['stock_close_price']
                if stock_trade_price in [0, 0.0, None]:
                    try:
                        ticker = yf.Ticker(symbol)
                        trade_date = pd.to_datetime(first_valid_date)
                        next_day = (trade_date + timedelta(days=5)).strftime('%Y-%m-%d')
                        df_hist = ticker.history(start=trade_date, end=next_day)
                        if not df_hist.empty:
                            stock_trade_price = round(df_hist['Open'].iloc[0], 2)
                    except Exception as e:
                        st.warning(f"⚠️ Could not fetch stock open price: {e}")
                
                if call_trade_price in [0, 0.0, None]:
                    call_trade_price = round(first_valid_call_close, 2)
                if put_trade_price in [0, 0.0, None]:
                    put_trade_price = round(first_valid_put_close, 2)
                if stock_trade_price in [0, 0.0, None]:
                    stock_trade_price = round(first_valid_stock_close, 2)
                    st.info(f"Auto-filled stock_trade_price with stock_close_price on {first_valid_date}: {stock_trade_price}")

            for col in ['call_close_price', 'put_close_price']:
                if option_data[col].isnull().any():
                    first_valid = option_data[col].dropna().iloc[0] if not option_data[col].dropna().empty else None
                    if first_valid is not None:
                        option_data[col] = option_data[col].fillna(first_valid)

            trade_key = f"{trade_date}_{expiration}_{call_action_type}_{put_action_type}_{symbol}_{stock_trade_price}_{call_trade_price}_{put_trade_price}_{strike}_{effective_delta}_{num_call_contracts}_{num_put_contracts}"
            trade_id = hashlib.md5(trade_key.encode()).hexdigest()

            trade_key_display = (
                f"Date: {trade_date} | Exp: {expiration} | Sym: {symbol} | Strike: {strike} | "
                f"Call: {call_action_type} {num_call_contracts} @ {call_trade_price} | "
                f"Put: {put_action_type} {num_put_contracts} @ {put_trade_price} | "
                f"Stock: {stock_trade_price} | Delta: {effective_delta}"
            )

            if market_open():
                options = calls_and_puts(symbol, expiration, strike)
                if options and len(options) == 2:
                    call_close_price, call_ask, call_bid = getIndexOption(symbol, options[0])
                    put_close_price, put_ask, put_bid = getIndexOption(symbol, options[1])
                    option_data.at[option_data.index[-1], 'call_close_price'] = call_ask if call_action_type == "sell" else call_bid
                    option_data.at[option_data.index[-1], 'put_close_price'] = put_ask if put_action_type == "sell" else put_bid

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
                    'actual_trade_date': trade_date,  # Store the actual trade date
                    'trade_date': row['date'].strftime('%Y-%m-%d'),  # Current data date
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

                if st.session_state.trades[
                    (st.session_state.trades['trade_id'] == trade_id) &
                    (st.session_state.trades['trade_date'] == row['date'].strftime('%Y-%m-%d'))
                ].empty:
                    if pd.DataFrame([new_trade]).dropna(how='all').shape[0] > 0:
                        st.session_state.trades = pd.concat(
                            [st.session_state.trades, pd.DataFrame([new_trade])], ignore_index=True
                        )


            st.success("✅ Trade(s) added successfully!")
        else:
            st.warning("⚠️ No data found for the given input.")

# Plotting
if not st.session_state.trades.empty:
    st.subheader("📈 Index PNL Chart")

    trade_info_mapping = {
        f"{row['trade_key_display']} [{row['trade_id'][:8]}]": row['trade_id']
        for _, row in st.session_state.trades.drop_duplicates('trade_id').iterrows()
    }
    options_list = list(trade_info_mapping.keys())
    latest_trade_id = st.session_state.trades.iloc[-1]['trade_id']
    latest_index = next((i for i, label in enumerate(options_list) if trade_info_mapping[label] == latest_trade_id), 0)

    selected_label = st.selectbox("Select Trade to View", options=options_list, index=latest_index)
    selected_trade_id = trade_info_mapping[selected_label]

    selected_trade_info = st.session_state.trades[
        st.session_state.trades['trade_id'] == selected_trade_id
    ]['trade_key_display'].iloc[0]
    
    # Get actual trade date for display
    # actual_trade_date_display = st.session_state.trades[
    #     st.session_state.trades['trade_id'] == selected_trade_id
    # ]['actual_trade_date'].iloc[0]
    
    st.info(f"**Trade Info:** {selected_trade_info}")

    chart_data = st.session_state.trades[
        st.session_state.trades['trade_id'] == selected_trade_id
    ].copy()
    chart_data['trade_date'] = pd.to_datetime(chart_data['trade_date'])
    chart_data['actual_trade_date'] = pd.to_datetime(chart_data['actual_trade_date'])
    chart_data = chart_data.sort_values(by='trade_date')
    
    # Filter data to start from actual trade date or later
    actual_trade_date = chart_data['actual_trade_date'].iloc[0]
    chart_data = chart_data[chart_data['trade_date'] >= actual_trade_date]

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