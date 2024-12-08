from google.oauth2 import service_account
import os
import json
import logging

logging.basicConfig(level=logging.DEBUG)

SCOPES = [
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.readonly'
]

def get_credentials():
    user_email = os.environ.get('GMAIL_SENDER_EMAIL')
    if not user_email:
        raise ValueError("GMAIL_SENDER_EMAIL environment variable not found")

    creds_json = os.environ.get('GOOGLE_CREDENTIALS')
    if not creds_json:
        raise ValueError("GOOGLE_CREDENTIALS environment variable not found")

    try:
        # First try to load the JSON directly
        try:
            creds_dict = json.loads(creds_json)
        except json.JSONDecodeError:
            # If that fails, try to clean up the JSON string
            # Remove any literal newlines and extra whitespace
            creds_json = creds_json.replace('\n', '').replace('\r', '').strip()
            creds_dict = json.loads(creds_json)
        
        # Now fix the private key after we have the dict
        if 'private_key' in creds_dict:
            private_key = creds_dict['private_key']
            # Handle both escaped and unescaped newlines
            private_key = private_key.replace('\\n', '\n').replace('n', '\n')
            
            # Ensure proper PEM format
            if not private_key.startswith('-----BEGIN PRIVATE KEY-----'):
                private_key = '-----BEGIN PRIVATE KEY-----\n' + private_key
            if not private_key.endswith('-----END PRIVATE KEY-----'):
                private_key = private_key + '\n-----END PRIVATE KEY-----'
                
            creds_dict['private_key'] = private_key
            logging.debug(f"Processed private key format: {private_key}")
        
        credentials = service_account.Credentials.from_service_account_info(
            creds_dict,
            scopes=SCOPES
        )
        
        delegated_credentials = credentials.with_subject(user_email)
        logging.info(f"Created delegated credentials for {user_email}")
        return delegated_credentials
        
    except json.JSONDecodeError as e:
        logging.error(f"Error parsing credentials JSON: {str(e)}")
        logging.error(f"Raw credentials string: {creds_json}")
        raise
    except Exception as e:
        logging.error(f"Error creating credentials: {str(e)}")
        raise

if __name__ == "__main__":
    get_credentials()