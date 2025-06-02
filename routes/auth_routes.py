from flask import Blueprint, render_template, redirect, url_for, flash, request
from models import User, AdminUser # Ensure these models are correctly imported
from forms import LoginForm, RegistrationForm # Ensure these forms are correctly imported
from database import db # Ensure db instance is correctly imported
from werkzeug.security import generate_password_hash # Used for hashing password during registration

from flask_login import login_user, logout_user, login_required, current_user

# Define the Blueprint for authentication routes
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # If user is already authenticated, redirect them based on their role
    if current_user.is_authenticated:
        # Check if logged in user is admin by type (more robust)
        if isinstance(current_user, AdminUser):
            return redirect(url_for('admin.dashboard')) # Assuming admin dashboard route exists
        # Check if logged in user is regular user by type
        elif isinstance(current_user, User):
            return redirect(url_for('user.dashboard')) # Assuming user dashboard route exists
    
    form = LoginForm() # Create an instance of the login form
    if form.validate_on_submit(): # Process form submission if valid
        username = form.username.data
        password = form.password.data

        # Try logging in as regular user first
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user) # Log in the user
            flash('ব্যবহারকারী হিসেবে লগইন সফল!', 'success') # Success message
            return redirect(url_for('user.dashboard')) # Redirect to user dashboard
        
        # If not a regular user, try logging in as an admin
        admin_user = AdminUser.query.filter_by(username=username).first()
        if admin_user and admin_user.check_password(password):
            login_user(admin_user) # Log in the admin
            flash('অ্যাডমিন হিসেবে লগইন সফল!', 'success') # Success message
            return redirect(url_for('admin.dashboard')) # Redirect to admin dashboard
        
        # If neither user type found or password incorrect
        flash('ভুল ইউজারনেম বা পাসওয়ার্ড।', 'danger') # Error message
    return render_template('auth/login.html', form=form) # Render login page

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    # If user is already authenticated, redirect them
    if current_user.is_authenticated:
        return redirect(url_for('user.dashboard')) 
    
    form = RegistrationForm() # Create an instance of the registration form
    if form.validate_on_submit(): # Process form submission if valid
        # Check if username or email already exists
        existing_username = User.query.filter_by(username=form.username.data).first()
        existing_email = User.query.filter_by(email=form.email.data).first()
        
        if existing_username:
            flash('এই ইউজারনেমটি ইতিমধ্যে ব্যবহৃত হয়েছে।', 'danger')
        elif existing_email:
            flash('এই ইমেইলটি ইতিমধ্যে ব্যবহৃত হয়েছে।', 'danger')
        else:
            # Hash the password before storing
            hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
            
            # Create a new User object
            new_user = User(
                username=form.username.data, 
                email=form.email.data, 
                password_hash=hashed_password,
                selected_class=form.selected_class.data
            )
            db.session.add(new_user) # Add new user to database session
            db.session.commit() # Commit changes to database
            flash('রেজিস্ট্রেশন সফল! আপনি এখন লগইন করতে পারেন।', 'success') # Success message
            return redirect(url_for('auth.login')) # Redirect to login page
    return render_template('auth/register.html', form=form) # Render registration page

@auth_bp.route('/logout')
@login_required # Requires user to be logged in to access this route
def logout():
    logout_user() # Log out the current user
    flash('আপনি লগআউট করেছেন।', 'info') # Info message
    return redirect(url_for('auth.login')) # Redirect to login page