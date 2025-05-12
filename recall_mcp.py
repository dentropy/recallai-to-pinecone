import psycopg2
from urllib.parse import urlparse
import requests
from pgvector.psycopg2 import register_vector
import os

DATABASE_URL = os.getenv('RECALL_PG_CONN_STRING')
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


from fastmcp import FastMCP

# Create a server instance
mcp = FastMCP(name="Chat Listener Assistant")

"""

export RECALL_PG_CONN_STRING="postgres://postgres:postgres@localhost:5435/postgres"
export RECALL_CHAT_ID="db4cedd7-f803-4952-9822-05a4d5d6678b"
export OLLAMA_EMBEDDING_MODEL="nomic-embed-text"
export OLLAMA_EMBEDDING_URL="http://localhost:11434/api/embeddings"

"""

@mcp.tool()
def recall_chat_logs(search_string: str) -> float:
    """Recall Chat Logs."""
    data = {
        "model": os.getenv('OLLAMA_EMBEDDING_MODEL'),
        "prompt": search_string
    }
    response = requests.post(os.getenv("OLLAMA_EMBEDDING_URL"), json=data)
    json_response = response.json()
    embedding = json_response["embedding"]
    recall_query = """
        SELECT
            body, from_timestamp_relative, to_timestamp_relative
        FROM
            embedded_chats_t
        WHERE
            transcript_id = %s
        ORDER BY
            embedding <-> %s::vector
        LIMIT 5
    """
    print(embedding)
    cursor.execute(recall_query, (os.getenv("RECALL_CHAT_ID"), embedding,))
    results = cursor.fetchall()
    if len(results) == 0:
        return "NO CHAT LOGS IN SYSTEM"
    else:
        return results[0][0]

if __name__ == "__main__":
    # mcp.run()  # Default: uses STDIO transport
    # mcp.run(transport="streamable-http", host="0.0.0.0", port=8000, path="/recall_mcp")
    mcp.run(transport="sse", host="0.0.0.0", port=8000)
    
    
    # result = recall_chat_logs("S3 AWS Stuff")
    # print(result)