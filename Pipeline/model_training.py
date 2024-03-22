import pandas as pd
import io
import pickle
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from google.cloud import storage

def train_model():
    # Loading data
    project_id = "ipl-score-prediction-418007"
    # Initialize GCP storage client
    storage_client = storage.Client(project=project_id)

    # Fetch dataset from GCP bucket
    bucket_name = "score_prediction_training_dataset"
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob("preprocessed_data/preprocessedData.csv")

    # Download CSV files as bytes
    preprocessed_bytes = blob.download_as_bytes()

    # Convert bytes to string
    preprocessed_text = preprocessed_bytes.decode("utf-8")

    # Read CSV files into DataFrame
    preprocessed_data = pd.read_csv(io.StringIO(preprocessed_text))

    # Dropping null values
    preprocessed_data.dropna(inplace=True)

    # Filtering out rows where balls_left = 0
    preprocessed_data = preprocessed_data[preprocessed_data['balls_left'] != 0]

    # Splitting data into train and test sets
    X = preprocessed_data.drop('result', axis=1)
    y = preprocessed_data['result']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=1)

    # Defining categorical columns for one-hot encoding
    categorical_columns = ['batting_team', 'bowling_team', 'city']
    # Defining ColumnTransformer
    column_transformer = ColumnTransformer(
        transformers=[('encoder', OneHotEncoder(drop='first'), categorical_columns)],
        remainder='passthrough'
    )

    # Defining Logistic Regression Pipeline
    logistic_pipeline = Pipeline([
        ('preprocessor', column_transformer),
        ('classifier', LogisticRegression(solver='liblinear'))
    ])

    # Fitting Logistic Regression model
    logistic_pipeline.fit(X_train, y_train)
    logistic_accuracy = logistic_pipeline.score(X_test, y_test)
    print("Logistic Regression Accuracy:", logistic_accuracy)

    # # Saving Logistic Regression model
    # pickle.dump(logistic_pipeline, open('logistic_model.pkl', 'wb'))

    # Defining Random Forest Pipeline
    random_forest_pipeline = Pipeline([
        ('preprocessor', column_transformer),
        ('classifier', RandomForestClassifier())
    ])

    # Fitting Random Forest model
    random_forest_pipeline.fit(X_train, y_train)
    random_forest_accuracy = random_forest_pipeline.score(X_test, y_test)
    print("Random Forest Accuracy:", random_forest_accuracy)

    # # Saving Random Forest model
    # pickle.dump(random_forest_pipeline, open('random_forest_model.pkl', 'wb'))

    # Save models to GCP bucket
    trained_model_bucket = storage_client.get_bucket("trained_score_prediction_models")
    pickle.dump(logistic_pipeline, open('logistic_model.pkl', 'wb'))
    logistic_blob = trained_model_bucket.blob("logistic_model.pkl")
    logistic_blob.upload_from_filename("logistic_model.pkl")
    
    pickle.dump(random_forest_pipeline, open('random_forest_model.pkl', 'wb'))
    rf_blob = trained_model_bucket.blob("random_forest_model.pkl")
    rf_blob.upload_from_filename("random_forest_model.pkl")

if __name__ == "__main__":
    train_model()
