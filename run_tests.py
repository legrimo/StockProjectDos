import pytest
import sys

def main():
    """Run the test suite"""
    args = [
        "-v",
        "--html=test_report.html",
        "--self-contained-html",
        "tests"
    ]
    
    exit_code = pytest.main(args)
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
