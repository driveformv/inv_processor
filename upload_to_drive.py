from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from authorize import get_credentials
import os
import mimetypes
import json
import hashlib
from datetime import datetime

# Target folder ID for uploads
TARGET_FOLDER_ID = '1adzLMJObHtkliMT1GA2k1msS8x2RK1oQ'
UPLOAD_HISTORY_FILE = 'upload_history.json'

def get_service():
    """Get authorized Google Drive service"""
    credentials = get_credentials()
    return build('drive', 'v3', credentials=credentials)

def get_file_hash(file_path):
    """Calculate MD5 hash of file to track changes"""
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        buf = f.read(65536)  # Read in 64kb chunks
        while len(buf) > 0:
            hasher.update(buf)
            buf = f.read(65536)
    return hasher.hexdigest()

def load_upload_history():
    """Load the history of uploaded files"""
    if os.path.exists(UPLOAD_HISTORY_FILE):
        with open(UPLOAD_HISTORY_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_upload_history(history):
    """Save the upload history to file"""
    with open(UPLOAD_HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

def get_mime_type(file_path):
    """Get the MIME type based on file extension"""
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type is None:
        mime_type = 'application/octet-stream'
    return mime_type

def upload_file_to_drive(file_path, file_name=None, folder_id=TARGET_FOLDER_ID):
    """
    Uploads a file to Google Drive.

    :param file_path: Path to the file
    :param file_name: Name to save the file as in Google Drive (optional)
    :param folder_id: ID of the folder to upload to (defaults to TARGET_FOLDER_ID)
    :return: ID of the uploaded file
    """
    service = get_service()
    
    if not file_name:
        file_name = os.path.basename(file_path)
    
    file_metadata = {
        'name': file_name,
        'parents': [folder_id]
    }
    
    mime_type = get_mime_type(file_path)
    media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
    
    try:
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        return file.get('id')
    except Exception as e:
        print(f"Error uploading {file_name}: {str(e)}")
        return None

def process_uploads():
    """Process files in the uploads directory and only upload new or modified files"""
    test_dir = 'uploads'
    if not os.path.exists(test_dir):
        os.makedirs(test_dir)
    
    # Load upload history
    upload_history = load_upload_history()
    
    # Get list of files in uploads directory
    files = [f for f in os.listdir(test_dir) if os.path.isfile(os.path.join(test_dir, f))]
    
    if not files:
        print(f"No files found in {test_dir} directory")
        return
    
    print(f"Checking {len(files)} files for new uploads...")
    new_uploads = 0
    
    for file_name in files:
        file_path = os.path.join(test_dir, file_name)
        file_hash = get_file_hash(file_path)
        
        # Check if file has been uploaded before and hasn't changed
        if file_name in upload_history and upload_history[file_name]['hash'] == file_hash:
            print(f"Skipping {file_name} (already uploaded)")
            continue
        
        try:
            file_id = upload_file_to_drive(file_path)
            # Update upload history
            upload_history[file_name] = {
                'hash': file_hash,
                'drive_id': file_id,
                'upload_date': datetime.now().isoformat(),
                'file_size': os.path.getsize(file_path)
            }
            new_uploads += 1
            print(f"Successfully uploaded new file: {file_name}")
        except Exception as e:
            print(f"Error uploading {file_name}: {str(e)}")
    
    # Save updated upload history
    save_upload_history(upload_history)
    print(f"\nUpload session complete:")
    print(f"- New files uploaded: {new_uploads}")
    print(f"- Total files tracked: {len(upload_history)}")

if __name__ == "__main__":
    process_uploads()
