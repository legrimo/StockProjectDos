import pytest
import sys
import os

# Add the project root directory to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils import check_stock_rule, get_stock_data, send_email_notification

def test_check_stock_rule_triggers():
    """Test stock rule triggering logic"""
    rules = [
        {"symbol": "AAPL", "percentage": 5.0},
        {"symbol": "GOOGL", "percentage": -3.0}
    ]
    
    # Test positive threshold
    triggered, threshold = check_stock_rule("AAPL", 6.0, rules)
    assert triggered == True
    assert threshold == 5.0
    
    # Test no trigger
    triggered, threshold = check_stock_rule("AAPL", 2.0, rules)
    assert triggered == False
    assert threshold is None

@pytest.mark.integration
def test_stock_data_fetching():
    """Test stock data fetching functionality"""
    hist, info = get_stock_data('AAPL', period='1d')
    assert hist is not None
    assert info is not None
    assert 'Close' in hist.columns

@pytest.mark.mock
def test_email_notification(mocker):
    """Test email notification with mocked SMTP"""
    # Mock SMTP
    mock_smtp = mocker.patch('smtplib.SMTP')
    
    # Test data
    email_list = ['test@example.com']
    triggered_stocks = [{
        'symbol': 'AAPL',
        'price_change_pct': 5.5,
        'threshold': 5.0
    }]
    
    # Mock environment variables
    mocker.patch.dict('os.environ', {
        'SMTP_SERVER': 'smtp.test.com',
        'SMTP_PORT': '587',
        'EMAIL_USERNAME': 'test@example.com',
        'EMAIL_PASSWORD': 'password123'
    })
    
    # Execute
    send_email_notification(email_list, triggered_stocks)
    
    # Verify SMTP interactions
    mock_smtp.assert_called_once_with('smtp.test.com', 587)
