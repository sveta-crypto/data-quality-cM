# Data Quality Checker for citizenM Events Data
## Overview

This project is designed to perform data quality checks on the citizenM events data stored in Google BigQuery. The script ensures that event names and screen names follow the correct naming conventions by comparing them against a predefined whitelist fetched from a Google Spreadsheet.

### key features: 
- Google BigQuery Integration: To Query event data from BigQuery and aggregates data to generate reports on missing or incorrectly named events/screens.
- Google Sheets Integration: Fetches a whitelist of event names and screen names.
- Slack Integration: Sends alerts via Slack if discrepancies are found in the data.



## Function Overview

1. get_whitelist(sheet_element)
- Purpose: Fetches a list of event or screen names from Google Sheets.
- Parameters: sheet_element (either 'Events' or 'Screens').
- Returns: A list of names from the specified column.
2. get_query_results(sheet_element, element)
- Purpose: Queries citizenM events data from BigQuery and aggregates results.
- Parameters:
  sheet_element ('Events' or 'Screens')
  element ('event_name' or 'screen_name')
- Returns: A dictionary with event names, platforms, and their counts.
3. send_alert(list_for_alerts, element)
- Purpose: Sends a Slack message if discrepancies are found.
- Parameters:
  list_for_alerts: List of missing names.
  element: Indicates whether it's for event names or screen names.
4. handler(sheet_element, element)
- Purpose: Main function that checks data quality by combining all the above functions.
- Parameters:
  sheet_element: 'Events' or 'Screens'
  element: 'event_name' or 'screen_name'

### Running the script locally
To run script use a service account from google cloud that has access to bigquery and make sure environment variables are added with following:
- CREDENTIALS contains the following information: {
    "type": 'service_account'
    "project_id": 'BQ_PROJECT_ID'
    "private_key_id": 'some number'
    "private_key": 'some key'
    "client_email": 'service account email'
    "client_id": 'some number'
    "auth_uri": 'auth link'
    "token_uri": 'token link'
    "auth_provider_x509_cert_url": 'link'
    "client_x509_cert_url": 'link'
    "universe_domain": "googleapis.com"
    }

- GSPREAD contains the link to the google spreadsheet for example: 'https://docs.google.com/spreadsheets/d/...'
- BIGQUERY_SOURCE contains the pathway to the bigquery events table for example: 'PROJECT_ID.DATASET_ID.TABLE_ID'
- BIGQUERY_RESULTS_TARGET contains the target table to write results to for example: 'PROJECT_ID.DATASET_ID.TABLE_ID'
- SLACK_BOT_TOKEN contains the token to access slack
- CHANNEL_ID contains to id to access channel within slack
  
1. install the following packages
   ```
    $ pip install -r requirements.txt

2. run the function
   
   ```
     $ functions-framework --target=handler
   ```
