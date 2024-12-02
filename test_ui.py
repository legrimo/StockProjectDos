from flask import Flask, render_template, jsonify
import subprocess
import json

app = Flask(__name__)

@app.route('/')
def test_dashboard():
    """Display test results dashboard"""
    return render_template('test_dashboard.html')

@app.route('/run_tests', methods=['POST'])
def run_tests():
    """Execute pytest and return results"""
    try:
        # Run pytest with JSON output
        result = subprocess.run(
            ['python3', 'run_tests.py'],
            capture_output=True,
            text=True
        )
        
        # Parse the output
        output_lines = result.stdout.split('\n')
        test_results = []
        current_test = None
        
        for line in output_lines:
            if '::test_' in line:
                # Extract test information
                parts = line.split('::')
                if len(parts) >= 2:
                    test_name = parts[1].split()[0]
                    status = 'PASSED' if 'PASSED' in line else 'FAILED'
                    if '[' in line and ']' in line:
                        duration = line[line.find('[')+1:line.find(']')]
                    else:
                        duration = 'N/A'
                    
                    # Get test description from docstring
                    description = ""
                    try:
                        with open('tests/test_stock_notifications.py', 'r') as f:
                            test_content = f.read()
                            test_lines = test_content.split('\n')
                            for i, content in enumerate(test_lines):
                                if f'def {test_name}' in content:
                                    # Look for docstring in next lines
                                    if i + 1 < len(test_lines) and '"""' in test_lines[i + 1]:
                                        description = test_lines[i + 1].split('"""')[1].strip()
                    except Exception as e:
                        print(f"Error reading test description: {e}")
                    
                    test_results.append({
                        "name": test_name,
                        "status": status,
                        "duration": duration,
                        "description": description
                    })
        
        # Process any errors
        error_message = None
        if result.stderr:
            error_lines = result.stderr.split('\n')
            error_message = '\n'.join(line for line in error_lines if line.strip())

        return jsonify({
            'success': result.returncode == 0,
            'results': test_results,
            'error': error_message,
            'summary': {
                'total': len(test_results),
                'passed': sum(1 for test in test_results if test['status'] == 'PASSED'),
                'failed': sum(1 for test in test_results if test['status'] == 'FAILED')
            }
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'results': [],
            'error': f"Error executing tests: {str(e)}\n{traceback.format_exc()}",
            'summary': {
                'total': 0,
                'passed': 0,
                'failed': 0
            }
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
