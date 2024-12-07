import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Zapier webhook URL
zapier_url = os.getenv('ZAPIER_WEBHOOK_URL')

# Test data with actual Google Drive file ID
test_drive_file_id = '1adzLMJObHtkliMT1GA2k1msS8x2RK1oQ'  # Using your actual folder ID as an example
test_drive_url = f'https://drive.google.com/file/d/{test_drive_file_id}/view'

# Test data
test_data = {
    'analysis_result': {
        'invoice_number': 'TEST-002',
        'date': '2024-12-07',
        'amount': '1234.56',
        'customer_name': 'Test Customer',
        'vendor': 'Test Vendor Inc.',
        'credit_card': '**** 4321',
        'description_of_items_or_services': ['Item 1 - $500', 'Item 2 - $734.56'],
        'billing_address': '123 Test Street, Test City, TS 12345',
        'payment_method': 'Credit Card'
    },
    'drive_file_id': test_drive_file_id,
    'google_drive_url': test_drive_url
}

# Send test data to Zapier
response = requests.post(zapier_url, json=test_data)

print(f'Status Code: {response.status_code}')
print(f'Response: {response.text}')
print(f'\nSent Google Drive URL: {test_drive_url}')
