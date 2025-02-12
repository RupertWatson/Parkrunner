# Parkrunner Data Pipeline Project

## Streamlit Preview

<p float="left">
  <img src="/images/preview_1.png" width="600" />
  <img src="/images/preview_2.png" width="600" /> 
</p>
<p float="left">
  <img src="/images/preview_3.png" width="600" />
  <img src="/images/preview_4.png" width="600" /> 
</p>

## Extraction Script Instructions

1. **Environment Setup**  
   An `.env` file must be included in the project root with the following variables:
   - `DB_HOST`
   - `DB_PORT`
   - `DB_USER`
   - `DB_PASSWORD`
   - `DB_NAME`

2. **Dependency Installation**  
   Ensure all necessary packages are installed by running:
   pip install -r requirements.txt
   
3. **Data Extraction and Insertion**  
   Run the extraction script using:

   `python runETL.py`

   The script will:
    Get a list of all UK parkrun events.
    Request the url from each event's most recent result page.
    Etract and store the result data from each event.
    Transform the results into a DataFrame
    Insert the cleaned data into the Pagilla database.

## Cron Details

The extraction script should be scheduled to run **weekly on a weekday**(e.g. Every Monday at 10 PM GMT). 
The extraction process should take between **2-4 hours**, due to request delays to reduce server load.
Please do not run the script on weekends.
