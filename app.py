import os
from flask import Flask, render_template, redirect, url_for, flash, request, session
from dotenv import load_dotenv
from config import Config
from database import db, init_db
from models import User, AdminUser, Subject, Chapter, QuizQuestion, SiteSetting
from utils.file_upload_handler import init_cloudinary
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash
from datetime import datetime
import logging 
from flask_session import Session # Import Flask-Session after db is initialized

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

# --- Flask-Session configuration for Server-Side Sessions ---
app.config['SESSION_TYPE'] = 'sqlalchemy' 
app.config['SESSION_SQLALCHEMY'] = db 
app.config['SESSION_USE_SIGNER'] = True 
app.config['SESSION_PERMANENT'] = False 
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax' 

# IMPORTANT for Render/Production (HTTPS):
app.config['SESSION_COOKIE_SECURE'] = True      
app.config['REMEMBER_COOKIE_SECURE'] = True     
app.config['SESSION_COOKIE_HTTPONLY'] = True    
app.config['REMEMBER_COOKIE_HTTPONLY'] = True   


# Ensure local upload folder exists if local testing
if not os.path.exists(os.path.join(app.root_path, app.config['UPLOAD_FOLDER'])):
    os.makedirs(os.path.join(app.root_path, app.config['UPLOAD_FOLDER']))

# Initialize extensions
init_db(app) 
server_session = Session(app) # Initialize Flask-Session
init_cloudinary(app) 

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
    db.create_all() 
    # REMOVED: server_session.create_all() # This line caused the error, db.create_all() handles it

    if not AdminUser.query.filter_by(username='admin').first():
        default_admin = AdminUser(username='admin')
        default_admin.set_password('QizMaker*001%') 
        db.session.add(default_admin)
        db.session.commit()
        logger.info("Default admin user 'admin' created. **CHANGE PASSWORD IMMEDIATELY AFTER FIRST LOGIN!**")

    # Set initial site settings for homepage notice and theme if they don't exist
    # Also for developer info if it doesn't exist
    if not SiteSetting.query.filter_by(setting_key='homepage_notice').first():
        db.session.add(SiteSetting(setting_key='homepage_notice', setting_value=''))
    if not SiteSetting.query.filter_by(setting_key='default_theme').first():
        db.session.add(SiteSetting(setting_key='default_theme', setting_value='default'))
    
    # Initialize developer info settings if not exist
    if not SiteSetting.query.filter_by(setting_key='developer_name_text').first():
        db.session.add(SiteSetting(setting_key='developer_name_text', setting_value='Developed by Mujahid'))
    if not SiteSetting.query.filter_by(setting_key='developer_image_url').first():
        db.session.add(SiteSetting(setting_key='developer_image_url', setting_value='')) 
    if not SiteSetting.query.filter_by(setting_key='facebook_link').first():
        db.session.add(SiteSetting(setting_key='facebook_link', setting_value=''))
    if not SiteSetting.query.filter_by(setting_key='instagram_link').first():
        db.session.add(SiteSetting(setting_key='instagram_link', setting_value=''))
    
    db.session.commit()


# --- Global context processor for current theme and notice and developer info ---
@app.context_processor
def inject_global_data():
    notice_setting = SiteSetting.query.filter_by(setting_key='homepage_notice').first()
    current_notice = notice_setting.setting_value if notice_setting else ''

    theme_setting = SiteSetting.query.filter_by(setting_key='default_theme').first()
    current_theme = theme_setting.setting_value if theme_setting else 'default'

    developer_name_setting = SiteSetting.query.filter_by(setting_key='developer_name_text').first()
    developer_image_setting = SiteSetting.query.filter_by(setting_key='developer_image_url').first()
    facebook_link_setting = SiteSetting.query.filter_by(setting_key='facebook_link').first()
    instagram_link_setting = SiteSetting.query.filter_by(setting_key='instagram_link').first()

    current_site_settings = {
        'developer_name_text': developer_name_setting.setting_value if developer_name_setting else '',
        'developer_image_url': developer_image_setting.setting_value if developer_image_setting else '',
        'facebook_link': facebook_link_setting.setting_value if facebook_link_setting else '',
        'instagram_link': instagram_link_setting.setting_value if instagram_link_setting else ''
    }

    return dict(current_notice=current_notice, current_theme=current_theme, datetime=datetime, current_site_settings=current_site_settings)


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