#!/usr/bin/env python3
"""
Setup script to authenticate with Google Calendar and store credentials in AWS SSM.
Run this script locally once to set up the integration.
"""

import os
import json
import boto3
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Scopes needed for Calendar and Gmail API
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/gmail.send'
]

def main():
    if not os.path.exists('credentials.json'):
        print("❌ Error: credentials.json not found in current directory.")
        print("Please download it from Google Cloud Console and place it here.")
        return

    print("🔑 Initiating Google OAuth Flow...")
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    creds = flow.run_local_server(port=0)

    # Validate that we can read calendar info
    try:
        service = build('calendar', 'v3', credentials=creds)
        calendar = service.calendars().get(calendarId='primary').execute()
        primary_email = calendar.get('id')
        print(f"✅ Successfully authenticated as: {primary_email}")
    except Exception as e:
        print(f"❌ Failed to verify credentials: {e}")
        return

    print("🔐 Storing credentials in AWS SSM Parameter Store...")
    ssm = boto3.client('ssm', region_name='us-east-1')

    # Read the client ID and secret from credentials.json
    with open('credentials.json', 'r') as f:
        client_config = json.load(f)
        client_type = 'installed' if 'installed' in client_config else 'web'
        client_id = client_config[client_type]['client_id']
        client_secret = client_config[client_type]['client_secret']

    parameters = {
        '/reumatologia-app/google-client-id': client_id,
        '/reumatologia-app/google-client-secret': client_secret,
        '/reumatologia-app/google-refresh-token': creds.refresh_token,
        '/reumatologia-app/google-calendar-id': primary_email  # We default to the primary calendar of the auth'd account
    }

    for name, value in parameters.items():
        try:
            ssm.put_parameter(
                Name=name,
                Value=value,
                Type='SecureString',
                Overwrite=True
            )
            print(f"✅ Stored {name}")
        except Exception as e:
            print(f"❌ Failed to store {name}: {e}")
            
    print("\n🎉 Setup complete! The AWS backend can now sync with Google Calendar.")

if __name__ == '__main__':
    main()
