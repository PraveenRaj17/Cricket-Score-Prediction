import pandas as pd
import io
# import numpy as np
# import seaborn as sn
# import matplotlib.pyplot as plt
from google.cloud import storage

def preprocess_data():
    # Your data preprocessing code here
    # Loading data
    project_id = "ipl-score-prediction-418007"
    # Initialize GCP storage client
    storage_client = storage.Client(project=project_id)

    # Fetch dataset from GCP bucket
    bucket_name = "score_prediction_training_dataset"
    bucket = storage_client.get_bucket(bucket_name)
    blob_matches = bucket.blob("matches.csv")
    blob_deliveries = bucket.blob("deliveries.csv")
    # matches_data = pd.read_csv(blob_matches.download_as_text())
    # deliveries_data = pd.read_csv(blob_deliveries.download_as_text())

    # Download CSV files as bytes
    matches_bytes = blob_matches.download_as_bytes()
    deliveries_bytes = blob_deliveries.download_as_bytes()

    # Convert bytes to string
    matches_text = matches_bytes.decode("utf-8")
    deliveries_text = deliveries_bytes.decode("utf-8")

    # Read CSV files into DataFrame
    matches_data = pd.read_csv(io.StringIO(matches_text))
    deliveries_data = pd.read_csv(io.StringIO(deliveries_text))

    # matches_data = pd.read_csv('matches.csv')
    # deliveries_data = pd.read_csv('deliveries.csv')

    totalrun_df = deliveries_data.groupby(['match_id','inning']).sum()['total_runs'].reset_index()

    totalrun_df = totalrun_df[totalrun_df['inning']==1]
    totalrun_df['target_set'] = totalrun_df['total_runs'].apply(lambda x:x+1)

    # Replacing old team names with new ones
    teams_mapping = {
        'Delhi Daredevils': 'Delhi Capitals',
        'Deccan Chargers': 'Sunrisers Hyderabad'
    }
    matches_data.replace({'team1': teams_mapping, 'team2': teams_mapping}, inplace=True)

    # Filtering frequently occurring teams
    # Excluding teams like Kochi Tuskers, Pune Warriors, etc.
    frequent_teams = [
        'Sunrisers Hyderabad', 'Mumbai Indians', 'Royal Challengers Bangalore',
        'Kolkata Knight Riders', 'Kings XI Punjab', 'Chennai Super Kings',
        'Rajasthan Royals', 'Delhi Capitals'
    ]
    filtered_matches_data = matches_data[matches_data['team1'].isin(frequent_teams) & matches_data['team2'].isin(frequent_teams)]

    # Handling DL method and filtering columns
    # We reject matches involving DL method just to avoid confusing our model
    matches_without_dl = filtered_matches_data[filtered_matches_data['dl_applied'] == 0]
    matches_without_dl = matches_without_dl[['id', 'city', 'winner']]

    matches_without_dl = matches_without_dl.merge(totalrun_df[['match_id', 'target_set']],
                        left_on='id',right_on='match_id')

    # Merging match data with deliveries data
    merged_data = matches_without_dl.merge(deliveries_data, left_on='id', right_on='match_id')

    # Filtering second innings data
    second_innings_data = merged_data[merged_data['inning'] == 2]

    # filling nan values with "0"

    second_innings_data['player_dismissed'] = second_innings_data['player_dismissed'].fillna("0")

    # now we will convert this player_dismissed col into a boolean col
    # if the player is not dismissed then it's 0 else it's 1

    second_innings_data['player_dismissed'] = second_innings_data['player_dismissed'].apply(lambda x:x
                                                                        if x=="0" else "1")

    # converting string to int

    second_innings_data['player_dismissed'] = second_innings_data['player_dismissed'].astype('int')

    # Calculating current score, runs left, balls left, wickets left, current run rate, and required run rate
    second_innings_data['current_score'] = second_innings_data.groupby('match_id_y')['total_runs'].cumsum()
    second_innings_data['runs_left'] = second_innings_data['target_set'] - second_innings_data['current_score']
    second_innings_data['balls_left'] = 126 - (second_innings_data['over'] * 6 + second_innings_data['ball'])
    second_innings_data['wickets_left'] = 10 - second_innings_data.groupby('match_id_y')['player_dismissed'].cumsum()
    second_innings_data['cur_run_rate'] = (second_innings_data['current_score'] * 6) / (120 - second_innings_data['balls_left'])
    second_innings_data['req_run_rate'] = (second_innings_data['runs_left'] * 6) / second_innings_data['balls_left']

    # Creating result column indicating win/lose
    second_innings_data.loc[:, 'result'] = second_innings_data['batting_team'] == second_innings_data['winner']
    second_innings_data.loc[:, 'result'] = second_innings_data['result'].astype(int)
    second_innings_data['result']

    # Final DataFrame with features for modeling
    final_data = second_innings_data[['batting_team', 'bowling_team', 'city', 'runs_left',
                                    'balls_left', 'wickets_left', 'target_set', 'cur_run_rate',
                                    'req_run_rate', 'result']]
    final_data

    # Dropping null values
    final_data.dropna(inplace=True)

    # Filtering out rows where balls_left = 0
    final_data = final_data[final_data['balls_left'] != 0]

    preprocessedData = final_data
    bucket = storage_client.get_bucket("score_prediction_training_dataset")
    preprocessed_blob = bucket.blob("preprocessed_data/preprocessedData.csv")
    preprocessed_blob.upload_from_string(preprocessedData.to_csv(index=False), "text/csv")

if __name__ == "__main__":
    preprocess_data()