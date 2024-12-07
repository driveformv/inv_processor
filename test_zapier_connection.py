import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_zapier_connection():
    """Test the connection to Zapier webhook"""
    zapier_webhook_url = os.getenv('ZAPIER_WEBHOOK_URL')
    
    if not zapier_webhook_url:
        print("Error: ZAPIER_WEBHOOK_URL not found in environment variables")
        return False
    
    test_data = {
        'test': True,
        'message': 'This is a test message from the receipt upload app'
    }
    
    try:
        response = requests.post(zapier_webhook_url, json=test_data, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to Zapier: {str(e)}")
        return False

if __name__ == "__main__":
    print("Testing Zapier connection...")
    success = test_zapier_connection()
    print(f"Test {'successful' if success else 'failed'}")
