import requests
import json
import bs4
import pandas as pd
from bs4 import BeautifulSoup
import random
import time
import numpy as np
from datetime import date, timedelta
import ast
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

DELAY_MIN = 5  # Minimum delay time between requests
DELAY_MAX = 10  # Max delay time between requests
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}
events_results = []
base_url = "https://www.parkrun.org.uk/"
event_data_url = "https://images.parkrun.com/events.json"

# Function to make request to URL and return response

def make_a_request(link, headers, max_retries=5, wait_time=4):
    try:
        for attempt in range(max_retries):
            response = requests.get(link, headers=headers)         
            # If the status code is 200, return the response
            if response.status_code == 200:
                return response
            # If a 503 error is received, print a message and retry
            elif response.status_code == 503:
                print(f"Error 503: Service Unavailable. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)  # Wait before retrying
                wait_time *= 2  # Increase the wait time for the next attempt
            # For other errors, print the status code and return None
            else:
                print(f"Error: Received status code {response.status_code}")
                return None
        # If max retries are reached and still no successful request, return None
        print("Max retries reached. Request failed.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None


def wait_function():
    delay = random.uniform(DELAY_MIN, DELAY_MAX)  # Random delay between 5 and 10s
    print(f"Sleeping for {delay:.2f} seconds...")
    time.sleep(delay)


def extract_table_body(response):
    try:
        html_content = response.content
        soup = BeautifulSoup(html_content, "html.parser") if html_content else None
        if not soup:
            return {}
        table_body = soup.find('tbody')
        if not table_body:
            return {}
        return table_body
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return {}


def extract_data_from_table_body(table_body):
    result_data = []
    for row in table_body.find_all('tr', class_='Results-table-row'):
        # Extract data-* attributes
        name = row.get('data-name', None)
        age_group = row.get('data-agegroup', None)
        gender = row.get('data-gender', None)
        position = row.get('data-position', None)
        runs = row.get('data-runs', None)
        achievement = row.get('data-achievement', None)
        
        time_div = row.find('td', class_='Results-table-td Results-table-td--time')
        if not time_div:
            time_div = row.find('td', class_='Results-table-td Results-table-td--time Results-table-td--ft')
        if not time_div:
            time_div = row.find('td', class_='Results-table-td Results-table-td--time Results-table-td--pb')
        if time_div:
            compact_time = time_div.find('div', class_='compact')
            time = compact_time.text.strip() if compact_time else None
        else:
            time = None
        # Append extracted data to the list
        row_data = {
            "Name": name or "N/A",
            "Age Group": age_group or "N/A",
            "Gender": gender or "N/A",
            "Position": position or "N/A",
            "Runs": runs or "N/A",
            "Achievement": achievement or "N/A",
            "Time": time or "N/A"
        }
        result_data.append(row_data)
    return result_data

# 1. EXTRACT
# ----------------------------------------------------#

# Retrieve a list of UK Parkruns


print("Attempting to retrieve list of UK Parkruns...")
# Get the event JSON data from the URL
response = requests.get(event_data_url)
if response.status_code == 200:
    data = response.json()  # Parse JSON data   
    # Extract event names, EventLongName, and coordinates where the country code is 97
    uk_parkruns = [
        {
            "eventname": feature["properties"]["eventname"],
            "EventLongName": feature["properties"]["EventLongName"],
            "coordinates": feature["geometry"]["coordinates"]
        }
        for feature in data["events"]["features"]
        if feature["properties"]["countrycode"] == 97 and feature["properties"]["seriesid"] == 1
    ]
    wait_function()
    print(f"Found {len(uk_parkruns)} Parkruns in the UK (excluding Junior runs):")
else:
    print(f"Failed to fetch data: HTTP {response.status_code}")

# For each Parkrun event, access results page and extract data

for parkrun_id, parkrun_name in enumerate(uk_parkruns[0:2]):
    # Construct url
    url = f"{base_url}{parkrun_name['eventname']}/results/latestresults/" 
    response = make_a_request(url, headers=HEADERS)
    table_body = extract_table_body(response)
    result_data = extract_data_from_table_body(table_body)
    # Store event and its results as a dictionary
    event_data = {
        "Event ID": parkrun_id,
        "Event Name": parkrun_name['eventname'],
        "Results": result_data
    }
    # Add event data to the list
    events_results.append(event_data)
    print(f"results added for {parkrun_name['eventname']} parkrun")
    wait_function()

df = pd.DataFrame(events_results)
df_info = pd.DataFrame(uk_parkruns)
print("Extraction Complete")

# 2. TRANSFORM
# ----------------------------------------------------#
print("Transforming data...")

# Concatenate Data frames
df_info = df_info.drop(columns='eventname')
df = pd.concat([df_info, df], axis=1)

# # Convert latitude and longitude to separate columns
# df[['Longitude', 'Latitude']] = pd.DataFrame(df['coordinates'].apply(ast.literal_eval).to_list(), index=df.index)
# df.drop(columns="coordinates")

# Reorder columns
# new_column_order = ['Event ID', 'Event Name', 'EventLongName', 'Longitude','Latitude', 'Results']
new_column_order = ['Event ID', 'Event Name', 'EventLongName', 'coordinates', 'Results']
df = df[new_column_order]

# Convert the lists in results individual rows
print("Converting dictionaries to rows...")
df['Results'] = df['Results'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
df['Results'] = df['Results'].apply(lambda x: x if isinstance(x, list) else [])
df_exploded = df.explode('Results', ignore_index=True)
df_flattened = pd.json_normalize(df_exploded['Results'])
df = pd.concat([df_exploded.drop('Results', axis=1), df_flattened], axis=1)

# Deal with na values 
print("Dealing with missing values...")
df['Achievement'] = df['Achievement'].fillna('None')
df['Achievement'] = df['Achievement'].replace('N/A', 'No Achievement')
df = df.dropna(subset=['Age Group'])
df = df[df['Age Group'] != 'N/A']  # Remove rows with 'N/A' string

# Change data types
df['Event Name'] = df['Event Name'].astype(str)
df['Position'] = df['Position'].fillna(0).astype(int)
df['Runs'] = df['Runs'].fillna(0).astype(int)

# Convert times to actual durations using time_delta
df = df.dropna(subset=['Time']) # Drop rows where 'Time' is NaN or missing
df['Time'] = df['Time'].astype(str)
df['Time'] = df['Time'].apply(lambda x: f"00:{x}" if len(x.split(':')) == 2 else x)
df['Time'] = pd.to_timedelta(df['Time'], errors='coerce')

print("Data transformation complete.")

# 3. LOAD
# ----------------------------------------------------#
print("Loading data...")


# Load environment variables from .env file
load_dotenv()
print("Received credentials...")

# Define the connection details
hostname = os.getenv("DB_HOST")
port = os.getenv("DB_PORT")
database = os.getenv("DB_NAME")
username = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")

table_name = 'rw_parkrun'
schema_name = 'student'

# Create the SQLAlchemy engine
try:
    engine = create_engine(f"postgresql://{username}:{password}@{hostname}:{port}/{database}")

    # Use Pandas' to_sql method to insert data
    df.to_sql(
        table_name,
        engine,
        schema=schema_name,  # Specify the schema separately
        if_exists='replace',  # Only keep latest week's results
        index=False
    )

    print(f"Data inserted into table {schema_name}.{table_name} successfully.")

except Exception as e:
    print(f"An error occurred: {e}")

print("Data loading complete.")
