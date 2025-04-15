from flask import Flask, request
import json
from datetime import datetime
import os

app = Flask(__name__)

# Define the file where requests will be stored
LOG_FILE = "webhook_requests.json"

# Ensure the file exists and initialize it as an empty list if it doesn't
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, 'w') as f:
        json.dump([], f)

@app.route('/webhook', methods=['GET', 'POST', 'PUT', 'DELETE'])
def handle_webhook():
    # Create a request data dictionary
    request_data = {
        'timestamp': datetime.utcnow().isoformat(),
        'method': request.method,
        'headers': dict(request.headers),
        'query_params': request.args.to_dict(),
        'body': {}
    }
    
    # Try to parse the body as JSON, if possible
    try:
        if request.method in ['POST', 'PUT']:
            if request.is_json:
                request_data['body'] = request.get_json()
            else:
                request_data['body'] = request.data.decode('utf-8')
    except Exception as e:
        request_data['body'] = f"Error decoding body: {str(e)}"
    
    # Read existing data
    try:
        with open(LOG_FILE, 'r') as f:
            existing_data = json.load(f)
    except json.JSONDecodeError:
        existing_data = []
    
    # Append new request
    existing_data.append(request_data)
    
    # Write back to file
    with open(LOG_FILE, 'w') as f:
        json.dump(existing_data, f, indent=2)
    
    # Return success response
    return {'status': 'success', 'message': 'Request logged'}, 200

# Define the file where requests will be stored
LOG_FILE2 = "realtime.json"

# Ensure the file exists and initialize it as an empty list if it doesn't
if not os.path.exists(LOG_FILE2):
    with open(LOG_FILE2, 'w') as f:
        json.dump([], f)

@app.route('/realtime', methods=['GET', 'POST', 'PUT', 'DELETE'])
def handle_realtime_webhook():
    # Create a request data dictionary
    request_data = {
        'timestamp': datetime.utcnow().isoformat(),
        'method': request.method,
        'headers': dict(request.headers),
        'query_params': request.args.to_dict(),
        'body': {}
    }
    
    # Try to parse the body as JSON, if possible
    try:
        if request.method in ['POST', 'PUT']:
            if request.is_json:
                request_data['body'] = request.get_json()
            else:
                request_data['body'] = request.data.decode('utf-8')
    except Exception as e:
        request_data['body'] = f"Error decoding body: {str(e)}"
    
    # Read existing data
    try:
        with open(LOG_FILE2, 'r') as f:
            existing_data = json.load(f)
    except json.JSONDecodeError:
        existing_data = []
    
    # Append new request
    existing_data.append(request_data)
    
    # Write back to file
    with open(LOG_FILE2, 'w') as f:
        json.dump(existing_data, f, indent=2)
    
    # Return success response
    return {'status': 'success', 'message': 'Request logged'}, 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

