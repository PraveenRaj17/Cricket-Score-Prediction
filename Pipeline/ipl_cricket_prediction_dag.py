from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
from data_preprocessing import preprocess_data
from model_training import train_model
from api_call import fetch_live_score
from prediction import make_prediction

# Define the default arguments for the DAGs
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Define the first DAG: preprocess_task >> train_model_task
dag_preprocess_train = DAG(
    'preprocess_train_model_dag',
    default_args=default_args,
    description='DAG for preprocessing data and training the model',
    schedule_interval=None,
)

# Define the second DAG: fetch_score_task >> prediction_task
dag_fetch_score_predict = DAG(
    'fetch_score_predict_dag',
    default_args=default_args,
    description='DAG for fetching live scores and making predictions',
    schedule_interval=timedelta(minutes=5),  # Example: Fetch every 5 minutes
)

# Define tasks for the first DAG
preprocess_task = PythonOperator(
    task_id='preprocess_data',
    python_callable=preprocess_data,
    dag=dag_preprocess_train,
)

train_model_task = PythonOperator(
    task_id='train_model',
    python_callable=train_model,
    dag=dag_preprocess_train,
)

# Define tasks for the second DAG
fetch_score_task = PythonOperator(
    task_id='fetch_live_score',
    python_callable=fetch_live_score,
    dag=dag_fetch_score_predict,
)

predict_task = PythonOperator(
    task_id='make_prediction',
    python_callable=make_prediction,
    dag=dag_fetch_score_predict,
)

# Define dependencies for the first DAG
preprocess_task >> train_model_task

# Define dependencies for the second DAG
fetch_score_task >> predict_task
