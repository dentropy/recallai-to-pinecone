from flask import Flask, request
import json
from datetime import datetime
import os
from pinecone import Pinecone
import uuid
from pprint import pprint
import psycopg2
from urllib.parse import urlparse
import requests
from pgvector.psycopg2 import register_vector
import numpy as np
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
register_vector(conn)
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

def chunk_my_data(transcript_id, from_timestamp_relative):
    # Check the last 30 second increment in the Database
    check_time_query = """
        SELECT
            from_timestamp_relative
        FROM
            embedded_chats_t
        WHERE
            transcript_id = %s
        ORDER BY
            from_timestamp_relative DESC
        LIMIT 1
    """
    cursor.execute(check_time_query, (str(transcript_id),))
    rows = cursor.fetchall()
    print("PAUL_WAS_HERE_15")
    print(rows)
    latest_chunked_timestamp = 0
    if (len(rows) != 0):
        latest_chunked_timestamp = rows[0][0]
    # If current timestamp if a Minute in the Future
    if( from_timestamp_relative < (latest_chunked_timestamp + 10)):
        print("WE_ARE_ALMOST_THERE")
        return False
    # Get the previous chats
    check_time_query = """
        SELECT
            speaker, chunk_test, from_timestamp_relative, to_timestamp_relative
        FROM
            transcribed_snippits_t
        WHERE
            transcript_id = %s
            AND from_timestamp_relative > %s
        ORDER BY
            from_timestamp_relative DESC
    """
    cursor.execute(check_time_query, (str(transcript_id),from_timestamp_relative - 15))
    rows = cursor.fetchall()
    print("PAUL_WAS_HERE_17")
    print(rows)
    embedding_text = ""
    from_timestamp_relative = rows[0][2]
    to_timestamp_relative = rows[len(rows) - 1][3]
    for row in rows:
        embedding_text += f"{row[0]}: {row[1]}\n\n"
    url = f"http://localhost:11434/api/embeddings"
    data = {
        "model": "nomic-embed-text",
        "prompt": embedding_text
    }
    response = requests.post(url, json=data)
    json_response = response.json()
    embedding = json_response["embedding"]
    # TODO Check 200 response
    embedding_insert_data = {
        "transcript_id": transcript_id,
        "model_name": "nomic-embed-text",
        "from_timestamp_relative": from_timestamp_relative,
        "to_timestamp_relative": to_timestamp_relative,
        "title": "TODO",
        "body": embedding_text,
        "embedding": embedding
    }
    embedding_insert_tuple = (
        embedding_insert_data["transcript_id"],
        embedding_insert_data["model_name"],
        embedding_insert_data["from_timestamp_relative"],
        embedding_insert_data["to_timestamp_relative"],
        embedding_insert_data["title"],
        embedding_insert_data["body"],
        embedding_insert_data["embedding"] 
    )
    # pprint(embedding_insert_data)
    # print("embedding_insert_data")
    insert_embedded_chats_t_query = """
        INSERT INTO embedded_chats_t (
            transcript_id,
            model_name,
            from_timestamp_relative,
            to_timestamp_relative,
            title,
            body,
            embedding
        ) VALUES (
            %s, %s, %s,
            %s, %s, %s,
            %s
        )
        
    """
    pprint("PAUL_IS_ABOUT_TO_INSERT")
    cursor.execute(
        insert_embedded_chats_t_query,
        embedding_insert_tuple
    )
    conn.commit()
    print("WE_AT_LEAST_EXECUTED")
    print("WE_ARE_DONE_FOR_NOW")
    # Save to the Database
    pass

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
            print("\n\nWE_GOT_HERE\n\n")
            print("request_data")
            pprint(request_data)
            # vector_db_record["_id"] = str(uuid.uuid4())
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
                    %s, %s, %s
                )
            """
            insert_params = (
                # vector_db_record["_id"],
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
            print(insert_params)
            cursor.execute(insert_query, insert_params)
            print("SENT_IT")
            conn.commit()
            print("GOT_IT")
            chunk_my_data(
                vector_db_record["transcript_id"],
                vector_db_record["from_timestamp_relative"]
            )
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
