import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
from utils.db_connection import get_db_connection 
import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import re

st.title("Leaderboards 🏆")
tab1, tab2 = st.tabs(["Event Leaderboard", "Individual Leaderboard"])

with st.spinner("Loading results..."):
    # Connect to the database
    connection = get_db_connection()

    if connection:
        query = """
        SELECT 
        "Time" AS finish_time,
        "EventLongName",
        "Age Group",
        "Runs"
        FROM student.rw_parkrun_2
        ORDER BY finish_time ASC;
        """
        try:
            leaderboard_df = pd.read_sql(query, connection)
        except Exception as e:
            st.error(f"Error fetching data: {e}")
        query = """
        SELECT 
        "EventLongName", 
        COUNT("Position") AS participant_count,
        AVG("Time") AS avg_finish_time,
        ROUND(AVG("Runs"),1) AS avg_num_of_runs,
        COUNT(CASE WHEN "Achievement" = 'New PB!' THEN 1 END) AS pb_count,
        ROUND((COUNT(CASE WHEN "Achievement" = 'New PB!' THEN 1 END) * 100.0 / COUNT("Position")),1) AS percent_pb,
        COUNT(CASE WHEN "Achievement" = 'First Timer!' THEN 1 END) AS first_time_count,
        ROUND((COUNT(CASE WHEN "Achievement" = 'First Timer!' THEN 1 END) * 100.0 / COUNT('First Timer!')),1) AS first_time_percent
        FROM student.rw_parkrun_2
        GROUP BY "EventLongName"
        ORDER BY participant_count DESC;
        """
        try:
            event_df = pd.read_sql(query, connection)
        except Exception as e:
            st.error(f"Error fetching data: {e}")
    else:
        st.error("Could not connect to the database.")    
        

    leaderboard_df["finish_time"] = pd.to_timedelta(leaderboard_df["finish_time"])
    leaderboard_df["finish_time"] = leaderboard_df["finish_time"].apply(
        lambda x: f"{int(x.total_seconds() // 3600):02}:{int((x.total_seconds() % 3600) // 60):02}:{int(x.total_seconds() % 60):02}"
    )
    event_df["avg_finish_time"] = pd.to_timedelta(event_df["avg_finish_time"])
    event_df["avg_finish_time"] = event_df["avg_finish_time"].apply(
        lambda x: f"{int(x.total_seconds() // 3600):02}:{int((x.total_seconds() % 3600) // 60):02}:{int(x.total_seconds() % 60):02}"
    )

    leaderboard_df.index += 1
    leaderboard_df.index.name = "Overall Position"
    leaderboard_df = leaderboard_df.reset_index()
    leaderboard_df = leaderboard_df.rename(columns={
        'EventLongName': 'Location',
        'finish_time': 'Finish Time',
        'runs':'Number of Runs'
    })

    # Filter and rename columns
    filtered_event_df = event_df[['EventLongName', 'participant_count', 'avg_finish_time', 'percent_pb', 'first_time_percent','avg_num_of_runs']]
    filtered_event_df = filtered_event_df.rename(columns={
        'EventLongName': 'Location',
        'participant_count': 'Number of Finishers',
        'avg_finish_time': 'Average Finish Time',
        'percent_pb': 'Personal best %',
        'first_time_percent': 'First Timer %',
        'avg_num_of_runs':'Average Number of Runs'
    })

    def extract_first_number_and_letter(age_group):
        match = re.match(r"([A-Za-z]+)(\d+)-", age_group)
        if match:
            return (int(match.group(2)), match.group(1))  # First number as integer, then letter prefix
        return (float('inf'), "")  # In case of an invalid format, put it at the end

    with tab1:
        st.header("Event Leaderboard")
        # Sorting popover
        with st.popover("Sort Leaderboard 🏅"):
            sort_option = st.radio(
                "Sort by:",
                ["Number of Finishers","Average Finish Time",  "Personal best %", 'First Timer %', 'Average Number of Runs'],
                index=0
            )
        # Sort DataFrame based on selected column
        if sort_option == "Average Finish Time":
            filtered_event_df = filtered_event_df.sort_values(by=sort_option, ascending=True).reset_index(drop=True)
        else:
            filtered_event_df = filtered_event_df.sort_values(by=sort_option, ascending=False).reset_index(drop=True)

        # Recalculate position after sorting
        filtered_event_df["Position"] = range(1, len(filtered_event_df) + 1)
        cols = ["Position"] + [col for col in filtered_event_df.columns if col != "Position"]
        filtered_event_df = filtered_event_df[cols]
        
        # Allow you to find your event in the leaderboard
        selected_location = st.selectbox("Or find a :orange[Parkrun] from the list:", filtered_event_df["Location"].tolist(), index=None, placeholder="Select Parkrun",)
        if selected_location:
            filtered_event_df = filtered_event_df[filtered_event_df["Location"] == selected_location]
    
        st.dataframe(filtered_event_df, use_container_width=True, hide_index=True)

        # st.scatter_chart(
        #     filtered_event_df,
        #     x="Personal best %",
        #     y='Average Number of Runs',
        #     size="Number of Finishers",
        # )   
        
    with tab2:
        
        # Add a dropdown to filter by Age Group
        st.header("Individual Leaderboard (Top 100)")
        age_group_filter = st.selectbox(
            "Filter By Age Group:",
            options=["All"] + sorted(leaderboard_df["Age Group"].unique().tolist(), key=extract_first_number_and_letter),
            index=0,
        )
        # Filter the DataFrame based on the selected Age Group
        if age_group_filter != "All":
            filtered_df = leaderboard_df[leaderboard_df["Age Group"] == age_group_filter]
        else:
            filtered_df = leaderboard_df 
        st.dataframe(filtered_df.head(100), use_container_width=True, hide_index=True)

        with st.expander(label="Show Distribution Plot"):
            # Convert the "finish_time" column to timedelta
            filtered_df["Finish Time"] = pd.to_timedelta(filtered_df["Finish Time"])
            # Now convert to seconds and then to minutes
            filtered_df["finish_time_minutes"] = filtered_df["Finish Time"].dt.total_seconds() / 60
            # Matplotlib Seaborn Plot
            plt.figure(figsize=(3, 3))
            sns.displot(filtered_df["finish_time_minutes"], color="orange", kind="hist", fill="true", height=2, aspect=2)
            # Customizing the plot
            plt.title("Distribution of Finish Times (in Minutes)", fontsize=16)
            plt.xlabel("Finish Time (Minutes)", fontsize=12)
            plt.ylabel("# of Finishers", fontsize=12)
            plt.xlim(left=0)
            plt.xlim(right=80)
            plt.xticks([0, 10, 20, 30,40,50,60,70,80])
            st.pyplot(plt, use_container_width=False)
