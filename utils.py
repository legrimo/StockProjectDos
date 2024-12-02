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
    
    import smtplib
    import ssl
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    import os

    # Get email configuration from environment variables
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port_str = os.getenv('SMTP_PORT')
    sender_email = os.getenv('EMAIL_USERNAME')
    password = os.getenv('EMAIL_PASSWORD')

    # Default port based on common SMTP servers
    smtp_port = 587
    if smtp_port_str:
        try:
            smtp_port = int(smtp_port_str)
        except ValueError:
            print(f"Warning: Invalid SMTP port value: {smtp_port_str}, using default port 587")
    
    print(f"Debug: Starting email notification process...")
    print(f"Debug: Using SMTP settings - Server: {smtp_server}, Port: {smtp_port}, From: {sender_email}")

    if not all([smtp_server, sender_email, password]):
        print("Error: Email configuration is incomplete. Missing required settings:")
        if not smtp_server: print("- SMTP_SERVER not set")
        if not sender_email: print("- EMAIL_USERNAME not set")
        if not password: print("- EMAIL_PASSWORD not set")
        return

    symbols = ", ".join([stock['symbol'] for stock in triggered_stocks])
    subject = f"Stock Price Alert: {symbols}"
    
    body = "The following stock rules were triggered due to price movements:\n\n"
    for stock in triggered_stocks:
        body += f"- {stock['symbol']}: {stock['price_change_pct']:+.2f}% (Threshold: {stock['threshold']:+.2f}%)\n"

    for recipient in email_list:
        try:
            # Create message
            message = MIMEMultipart()
            message["From"] = sender_email
            message["To"] = recipient
            message["Subject"] = subject

            # Add body to email
            message.attach(MIMEText(body, "plain"))

            # Create SMTP session and send email
            print(f"Debug: Attempting to connect to SMTP server: {smtp_server}:{smtp_port}")
            
            context = ssl.create_default_context()
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.set_debuglevel(1)  # Enable debug output
            print("Debug: Starting TLS connection...")
            server.starttls(context=context)
            
            print("Debug: Attempting login...")
            server.login(sender_email, password)
            
            print("Debug: Sending message...")
            server.send_message(message)
            print(f"Success: Email notification sent to {recipient}")
            
            server.quit()  # Properly close the connection
                
        except smtplib.SMTPAuthenticationError as e:
            print(f"Error: SMTP Authentication failed. Please check your credentials.")
            print(f"Debug: Authentication error details - {str(e)}")
        except smtplib.SMTPConnectError as e:
            print(f"Error: Failed to connect to SMTP server: {smtp_server}:{smtp_port}")
            print(f"Debug: Connection error details - {str(e)}")
        except smtplib.SMTPServerDisconnected as e:
            print(f"Error: Server disconnected. This might be due to connection timeout or server issues.")
            print(f"Debug: Disconnection details - {str(e)}")
        except Exception as e:
            print(f"Error: Failed to send email to {recipient}")
            print(f"Debug: Error type: {type(e).__name__}")
            print(f"Debug: Error details - {str(e)}")
