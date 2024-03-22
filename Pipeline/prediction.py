import pickle
from google.cloud import storage
import json
import math
import pandas as pd

def make_prediction():
    project_id = "ipl-score-prediction-418007"
    storage_client = storage.Client(project=project_id)
    # Load the trained model from GCP bucket
    trained_model_bucket = storage_client.get_bucket("trained_score_prediction_models")
    logistic_blob = trained_model_bucket.blob("logistic_model.pkl")
    logistic_blob.download_to_filename("logistic_model.pkl")
    logistic_model = pickle.load(open('logistic_model.pkl', 'rb'))

    # Load live score data from GCP bucket
    live_score_bucket = storage_client.get_bucket("livescore_and_prediction")
    live_score_blob = live_score_bucket.blob("live_score_data.json")
    live_score_data = json.loads(live_score_blob.download_as_string())

    batting_team = live_score_data['batting_team']
    bowling_team = live_score_data['bowling_team']
    venue = live_score_data['venue']
    target_score = live_score_data['target_score']
    current_score = live_score_data['current_score']
    over = live_score_data['over']
    wickets_fallen = live_score_data['wickets_fallen']

    runs_left = target_score-current_score
    balls_bowled = (math.floor(over)*6)+(over - math.floor(over))

    balls_left = 120-(balls_bowled)
    wickets_left = 10-wickets_fallen

    # Checking for different match results based on the input provided
    if current_score > target_score:
        content = f"{batting_team} won the match"
        
    elif current_score == target_score-1 and over==20:
        content = "Match Drawn"
        
    elif wickets_fallen==10 and current_score < target_score-1:
        content = f"{bowling_team} won the match"
        
    elif wickets_fallen==10 and current_score == target_score-1:
        content = "Match tied"
    
    else:        
        # Calculating the current Run-Rate of the batting team
        currentrunrate = current_score/over
        
        # Calculating the Required Run-Rate for the batting team to win
        requiredrunrate = (runs_left*6)/balls_left
                        
        # Creating a pandas DataFrame containing the user inputs
        input_df = pd.DataFrame(
                        {'batting_team': [batting_team], 
                        'bowling_team': [bowling_team], 
                        'city': [venue], 
                        'runs_left': [runs_left], 
                        'balls_left': [balls_left],
                        'wickets': [wickets_left], 
                        'total_runs_x': [target_score], 
                        'cur_run_rate': [currentrunrate], 
                        'req_run_rate': [requiredrunrate]})

        # Loading the trained LR model to make the prediction
        result = logistic_model.predict_proba(input_df)
        
        # Extracting the likelihood of loss and win
        lossprob = result[0][0]
        winprob = result[0][1]
        content = f"Batting: {batting_team} ; Runs: {current_score} ; Wickets: {wickets_fallen} ; Over: {over} ; Target: {target_score}"
        content = content + "\n\n" + f"{batting_team}- {round(winprob*100)}%\n{bowling_team}- {round(lossprob*100)}%"

    win_probability_bucket = storage_client.get_bucket("livescore_and_prediction")
    win_probability_blob = win_probability_bucket.blob("win_probability.txt")
    win_probability_blob.upload_from_string(content, content_type='text/plain')
