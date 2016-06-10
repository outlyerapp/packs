#!/usr/bin/env python

import httplib2
import time
import traceback
from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.client import SignedJwtAssertionCredentials
from oauth2client.client import AccessTokenRefreshError

"""
Google Analytics Plugin

Please refer to the README.md for instructions on setting up a Service Account to access the API and how to edit the
plugin for additional metrics

"""

# Set Variables to access Google Analytics

# Service Account Email address given in Google Developer Console
SERVICE_ACCOUNT_EMAIL = "......@developer.gserviceaccount.com"
# Cut and paste your private key here
OAUTH2_PRIVATE_KEY = "-----BEGIN PRIVATE KEY-----\n............\n-----END PRIVATE KEY-----\n"
# Profile IDs - dictionary of profile IDs of each of the web properties you want to query beginning with UA-
PROFILES = { "profile1": "UA-XXXXXXXX-1", "profile2": "UA-XXXXXXXX-2" }

# Main method
def main():

    metrics = {}

    try:

        # Initialise API client
        service = _get_ga_service()

        # Get today's date, must be in YYYY-MM-DD Format
        todaysDate = time.strftime("%Y-%m-%d")

        for profile in PROFILES:

            # Get internal system profile ID from UA-... ID
            profileId = _get_profile_id(service, PROFILES[profile])

            # Exit if no valid profileId found
            if profileId is None:
                print 'No valid profile was found for ' + PROFILES[profile] + '. Exiting.'
                exit(2)

            '''
                CUSTOMISE METRICS HERE
            '''

            metrics["users." + profile] = get_total_metric(service, profileId, todaysDate, todaysDate, 'ga:users')
            metrics["newusers." + profile] = get_total_metric(service, profileId, todaysDate, todaysDate, 'ga:newUsers')
            metrics["percentNewSessions." + profile] = str(round(float(get_total_metric(service, profileId, todaysDate, todaysDate, 'ga:percentNewSessions')),2)) + "%"
            metrics["sessions." + profile] = get_total_metric(service, profileId, todaysDate, todaysDate, 'ga:sessions')
            metrics["avgSessionDuration." + profile] = str(round(float(get_total_metric(service, profileId, todaysDate, todaysDate, 'ga:avgSessionDuration')),0)) + "s"
            metrics["bounceRate." + profile] = str(round(float(get_total_metric(service, profileId, todaysDate, todaysDate, 'ga:bounceRate')),2)) + "%"
            metrics["avgPageLoadTime." + profile] = get_total_metric(service, profileId, todaysDate, todaysDate, 'ga:avgPageLoadTime') + "s"

            '''
                / CUSTOMISE METRICS HERE
            '''

        print_output(metrics)

    except TypeError, error:
        # Handle errors in constructing a query.
        print 'There was an error in constructing your query : %s' % error
        traceback.print_exc()
        exit(2)

    except HttpError, error:
        # Handle API errors.
        print 'Arg, there was an API error : %s : %s' % (error.resp.status, error._get_reason())
        traceback.print_exc()
        exit(2)

    except AccessTokenRefreshError:
        # Handle Auth errors.
        print 'The credentials have been revoked or expired, ' \
              'please check your private key file and SERVICE_ACCOUNT_EMAIL are valid'
        traceback.print_exc()
        exit(2)

    except IOError, error:
        # Handle file system errors
        print 'There was an error opening a file: %s' % error
        traceback.print_exc()
        exit(2)

# Helper method to get a total metric value for a given metric from API with optional filters
def get_total_metric(service, profileId, start_date, end_date, metric, filters=None):

    if filters is not None:
        return service.data().ga().get(
            ids='ga:' + profileId,
            start_date=start_date,
            end_date=end_date,
            filters=filters,
            metrics=metric).execute().get('totalsForAllResults').get(metric)
    else:
        return service.data().ga().get(
            ids='ga:' + profileId,
            start_date=start_date,
            end_date=end_date,
            metrics=metric).execute().get('totalsForAllResults').get(metric)

# Initialises and gets a new authorised service object to access the GA APIs
def _get_ga_service():

    # Create the JWT
    credentials = SignedJwtAssertionCredentials(
        SERVICE_ACCOUNT_EMAIL, OAUTH2_PRIVATE_KEY,
        scope="https://www.googleapis.com/auth/analytics.readonly"
    )

    # Create an authorized http instance
    http = httplib2.Http()
    http = credentials.authorize(http)

    # Create a service call to the calendar API
    service = build("analytics", "v3", http=http)

    return service


# Utility method to get the system profile ID for a property given the UA-.... ID
# Will return None if not found
def _get_profile_id(service, profileId):

    # Get list of accounts and iterate till we find UA-... profile ID
    webProperties = service.management().webproperties().list(accountId='~all').execute()

    if webProperties.get('items'):

        # Iterate through all web properties until match with 'id' field, return system 'defaultProfileId'
        for profile in webProperties.get('items'):
            id = profile.get('id')
            if id == profileId:
                return profile.get('defaultProfileId')

        # Didn't find the profile ID
        print 'Profile ID ' + "'" + profileId + "'" + ' was not found for your Account.'
        return None

    else:
        # The account has no web properties
        print 'No Web Properties found for Service User Account. Check Service Account has permissions to access web properties.'
        return None

# Print collected metrics in Nagios STDOUT Format and exit cleanly (Status code 0)
def print_output(metrics):
    # Print Nagios Format Output
    output = 'OK | '
    for metric in metrics:
        output += metric + '=' + metrics[metric] + ';;;; '

    print output
    exit(0)

# Run Main()
main()