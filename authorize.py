from google.oauth2 import service_account
import os
import json
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Include both Drive and Gmail scopes
SCOPES = [
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.readonly'
]

def get_credentials():
    # Log the GOOGLE_CREDENTIALS environment variable
    logging.debug("GOOGLE_CREDENTIALS: %s", os.environ.get('GOOGLE_CREDENTIALS'))

    # Read service account credentials from environment variable
    creds_json = os.environ.get('GOOGLE_CREDENTIALS')
    if not creds_json:
        raise ValueError("GOOGLE_CREDENTIALS environment variable not found")
    
    # Log the credentials JSON
    logging.debug("Credentials JSON: %s", creds_json)

    # Parse the JSON string into a dictionary
    creds_dict = json.loads(creds_json)
    
    # Create credentials from service account info
    credentials = service_account.Credentials.from_service_account_info(
        creds_dict,
        scopes=SCOPES
    )
    
    return credentials

if __name__ == "__main__":
    get_credentials()
