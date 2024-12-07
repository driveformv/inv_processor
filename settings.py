import json
import os
from config import CREDIT_CARD_EMAILS, ADDITIONAL_RECIPIENTS

# Use absolute path for settings file
SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'settings.json')

def get_credit_card_emails():
    """Get credit card email mappings"""
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            settings = json.load(f)
            return settings['credit_card_emails']
    return CREDIT_CARD_EMAILS

def get_additional_recipients():
    """Get additional recipients list"""
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            settings = json.load(f)
            return settings['additional_recipients']
    return ADDITIONAL_RECIPIENTS

def get_settings():
    """Get system settings"""
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            settings = json.load(f)
            return settings['settings']
    return {
        'emails_enabled': True,
        'zapier_enabled': True
    }
