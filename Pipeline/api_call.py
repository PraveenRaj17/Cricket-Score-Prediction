import requests
import json
from google.cloud import storage

def fetch_live_score():
    # API request code to fetch live score to be implemented here

    # Save the live score data to GCP bucket
    project_id = "ipl-score-prediction-418007"
    # Initialize GCP storage client
    storage_client = storage.Client(project=project_id)
    live_score_bucket = storage_client.get_bucket("livescore_and_prediction")
    live_score_blob = live_score_bucket.blob("live_score_data.json")
    live_score_blob.upload_from_string(json.dumps(live_score_data), "application/json")
