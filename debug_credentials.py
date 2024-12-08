import os
import json
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def debug_credentials():
    # Get the raw credentials from environment
    creds_json = os.environ.get('GOOGLE_CREDENTIALS')
    if not creds_json:
        logger.error("GOOGLE_CREDENTIALS not found in environment")
        return
        
    logger.info("=== Raw Credentials String ===")
    logger.info(creds_json)
    
    try:
        # Try to parse as JSON
        creds_dict = json.loads(creds_json)
        logger.info("\n=== Parsed JSON Successfully ===")
        
        # Check required fields
        required_fields = ['type', 'project_id', 'private_key', 'client_email']
        missing_fields = [f for f in required_fields if f not in creds_dict]
        if missing_fields:
            logger.error(f"Missing required fields: {missing_fields}")
        else:
            logger.info("All required fields present")
            
        # Try to fix the private key
        if 'private_key' in creds_dict:
            fixed_key = creds_dict['private_key']
            logger.info("\n=== Fixed Private Key ===")
            logger.info(fixed_key)
            
            # Check if key looks valid
            if "-----BEGIN PRIVATE KEY-----" in fixed_key and "-----END PRIVATE KEY-----" in fixed_key:
                logger.info("Private key format looks valid")
            else:
                logger.error("Private key format is invalid")
                
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {str(e)}")
        
if __name__ == "__main__":
    debug_credentials()
