from google.oauth2 import service_account
import os
import json
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

SCOPES = [
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.readonly'
]

def get_credentials():
    logger.info("Starting credentials retrieval process...")
    
    # Get the sender email for delegation
    user_email = os.environ.get('GMAIL_SENDER_EMAIL')
    if not user_email:
        logger.error("GMAIL_SENDER_EMAIL environment variable is not set")
        raise ValueError("GMAIL_SENDER_EMAIL environment variable is not set")

    # Get the service account credentials JSON
    creds_json = os.environ.get('GOOGLE_CREDENTIALS')
    if not creds_json:
        logger.error("GOOGLE_CREDENTIALS environment variable is not set")
        raise ValueError("GOOGLE_CREDENTIALS environment variable is not set")
    
    try:
        # Parse the JSON string into a Python dictionary
        logger.info("Parsing credentials JSON...")
        credentials_dict = json.loads(creds_json)
        logger.info("Successfully parsed credentials JSON")
        
        # Create service account credentials
        logger.info("Creating service account credentials...")
        credentials = service_account.Credentials.from_service_account_info(
            credentials_dict,
            scopes=SCOPES
        )
        logger.info("Successfully created service account credentials")
        
        # Delegate credentials to the sender email
        logger.info(f"Delegating credentials to {user_email}...")
        delegated_credentials = credentials.with_subject(user_email)
        logger.info("Successfully created delegated credentials")
        
        return delegated_credentials
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in GOOGLE_CREDENTIALS: {e}")
        logger.error(f"First 100 chars of credentials: {creds_json[:100]}...")
        raise ValueError(f"Invalid JSON in GOOGLE_CREDENTIALS: {e}")
    except Exception as e:
        logger.error(f"Failed to create service account credentials: {e}")
        raise RuntimeError(f"Failed to create service account credentials: {e}")

if __name__ == "__main__":
    get_credentials()