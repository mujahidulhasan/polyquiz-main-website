import os
from flask import Flask, render_template, redirect, url_for, flash, request
from dotenv import load_dotenv
from config import Config
from database import db, init_db
from models import User, AdminUser, Subject, Chapter, QuizQuestion, SiteSetting
from utils.file_upload_handler import init_cloudinary
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash # For initial admin user
from datetime import datetime # For datetime.now().year in templates

# --- Load environment variables from .env file ---
load_dotenv()

app = Flask(__name__, instance_relative_config=True)
app.config.from_object(Config)

# --- CORRECTED PLACEMENT OF SECRET_KEY ASSIGNMENT ---
# Explicitly set SECRET_KEY here, immediately after app.config.from_object(Config)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
# --- END CORRECTED PLACEMENT ---

# --- Explicitly set SQLALCHEMY_DATABASE_URI and SQLALCHEMY_TRACK_MODIFICATIONS ---
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# --- END ADDITION ---

# --- ADDED: Session cookie configuration for local development ---
# Set to True in production (HTTPS on Render)
app.config['SESSION_COOKIE_SECURE'] = True
app.config['REMEMBER_COOKIE_SECURE'] = True
# --- END ADDITION ---


# Ensure local upload folder exists if local testing
if not os.path.exists(os.path.join(app.root_path, app.config['UPLOAD_FOLDER'])):
    os.makedirs(os.path.join(app.root_path, app.config['UPLOAD_FOLDER']))

# Initialize extensions
init_db(app) # Initialize SQLAlchemy
init_cloudinary(app) # Initialize Cloudinary (requires CLOUDINARY_CLOUD_NAME etc. in .env)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login' # Define the login view for redirection
login_manager.login_message_category = 'info'
login_manager.login_message = "Please log in to access this page."

# IMPORTANT: UserAdapter and load_user for handling both User and AdminUser types with Flask-Login
# This makes current_user.is_admin, current_user.username work correctly.
class UserAdapter(UserMixin):
    def __init__(self, obj):
        self.obj = obj

    def get_id(self):
        # Flask-Login calls this to get the ID to store in the session.
        # We prefix admin IDs to distinguish them from regular users.
        if isinstance(self.obj, AdminUser):
            return f"admin_{self.obj.id}"
        return str(self.obj.id)

    def __getattr__(self, name):
        # This allows current_user.username, current_user.is_admin etc. to work
        # by delegating calls to the underlying User or AdminUser object.
        return getattr(self.obj, name)

# Flask-Login: Tells how to load a user from the user ID stored in the session
@login_manager.user_loader
def load_user(user_id):
    if user_id.startswith('admin_'):
        admin_id = int(user_id.split('_')[1])
        admin_user = AdminUser.query.get(admin_id)
        if admin_user:
            return UserAdapter(admin_user) # Wrap AdminUser in UserAdapter
    else:
        user_id = int(user_id) # Regular user ID is just integer
        regular_user = User.query.get(user_id)
        if regular_user:
            return UserAdapter(regular_user) # Wrap User in UserAdapter
    return None # Return None if user not found


# --- Blueprints ---
# Import all blueprints correctly
from routes.auth_routes import auth_bp
from routes.user_routes import user_bp
from routes.admin_routes import admin_bp

# Register blueprints with their URL prefixes
app.register_blueprint(auth_bp)
app.register_blueprint(user_bp, url_prefix='/user')
app.register_blueprint(admin_bp, url_prefix='/admin')

# --- Database Initialization and Initial Data Setup ---
# This block runs when the app context is available (e.g., during app startup)
with app.app_context():
    db.create_all() # Create all tables in the database

    # Create a default Admin user if none exists for initial access
    if not AdminUser.query.filter_by(username='admin').first():
        default_admin = AdminUser(username='admin')
        # SET YOUR ADMIN PASSWORD HERE. CHANGE IT TO A SECURE ONE!
        default_admin.set_password('QizMaker*001%') 
        db.session.add(default_admin)
        db.session.commit()
        print("Default admin user 'admin' created. **CHANGE PASSWORD IMMEDIATELY AFTER FIRST LOGIN!**")

    # Set initial site settings for homepage notice and theme if they don't exist
    if not SiteSetting.query.filter_by(setting_key='homepage_notice').first():
        db.session.add(SiteSetting(setting_key='homepage_notice', setting_value=''))
    if not SiteSetting.query.filter_by(setting_key='default_theme').first():
        db.session.add(SiteSetting(setting_key='default_theme', setting_value='default'))
    db.session.commit()

# --- Global context processor for current theme and notice ---
# This makes current_notice, current_theme, and datetime available in all templates
@app.context_processor
def inject_global_data():
    notice_setting = SiteSetting.query.filter_by(setting_key='homepage_notice').first()
    current_notice = notice_setting.setting_value if notice_setting else ''

    theme_setting = SiteSetting.query.filter_by(setting_key='default_theme').first()
    current_theme = theme_setting.setting_value if theme_setting else 'default'

    return dict(current_notice=current_notice, current_theme=current_theme, datetime=datetime)


# --- Error Handlers (for 404 and 500 pages) ---
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

# --- Main route for homepage ---
@app.route('/')
def index():
    subjects = Subject.query.filter_by(is_active=True).all()
    return render_template('index.html', subjects=subjects)

# --- Entry point for running the Flask application ---
if __name__ == '__main__':
    app.run(debug=True)