import os
import base64
from flask import Flask, request, render_template, jsonify
from werkzeug.utils import secure_filename
from openai import OpenAI
from pdf2image import convert_from_path
import tempfile
import json
import requests
from config import CREDIT_CARD_EMAILS, ADDITIONAL_RECIPIENTS
from gmail_service import get_gmail_service, create_message_with_attachment, send_message, logger
from dotenv import load_dotenv
load_dotenv(override=True)
from upload_to_drive import upload_file_to_drive
from settings import get_settings
from admin import admin_bp

app = Flask(__name__)
# Get absolute path for uploads folder
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Set poppler path based on environment
if os.name == 'nt':  # Windows
    POPPLER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'poppler', 'poppler-24.08.0', 'Library', 'bin')
else:  # Linux/Unix
    POPPLER_PATH = '/usr/bin'  # Default path for poppler-utils on Linux

# Ensure upload folder exists with proper permissions
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize the OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

app.register_blueprint(admin_bp)
app.secret_key = 'your-secret-key-here'  # Required for flash messages

def encode_image(image_path):
    """
    Encode an image file to base64 string.
    
    Args:
        image_path (str): Path to the image file.
    Returns:
        str: Base64 encoded string of the image.
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def convert_pdf_to_image(pdf_path):
    """
    Convert first page of PDF to image
    
    Args:
        pdf_path (str): Path to PDF file
    Returns:
        str: Path to the converted image
    """
    try:
        print(f"Converting PDF: {pdf_path}")
        print(f"Poppler path: {POPPLER_PATH}")
        
        # Convert PDF to image using local poppler
        images = convert_from_path(pdf_path, first_page=1, last_page=1, poppler_path=POPPLER_PATH)
        
        if images:
            # Save the first page as image
            image_path = os.path.join(os.path.dirname(pdf_path), 
                                    os.path.splitext(os.path.basename(pdf_path))[0] + '.jpg')
            print(f"Saving image to: {image_path}")
            images[0].save(image_path, 'JPEG')
            return image_path
        return None
    except Exception as e:
        print(f"Error converting PDF: {str(e)}")
        raise

def analyze_image(file_path):
    """
    Send an encoded image to GPT-4 for analysis
    
    Args:
        file_path (str): Path to the image file.
    """
    try:
        print(f"Processing file: {file_path}")
        
        # Check if file exists
        if not os.path.exists(file_path):
            raise Exception(f"File not found: {file_path}")
        
        # Check if file is PDF
        if file_path.lower().endswith('.pdf'):
            image_path = convert_pdf_to_image(file_path)
            if image_path is None:
                raise Exception("Failed to convert PDF to image")
            # Use the image for analysis but keep the original PDF
            original_file_path = file_path
            file_path = image_path

        # First encode the image
        base64_image = encode_image(file_path)
        
        # Send to GPT-4 for analysis
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """Extract the following from this invoice and return ONLY a JSON object:
                            {
                                "invoice_number": "any invoice/order number",
                                "date": "any date found",
                                "amount": "total amount (no currency symbol)",
                                "customer_name": "name if present",
                                "vendor": "business name",
                                "credit_card": "last 4 digits if shown",
                                "description_of_items_or_services": "list all items/services",
                                "billing_address": "full address if shown",
                                "payment_method": "payment type used"
                            }
                            
                            Important:
                            1. Extract values EXACTLY as they appear
                            2. Use "N/A" if not found
                            3. Remove currency symbols from amount
                            4. Include ONLY last 4 digits of credit card"""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1500
        )

        # Output GPT-4's analysis
        print("\nReceipt Analysis:")
        content = response.choices[0].message.content
        
        # Clean up markdown formatting if present
        if "```json" in content:
            content = content.replace("```json", "").replace("```", "").strip()
        
        # Validate it's proper JSON
        try:
            json.loads(content)  # Test if it's valid JSON
            print(content)
            return content, original_file_path if 'original_file_path' in locals() else file_path
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON response: {e}"
            print(error_msg)
            return error_msg, original_file_path if 'original_file_path' in locals() else file_path
    except Exception as e:
        error_msg = f"Error analyzing image: {e}"
        print(error_msg)
        return error_msg, original_file_path if 'original_file_path' in locals() else file_path

def send_email(recipient_email, subject, body, attachment_path, cc=None):
    """
    Send email with attachment using Gmail API
    """
    try:
        # Check if emails are enabled
        settings = get_settings()
        if not settings.get('emails_enabled', True):
            logger.info("=== Email notifications are disabled ===")
            return True  # Return True to avoid error handling, since this is an intentional skip
            
        logger.info("=== Starting Email Send Process ===")
        logger.info(f"Recipient: {recipient_email}")
        logger.info(f"Subject: {subject}")
        logger.info(f"Attachment: {attachment_path}")
        
        # Get Gmail API service
        service = get_gmail_service()
        
        # Use configured sender email from environment variable
        sender_email = os.getenv('GMAIL_SENDER_EMAIL')
        if not sender_email:
            raise ValueError("GMAIL_SENDER_EMAIL environment variable not set")
        logger.info(f"Sender email: {sender_email}")

        # Create message with attachment
        message = create_message_with_attachment(
            sender_email,
            recipient_email,
            cc=cc,
            subject=subject,
            message_text=body,
            file_path=attachment_path
        )
        
        # Send message
        result = send_message(service, 'me', message)
        success = result is not None and 'id' in result
        
        if success:
            logger.info("=== Email Send Process Completed Successfully ===")
        else:
            logger.error("=== Email Send Process Failed ===")
            
        return success
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        return False

# Webhook endpoint for Zapier integration
@app.route('/webhook/invoice', methods=['POST'])
def zapier_webhook():
    try:
        data = request.json
        
        # Extract the analysis result and Google Drive link
        analysis_result = data.get('analysis_result', {})
        drive_file_id = data.get('drive_file_id', '')
        
        # Create the Google Drive sharing URL
        drive_link = f"https://drive.google.com/file/d/{drive_file_id}/view" if drive_file_id else ''
        
        # Format response for Zapier
        zapier_data = {
            'invoice_number': analysis_result.get('invoice_number', 'N/A'),
            'date': analysis_result.get('date', 'N/A'),
            'amount': analysis_result.get('amount', 'N/A'),
            'customer_name': analysis_result.get('customer_name', 'N/A'),
            'vendor': analysis_result.get('vendor', 'N/A'),
            'credit_card': analysis_result.get('credit_card', 'N/A'),
            'description_of_items_or_services': analysis_result.get('description_of_items_or_services', 'N/A'),
            'billing_address': analysis_result.get('billing_address', 'N/A'),
            'payment_method': analysis_result.get('payment_method', 'N/A'),
            'google_drive_url': drive_link  # Changed to a more descriptive name
        }
        
        return jsonify(zapier_data), 200
        
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    try:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        print(f"Saving file to: {filepath}")
        file.save(filepath)
        
        result, attachment_path = analyze_image(filepath)
        
        # Clean up the uploaded file
        if os.path.exists(filepath):
            os.remove(filepath)
        
        return jsonify({'result': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/upload', methods=['POST'])
def upload():
    try:
        logger.info("=== Starting Upload Process ===")
        
        # Load settings first
        settings = get_settings()
        emails_enabled = settings.get('emails_enabled', True)
        zapier_enabled = settings.get('zapier_enabled', True)
        
        if 'file' not in request.files:
            logger.error("No file uploaded")
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        credit_card = request.form.get('credit_card')
        expense_reason = request.form.get('expense_reason')
        user_name = request.form.get('user_name')
        
        logger.info(f"Credit Card: {credit_card}")
        logger.info(f"Expense Reason: {expense_reason}")
        logger.info(f"User Name: {user_name}")
        
        if not credit_card or not expense_reason or not user_name:
            logger.error("Missing credit card, expense reason, or user name")
            return jsonify({'error': 'Missing credit card, expense reason, or user name'}), 400
        
        if file.filename == '':
            logger.error("No file selected")
            return jsonify({'error': 'No file selected'}), 400
            
        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            logger.info(f"File saved to: {filepath}")
            
            # Upload to Google Drive
            try:
                drive_file_id = upload_file_to_drive(filepath, filename)
                logger.info(f"File uploaded to Google Drive with ID: {drive_file_id}")
            except Exception as e:
                logger.error(f"Error uploading to Google Drive: {str(e)}")
                drive_file_id = None
                # Continue with the process even if Drive upload fails
            
            # Analyze the file using existing analyzer
            logger.info("Starting file analysis...")
            analysis_result, attachment_path = analyze_image(filepath)
            logger.info(f"Analysis result: {analysis_result}")
            
            # Parse and format the analysis result
            try:
                # Remove markdown formatting if present
                clean_result = analysis_result
                if "```json" in clean_result:
                    clean_result = clean_result.replace("```json", "").replace("```", "").strip()
                
                # Parse the JSON
                result_dict = json.loads(clean_result)
                
                # Format the analysis results nicely
                formatted_analysis = "\n".join([
                    "=== Analysis Results ===",
                    f"Invoice Number: {result_dict.get('invoice_number', 'N/A')}",
                    f"Date: {result_dict.get('date', 'N/A')}",
                    f"Amount: ${result_dict.get('amount', 'N/A')}",
                    f"Customer Name: {result_dict.get('customer_name', 'N/A')}",
                    f"Vendor: {result_dict.get('vendor', 'N/A')}",
                    f"Credit Card: {result_dict.get('credit_card', 'N/A')}",
                    f"Payment Method: {result_dict.get('payment_method', 'N/A')}",
                    f"Billing Address: {result_dict.get('billing_address', 'N/A')}",
                    "\nItems/Services:",
                    "----------------"
                ])
                
                # Add items if present
                items = result_dict.get('description_of_items_or_services', [])
                if isinstance(items, list):
                    formatted_analysis += "\n" + "\n".join(f"- {item}" for item in items)
                else:
                    formatted_analysis += f"\n{items}"
                
            except Exception as e:
                logger.error(f"Error formatting analysis: {str(e)}")
                formatted_analysis = analysis_result  # Use original if parsing fails
            
            # Get recipient email from credit card mapping
            recipient_email = CREDIT_CARD_EMAILS.get(credit_card)
            if not recipient_email:
                logger.error(f"Invalid credit card selected: {credit_card}")
                return jsonify({'error': 'Invalid credit card selected'}), 400
            
            # Prepare email content
            subject = f"Expense Receipt - {result_dict.get('invoice_number', 'N/A')} - {result_dict.get('vendor', 'N/A')}"
            body = f"""
