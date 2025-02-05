import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
from utils.db_connection import get_db_connection 
import ast
import altair as alt
import re

st.set_page_config(
    page_title="Parkrunner",
    page_icon="👋",
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

st.title("Welcome to :orange[Parkrunner] UK! 🏃")

col1, col2, col3 = st.columns([1, 3, 1])

# if event.selection.indices:
#     col1.metric("Finishers:", format_number_with_commas(int(participant_count_df.iloc[0,0])), border=True)
# else:
col1.metric("Finishers", format_number_with_commas(int(participant_count_df.iloc[0,0])), border=True)

col1.metric("Locations", format_number_with_commas(int(event_count_df.iloc[0,0])), border=True)
col1.metric("Personal Bests", format_number_with_commas(int(pb_count_df.iloc[0,0])), border=True)
col1.metric("Earths circumnavigated", round((int(participant_count_df.iloc[0,0]) * 5) / 40075, 1), border=True)

# Chart setup
# Gender Chart
colour_scheme = alt.Scale(domain=["Male", "Female"], range=["#1f77b4", "#ff70ec"])

gender_chart = alt.Chart(gender_df).mark_arc(innerRadius=30).encode(
    theta=alt.Theta(field="count", type="quantitative"),
    color=alt.Color(field="Gender", type="nominal", scale=colour_scheme),
).properties(
    width=200,  # Increase chart width
    height=200  # Increase chart height
)
# Age Chart

# Function to recategorize age groups into Junior, Senior, or Veteran
def recategorize_age_group(age_group):
    if age_group[0] == 'J':
        return 'Junior (10-17)'
    elif age_group[0] == 'S':
        return 'Senior (18-34)'
    elif age_group[0] == 'V':
        return 'Veteran (35+)'
    else:
        return None  # Return None for categories that do not match J, S, or V

# Apply the function to the 'Age Group' column and create a new 'Category' column
age_df['Age Group'] = age_df['Age Group'].apply(recategorize_age_group)

# Drop rows where the 'Category' is None
age_df = age_df.dropna(subset=['Age Group'])
collapsed_age_df = age_df.groupby('Age Group').sum()

age_chart = alt.Chart(collapsed_age_df.reset_index()).mark_arc(innerRadius=30).encode(
    theta=alt.Theta(field="count", type="quantitative"),
    color=alt.Color(field="Age Group", type="nominal"),
    tooltip=[alt.Tooltip('Age Group:N', title='Age Group'),
             alt.Tooltip('count:Q', title='Count')]
).properties(
    width=200,  # Increase chart width
    height=200  # Increase chart height
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
