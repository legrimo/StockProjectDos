from flask import Flask, render_template
import pytest

app = Flask(__name__)

@app.route('/')
def test_dashboard():
    """Display test results dashboard"""
    return render_template('test_dashboard.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)