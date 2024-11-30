from airflow import DAG
from airflow.providers.http.operators.http import SimpleHttpOperator
from airflow.decorators import task
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.utils.dates import days_ago
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json

from models import Base, APODData

with DAG(
    dag_id='nasa_apod_postgres',
    start_date=days_ago(1),
    schedule_interval='@daily',
    catchup=False
) as dag:

    #step 1: Create table if it does not exist
    @task
    def create_table():
        # Get PostgreSQL connection details from Airflow connection
        postgres_hook = PostgresHook(postgres_conn_id="my_postgres_connection")
        conn_uri = postgres_hook.get_uri()
        
        # Create SQLAlchemy engine
        engine = create_engine(conn_uri)
        
        # Create all tables defined in models
        Base.metadata.create_all(engine)

    #step 2: Extract the NASA API data
    extract_apod = SimpleHttpOperator(
        task_id='extract_apod',
        http_conn_id='nasa_api',
        endpoint='planetary/apod',
        method='GET',
        data={"api_key":"{{ conn.nasa_api.extra_dejson.api_key}}"},
        response_filter=lambda response: response.json(),
    )

    #step 3: Transform the data
    @task
    def transform_apod_data(response):
        return {
            'title': response.get('title', ''),
            'explanation': response.get('explanation', ''),
            'url': response.get('url', ''),
            'date': datetime.strptime(response.get('date', ''), '%Y-%m-%d').date(),
            'media_type': response.get('media_type', '')
        }

    #step 4: Load the data into Postgres using SQLAlchemy
    @task
    def load_data_to_postgres(apod_data):
        # Get PostgreSQL connection details
        postgres_hook = PostgresHook(postgres_conn_id='my_postgres_connection')
        conn_uri = postgres_hook.get_uri()
        
        # Create SQLAlchemy engine and session
        engine = create_engine(conn_uri)
        Session = sessionmaker(bind=engine)
        session = Session()

        try:
            # Create new APOD entry
            new_apod = APODData(
                title=apod_data['title'],
                explanation=apod_data['explanation'],
                url=apod_data['url'],
                date=apod_data['date'],
                media_type=apod_data['media_type']
            )
            
            # Add and commit the new entry
            session.add(new_apod)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    # Define task dependencies
    create_table() >> extract_apod
    api_response = extract_apod.output
    transformed_data = transform_apod_data(api_response)
    load_data_to_postgres(transformed_data)