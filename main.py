import streamlit as st
import plotly.graph_objects as go
from utils import (
    get_stock_data,
    get_key_metrics,
    check_stock_rule,
    send_email_notification
)
import pandas as pd
import base64
from datetime import datetime
import uuid

# Page config
st.set_page_config(
    page_title="Stock Data Visualization",
    page_icon="📈",
    layout="wide"
)

# Initialize session state
if 'stock_rules' not in st.session_state:
    st.session_state.stock_rules = []
if 'email_list' not in st.session_state:
    st.session_state.email_list = []
if 'simulation_entries' not in st.session_state:
    st.session_state.simulation_entries = []

# Load custom CSS
with open("styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Header
st.title("📈 Stock Data Visualization")

# Email Management Section
st.header("Email Management")
col1, col2 = st.columns([3, 1])
with col1:
    new_email = st.text_input("Enter Email Address", placeholder="example@email.com")
with col2:
    if st.button("Add Email"):
        if new_email:
            if '@' in new_email and '.' in new_email:  # Basic email validation
                if new_email in st.session_state.email_list:
                    st.error("This email is already in the list!")
                else:
                    st.session_state.email_list.append(new_email)
                    st.success("Email added successfully!")
            else:
                st.error("Please enter a valid email address")

if st.session_state.email_list:
    st.subheader("Current Email List")
    for idx, email in enumerate(st.session_state.email_list):
        col1, col2 = st.columns([4, 1])
        with col1:
            st.write(email)
        with col2:
            if st.button("Remove", key=f"remove_email_{idx}"):
                st.session_state.email_list.pop(idx)
                st.rerun()

st.markdown("---")

# Stock Rules Section
st.header("Stock Rules")
with st.form("stock_rule_form"):
    col1, col2 = st.columns([2, 1])
    with col1:
        rule_symbol = st.text_input("Stock Symbol", placeholder="e.g., AAPL").upper()
    with col2:
        percentage_change = st.number_input("Percentage Change (%)", min_value=-100.0, max_value=100.0, value=0.0, step=0.1)
    
    submitted = st.form_submit_button("Add Rule")
    if submitted and rule_symbol:
        new_rule = {
            "id": str(uuid.uuid4()),
            "symbol": rule_symbol,
            "percentage": percentage_change
        }
        st.session_state.stock_rules.append(new_rule)
        st.success(f"Rule added for {rule_symbol}")

# Display rules table
if st.session_state.stock_rules:
    st.subheader("Current Rules")
    rules_df = pd.DataFrame(st.session_state.stock_rules)
    rules_df = rules_df[["symbol", "percentage"]]
    rules_df.columns = ["Symbol", "Percentage Change (%)"]
    
    # Display each rule with a delete button
    for idx, rule in enumerate(st.session_state.stock_rules):
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            st.write(f"Symbol: {rule['symbol']}")
        with col2:
            st.write(f"Percentage: {rule['percentage']}%")
        with col3:
            if st.button("Delete", key=f"delete_{rule['id']}"):
                st.session_state.stock_rules.pop(idx)
                st.rerun()
    
st.markdown("---")

# Input section
market_tab, simulation_tab = st.tabs(["Market Data", "Stock Price Simulation"])

with market_tab:
    col1, col2 = st.columns([2, 1])
    with col1:
        symbol = st.text_input("Enter Stock Symbol (e.g., AAPL, GOOGL)", value="AAPL").upper()
    with col2:
        period = st.selectbox(
            "Select Time Period",
            options=["1mo", "3mo", "6mo", "1y", "2y", "5y"],
            index=3
        )

with simulation_tab:
    # Add new entry form
    st.subheader("Add Simulation Entry")
    with st.form("add_simulation_entry"):
        col1, col2 = st.columns([2, 1])
        with col1:
            sim_symbol = st.text_input("Stock Symbol", value="AAPL").upper()
        with col2:
            sim_price = st.number_input("Simulated Price ($)", min_value=0.01, value=100.00, step=0.01)
        
        if st.form_submit_button("Add Entry"):
            if sim_symbol:
                new_entry = {"symbol": sim_symbol, "price": sim_price}
                st.session_state.simulation_entries.append(new_entry)
                st.success(f"Added simulation entry for {sim_symbol}")
    
    # Display current entries
    if st.session_state.simulation_entries:
        st.subheader("Current Simulation Entries")
        for idx, entry in enumerate(st.session_state.simulation_entries):
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.write(f"Symbol: {entry['symbol']}")
            with col2:
                st.write(f"Price: ${entry['price']:.2f}")
            with col3:
                if st.button("Remove", key=f"remove_sim_{idx}"):
                    st.session_state.simulation_entries.pop(idx)
                    st.rerun()
        
        if st.button("Run Simulation"):
            st.subheader("Simulation Results")
            triggered_stocks = []
            
            for entry in st.session_state.simulation_entries:
                sim_hist, sim_info = get_stock_data(entry['symbol'])
                if sim_hist is not None and sim_info is not None:
                    market_price = sim_hist['Close'].iloc[-1]
                    price_diff = entry['price'] - market_price
                    price_change_pct = (price_diff / market_price) * 100
                    
                    st.write(f"### {entry['symbol']}")
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Market Price", f"${market_price:.2f}")
                    col2.metric("Simulated Price", f"${entry['price']:.2f}")
                    col3.metric("Difference", 
                            f"${price_diff:+.2f}",
                            f"{price_change_pct:+.2f}%")
                    
                    # Check if any rules are triggered
                    rule_triggered, threshold = check_stock_rule(
                        entry['symbol'], 
                        price_change_pct, 
                        st.session_state.stock_rules
                    )
                    
                    if rule_triggered:
                        st.warning("⚠️ This result triggered a rule!")
                        triggered_stocks.append({
                            'symbol': entry['symbol'],
                            'price_change_pct': price_change_pct,
                            'threshold': threshold
                        })
                    else:
                        st.info("ℹ️ There are no rules triggered for this stock.")
                else:
                    st.error(f"Error: Could not fetch data for symbol {entry['symbol']}")
            
            # Send email notifications if any rules were triggered
            if triggered_stocks:
                send_email_notification(st.session_state.email_list, triggered_stocks)

if symbol:
    # Fetch data
    historical_data, info = get_stock_data(symbol, period)
    
    if historical_data is not None and info is not None:
        # Current price and company name
        current_price = historical_data['Close'].iloc[-1]
        company_name = info.get('longName', symbol)
        
        st.header(f"{company_name} ({symbol})")
        
        # Price metrics
        price_change = current_price - historical_data['Close'].iloc[-2]
        price_change_pct = (price_change / historical_data['Close'].iloc[-2]) * 100
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Current Price", f"${current_price:.2f}", 
                   f"{price_change:+.2f} ({price_change_pct:+.2f}%)")
        col2.metric("Volume", format(info.get('volume', 0), ','))
        col3.metric("Market Cap", f"${info.get('marketCap', 0)/1e9:.2f}B")
        
        # Interactive price chart
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=historical_data.index,
            open=historical_data['Open'],
            high=historical_data['High'],
            low=historical_data['Low'],
            close=historical_data['Close'],
            name='OHLC'
        ))
        
        fig.update_layout(
            title=f"{symbol} Stock Price",
            yaxis_title="Price (USD)",
            xaxis_title="Date",
            template="plotly_white",
            height=600
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Key metrics table
        st.subheader("Key Metrics")
        metrics = get_key_metrics(info)
        metrics_df = pd.DataFrame.from_dict(metrics, orient='index', columns=['Value'])
        st.table(metrics_df)
        
        # Download button for CSV
        csv = historical_data.to_csv()
        b64 = base64.b64encode(csv.encode()).decode()
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{symbol}_stock_data_{current_time}.csv"
        
        st.download_button(
            label="Download Data as CSV",
            data=csv,
            file_name=filename,
            mime="text/csv",
            key="download-csv",
        )
        
    else:
        st.error(f"Error: Could not fetch data for symbol {symbol}. Please check if the symbol is correct.")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>Data provided by Yahoo Finance. Refresh for latest data.</p>
</div>
""", unsafe_allow_html=True)
