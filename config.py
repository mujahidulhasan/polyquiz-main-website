import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    # --- Make sure these two lines are exactly as below ---
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # --- End of crucial lines ---

    UPLOAD_FOLDER = 'static/uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'webm', 'pdf'}

    CLOUDINARY_CLOUD_NAME = os.getenv('CLOUDINARY_CLOUD_NAME')
    CLOUDINARY_API_KEY = os.getenv('CLOUDINARY_API_KEY')
    CLOUDINARY_API_SECRET = os.getenv('CLOUDINARY_API_SECRET')
    CLOUDINARY_UPLOAD_FOLDER = os.getenv('CLOUDINARY_UPLOAD_FOLDER', 'polyquiz_media')