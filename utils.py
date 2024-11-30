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
