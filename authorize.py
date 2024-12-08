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
    logging.debug("GOOGLE_CREDENTIALS: %s", os.environ.get('GOOGLE_CREDENTIALS'))

    user_email = os.environ.get('GMAIL_SENDER_EMAIL')
    if not user_email:
        raise ValueError("GMAIL_SENDER_EMAIL environment variable not found")

    creds_json = os.environ.get('GOOGLE_CREDENTIALS')
    if not creds_json:
        raise ValueError("GOOGLE_CREDENTIALS environment variable not found")
    
    logging.debug("Credentials JSON: %s", creds_json)

    creds_dict = json.loads(creds_json)
    
    if 'private_key' in creds_dict:
        private_key = creds_dict['private_key']
        
        # Clean up the private key string
        private_key = private_key.replace('\\n', '\n')  # Handle JSON escaped newlines
        private_key = private_key.replace('-----n', '-----')  # Remove n after delimiters
        
        # Split the key into parts
        key_parts = private_key.split('\n')
        
        # Reconstruct the key with proper formatting
        formatted_key = []
        for part in key_parts:
            if part.startswith('-----'):
                formatted_key.append(part)
            elif part.strip():  # Only process non-empty lines
                # Remove any remaining 'n' characters and add proper line breaks
                clean_part = part.replace('n', '')
                if clean_part:
                    formatted_key.append(clean_part)
        
        # Ensure proper beginning and ending
        if not formatted_key[0].endswith('-----'):
            formatted_key[0] = formatted_key[0].replace('-----n', '-----')
        if not formatted_key[-1].startswith('-----'):
            formatted_key[-1] = formatted_key[-1].replace('n-----', '-----')
            
        # Join with proper newlines
        creds_dict['private_key'] = '\n'.join(formatted_key)
        logging.debug("Formatted private key: %s", creds_dict['private_key'])
    
    try:
        credentials = service_account.Credentials.from_service_account_info(
            creds_dict,
            scopes=SCOPES
        )
        
        delegated_credentials = credentials.with_subject(user_email)
        logging.info(f"Created delegated credentials for {user_email}")
        return delegated_credentials
        
    except Exception as e:
        logging.error(f"Error creating credentials: {str(e)}")
        raise

if __name__ == "__main__":
    get_credentials()