"""
--------------------------------------------------------------------------------
Data Quality Checker for citizenM Events Data

This script is designed to perform data quality checks on citizenM events data from Google BigQuery.
It ensures that event names and screen have the correct naming conventions and are present in the data.
The script consists of four main functions, each responsible for a specific part of the
data quality checking process.

Functions:

1. get_whitelist():
    - This function fetches a list of event names or screen names that need to be checked
      on the naming convention.
    - The list is retrieved from a Google Spreadsheet, which acts as a
      whitelist for the naming conventions of the event and screen names.

2. query_data():
    - This function queries the citizenM events data from BigQuery.
    - It creates a whitelist table with columns for screens or events, as well
      as columns for different platforms (iOS and Android).
    - Joins the events data with this whitelist table and aggregates it by
      counting the occurrences of each name in the events data.
    - The resulting aggregated table helps identify how many times each name
      appears in the dataset. This table is written away in new dataset to keep
      track of historical data quality results.

3. handler():
    - Processes the aggregated data from the previous step, by checking if the count for
      any event or screen name is zero, indicating that a particular name is missing from the dataset.

4. send_alert():
    - Sends an alert to stakeholders if any discrepancies are found during the data quality check.
    - By doing this we notify the relevant team members about missing or incorrectly named
      events/screens, ensuring timely intervention.


This script can be scheduled to run periodically to maintain data integrity in the citizenM events dataset.
It helps to identify missing or incorrectly named events/screens, thereby ensuring that data is accurate and reliable for analysis.

In this script the following environment variables are used:
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
--------------------------------------------------------------------------------
"""
from google.oauth2.service_account import Credentials
from google.cloud import bigquery
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from flask import request, jsonify
from google.api_core.exceptions import (
    GoogleAPICallError,
    BadRequest,
    NotFound,
    Forbidden,
    InternalServerError,
    RetryError,
)
import functions_framework
import logging
import gspread
import os

#set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("data_quality_checker.log"),
        logging.StreamHandler()
    ]
)

load_dotenv()

try:
    client = bigquery.Client()
except GoogleAPICallError as e:
    logging.error(f"Failed to initialize BigQuery client: {e}")
    raise

#function to extract and return whitelist from Google sheets
#sheet_element tells the function to extract event names or screen names
def get_whitelist(sheet_element):
    try:
        #create a gspread instance for accessing Google Sheets
        credentials_file = os.getenv('CREDENTIALS')
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_file(credentials_file, scopes = scopes)
        client = gspread.authorize(creds)

        #get gspread link and open spreadsheet
        spreadsheet_url = os.getenv('GSPREAD')
        sheet = client.open_by_url(spreadsheet_url).sheet1

        #get whitelist consisting of events names or screen names
        if sheet_element == 'Events':
            data = sheet.col_values(col = 1)
        if sheet_element == 'Screens':
            data = sheet.col_values (col = 2)

        logging.info(f"Successfully fetched whitelist for {sheet_element}")
        return data

    except Exception as e:
        logging.error(f"Error fetching whitelist from Google Sheets: {e}")
        return []

