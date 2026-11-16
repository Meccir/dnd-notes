import os
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

load_dotenv()

def get_conn():
    return psycopg.connect(os.environ["DATABASE_URL"], row_factory=dict_row)