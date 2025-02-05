from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

def get_db_connection():
    """
    Establish and return a connection to the PostgreSQL database.
    """
    # Load environment variables from .env file
    load_dotenv()

    # Define the connection details
    hostname = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    database = os.getenv("DB_NAME")
    username = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    
    try:
        # Create the connection string
        engine = create_engine(f"postgresql://{username}:{password}@{hostname}:{port}/{database}")
        connection = engine.connect()
        print("Database connection successful.")
        return connection
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return None
