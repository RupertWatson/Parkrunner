import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
#from utils.db_connection import get_db_connection 
import ast
import altair as alt
import re
from sqlalchemy import create_engine
import os

def get_db_connection():
    """
    Establish and return a connection to the PostgreSQL database.
    """
    # Define the connection details
    hostname=st.secrets["DB_HOST"]
    port=st.secrets["DB_PORT"]
    database=st.secrets["DB_NAME"]
    username=st.secrets["DB_USER"]
    password=st.secrets["DB_PASSWORD"]
      
    try:
        # Create the connection string
        engine = create_engine(f"postgresql://{username}:{password}@{hostname}:{port}/{database}")
        connection = engine.connect()
        print("Database connection successful.")
        return connection
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return None

st.set_page_config(
    page_title="Parkrunner",
    #page_icon="🏃",
    layout="wide"
)

connection = get_db_connection()

if connection:
    participant_count_query = """
    SELECT COUNT(*) AS total_participants
    FROM student.rw_parkrun_2;
    """
    try:
        participant_count_df = pd.read_sql(participant_count_query, connection)
    except Exception as e:
        st.error(f"Error fetching data: {e}")
    
    gender_query = """
    SELECT "Gender" ,count("Gender")
    FROM student.rw_parkrun_2
    GROUP BY "Gender" 
    """
    try:
        gender_df = pd.read_sql(gender_query, connection)
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        
    age_query = """
    SELECT 
	"Age Group", 
	COUNT("Age Group"),
	AVG("Time") AS avg_finish_time
    FROM student.rw_parkrun_2
    GROUP BY "Age Group"
    """
    try:
        age_df = pd.read_sql(age_query, connection)
    except Exception as e:
        st.error(f"Error fetching data: {e}")
    
    event_count_query = """
    SELECT COUNT(*) AS total_events
    FROM(
	SELECT COUNT(*)
	FROM student.rw_parkrun_2
	GROUP BY "EventLongName")
    """
    try:
        event_count_df = pd.read_sql(event_count_query, connection)
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        
    pb_count_query = """
    SELECT COUNT(*) AS total_pbs
    FROM student.rw_parkrun_2
    WHERE "Achievement" = 'New PB!'
    """
    try:
        pb_count_df = pd.read_sql(pb_count_query, connection)
        #st.dataframe(pb_count_df)
    except Exception as e:
        st.error(f"Error fetching data: {e}")
    
    query = """
    SELECT 
    "EventLongName", 
    COUNT("Position") AS participant_count,
    "coordinates"
    FROM student.rw_parkrun_2
    GROUP BY "EventLongName", "coordinates";
    """
    try:
        df = pd.read_sql(query, connection)
        #st.dataframe(df.sort_values(by="participant_count", ascending=False).head(10))
    except Exception as e:
        st.error(f"Error fetching data: {e}")
else:
    st.error("Could not connect to the database.")

def format_number_with_commas(number):
    return f"{number:,}"

st.title("Welcome to :orange[Parkrunner]! 🏃")

col1, col2, col3 = st.columns([1, 3, 1])

# if event.selection.indices:
#     col1.metric("Finishers:", format_number_with_commas(int(participant_count_df.iloc[0,0])), border=True)
# else:
col1.metric(":orange[Finishers]", format_number_with_commas(int(participant_count_df.iloc[0,0])), border=True, help="Number of Parkrun finishers in the UK this week")
col1.metric(":orange[Locations]", format_number_with_commas(int(event_count_df.iloc[0,0])), border=True, help="Number of Parkrun events held in the UK this week")
col1.metric(":orange[Personal Bests]", format_number_with_commas(int(pb_count_df.iloc[0,0])), border=True, help="Number of Personal Best times achieved in the UK this week")
col1.metric(":orange[Earths circumnavigated]", round((int(participant_count_df.iloc[0,0]) * 5) / 40075, 1), border=True, help="Number of times Parkrunners collectively ran around the Earth this week")

