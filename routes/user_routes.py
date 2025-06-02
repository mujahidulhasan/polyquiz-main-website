from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models import User, AdminUser, Subject, Chapter # Ensure AdminUser is imported if used in dashboard check
from database import db # Ensure db is imported

user_bp = Blueprint('user', __name__)

@user_bp.route('/dashboard')
@login_required # Requires user to be logged in
def dashboard():
    # If the user is an AdminUser but somehow lands here, redirect to admin dashboard
    # This check ensures that only regular 'User' type can access this specific dashboard.
    if isinstance(current_user, AdminUser): # Check if it's explicitly an AdminUser object
        flash('অ্যাডমিন ড্যাশবোর্ডে প্রবেশ করুন।', 'info')
        return redirect(url_for('admin.dashboard')) # Redirect to admin dashboard route

    # Logic for regular user dashboard
    user_subjects = []
    user_chapters = [] # Chapters relevant to user's selected class

    if current_user.selected_class:
        # Get chapters for the user's class that are active
        user_chapters = Chapter.query.filter_by(for_class=current_user.selected_class, is_active=True).all()
        
        # Get unique subjects for these chapters
        seen_subject_ids = set()
        for chapter in user_chapters:
            # Ensure chapter.subject is not None and subject is active before adding
            if chapter.subject and chapter.subject.is_active and chapter.subject.id not in seen_subject_ids:
                user_subjects.append(chapter.subject) # Append the Subject object
                seen_subject_ids.add(chapter.subject.id)

    return render_template('user_dashboard.html', user_subjects=user_subjects, user_chapters=user_chapters)

# Add more user-specific routes here later (e.g., quiz play, results)