import cloudinary
import cloudinary.uploader
import os
from flask import current_app

# Cloudinary credentials will be loaded from app.config
def init_cloudinary(app):
    cloudinary.config(
        cloud_name=app.config['CLOUDINARY_CLOUD_NAME'],
        api_key=app.config['CLOUDINARY_API_KEY'],
        api_secret=app.config['CLOUDINARY_API_SECRET']
    )

def allowed_file(filename):
    """Checks if the file's extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def upload_file_to_cloudinary(file, folder_name=None):
    """
    Uploads a file to Cloudinary.
    Optionally organizes files into a specific folder within Cloudinary.
    """
    try:
        # Create a unique public_id for Cloudinary
        # Cloudinary public_ids should use forward slashes for folders
        # secure_filename returns a safe filename, then we ensure forward slashes
        from werkzeug.utils import secure_filename
        filename = secure_filename(file.filename)
        
        # Construct public_id: CLOUDINARY_UPLOAD_FOLDER/folder_name/filename_without_extension
        upload_folder_base = current_app.config['CLOUDINARY_UPLOAD_FOLDER']
        
        # Use os.path.splitext to separate name and extension
        name_without_ext, file_extension = os.path.splitext(filename)
        
        # Combine folder parts and filename part with forward slashes
        # Ensure path is always forward slashes for Cloudinary
        if folder_name:
            # Combine base upload folder, specific folder, and filename
            # Replace backslashes with forward slashes to ensure Cloudinary compatibility
            cloudinary_path = f"{upload_folder_base}/{folder_name}/{name_without_ext}"
        else:
            cloudinary_path = f"{upload_folder_base}/{name_without_ext}"
        
        # Cloudinary upload options
        options = {
            "public_id": cloudinary_path.replace("\\", "/"), # Ensure all slashes are forward
            "overwrite": True,
            "resource_type": "auto", # auto-detect image/video
        }
        
        # Perform the upload
        upload_result = cloudinary.uploader.upload(file, **options)
        
        # Return the secure URL of the uploaded file
        return upload_result['secure_url']
    except Exception as e:
        current_app.logger.error(f"Error uploading file to Cloudinary: {e}")
        # Log the problematic public_id if possible for debugging
        if 'cloudinary_path' in locals():
             current_app.logger.error(f"Problematic public_id: {cloudinary_path}")
        return None

def delete_file_from_cloudinary(image_url):
    """Deletes a file from Cloudinary using its public_id."""
    if not image_url:
        return True # Nothing to delete
    
    try:
        # Extract public_id from Cloudinary URL
        # URL format: https://res.cloudinary.com/cloud_name/image/upload/v12345/public_id.extension
        # Need to parse the public_id part
        parts = image_url.split('/')
        
        # The public_id starts after 'upload/vXXXXXXXXX/' and before the last dot (extension)
        # Find the index of 'upload' and get the parts after it
        upload_index = -1
        for i, part in enumerate(parts):
            if part == 'upload':
                upload_index = i
                break
        
        if upload_index == -1 or upload_index + 2 >= len(parts):
            current_app.logger.warning(f"Could not parse public_id from URL: {image_url}")
            return False

        # public_id is everything after 'upload/vXXXXX/' up to the file extension
        # Join parts from 'upload_index + 2' to the second last part (excluding version number and extension)
        public_id_with_extension = "/".join(parts[upload_index + 2:])
        
        # Remove file extension to get the clean public_id
        public_id = os.path.splitext(public_id_with_extension)[0]

        # Cloudinary delete options
        delete_result = cloudinary.uploader.destroy(public_id, resource_type="image") # Assuming it's an image
        
        if delete_result.get('result') == 'ok':
            return True
        else:
            current_app.logger.error(f"Cloudinary delete failed for public_id {public_id}: {delete_result}")
            return False
    except Exception as e:
        current_app.logger.error(f"Error deleting file from Cloudinary: {e}")
        return False