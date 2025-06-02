import cloudinary
import cloudinary.uploader
import os
from flask import url_for, current_app # Added current_app for allowed_file

def init_cloudinary(app):
    """Initializes Cloudinary configuration with app settings."""
    cloudinary.config(
        cloud_name=app.config['CLOUDINARY_CLOUD_NAME'],
        api_key=app.config['CLOUDINARY_API_KEY'],
        api_secret=app.config['CLOUDINARY_API_SECRET']
    )

def upload_file_to_cloudinary(file, folder_name=None):
    """
    Uploads a file to Cloudinary.
    :param file: The file object from Flask's request.files.
    :param folder_name: Optional subfolder name within the main Cloudinary upload folder.
    :return: The secure URL of the uploaded file, or None if upload fails.
    """
    if not file:
        return None
    try:
        # Get the base upload folder from app.config (e.g., 'polyquiz_media')
        base_upload_folder = current_app.config['CLOUDINARY_UPLOAD_FOLDER']
        
        # Combine base folder with a subfolder if provided, otherwise just use base folder
        full_folder_path_on_cloudinary = os.path.join(base_upload_folder, folder_name or 'misc_uploads')
        
        # Upload the file
        upload_result = cloudinary.uploader.upload(file, folder=full_folder_path_on_cloudinary)
        
        # Return the secure URL of the uploaded file
        return upload_result.get('secure_url')
    except Exception as e:
        print(f"Error uploading file to Cloudinary: {e}")
        # In a production app, you might log the full traceback here
        return None

def delete_file_from_cloudinary(url):
    """
    Deletes a file from Cloudinary using its URL.
    :param url: The secure URL of the file on Cloudinary.
    :return: True if deletion is successful, False otherwise.
    """
    if not url:
        return False
    try:
        # Extract the public ID including the folder path from the URL
        # Example URL: https://res.cloudinary.com/cloud_name/image/upload/v12345/my_base_folder/sub_folder/public_id_of_file.png
        # We need: my_base_folder/sub_folder/public_id_of_file
        
        # Get the path part after '/upload/' or '/v<version>/'
        parts = url.split('/upload/')
        if len(parts) < 2:
            parts = url.split('/v') # Fallback if /upload/ is missing
            if len(parts) < 2: return False # Not a valid Cloudinary URL
            
        public_id_with_version = parts[-1]
        
        # Remove version number if present (like v1234567890/) and file extension
        public_id_path_with_ext = '/'.join(public_id_with_version.split('/')[1:]) # Removes potential 'v1234567890' part
        public_id_without_ext = os.path.splitext(public_id_path_with_ext)[0] # Removes '.png' or '.jpg'

        # Finally, delete from Cloudinary
        cloudinary.uploader.destroy(public_id_without_ext)
        print(f"Deleted {public_id_without_ext} from Cloudinary.")
        return True
    except Exception as e:
        print(f"Error deleting file from Cloudinary: {e}")
        return False

def allowed_file(filename):
    """
    Checks if a file's extension is allowed based on app configuration.
    :param filename: The name of the file.
    :return: True if extension is allowed, False otherwise.
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']