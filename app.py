from flask import Flask, request
import json
from datetime import datetime
import os
from pinecone import Pinecone
import uuid

app = Flask(__name__)


pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
# Create a dense index with integrated embedding
index_name = "dense-index"
if not pc.has_index(index_name):
    pc.create_index_for_model(
        name=index_name,
        cloud="aws",
        region="us-east-1",
        embed={
            "model":"llama-text-embed-v2",
            "field_map":{"text": "chunk_text"}
        }
    )
dense_index = pc.Index(index_name)

# Define the file where requests will be stored
LOG_FILE = "webhook_requests.json"

# Ensure the file exists and initialize it as an empty list if it doesn't
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, 'w') as f:
        json.dump([], f)

@app.route('/<route>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def handle_webhook(route):
    # Create a request data dictionary
    request_data = {
        'timestamp': datetime.utcnow().isoformat(),
        'method': request.method,
        'route': route,
        'headers': dict(request.headers),
        'query_params': request.args.to_dict(),
        'body': {}
    }
    print("Raw Request Data")
    print(request_data)
    
    # Try to parse the body as JSON, if possible
    try:
        if request.method in ['POST', 'PUT']:
            if request.is_json:
                request_data['body'] = request.get_json()
            else:
                request_data['body'] = request.data.decode('utf-8')
    except Exception as e:
        print("Error decoding response")
        print(str(e))
        request_data['body'] = f"Error decoding body: {str(e)}"
    
    # Read existing data
    try:
        with open(LOG_FILE, 'r') as f:
            existing_data = json.load(f)
    except json.JSONDecodeError:
        existing_data = []
    
    print("About to write to DB")
    try:
        if "event" in request_data["body"]:
            request_data["_id"] = str(uuid.uuid4())
            request_data["chunk_test"] = request_data["body"]["data"]["data"]["words"][0]["text"]
    except Exception as e:
        print("We got an Error rewriteing the event to fit into Vecotr DV")
        print(e)
    try:
        dense_index.upsert_records("example-namespace", [request_data])
    except Exception as e:
        print("Error inserting into Vector DB")
        print(e)
        
    # Append new request
    existing_data.append(request_data)
    
    # Write back to file
    with open(LOG_FILE, 'w') as f:
        json.dump(existing_data, f, indent=2)
    
    # Return success response
    return {'status': 'success', 'message': 'Request logged'}, 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