An invoice has been processed and sent to BMO.

User: {user_name}
Credit Card: {credit_card}
Reason: {expense_reason}

{formatted_analysis}
"""
            
            # Convert CC list to a comma-separated string
            cc_string = ', '.join(ADDITIONAL_RECIPIENTS)
            
            # Send email with CC if enabled
            if emails_enabled:
                email_sent = send_email(recipient_email, subject, body, attachment_path, cc=cc_string)
                if not email_sent:
                    logger.error("Failed to send email")
                    return jsonify({'error': 'Failed to send email'}), 500
            else:
                logger.info("Email notifications are disabled - skipping email send")
                
            # Create Google Drive link
            drive_link = f"https://drive.google.com/file/d/{drive_file_id}/view" if drive_file_id else ''
            
            # Send data to Zapier if enabled
            try:
                if zapier_enabled:
                    zapier_webhook_url = os.getenv('ZAPIER_WEBHOOK_URL')
                    if zapier_webhook_url:
                        logger.info(f"Sending data to Zapier webhook: {zapier_webhook_url}")
                        webhook_data = {
                            'invoice_number': result_dict.get('invoice_number', 'N/A'),
                            'date': result_dict.get('date', 'N/A'),
                            'amount': result_dict.get('amount', 'N/A'),
                            'customer_name': result_dict.get('customer_name', 'N/A'),
                            'vendor': result_dict.get('vendor', 'N/A'),
                            'credit_card': result_dict.get('credit_card', 'N/A'),
                            'description_of_items_or_services': result_dict.get('description_of_items_or_services', 'N/A'),
                            'billing_address': result_dict.get('billing_address', 'N/A'),
                            'payment_method': result_dict.get('payment_method', 'N/A'),
                            'google_drive_url': drive_link,
                            'selected_credit_card': credit_card,
                            'expense_reason': expense_reason,
                            'user_name': user_name
                        }
                        
                        try:
                            response = requests.post(zapier_webhook_url, json=webhook_data, timeout=10)
                            if response.status_code != 200:
                                logger.error(f"Failed to send data to Zapier. Status code: {response.status_code}, Response: {response.text}")
                            else:
                                logger.info("Successfully sent data to Zapier")
                        except requests.exceptions.RequestException as req_err:
                            logger.error(f"Request to Zapier failed: {str(req_err)}")
                    else:
                        logger.warning("Zapier webhook URL not found in environment variables")
            except Exception as e:
                logger.error(f"Error in Zapier integration: {str(e)}")
                # Continue even if Zapier fails
            
            # Clean up files
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
                if os.path.exists(attachment_path) and attachment_path != filepath:
                    os.remove(attachment_path)
            except Exception as e:
                logger.error(f"Error cleaning up files: {str(e)}")
            
            # Return success with status message
            status_message = "Receipt processed successfully."
            if not emails_enabled:
                status_message += " (Email notifications are disabled)"
            if not zapier_enabled:
                status_message += " (Zapier integration is disabled)"
                
            return jsonify({
                'message': status_message,
                'analysis': result_dict,
                'drive_link': drive_link,
                'email_sent': emails_enabled
            })
            
    except Exception as e:
        logger.error(f"Error in upload process: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/authorize_gmail')
def authorize_gmail():
    """Handle Gmail authorization flow"""
    try:
        logger.info("Starting Gmail authorization...")
        
        # Check if credentials.json exists
        if not os.path.exists('credentials.json'):
            error_msg = "credentials.json not found. Please download it from Google Cloud Console."
            logger.error(error_msg)
            return jsonify({'error': error_msg}), 400
            
        # Force HTTPS off for local development
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
        
        # Create the flow using the client secrets file
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json',
                scopes=['https://www.googleapis.com/auth/gmail.send',
                       'https://www.googleapis.com/auth/gmail.compose',
                       'https://www.googleapis.com/auth/gmail.modify',
                       'https://www.googleapis.com/auth/gmail.readonly']
            )
        except Exception as e:
            error_msg = f"Error creating OAuth flow: {str(e)}. Please check your credentials.json file."
            logger.error(error_msg)
            return jsonify({'error': error_msg}), 400
        
        # Run the OAuth flow
        try:
            creds = flow.run_local_server(
                host='localhost',
                port=8080,
                open_browser=True,
                prompt='consent'
            )
        except Exception as e:
            error_msg = f"OAuth flow failed: {str(e)}"
            logger.error(error_msg)
            return jsonify({'error': error_msg}), 500
        
        # Save the credentials
        try:
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
            logger.info("Successfully saved credentials to token.pickle")
        except Exception as e:
            error_msg = f"Error saving credentials: {str(e)}"
            logger.error(error_msg)
            return jsonify({'error': error_msg}), 500
        
        # Verify the credentials work by attempting to create a service
        try:
            service = get_gmail_service()
            if service:
                logger.info("Successfully verified Gmail credentials")
                return jsonify({
                    'message': 'Gmail authorization successful',
                    'email': creds.token['email'] if 'email' in creds.token else 'Unknown'
                })
        except Exception as e:
            error_msg = f"Error verifying credentials: {str(e)}"
            logger.error(error_msg)
            # Delete the token file since it might be invalid
            if os.path.exists('token.pickle'):
                os.remove('token.pickle')
            return jsonify({'error': error_msg}), 500
            
    except Exception as e:
        error_msg = f"Gmail authorization error: {str(e)}"
        logger.error(error_msg)
        return jsonify({'error': error_msg}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
