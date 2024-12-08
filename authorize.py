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
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.readonly'
]

def get_credentials():
    # Log the GOOGLE_CREDENTIALS environment variable
    logging.debug("GOOGLE_CREDENTIALS: %s", os.environ.get('GOOGLE_CREDENTIALS'))

    # Get the email to impersonate
    user_email = os.environ.get('GMAIL_SENDER_EMAIL')
    if not user_email:
        raise ValueError("GMAIL_SENDER_EMAIL environment variable not found")

    # Read service account credentials from environment variable
    creds_json = os.environ.get('GOOGLE_CREDENTIALS')
    if not creds_json:
        raise ValueError("GOOGLE_CREDENTIALS environment variable not found")
    
    # Log the credentials JSON
    logging.debug("Credentials JSON: %s", creds_json)

    # Parse the JSON string into a dictionary
    creds_dict = json.loads(creds_json)
    
    # Fix private key newlines
    if 'private_key' in creds_dict:
        # Replace literal 'n' with newline at start and end of key
        private_key = creds_dict['private_key']
        if private_key.startswith('-----BEGIN PRIVATE KEY-----n'):
            private_key = private_key.replace('-----BEGIN PRIVATE KEY-----n', '-----BEGIN PRIVATE KEY-----\n')
        if private_key.endswith('n-----END PRIVATE KEY-----n'):
            private_key = private_key.replace('n-----END PRIVATE KEY-----n', '\n-----END PRIVATE KEY-----\n')
        creds_dict['private_key'] = private_key
    
    # Create credentials from service account info with domain-wide delegation
    credentials = service_account.Credentials.from_service_account_info(
        creds_dict,
        scopes=SCOPES
    )
    
    # Create delegated credentials
    delegated_credentials = credentials.with_subject(user_email)
    logging.info(f"Created delegated credentials for {user_email}")
    
    return delegated_credentials

if __name__ == "__main__":
    get_credentials()
