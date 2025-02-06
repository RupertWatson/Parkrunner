import streamlit as st
import pandas as pd

st.title("Planning and Development 🛠️")
st.divider()
st.markdown("## Project Brief")
st.markdown('''
           The goal of this project is to provide national level insights into UK-based Parkrun results. Parkrun is a :orange[weekly 5km run] held every Saturday in :orange[over 800 locations] across the UK, focused on strengthening local communities and inclusivity. While individual event results are available on the [Parkrun website](https://www.parkrun.org.uk/), there is no easy way to view and compare results across multiple locations.

This project involved building an ETL pipeline to extract data from the Parkrun website on a weekly schedule and generate visualisations in Streamlit. The application will highlight the :orange[fastest times of the week], compare local Parkrun stats to :orange[national averages], and analyse demographics such as :orange[age distributions].            ''')
st.divider()
st.markdown('''
            ## Project Scope

- Each week, obtain only the ***most recent*** parkrun results for each location.
- Only obtain data for Parkrun events within the ***U.K***. 

''')
st.divider()
st.markdown("## Data Flow Diagram")
st.image('flowchartlr.png')
st.divider()
st.markdown('''
## Project Backlog

- [X] Get a list of all Parkrun events within the UK
- [X] Scrape the results from all UK parkruns
- [X] Clean the results
- [X] Transform the results
- [X] Load the data into Pagilla Database
- [X] Build a Streamlit Application to make visualisations
- [ ] Deploy the pipeline, updating the dataset on a weekly basis
'''
)
st.divider()
st.markdown('''
## Ethical Considerations Concerning Webscraping

I researched how I could obtain the Parkrun data. Unfortunately, there is no publicly available Parkrun API, so I opted to scrape the data from their website. To ensure ethical use of their data, I adhered to the following practices:

1. Ensure that requests are not made during peak times.
2. Add a wait time between requests.
3. Only extract publicly accessible data.
4. Do not use the data for personal monetary gain.
5. If I was to expand on and update this project further, I would contact the Parkrun administrators for guidance.
            ''')
st.divider()
st.markdown('''
## Challenges
- Webscraping was difficult due to inconsistencies between result tables and handling missing data.
- Difficulty when running the ETL process from a cloud VM
            ''')
st.divider()
st.markdown('''
## Possible next steps
- Include data from other countries
- Add historical results to compare trends 
            ''')
