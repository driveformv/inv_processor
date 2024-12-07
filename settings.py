import json
import os
from config import CREDIT_CARD_EMAILS, ADDITIONAL_RECIPIENTS

# Use environment variables for settings
def get_credit_card_emails():
    """Get credit card email mappings"""
    env_settings = os.environ.get('APP_SETTINGS')
    if env_settings:
        try:
            settings = json.loads(env_settings)
            return settings.get('credit_card_emails', CREDIT_CARD_EMAILS)
        except json.JSONDecodeError:
            return CREDIT_CARD_EMAILS
    return CREDIT_CARD_EMAILS

def get_additional_recipients():
    """Get additional recipients list"""
    env_settings = os.environ.get('APP_SETTINGS')
    if env_settings:
        try:
            settings = json.loads(env_settings)
            return settings.get('additional_recipients', ADDITIONAL_RECIPIENTS)
        except json.JSONDecodeError:
            return ADDITIONAL_RECIPIENTS
    return ADDITIONAL_RECIPIENTS

def get_settings():
    """Get system settings"""
    env_settings = os.environ.get('APP_SETTINGS')
    if env_settings:
        try:
            settings = json.loads(env_settings)
            return settings.get('settings', {'emails_enabled': True, 'zapier_enabled': True})
        except json.JSONDecodeError:
            return {'emails_enabled': True, 'zapier_enabled': True}
    return {'emails_enabled': True, 'zapier_enabled': True}
