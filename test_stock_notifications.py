import pytest
from utils import check_stock_rule, get_stock_data

def test_check_stock_rule_triggers():
    """Test stock rule triggering logic"""
    # Test cases
    rules = [
        {"symbol": "AAPL", "percentage": 5.0},
        {"symbol": "GOOGL", "percentage": -3.0}
    ]
    
    # Test positive threshold
    triggered, threshold = check_stock_rule("AAPL", 6.0, rules)
    assert triggered == True
    assert threshold == 5.0
    
    # Test negative threshold
    triggered, threshold = check_stock_rule("GOOGL", -4.0, rules)
    assert triggered == True
    assert threshold == -3.0
    
    # Test no trigger
    triggered, threshold = check_stock_rule("AAPL", 2.0, rules)
    assert triggered == False
    assert threshold is None

def test_stock_data_fetching():
    """Test stock data fetching functionality"""
    # Test with a real stock symbol
    hist, info = get_stock_data('AAPL', period='1d')
    
    assert hist is not None
    assert info is not None
    assert len(hist) > 0
    assert 'Close' in hist.columns