# function that takes sheet_element and element to look at either events or screens.
def get_query_results(sheet_element, element):

    #create whitelist
    whitelist = get_whitelist(sheet_element = sheet_element)
    if not whitelist:
            logging.warning("Whitelist is empty. Skipping BigQuery execution.")
            return {}

    try:
        #query to get event_name
        if element == 'event_name':
            query_a = f"""
            with base as(
                SELECT
                    session.value.int_value as session_id,
                    {element},
                    platform
                FROM
                    {os.getenv('BIGQUERY_SOURCE')},
                    UNNEST(user_properties) AS Session
                WHERE
                    event_name IS NOT NULL
                    AND platform IN ('ANDROID', 'IOS')
                ),
                    """
        #query to get screen_name
        if element == 'screen_name':
            query_a = f"""
            with base as(
                SELECT
                    session.value.int_value as session_id,
                    Screen.value.string_value AS {element},
                    platform
                FROM
                    {os.getenv('BIGQUERY_SOURCE')},
                    UNNEST(user_properties) AS Session,
                    UNNEST(event_params) AS Screen
                WHERE
                    event_name = 'screen_view'
                    AND platform IN ('ANDROID', 'IOS')
                    AND Screen.key = "firebase_screen"
                    ),
                    """

        query_b = "whitelist AS ("

        #list for whitelist query parts
        query_parts = []

        #create and append whiteliste queryparts to list.
        for list_element in whitelist:
            for platform in ['IOS', 'ANDROID']:
                query_parts.append(f'SELECT "{list_element}" AS {element}, "{platform}" AS platform')

        #join all query parts from list
        query_b += " UNION ALL ".join(query_parts)
        query_b += ")"

        #query that joins whitelist and events data and aggergates by count
        query_c=f"""
        SELECT
        whitelist.{element},
        whitelist.platform,
        COUNT(base.session_id) as count,
        FROM
        whitelist
        LEFT JOIN base USING({element}, platform)
        GROUP BY ALL
    """

        #create one query with query a,b and c
        query = query_a + query_b + query_c

        #table to write away resulting aggregated table source
        target_table = os.getenv('BQTABLE_RESULTS_TARGET')

        #create destination table instance
        job_config = bigquery.QueryJobConfig(
        destination=target_table,
        write_disposition="WRITE_TRUNCATE",
        )

        #execute query with destination table
        query_job = client.query(query, job_config=job_config)
        rows = query_job.result()


        #create dictionary with results
        event = []
        platform = []
        count = []

        for row in rows:

            event.append(row[0])
            platform.append(row[1])
            count.append(row[2])
        print(len(event))

        dict = {
            'events' : event,
            'platform': platform,
            'count' : count,

        }

        #return dictionary
        return dict

    except (BadRequest, NotFound, Forbidden, InternalServerError, RetryError, GoogleAPICallError) as e:
        logging.error(f"An unexpected error occurred: {e}")
        raise




#send alerting if discrepancies are found
def send_alert(list_for_alerts, element):

    #load the token from an environment variable
    client = WebClient(token=os.getenv('SLACK_BOT_TOKEN'))

    channel_id = os.getenv('CHANNEL_ID')
    message = f"The following list with {element} names was not found in BQ", f"{list_for_alerts}"

    try:
        response = client.chat_postMessage(channel=channel_id, text=message)
        print(f"Message sent successfully: {response['message']['text']}")
    except SlackApiError as e:
        print(f"Error sending message: {e.response['error']}")




#main function that gets dictionary from query and checks counts by event or screen name with variables
#sheet_element and element
@functions_framework.http
def handler(request):
    sheet_list = ['Events', 'Screens']
    element_list = ['event_name', 'screen_name']
    missing_events = []
    missing_screens = []
    try:
        for i in range(len(sheet_list)):

            sheet_element = sheet_list[i]
            element = element_list[i]
            dict_to_check = get_query_results(sheet_element, element)
            if not dict_to_check:
                logging.warning("No data to process.")
                response = {
                'status': 'warning',
                'message': f'No items were found in dictionary for {element}',

                }
                return jsonify(response), 404

            list_to_check = dict_to_check.get('count', [])
            missing_names = []

            for idx, value in enumerate(list_to_check):
                if value == 0:
                    coresp_event = dict_to_check['events'][idx]
                    coresp_platform = dict_to_check['platform'][idx]
                    missing_names.append((coresp_event, coresp_platform))


            if missing_names:
                logging.info(f"Missing names were found: {missing_names}")


                if element == 'event_name':
                    missing_events = missing_names
                    # send_alert(missing_events, element)
                if element == 'screen_name':
                    missing_screens = missing_names
                    # send_alert(missing_screens, element)

                response = {
                'status': 'success',
                'message': f'Missing names were found from {element} list',
                'missing_elements': f'Missing events are: {missing_events} and missing screens are: {missing_screens}'
                }

            else:
                logging.info(f"No missing {element} names detected.")
                response = {
                'status': 'success',
                'message': f'No missing names were found from {element} list',
                'missing_names': f'{missing_names}'
                }

        return jsonify(response), 200


    except Exception as e:
        logging.error(f"Error in handler function: {e}")
        response = {
            'status': 'error',
            'message': f'an unexpected error occured: {e}'
        }
        return jsonify(response), 500
