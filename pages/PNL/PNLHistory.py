import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import hashlib
import yfinance as yf
from tools.pnl_tools import calculate_pnl, get_ticker, get_pnl

st.title("📘 Expired Option PNL Tracker")

# Initialize session state with trade_id for uniqueness
if 'trades_df' not in st.session_state:
    st.session_state.trades_df = pd.DataFrame(columns=[
        'trade_id', 'trade_key_display', 'trade_date', 'symbol', 'strike', 'expiration', 'stock_trade_price',
        'effective_delta', 'call_trade_price', 'call_action_type', 'num_call_contracts',
        'put_trade_price', 'put_action_type', 'num_put_contracts', 'stock_close_price',
        'call_close_price', 'put_close_price', 'daily_pnl', 'change'])

# Form input
with st.form("trade_form"):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        trade_date_input = st.date_input("Trade Date", datetime(2025, 5, 8))
        trade_date = trade_date_input.strftime('%Y-%m-%d')
        symbol = st.text_input("Symbol", 'IBM')
        strike = st.number_input("Strike Price", value=280.0, step=1.0, format="%.2f")
    with col2:
        expiration_input = st.date_input("Expiration Date", datetime(2025, 6, 20))
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
    st.session_state.trades_df = st.session_state.trades_df.iloc[0:0]
    st.success("🗑️ History cleared.")
    st.stop()

if submitted:
    # Fetch stock open price if input = 0
    if stock_trade_price == 0.0:
        try:
            ticker = yf.Ticker(symbol)
            next_day = (trade_date_input + timedelta(days=5)).strftime('%Y-%m-%d')
            df_hist = ticker.history(start=trade_date, end=next_day)
            if not df_hist.empty:
                stock_trade_price = round(df_hist['Open'].iloc[0], 2)
        except Exception as e:
            st.warning(f"⚠️ Could not fetch stock open price: {e}")

    call_ticker, put_ticker = get_ticker(strike, symbol, expiration)

    # Fetch call/put open prices if input = 0
    if call_trade_price == 0.0 or put_trade_price == 0.0:
        try:
            df_options = get_pnl(call_ticker, put_ticker, trade_date, stock_trade_price, effective_delta,
                                 call_action_type, num_call_contracts, 0,
                                 put_action_type, num_put_contracts, 0)
            if call_trade_price == 0.0:
                open_call = df_options['call_close_price'].iloc[0]
                call_trade_price = round(open_call, 2)
            if put_trade_price == 0.0:
                open_put = df_options['put_close_price'].iloc[0]
                put_trade_price = round(open_put, 2)
        except Exception as e:
            st.warning(f"⚠️ Could not fetch option open prices: {e}")

    pnl_data = get_pnl(call_ticker, put_ticker, trade_date, stock_trade_price, effective_delta,
                       call_action_type, num_call_contracts, call_trade_price,
                       put_action_type, num_put_contracts, put_trade_price)

    if pnl_data is not None and not pnl_data.empty:
        trade_key = f"{trade_date}_{expiration}_{call_action_type}_{put_action_type}_{symbol}_{stock_trade_price}_{call_trade_price}_{put_trade_price}_{strike}_{effective_delta}_{num_call_contracts}_{num_put_contracts}"
        trade_id = hashlib.md5(trade_key.encode()).hexdigest()

        trade_key_display = (
            f"Date: {trade_date} | Exp: {expiration} | Sym: {symbol} | Strike: {strike} | "
            f"Call: {call_action_type} {num_call_contracts} @ {call_trade_price} | "
            f"Put: {put_action_type} {num_put_contracts} @ {put_trade_price} | "
            f"Stock: {stock_trade_price} | Delta: {effective_delta}"
        )

        for _, row in pnl_data.iterrows():
            daily_pnl = calculate_pnl(call_action_type, put_action_type,
                                       num_call_contracts, call_trade_price, row['call_close_price'],
                                       num_put_contracts, put_trade_price, row['put_close_price'],
                                       effective_delta, stock_trade_price, row['stock'])
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
                'stock_close_price': round(row['stock'], 2),
                'call_close_price': row['call_close_price'],
                'put_close_price': row['put_close_price'],
                'daily_pnl': round(daily_pnl, 2),
                'change': change
            }

            new_trade_df = pd.DataFrame([new_trade])
            st.session_state.trades_df = pd.concat([
                st.session_state.trades_df,
                new_trade_df
            ], ignore_index=True).drop_duplicates(subset=['trade_id', 'trade_date'])

        st.success("✅ Trade(s) added successfully!")
    else:
        st.warning("⚠️ No data found for given input.")


# Plotting with trade_id selection
if not st.session_state.trades_df.empty:
    st.subheader("📈 Trade PNL Chart")
    trade_ids = st.session_state.trades_df['trade_id'].unique()
    trade_info_mapping = {
        f"{row['trade_key_display']} [{row['trade_id'][:8]}]": row['trade_id']
        for _, row in st.session_state.trades_df.drop_duplicates('trade_id').iterrows()
    }
    options_list = list(trade_info_mapping.keys())

    # Find the latest trade_id from the most recent appended record
    latest_trade_id = st.session_state.trades_df.iloc[-1]['trade_id']
    # Find its display label in the options list
    latest_index = next((i for i, label in enumerate(options_list) if trade_info_mapping[label] == latest_trade_id), 0)

    selected_label = st.selectbox("Select Trade to View", options=options_list, index=latest_index)

    selected_trade_id = trade_info_mapping[selected_label]

    selected_trade_info = st.session_state.trades_df[
        st.session_state.trades_df['trade_id'] == selected_trade_id
    ]['trade_key_display'].iloc[0]
    st.info(f"**Trade Info:** {selected_trade_info}")

    df = st.session_state.trades_df[st.session_state.trades_df['trade_id'] == selected_trade_id].copy()
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
        yaxis_title='PnL ($)',
        xaxis_title='Date',
        hovermode='closest',
        margin=dict(l=40, r=20, t=40, b=40)
    )

    st.plotly_chart(fig, use_container_width=True)
    st.subheader("📄 Trade Records")
    st.dataframe(df)
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV", csv, "trades.csv", "text/csv")
