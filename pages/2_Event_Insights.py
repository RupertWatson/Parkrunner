import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
from utils.db_connection import get_db_connection
import matplotlib.pyplot as plt
import seaborn as sns

# Connect to the database
connection = get_db_connection()

if connection:
    event_query = """
    SELECT 
    "EventLongName", 
    COUNT("Position") AS participant_count,
    AVG("Time") AS avg_finish_time,
    ROUND(AVG("Runs"),1) AS avg_num_of_runs
    FROM student.rw_parkrun_2
    GROUP BY "EventLongName"
    ORDER BY "EventLongName" ASC;
    """
    try:
        event_df = pd.read_sql(event_query, connection)
    except Exception as e:
        st.error(f"Error fetching data: {e}")
else:
    st.error("Could not connect to the database.")  

# Filter and rename columns
filtered_event_df = event_df.rename(columns={
    'EventLongName': 'Location',
    'participant_count': '# Finishers',
    'avg_finish_time': 'Average Finish Time',
    'percent_pb': '% pb',
    'first_time_percent': 'First Timer %'
})

st.title("Local Insights 📊")

# Search and selection
col1, col2 = st.columns([1,1]) 
with col1:
    #st.markdown("Search for a :orange[Parkrun] location:")
    search_query = st.text_input("Search for a :orange[Parkrun] location:", "")
    # Apply search filter if the user types something
    if search_query:
        filtered_event_df = filtered_event_df[filtered_event_df["Location"].str.contains(search_query, case=False, na=False)]

with col2:
    #st.markdown("Or select a :orange[Parkrun] from the list:")
    selected_location = st.selectbox("Then select a :orange[Parkrun] from the list:", filtered_event_df["Location"].tolist(), index=None,
    placeholder="Select Parkrun",)

# Insights
if selected_location:
    selection_string = f"You have selected :orange[{selected_location}]."
    st.markdown(selection_string)
tab1, tab2 = st.tabs(["Pace Comparison", "Demographics"])
# st.dataframe(filtered_event_df, use_container_width=True, hide_index=True)

if selected_location:
    if connection:
        query = """
        SELECT 
        "Time" AS finish_time,
        "EventLongName",
        "Age Group"
        FROM student.rw_parkrun_2
        ORDER BY finish_time ASC;
        """
        try:
            leaderboard_df = pd.read_sql(query, connection)
        except Exception as e:
            st.error(f"Error fetching data: {e}")
        selected_parkrun_query = """
        SELECT 
        "Time" AS finish_time,
        "EventLongName"
        FROM student.rw_parkrun_2
        WHERE "EventLongName" LIKE %s
        ORDER BY finish_time ASC;
        """
        try:
            # Ensure the selected_parkrun variable is defined
            selection_sql = f"%{selected_location}%"
            # Fetch the data with the parameterized query
            selected_parkrun_df = pd.read_sql(selected_parkrun_query, connection, params=(selection_sql,))
        except Exception as e:
            st.error(f"Error fetching data: {e}")
    else:
        st.error("Could not connect to the database.")  


    with tab1:
        # Convert the "finish_time" column to timedelta
        leaderboard_df["finish_time"] = pd.to_timedelta(leaderboard_df["finish_time"])
        selected_parkrun_df["finish_time"] = pd.to_timedelta(selected_parkrun_df["finish_time"])
        
        selected_parkrun = str(selected_location)
        avg_finish_time = selected_parkrun_df["finish_time"].mean()
        national_avg = leaderboard_df["finish_time"].mean()
        diff = national_avg - avg_finish_time
        # Convert timedelta to total seconds
        avg_finish_time_seconds = avg_finish_time.total_seconds()
        national_avg_seconds = national_avg.total_seconds()
        diff_s = diff.total_seconds()
        # Format as minutes and seconds
        selected_avg_formatted = f"{int(avg_finish_time_seconds // 60)}:{int(avg_finish_time_seconds % 60):02d}"
        diff_formatted = f"{int(abs(diff_s) // 60)}:{int(abs(diff_s) % 60):02d}"  # Absolute value to avoid negative time display

        faster_or_slower = "faster" if diff_s >= 0 else "slower"
        pace_comp_text = f"- :orange[{selected_parkrun}'s] average finish time is :orange-background[{selected_avg_formatted}], which is :orange-background[{diff_formatted}] {faster_or_slower} than the national average."
        st.markdown(pace_comp_text)
        
        national_completions = int(event_df["participant_count"].mean())
        selected_completions = selected_parkrun_df["finish_time"].count()
        diff_comps = selected_completions - national_completions
        more_less = "more" if diff_comps >= 0 else "less"
        finishers_text = f"- There were :orange-background[{selected_completions}] finishers this week, :orange-background[{abs(diff_comps)}] {more_less} than the national parkrun average."
        st.markdown(finishers_text)
        
        # Now convert to seconds and then to minutes
        leaderboard_df["finish_time_minutes"] = leaderboard_df["finish_time"].dt.total_seconds() / 60
        selected_parkrun_df["finish_time_minutes"] = selected_parkrun_df["finish_time"].dt.total_seconds() / 60
        
        plt.figure(figsize=(6, 3))  # Adjust the figure size for both datasets
        sns.kdeplot(leaderboard_df["finish_time_minutes"], color="orange", fill=True, label="National Average")
        sns.kdeplot(selected_parkrun_df["finish_time_minutes"], color="red", fill=True, label=selected_location)
        # Customizing the plot
        plt.title("Distribution of Finish Times (in Minutes)", fontsize=16)
        plt.xlabel("Finish Time (Minutes)", fontsize=12)
        plt.ylabel("Density", fontsize=12)
        plt.xlim(left=0)
        plt.xlim(right=80)  # Limit the x-axis to 80 minutes
        # Add a legend
        plt.legend()
        # Display the plot in Streamlit
        st.pyplot(plt, use_container_width=False)
    
    # with tab2:
    # Display demographic info
    # Get Age group data for selected parkrun
else:
    with tab1:
        st.write("Please select a Parkrun above.")
    with tab2:
        st.write("Please select a Parkrun above.")