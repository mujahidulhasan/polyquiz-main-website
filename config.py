import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'static/uploads'
    
    # --- Ensure this line explicitly includes 'xlsx' for Excel uploads ---
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'webm', 'pdf', 'xlsx'} 
    # --- End of ALLOWED_EXTENSIONS ---

    # Cloudinary configuration
    CLOUDINARY_CLOUD_NAME = os.getenv('CLOUDINARY_CLOUD_NAME')
    CLOUDINARY_API_KEY = os.getenv('CLOUDINARY_API_KEY')
    CLOUDINARY_API_SECRET = os.getenv('CLOUDINARY_API_SECRET')
    CLOUDINARY_UPLOAD_FOLDER = os.getenv('CLOUDINARY_UPLOAD_FOLDER', 'polyquiz_media')