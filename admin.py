import json
import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from functools import wraps
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Get admin credentials from environment variables
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'appmaster')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'AppMast3r.')

admin_bp = Blueprint('admin', __name__)

# Use absolute path for settings file
SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'settings.json')

def load_settings():
    """Load settings from JSON file"""
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f)
    return {
        'credit_card_emails': {},
        'additional_recipients': [],
        'settings': {
            'emails_enabled': True,
            'zapier_enabled': True
        }
    }

def save_settings(settings):
    """Save settings to JSON file"""
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=4)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/admin/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin.admin_dashboard'))
        flash('Invalid credentials')
    return render_template('admin_login.html')

@admin_bp.route('/admin/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin.login'))

@admin_bp.route('/admin')
@login_required
def admin_dashboard():
    """Render admin dashboard"""
    settings = load_settings()
    return render_template('admin.html',
                         credit_cards=settings['credit_card_emails'],
                         recipients=settings['additional_recipients'],
                         settings=settings['settings'])

@admin_bp.route('/admin/settings', methods=['POST'])
@login_required
def update_settings():
    """Update system settings"""
    settings = load_settings()
    settings['settings']['emails_enabled'] = 'emails_enabled' in request.form
    settings['settings']['zapier_enabled'] = 'zapier_enabled' in request.form
    save_settings(settings)
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/admin/credit-cards', methods=['POST'])
@login_required
def update_credit_cards():
    """Update credit card mappings"""
    settings = load_settings()
    
    # Get lists of card names and emails from form
    card_names = request.form.getlist('card_name[]')
    card_emails = request.form.getlist('card_email[]')
    
    # Create new mapping
    new_mappings = {}
    for name, email in zip(card_names, card_emails):
        if name and email:  # Only add if both fields are filled
            new_mappings[name] = email
    
    settings['credit_card_emails'] = new_mappings
    save_settings(settings)
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/admin/recipients', methods=['POST'])
@login_required
def update_recipients():
    """Update additional recipients"""
    settings = load_settings()
    
    # Get list of recipients from form
    recipients = request.form.getlist('recipients[]')
    
    # Filter out empty emails
    settings['additional_recipients'] = [email for email in recipients if email]
    save_settings(settings)
    return redirect(url_for('admin.admin_dashboard'))
