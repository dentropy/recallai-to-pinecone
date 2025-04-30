from flask import Flask, request
import json
from datetime import datetime
import os
from pinecone import Pinecone
import uuid
from pprint import pprint
import psycopg2
from urllib.parse import urlparse

app = Flask(__name__)

DATABASE_URL = os.getenv('PG_CONN_STRING')
# Parse the connection string (if using a URL format like Heroku)
if DATABASE_URL.startswith('postgres://'):
    parsed_url = urlparse(DATABASE_URL)
    db_params = {
        'dbname': parsed_url.path[1:],  # Remove leading '/'
        'user': parsed_url.username,
        'password': parsed_url.password,
        'host': parsed_url.hostname,
        'port': parsed_url.port
    }
else:
    # Assume DATABASE_URL is a direct connection string
    db_params = {'dsn': DATABASE_URL}

# Establish connection
conn = psycopg2.connect(**db_params)
cursor = conn.cursor()

# pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
# # Create a dense index with integrated embedding
# index_name = "dense-index"
# if not pc.has_index(index_name):
#     pc.create_index_for_model(
#         name=index_name,
#         cloud="aws",
#         region="us-east-1",
#         embed={
#             "model":"llama-text-embed-v2",
#             "field_map":{"text": "chunk_text"}
#         }
#     )
# dense_index = pc.Index(index_name)

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
    vector_db_record = {}
    print("request_data")
    pprint(request_data)
    try:
        if "event" in request_data["body"]:
            vector_db_record["_id"] = str(uuid.uuid4())
            vector_db_record["chunk_text"] = request_data["body"]["data"]["data"]["words"][0]["text"]
            vector_db_record["speaker"] = request_data["body"]["data"]["data"]["participant"]["name"]
            vector_db_record["from_timestamp"] = request_data["body"]["data"]["data"]["words"][0]["start_timestamp"]["absolute"]
            vector_db_record["to_timestamp"] = request_data["body"]["data"]["data"]["words"][0]["end_timestamp"]["absolute"]
            vector_db_record["from_timestamp_relative"] = request_data["body"]["data"]["data"]["words"][0]["start_timestamp"]["relative"]
            vector_db_record["to_timestamp_relative"] = request_data["body"]["data"]["data"]["words"][0]["end_timestamp"]["relative"]
            vector_db_record["transcript_id"] = request_data["body"]["data"]["transcript"]["id"]
            vector_db_record["record_id"] = request_data["body"]["data"]["recording"]["id"]
            vector_db_record["bot_id"] = request_data["body"]["data"]["bot"]["id"]
            print("vector_db_record")
            pprint(vector_db_record)
            insert_query = """
                INSERT INTO transcribed_snippits_t (
                    id,
                    chunk_test,
                    speaker,
                    from_timestamp,
                    to_timestamp,
                    from_timestamp_relative,
                    to_timestamp_relative,
                    transcript_id,
                    record_id,
                    bot_id
                ) VALUES (
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s
                )
            """
            insert_params = (
                vector_db_record["_id"],
                vector_db_record["chunk_text"],
                vector_db_record["speaker"],
                vector_db_record["from_timestamp"],
                vector_db_record["to_timestamp"],
                vector_db_record["from_timestamp_relative"],
                vector_db_record["to_timestamp_relative"],
                vector_db_record["transcript_id"],
                vector_db_record["record_id"],
                vector_db_record["bot_id"]
            )
            print("ALMOST")
            cursor.execute(insert_query, insert_params)
            print("SENT_IT")
            conn.commit()
            print("GOT_IT")
    except Exception as e:
        print("We got an Error rewriteing the event to fit into Vecotr DB")
        print(e)
    # try:
    #     dense_index.upsert_records("example-namespace", [vector_db_record])
    # except Exception as e:
    #     print("Error inserting into Vector DB")
    #     print(e)
        
    # Append new request
    existing_data.append(request_data)
    
    # Write back to file
    with open(LOG_FILE, 'w') as f:
        json.dump(existing_data, f, indent=2)
    
    # Return success response
    return {'status': 'success', 'message': 'Request logged'}, 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
