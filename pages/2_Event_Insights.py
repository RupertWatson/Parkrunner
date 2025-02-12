import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
#from utils.db_connection import get_db_connection
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from sqlalchemy import create_engine

def get_db_connection():
    """
    Establish and return a connection to the PostgreSQL database.
    """
    # Define the connection details
    hostname=st.secrets["DB_HOST"],
    port=int(st.secrets["DB_PORT"]),
    database=st.secrets["DB_NAME"],
    username=st.secrets["DB_USER"],
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

st.title("Event Insights 📊")

selected_location = st.selectbox("Select a :orange[Parkrun] from the list:", filtered_event_df["Location"].tolist(), index=None, placeholder="Select Parkrun",)

# Insights
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
            national_df = pd.read_sql(query, connection)
        except Exception as e:
            st.error(f"Error fetching data: {e}")
        selected_parkrun_query = """
        SELECT 
        "Time" AS finish_time,
        "Age Group",
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
        national_df["finish_time"] = pd.to_timedelta(national_df["finish_time"])
        selected_parkrun_df["finish_time"] = pd.to_timedelta(selected_parkrun_df["finish_time"])
        
        selected_parkrun = str(selected_location)
        avg_finish_time = selected_parkrun_df["finish_time"].mean()
        national_avg = national_df["finish_time"].mean()
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
        national_df["finish_time_minutes"] = national_df["finish_time"].dt.total_seconds() / 60
        selected_parkrun_df["finish_time_minutes"] = selected_parkrun_df["finish_time"].dt.total_seconds() / 60
        
        plt.figure(figsize=(6, 3))  # Adjust the figure size for both datasets
        sns.kdeplot(national_df["finish_time_minutes"], color="orange",bw_adjust=.2, fill=True, label="National Average")
        sns.kdeplot(selected_parkrun_df["finish_time_minutes"], color="red",bw_adjust=.4, fill=True, label=selected_location)
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
    
    with tab2:
        # Display demographic info
        # Get Age group data for selected parkrun
        national_df["New Age Group"] = national_df['Age Group'].apply(recategorize_age_group)
        total_count = len(national_df)
        age_group_summary_uk = national_df["New Age Group"].value_counts().reset_index()
        age_group_summary_uk.columns = ["New Age Group", 'Count UK']
        age_group_summary_uk['National'] = (age_group_summary_uk['Count UK'] / total_count) 
        
        # Calculate average finish_time for each New Age Group
        avg_finish_time_uk = national_df.groupby("New Age Group")["finish_time"].mean().reset_index()
        avg_finish_time_uk.columns = ["New Age Group", "National Average"]

        # Merge the average finish time into the summary dataframe
        age_group_summary_uk = pd.merge(age_group_summary_uk, avg_finish_time_uk, on="New Age Group", how="left")
        
        selected_parkrun_df["New Age Group"] = selected_parkrun_df['Age Group'].apply(recategorize_age_group)
        total_count = len(selected_parkrun_df)
        age_group_summary = selected_parkrun_df["New Age Group"].value_counts().reset_index()
        age_group_summary.columns = ["New Age Group", 'Count']
        age_group_summary['Local'] = (age_group_summary['Count'] / total_count)
        
        # Calculate average finish_time for each New Age Group
        avg_finish_time = selected_parkrun_df.groupby("New Age Group")["finish_time"].mean().reset_index()
        avg_finish_time.columns = ["New Age Group", "Local Average"]

        # Merge the average finish time into the summary dataframe
        age_group_summary = pd.merge(age_group_summary, avg_finish_time, on="New Age Group", how="left")
    
        age_merged = pd.merge(age_group_summary_uk, age_group_summary, on="New Age Group", how="left")
        age_merged = age_merged.sort_values(by="New Age Group")
        
        age_merged["National Average"] = age_merged["National Average"].dt.total_seconds() / 60
        age_merged["Local Average"] = age_merged["Local Average"].dt.total_seconds() / 60
        
        #st.dataframe(age_merged)
        
        age_merged['Local'] = -age_merged['Local']
        # Create pyramid chart
        fig = px.bar(
            age_merged,
            y='New Age Group',
            x=['National', 'Local'],
            orientation='h',
            #labels={'National':{selected_parkrun}, 'New Age Group': 'Age Group', 'value': 'Percentage (%)'},
            title=f"Age Group Distribution for {selected_parkrun} vs UK Average",
            barmode='relative',
            color_discrete_map={'National': 'orange', 'Local': 'tomato'} 
        )

        # Update the layout to properly format the x-axis
        fig.update_layout(
            xaxis=dict(
                tickformat=".0%", 
                title="Age Group Proportion (%)",
                showgrid=True,
                tickmode='array',  
                tickvals=[-1, -0.9, -0.8, -0.7, -0.6, -0.5, -0.4, -0.3, -0.2, -0.1, 0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1], 
                ticktext=['100%', '90%', '80%', '70%', '60%', '50%', '40%', '30%', '20%', '10%', '0%', '10%', '20%', '30%', '40%', '50%', '60%', '70%', '80%', '90%', '100%']
            ),
            yaxis=dict(
                title="Age Group",
            ),
            bargap=0.1, 
            legend_title='Legend',
        )
        fig.update_traces(
            hovertemplate='<b>%{y}</b><br>' +  # Show Age Group
                            'Fraction: %{x:.2f}<br>'
        )
        
        # Age Speed chart
        fig2 = px.bar(
            age_merged,
            x='New Age Group',
            y=['Local Average', 'National Average'],
            title=f"Average Finish Time Comparison by Age Group for {selected_parkrun} vs UK Average",
            #labels={'New Age Group': 'Age Group', 'value': 'Average Finish Time'},
            color_discrete_map={'National Average': 'orange', 'Local Average': 'tomato'},
            barmode='group',
        )
        fig2.update_layout(
            xaxis=dict(
                title="Age Group",
            ),
            yaxis={'title': 'Average Finish Time (minutes)'},
            legend_title='Legend'
        )
        fig2.update_traces(
            hovertemplate='<b>%{x}</b><br>' +  # Show Age Group
                            'Average: %{y:.1f} mins<br>'
        )
        # Display charts in Streamlit
        st.plotly_chart(fig) 
        st.plotly_chart(fig2)
        
#else:
    #with tab1:
        #st.info("Please select a Parkrun above.", icon="ℹ️")
    #with tab2:
        #st.info("Please select a Parkrun above.", icon="ℹ️")