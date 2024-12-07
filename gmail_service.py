from dotenv import load_dotenv
load_dotenv(override=True)  # Force reload

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import base64
import os
import pickle
import logging
from datetime import datetime
import webbrowser

# Configure logging
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# File handler for all logs
file_handler = logging.FileHandler('logs/all_processes.log')
file_handler.setFormatter(log_formatter)

# File handler for email-specific logs
email_handler = logging.FileHandler('logs/email.log')
email_handler.setFormatter(log_formatter)
email_handler.addFilter(lambda record: 'email' in record.getMessage().lower())

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, email_handler, console_handler]
)
logger = logging.getLogger(__name__)

# If modifying these scopes, delete the file token.pickle.
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.readonly'
]

def get_gmail_service():
    """Gets Gmail API service instance."""
    try:
        logger.info("Getting Gmail service...")
        
        # Get credentials from environment variable using authorize.py
        from authorize import get_credentials
        try:
            creds = get_credentials()
            logger.info("Successfully obtained credentials from environment variable")
        except Exception as e:
            error_msg = f"Error getting credentials from environment: {str(e)}"
            logger.error(error_msg)
            raise
        
        try:
            service = build('gmail', 'v1', credentials=creds)
            logger.info("Gmail service initialized successfully")
            return service
        except Exception as e:
            error_msg = f"Error building Gmail service: {str(e)}"
            logger.error(error_msg)
            raise
        
    except Exception as e:
        error_msg = f"Error getting Gmail service: {str(e)}"
        logger.error(error_msg)
        raise

def create_message_with_attachment(sender, to, cc, subject, message_text, file_path=None):
    """Create an email with optional attachment."""
    try:
        logger.info(f"Creating email - From: {sender}, To: {to}, CC: {cc}, Subject: {subject}")
        
        # Create message container
        message = MIMEMultipart()
        message['to'] = to
        message['cc'] = cc
        message['from'] = sender
        message['subject'] = subject
        
        # Add body
        message.attach(MIMEText(message_text))
        logger.info("Email body attached")
        
        # Add attachment if provided
        if file_path:
            logger.info(f"Attempting to attach file: {file_path}")
            if not os.path.isfile(file_path):
                error_msg = f"Attachment file not found: {file_path}"
                logger.error(error_msg)
                raise FileNotFoundError(error_msg)
            
            # Determine MIME type based on file extension
            file_ext = os.path.splitext(file_path)[1].lower()
            mime_type = 'application/pdf' if file_ext == '.pdf' else 'image/jpeg' if file_ext in ['.jpg', '.jpeg'] else 'image/png' if file_ext == '.png' else 'application/octet-stream'
            
            with open(file_path, 'rb') as attachment:
                part = MIMEBase(*mime_type.split('/'))
                part.set_payload(attachment.read())
                logger.info(f"File read successfully: {os.path.getsize(file_path)} bytes")
            
            # Encode the attachment
            encoders.encode_base64(part)
            
            # Add header
            filename = os.path.basename(file_path)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {filename}'
            )
            part.add_header('Content-Type', mime_type)
            
            # Attach the file
            message.attach(part)
            logger.info(f"File {filename} attached successfully as {mime_type}")
        
        # Convert to dict
        raw_message = message.as_bytes()
        raw_size = len(raw_message)
        logger.info(f"Raw message size before encoding: {raw_size} bytes")
        
        if raw_size > 25 * 1024 * 1024:  # 25MB is Gmail's limit
            logger.warning(f"Warning: Email size ({raw_size} bytes) is approaching Gmail's 25MB limit")
        
        raw = {
            'raw': base64.urlsafe_b64encode(raw_message).decode()
        }
        logger.info(f"Email created successfully for {to}")
        return raw
        
    except Exception as e:
        error_msg = f"Error creating email: {str(e)}"
        logger.error(error_msg)
        raise

def send_message(service, user_id, message):
    """Send an email message.

    Args:
        service: Authorized Gmail API service instance.
        user_id: User's email address. The special value "me" can be used to indicate the authenticated user.
        message: Message to be sent.

    Returns:
        Sent Message.
    """
    try:
        logger.info("=== Starting Email Send Process ===")
        logger.info(f"User ID: {user_id}")
        logger.info("Attempting to send email message...")
        
        # Log service details
        logger.info(f"Service type: {type(service)}")
        
        message = service.users().messages().send(userId=user_id, body=message).execute()
        logger.info(f'Message Id: {message["id"]} sent successfully')
        logger.info("=== Email Send Process Completed ===")
        return message
    except Exception as e:
        error_msg = f"An error occurred while sending the email: {str(e)}"
        logger.error(error_msg)
        logger.error(f"Full error details: {repr(e)}")
        
        # Check for specific error types and provide more helpful messages
        error_str = str(e).lower()
        if 'unauthorized' in error_str:
            logger.error("Authorization error. Please reauthorize at /authorize_gmail")
        elif 'quota' in error_str:
            logger.error("Gmail API quota exceeded. Please try again later.")
        elif 'invalid' in error_str and 'recipient' in error_str:
            logger.error("Invalid recipient email address")
        
        return None