# Chart setup
# Gender Chart
colour_scheme = alt.Scale(domain=["Male", "Female"], range=["#f54b42", "#f5bf36"])

gender_chart = alt.Chart(gender_df).mark_arc(innerRadius=30).encode(
    theta=alt.Theta(field="count", type="quantitative"),
    color=alt.Color(field="Gender", type="nominal", scale=colour_scheme),
    tooltip=[alt.Tooltip('Gender:N', title='Gender'),  
             alt.Tooltip('count:Q', title='Finishers')]  
).properties(
    title="Gender Breakdown",
    width=200, 
    height=200  
)
# Age Chart
age_groups = {
    '1': '10-19',
    '2': '20-29',
    '3': '30-39',
    '4': '40-49',
    '5': '50-59',
    '6': '60-69',
    '7': '70+',
    '8': '70+',
    '9': '70+'
}
def recategorize_age_group(age_group):
    if age_group[2] in age_groups:
        return age_groups[age_group[2]]
    else:
        return None  # Return None for categories that do not match

# Apply the function to the 'Age Group' column and create a new 'Category' column
age_df['Age Group'] = age_df['Age Group'].apply(recategorize_age_group)

# Drop rows where the 'Category' is None
age_df = age_df.dropna(subset=['Age Group'])
collapsed_age_df = age_df.groupby('Age Group').sum()

age_chart = alt.Chart(collapsed_age_df.reset_index()).mark_bar(color='orange').encode(
    x=alt.X('count:Q', title='Number of Finishers'),  # Quantitative count on the x-axis
    y=alt.Y('Age Group:N', title='Age Group', sort='descending'),  # Nominal age group on the y-axis
    tooltip=[alt.Tooltip('Age Group:N', title='Age Group'),  # Tooltip for Age Group
             alt.Tooltip('count:Q', title='Finishers')]  # Tooltip for Count
).properties(
    title="Age Breakdown",
    width=200,  # Set width of the chart
    height=300  # Set height of the chart
)

with col3:
    st.altair_chart(gender_chart, theme=None, use_container_width=True)
    st.altair_chart(age_chart, theme=None, use_container_width=True,)
## Map Setup

## Creates a "Fill_colour" column for the df for a colour scheme
min_count = df["participant_count"].min()
max_count = df["participant_count"].max()
df["normalised_count"] = (df["participant_count"] - min_count) / (max_count - min_count)
# Map the normalised values to RGB colours
def calculate_colour(value):
    r = int(255)
    g = int(255 * (1 - value))
    b = int(0)
    return [r, g, b]

df["fill_colour"] = df["normalised_count"].apply(calculate_colour)
# Drop the normalised_count column
df = df.drop(columns=["normalised_count"])

df["coordinates"] = df["coordinates"].apply(
    lambda x: list(map(float, re.findall(r"[-+]?\d*\.\d+|\d+", x))) if isinstance(x, str) else x
)

point_layer = pdk.Layer(
    "ScatterplotLayer",
    data=df,
    id="EventNameLong",
    get_position="coordinates",
    get_color="fill_colour",
    pickable=True,
    auto_highlight=True,
    get_radius="participant_count",
    radius_scale=6,
    opacity=0.5,
)

view_state = pdk.ViewState(
    latitude=53.56, longitude=-3.78, zoom=5, pitch=0, bearing=0,
)

chart = pdk.Deck(
    point_layer,
    initial_view_state=view_state,
    tooltip={"text": "{EventLongName}\nFinishers: {participant_count}"},
    width='100',
)

with col2:
    event = st.pydeck_chart(chart, on_select="rerun", selection_mode="multi-object")
    #st.write(event)
with st.expander(label="About:"):
    st.markdown(
        """
        Parkrunner is an app designed to deliver insights from Parkrun events across the UK. Data was obtained from https://www.parkrun.org.uk/
    """
    )
