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
    try:
        user_email = os.environ.get('GMAIL_SENDER_EMAIL')
        if not user_email:
            logging.error("GMAIL_SENDER_EMAIL environment variable not found")
            raise ValueError("GMAIL_SENDER_EMAIL environment variable not found")

        creds_json = os.environ.get('GOOGLE_CREDENTIALS')
        if not creds_json:
            logging.error("GOOGLE_CREDENTIALS environment variable not found")
            raise ValueError("GOOGLE_CREDENTIALS environment variable not found")

        logging.info("Attempting to parse credentials...")
        
        # First try to load the JSON directly
        try:
            creds_dict = json.loads(creds_json)
            logging.info("Successfully parsed credentials JSON")
        except json.JSONDecodeError as e:
            logging.warning(f"Initial JSON parse failed: {str(e)}")
            logging.info("Attempting to clean JSON string...")
            # If that fails, try to clean up the JSON string
            creds_json = creds_json.replace('\n', '').replace('\r', '').strip()
            try:
                creds_dict = json.loads(creds_json)
                logging.info("Successfully parsed cleaned credentials JSON")
            except json.JSONDecodeError as e:
                logging.error("Failed to parse credentials even after cleaning")
                logging.error(f"JSON Error: {str(e)}")
                logging.error(f"First 100 chars of credentials: {creds_json[:100]}...")
                raise
        
        # Verify required fields
        required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']
        missing_fields = [field for field in required_fields if field not in creds_dict]
        if missing_fields:
            logging.error(f"Missing required fields in credentials: {missing_fields}")
            raise ValueError(f"Credentials missing required fields: {missing_fields}")
        
        # Now fix the private key after we have the dict
        if 'private_key' in creds_dict:
            private_key = creds_dict['private_key']
            logging.debug("Original private key length: %d", len(private_key))
            
            # Handle both escaped and unescaped newlines
            private_key = private_key.replace('\\n', '\n').replace('n', '\n')
            
            # Ensure proper PEM format
            if not private_key.startswith('-----BEGIN PRIVATE KEY-----'):
                private_key = '-----BEGIN PRIVATE KEY-----\n' + private_key
            if not private_key.endswith('-----END PRIVATE KEY-----'):
                private_key = private_key + '\n-----END PRIVATE KEY-----'
            
            creds_dict['private_key'] = private_key
            logging.debug("Processed private key length: %d", len(private_key))
            logging.debug("Private key starts with: %s", private_key[:50])
            logging.debug("Private key ends with: %s", private_key[-50:])
        
        try:
            logging.info("Creating service account credentials...")
            credentials = service_account.Credentials.from_service_account_info(
                creds_dict,
                scopes=SCOPES
            )
            logging.info("Successfully created service account credentials")
            
            logging.info(f"Delegating credentials to {user_email}")
            delegated_credentials = credentials.with_subject(user_email)
            logging.info(f"Successfully created delegated credentials for {user_email}")
            
            return delegated_credentials
            
        except Exception as e:
            logging.error(f"Error creating service account credentials: {str(e)}")
            logging.error("Credential info: type=%s, project_id=%s, client_email=%s", 
                         creds_dict.get('type'), 
                         creds_dict.get('project_id'), 
                         creds_dict.get('client_email'))
            raise
            
    except Exception as e:
        logging.error(f"Fatal error in get_credentials: {str(e)}")
        raise

if __name__ == "__main__":
    get_credentials()