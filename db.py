import psycopg2

db_params = {
    'host': 'localhost',
    'port': '5432',
    'user': 'postgres',
    'password': '',
    'database': 'postgres'
}

conn = psycopg2.connect(**db_params)
conn.set_session(autocommit=True)
cursor = conn.cursor()