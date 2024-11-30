import streamlit as st
import plotly.graph_objects as go
from utils import get_stock_data, get_key_metrics
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

# Initialize session state for stock rules
if 'stock_rules' not in st.session_state:
    st.session_state.stock_rules = []

# Load custom CSS
with open("styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Header
st.title("📈 Stock Data Visualization")

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
col1, col2 = st.columns([2, 1])
with col1:
    symbol = st.text_input("Enter Stock Symbol (e.g., AAPL, GOOGL)", value="AAPL").upper()
with col2:
    period = st.selectbox(
        "Select Time Period",
        options=["1mo", "3mo", "6mo", "1y", "2y", "5y"],
        index=3
    )

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
