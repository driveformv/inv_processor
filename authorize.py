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

def fix_private_key(key):
    # Remove any 'n' characters after the header and before the footer
    key = key.replace('-----BEGIN PRIVATE KEY-----n', '-----BEGIN PRIVATE KEY-----\n')
    key = key.replace('n-----END PRIVATE KEY-----', '\n-----END PRIVATE KEY-----')
    
    # Replace remaining 'n' characters with newlines
    parts = key.split('\n')
    fixed_parts = []
    for part in parts:
        if part.startswith('-----'):
            fixed_parts.append(part)
        else:
            # Split by 'n' and filter out empty strings
            subparts = [p for p in part.split('n') if p]
            fixed_parts.extend(subparts)
    
    # Join with newlines and ensure proper ending
    fixed_key = '\n'.join(fixed_parts)
    if not fixed_key.endswith('\n'):
        fixed_key += '\n'
        
    return fixed_key

def get_credentials():
    user_email = os.environ.get('GMAIL_SENDER_EMAIL')
    if not user_email:
        raise ValueError("GMAIL_SENDER_EMAIL environment variable not found")

    creds_json = os.environ.get('GOOGLE_CREDENTIALS')
    if not creds_json:
        raise ValueError("GOOGLE_CREDENTIALS environment variable not found")

    try:
        creds_dict = json.loads(creds_json)
        
        if 'private_key' in creds_dict:
            # Fix the private key format
            creds_dict['private_key'] = fix_private_key(creds_dict['private_key'])
            logging.debug(f"Fixed private key: {creds_dict['private_key']}")
        
        credentials = service_account.Credentials.from_service_account_info(
            creds_dict,
            scopes=SCOPES
        )
        
        delegated_credentials = credentials.with_subject(user_email)
        logging.info(f"Created delegated credentials for {user_email}")
        return delegated_credentials
        
    except json.JSONDecodeError as e:
        logging.error(f"Error parsing credentials JSON: {str(e)}")
        raise
    except Exception as e:
        logging.error(f"Error creating credentials: {str(e)}")
        raise

if __name__ == "__main__":
    get_credentials()