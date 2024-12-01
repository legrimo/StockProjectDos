import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st

@st.cache_data(ttl=3600)  # Cache data for 1 hour
def get_stock_data(symbol: str, period: str = "1y"):
    """
    Fetch stock data from Yahoo Finance
    """
    try:
        stock = yf.Ticker(symbol)
        hist = stock.history(period=period)
        info = stock.info
        return hist, info
    except Exception as e:
        return None, None

def format_number(number):
    """
    Format large numbers with K, M, B suffixes
    """
    if number is None:
        return "N/A"
    
    if isinstance(number, str):
        return number
        
    if number >= 1e9:
        return f"{number/1e9:.2f}B"
    if number >= 1e6:
        return f"{number/1e6:.2f}M"
    if number >= 1e3:
        return f"{number/1e3:.2f}K"
    return f"{number:.2f}"

def get_key_metrics(info):
    """
    Extract key metrics from stock info
    """
    metrics = {
        "Market Cap": info.get("marketCap"),
        "PE Ratio": info.get("trailingPE"),
        "52 Week High": info.get("fiftyTwoWeekHigh"),
        "52 Week Low": info.get("fiftyTwoWeekLow"),
        "Volume": info.get("volume"),
        "Avg Volume": info.get("averageVolume"),
        "Dividend Yield": info.get("dividendYield", 0) * 100 if info.get("dividendYield") else None,
    }
    
    return {k: format_number(v) for k, v in metrics.items()}

def check_stock_rule(symbol: str, price_change_pct: float, rules: list) -> tuple:
    """
    Check if a stock's price change triggers any rules
    Returns: (bool, float) - (whether rule was triggered, threshold that was triggered)
    """
    matching_rules = [rule for rule in rules if rule['symbol'] == symbol]
    if not matching_rules:
        return False, None
    
    for rule in matching_rules:
        if abs(price_change_pct) >= abs(rule['percentage']):
            return True, rule['percentage']
    
    return False, None

def send_email_notification(email_list: list, triggered_stocks: list):
    """
    Send email notification for triggered stock rules
    """
    if not email_list or not triggered_stocks:
        return
    
    symbols = ", ".join([stock['symbol'] for stock in triggered_stocks])
    subject = f"Test Notification Alert: Stock Price change {symbols}"
    
    body = "The following stocks rules were triggered due to a price movement:\n\n"
    for stock in triggered_stocks:
        body += f"- {stock['symbol']}: {stock['price_change_pct']:+.2f}% (Threshold: {stock['threshold']:+.2f}%)\n"
    
    # For demonstration, print the email content
    print("\nEmail Notification:")
    print(f"To: {', '.join(email_list)}")
    print(f"Subject: {subject}")
    print(f"Body:\n{body}")
    # In production, implement actual email sending logic here
