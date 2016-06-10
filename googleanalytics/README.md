# Google Anayltics Pack

## Description:
Uses a Google Analytics service account to grab Google Analytics metrics via the Google Analytics API. 
You can specify multiple web properties and for each, the following metrics are returned by default
for today's date:

* Total Users (Unique Visitors)
* Total New Users (Unique New Visitors)
* Total Percent New Sessions (%)
* Total Sessions
* Average Session Duration (secs)
* Bounce Rate (%)
* Average Page Load Time (secs)

It intended as a starter plugin to be edited to read any metrics you want from Google Analytics into Dataloop.IO. See
Editing section below for more details on what metrics are available.

_NOTE: FOR NOW PLEASE CHANGE PLUGIN INTERVAL TO 1HR IN PLUGIN SETTINGS PAGE_
This will ensure you don't max out your API usage limits on Google Analytics

## Setup:

You will need to create a Service account that has permissions to access the Google Analytics APIs securely:

1. Login to Google's Developer Console: https://cloud.google.com/console/project
2. Create a new project that has 'Analytics API' enabled
3. Under 'Explore other Services' on the project dashboard, select 'Enable APIs and get credentials like keys' and select 'Credentials' in the left menu
4. Click the 'Create credentials' button, and select 'Service account key'
5. Select the account you want to get a key for or create a new one. Ensure key type is JSON
6. Download the JSON file and get the following details to edit the following variables at the top of the googleanalytics.py plugin:
    1. SERVICE_ACCOUNT_EMAIL: Copy and paste the email address (e.g. 123456789-....@developer.gserviceaccount.com)
    2. OAUTH2_PRIVATE_KEY: Copy and paste the private key found in the downloaded JSON file beginning with "-----BEGIN PRIVATE KEY-----" and ending with "-----END PRIVATE KEY-----\n"
    3. PROFILES: List all the website UA- profile ids with a memorable name so your metrics are segmented by profile in Dataloop
7. Add the email address to your Google Analytics users under Admin->Account->User Management with 'Read & Analyse' permissions. It may take a few minutes until the user is enabled

## Editing:

To add additional metrics from Google Analytics refer to this page on list of available metrics:

https://developers.google.com/analytics/devguides/reporting/core/dimsmets

As this pack / plugin does remote polling you should only assign the googleanalytics tag to a single agent responsible for
monitoring Google Analytics. A good one to use is the `dataloop` agent.