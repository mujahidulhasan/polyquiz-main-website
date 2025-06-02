import os
from flask import Flask, render_template, redirect, url_for, flash, request, session
from dotenv import load_dotenv
from config import Config
from database import db, init_db
from models import User, AdminUser, Subject, Chapter, QuizQuestion, SiteSetting
from utils.file_upload_handler import init_cloudinary
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash # For initial admin user
from datetime import datetime
import logging
from flask_session import Session # ADDED: Import Flask-Session

# --- Setup logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Load environment variables from .env file ---
load_dotenv()

app = Flask(__name__, instance_relative_config=True)
app.config.from_object(Config)

# --- Explicitly set SECRET_KEY ---
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
logger.info(f"App SECRET_KEY loaded (length: {len(app.config['SECRET_KEY']) if app.config['SECRET_KEY'] else 'None'})")

# --- Explicitly set SQLALCHEMY_DATABASE_URI and SQLALCHEMY_TRACK_MODIFICATIONS ---
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- ADDED: Flask-Session configuration for Server-Side Sessions ---
app.config['SESSION_TYPE'] = 'sqlalchemy' # Store sessions in SQLAlchemy database
app.config['SESSION_SQLALCHEMY'] = db # Use our existing SQLAlchemy database instance
app.config['SESSION_USE_SIGNER'] = True # Sign the session ID cookie for security
app.config['SESSION_PERMANENT'] = False # Sessions are not permanent by default (cleared on browser close)
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax' # Good default for CSRF protection

# IMPORTANT for Render/Production (HTTPS):
app.config['SESSION_COOKIE_SECURE'] = True      # Only send session cookie over HTTPS
app.config['REMEMBER_COOKIE_SECURE'] = True     # For Flask-Login's remember me cookie
app.config['SESSION_COOKIE_HTTPONLY'] = True    # Prevent client-side JS access to session cookie
app.config['REMEMBER_COOKIE_HTTPONLY'] = True   # For Flask-Login's remember me cookie
# --- END ADDITION ---


# Ensure local upload folder exists if local testing
if not os.path.exists(os.path.join(app.root_path, app.config['UPLOAD_FOLDER'])):
    os.makedirs(os.path.join(app.root_path, app.config['UPLOAD_FOLDER']))

# Initialize extensions
init_db(app) # Initialize SQLAlchemy
init_cloudinary(app) # Initialize Cloudinary (requires CLOUDINARY_CLOUD_NAME etc. in .env)

# Initialize Flask-Session AFTER db is initialized
server_session = Session(app) # ADDED: Initialize Flask-Session

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'
login_manager.login_message = "Please log in to access this page."

# IMPORTANT: UserAdapter and load_user for handling both User and AdminUser types with Flask-Login
class UserAdapter(UserMixin):
    def __init__(self, obj):
        self.obj = obj

    def get_id(self):
        if isinstance(self.obj, AdminUser):
            return f"admin_{self.obj.id}"
        return str(self.obj.id)

    def __getattr__(self, name):
        return getattr(self.obj, name)

# Flask-Login: Tells how to load a user from the user ID stored in the session
@login_manager.user_loader
def load_user(user_id):
    logger.info(f"load_user called for user_id: {user_id}")
    if user_id.startswith('admin_'):
        admin_id = int(user_id.split('_')[1])
        admin_user = AdminUser.query.get(admin_id)
        if admin_user:
            logger.info(f"load_user: Found AdminUser {admin_user.username}")
            return UserAdapter(admin_user)
    else:
        try:
            user_id_int = int(user_id)
            regular_user = User.query.get(user_id_int)
            if regular_user:
                logger.info(f"load_user: Found User {regular_user.username}")
                return UserAdapter(regular_user)
        except ValueError:
            logger.error(f"load_user: Invalid user_id format: {user_id}")
            return None
    logger.info(f"load_user: User with ID {user_id} not found.")
    return None


# --- Blueprints ---
from routes.auth_routes import auth_bp
from routes.user_routes import user_bp
from routes.admin_routes import admin_bp

app.register_blueprint(auth_bp)
app.register_blueprint(user_bp, url_prefix='/user')
app.register_blueprint(admin_bp, url_prefix='/admin')

# --- Database Initialization and Initial Data Setup ---
with app.app_context():
    # Flask-Session needs its table created explicitly
    db.create_all() # Create all application tables
    server_session.create_all() # ADDED: Create session table

    if not AdminUser.query.filter_by(username='admin').first():
        default_admin = AdminUser(username='admin')
        default_admin.set_password('QizMaker*001%')
        db.session.add(default_admin)
        db.session.commit()
        logger.info("Default admin user 'admin' created. **CHANGE PASSWORD IMMEDIATELY!**")

    if not SiteSetting.query.filter_by(setting_key='homepage_notice').first():
        db.session.add(SiteSetting(setting_key='homepage_notice', setting_value=''))
    if not SiteSetting.query.filter_by(setting_key='default_theme').first():
        db.session.add(SiteSetting(setting_key='default_theme', setting_value='default'))
    db.session.commit()

# --- Global context processor ---
@app.context_processor
def inject_global_data():
    notice_setting = SiteSetting.query.filter_by(setting_key='homepage_notice').first()
    current_notice = notice_setting.setting_value if notice_setting else ''

    theme_setting = SiteSetting.query.filter_by(setting_key='default_theme').first()
    current_theme = theme_setting.setting_value if theme_setting else 'default'

    return dict(current_notice=current_notice, current_theme=current_theme, datetime=datetime)


# --- Error Handlers ---
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