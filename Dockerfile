FROM quay.io/astronomer/astro-runtime:12.4.0
RUN pip install "SQLAlchemy>=1.4.0,<2.0.0" apache-airflow-providers-postgres psycopg2-binary