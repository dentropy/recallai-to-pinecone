import requests
import json
import time
import uuid
from pprint import pprint
# URL to send requests to (replace with your actual endpoint)
url = "http://localhost:5000/your-path"

# Headers for the request (modify as needed)
headers = {
    "Content-Type": "application/json"
}

convo_data = {
    "event": "transcript.data",
    "data": {
        "transcript": {
            "id": str(uuid.uuid4()),
            "metadata": {}
        },
        "realtime_endpoint": {
            "id": str(uuid.uuid4()),
            "metadata": {}
        },
        "recording": {
            "id": str(uuid.uuid4()),
            "metadata": {}
        },
        "bot": {
            "id": str(uuid.uuid4()),
            "metadata": {}
        }
    }
}

# Function to send each object as a separate request
def send_requests(data_list):
    print(data_list)
    for item in data_list:
        try:
            # Send POST request with the current object
            print(item)
            print("ITEM")
            convo_data["data"]["data"] = item["data"]
            print("\n\nconvo_data")
            pprint(convo_data)
            response = requests.post(url, json=convo_data, headers=headers)
            
            # Print response status and content
            print(f"Sent: {item}")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}\n")
            
            # Wait for 3 seconds before the next request
            time.sleep(3)
            
        except requests.exceptions.RequestException as e:
            print(f"Error sending request for {item}: {e}")

# Execute the function
if __name__ == "__main__":
    # If reading from a JSON file, uncomment and modify the following lines:
    with open('./convo_data.json', 'r') as file:
        json_data = json.load(file)
    send_requests(json_data)