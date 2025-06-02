import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from models import AdminUser, Subject, Chapter, QuizQuestion, SiteSetting, User # Import User model for management
from database import db
from forms import SubjectForm, ChapterForm, QuizUploadForm, QuestionForm, SiteSettingForm
from utils.excel_parser import parse_quiz_excel
from utils import file_upload_handler # Correct way to import the module for allowed_file
from werkzeug.utils import secure_filename # Import secure_filename here if used in this file

admin_bp = Blueprint('admin', __name__)

# --- Helper function to check if current user is admin ---
def is_admin():
    return current_user.is_authenticated and isinstance(current_user, AdminUser)

# --- Admin Dashboard and Root of Admin Blueprint ---
# This single route handles both /admin/ and /admin/dashboard
@admin_bp.route('/')
@admin_bp.route('/dashboard')
@login_required
def dashboard():
    if not is_admin():
        flash('আপনার অ্যাডমিন প্যানেলে প্রবেশ করার অনুমতি নেই।', 'danger')
        # Redirect to the main login page provided by auth_bp for all users
        return redirect(url_for('auth.login'))
    return render_template('admin/admin_dashboard.html')

# --- Admin Login Route (Redirects to main login) ---
# This route exists to provide an 'admin.login' endpoint that Flask-Login expects
# when it tries to redirect to admin login. It simply points to the main login page.
@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    return redirect(url_for('auth.login'))

# --- Subject Management ---
@admin_bp.route('/subjects', methods=['GET', 'POST'])
@login_required
def manage_subjects():
    if not is_admin(): return redirect(url_for('auth.login'))
    
    form = SubjectForm()
    if form.validate_on_submit():
        subject_name = form.name.data
        is_active = form.is_active.data
        existing_subject = Subject.query.filter_by(name=subject_name).first()
        if existing_subject:
            flash('এই বিষয় ইতিমধ্যে বিদ্যমান।', 'danger')
        else:
            new_subject = Subject(name=subject_name, is_active=is_active)
            db.session.add(new_subject)
            db.session.commit()
            flash('বিষয় সফলভাবে যোগ করা হয়েছে!', 'success')
            return redirect(url_for('admin.manage_subjects'))
    
    subjects = Subject.query.all()
    return render_template('admin/manage_subjects.html', subjects=subjects, form=form)

@admin_bp.route('/subjects/edit/<int:subject_id>', methods=['GET', 'POST'])
@login_required
def edit_subject(subject_id):
    if not is_admin(): return redirect(url_for('auth.login'))
    
    subject = Subject.query.get_or_404(subject_id)
    form = SubjectForm(obj=subject) # Populate form with existing data
    
    if form.validate_on_submit():
        subject.name = form.name.data
        subject.is_active = form.is_active.data
        db.session.commit()
        flash('বিষয় সফলভাবে আপডেট করা হয়েছে!', 'success')
        return redirect(url_for('admin.manage_subjects'))
    
    return render_template('admin/edit_subject.html', form=form, subject=subject)

@admin_bp.route('/subjects/delete/<int:subject_id>', methods=['POST'])
@login_required
def delete_subject(subject_id):
    if not is_admin(): return redirect(url_for('auth.login'))
    
    subject = Subject.query.get_or_404(subject_id)
    db.session.delete(subject)
    db.session.commit()
    flash('বিষয় সফলভাবে মুছে ফেলা হয়েছে!', 'info')
    return redirect(url_for('admin.manage_subjects'))

# --- Chapter Management ---
@admin_bp.route('/chapters', methods=['GET', 'POST'])
@login_required
def manage_chapters():
    if not is_admin(): return redirect(url_for('auth.login'))
    
    form = ChapterForm()
    form.subject_id.choices = [(s.id, s.name) for s in Subject.query.order_by(Subject.name).all()]
    form.subject_id.choices.insert(0, (0, 'একটি বিষয় নির্বাচন করুন')) # Add a default placeholder

    if form.validate_on_submit():
        chapter_name = form.name.data
        subject_id = form.subject_id.data
        for_class = form.for_class.data
        is_active = form.is_active.data

        existing_chapter = Chapter.query.filter_by(name=chapter_name, subject_id=subject_id, for_class=for_class).first()
        if existing_chapter:
            flash('এই অধ্যায়টি এই বিষয়ে এবং ক্লাসে ইতিমধ্যে বিদ্যমান।', 'danger')
        else:
            new_chapter = Chapter(name=chapter_name, subject_id=subject_id, for_class=for_class, is_active=is_active)
            db.session.add(new_chapter)
            db.session.commit()
            flash('অধ্যায় সফলভাবে যোগ করা হয়েছে!', 'success')
            return redirect(url_for('admin.manage_chapters'))
    
    chapters = Chapter.query.order_by(Chapter.subject_id, Chapter.name).all()
    return render_template('admin/manage_chapters.html', chapters=chapters, form=form)

@admin_bp.route('/chapters/edit/<int:chapter_id>', methods=['GET', 'POST'])
@login_required
def edit_chapter(chapter_id):
    if not is_admin(): return redirect(url_for('auth.login'))
    
    chapter = Chapter.query.get_or_404(chapter_id)
    form = ChapterForm(obj=chapter)
    form.subject_id.choices = [(s.id, s.name) for s in Subject.query.order_by(Subject.name).all()]
    
    if form.validate_on_submit():
        chapter.name = form.name.data
        chapter.subject_id = form.subject_id.data
        chapter.for_class = form.for_class.data
        chapter.is_active = form.is_active.data
        db.session.commit()
        flash('অধ্যায় সফলভাবে আপডেট করা হয়েছে!', 'success')
        return redirect(url_for('admin.manage_chapters'))
    
    return render_template('admin/edit_chapter.html', form=form, chapter=chapter)

@admin_bp.route('/chapters/delete/<int:chapter_id>', methods=['POST'])
@login_required
def delete_chapter(chapter_id):
    if not is_admin(): return redirect(url_for('auth.login'))
    
    chapter = Chapter.query.get_or_404(chapter_id)
    db.session.delete(chapter)
    db.session.commit()
    flash('অধ্যায় সফলভাবে মুছে ফেলা হয়েছে!', 'info')
    return redirect(url_for('admin.manage_chapters'))

# --- Quiz Upload (Excel) ---
@admin_bp.route('/quiz_upload', methods=['GET', 'POST'])
@login_required
def upload_quiz():
    if not is_admin(): return redirect(url_for('auth.login'))
    
    form = QuizUploadForm()
    form.subject_id.choices = [(s.id, s.name) for s in Subject.query.order_by(Subject.name).all()]
    form.chapter_id.choices = [(c.id, c.name) for c in Chapter.query.order_by(Chapter.name).all()]
    
    if form.validate_on_submit():
        subject_id = form.subject_id.data
        chapter_id = form.chapter_id.data
        excel_file = form.excel_file.data
        
        subject = Subject.query.get(subject_id)
        chapter = Chapter.query.get(chapter_id)

        if not subject or not chapter:
            flash('বৈধ বিষয় বা অধ্যায় নির্বাচন করুন।', 'danger')
            return render_template('admin/upload_quiz.html', form=form)

        if not excel_file:
            flash('কোনো ফাইল নির্বাচন করা হয়নি।', 'danger')
            return render_template('admin/upload_quiz.html', form=form)
        
        # Corrected: Call allowed_file from file_upload_handler module
        if not file_upload_handler.allowed_file(excel_file.filename):
            flash('শুধুমাত্র .xlsx ফাইল অনুমোদিত।', 'danger')
            return render_template('admin/upload_quiz.html', form=form)

        try:
            # Save locally temporarily to parse
            from werkzeug.utils import secure_filename # Import secure_filename locally for this function
            temp_filepath = os.path.join(current_app.root_path, current_app.config['UPLOAD_FOLDER'], secure_filename(excel_file.filename))
            excel_file.save(temp_filepath)
            
            # Parse the excel file
            questions_data = parse_quiz_excel(temp_filepath)
            
            # Add questions to DB
            for q_data in questions_data:
                # Check if question with same text/quiz_number already exists for this chapter/difficulty
                # You might need a more robust uniqueness check or allow duplicates
                existing_question = QuizQuestion.query.filter_by(
                    chapter_id=chapter.id, 
                    question_text=q_data['question_text']
                ).first()

                if existing_question:
                    # Update existing question
                    existing_question.option1 = q_data['option1']
                    existing_question.option2 = q_data['option2']
                    existing_question.option3 = q_data['option3']
                    existing_question.option4 = q_data['option4']
                    existing_question.correct_option_number = q_data['correct_option_number']
                    existing_question.point_value = q_data['point_value']
                    existing_question.negative_mark = q_data['negative_mark']
                    
                    # Handle media_url update/deletion if question is updated
                    if existing_question.media_url and q_data['media_url'] is None: # Old media exists, new is none
                        file_upload_handler.delete_file_from_cloudinary(existing_question.media_url)
                        existing_question.media_url = None
                    elif q_data['media_url']: # New media provided or updated
                        # If old exists and is different, delete old first
                        if existing_question.media_url and existing_question.media_url != q_data['media_url']:
                            file_upload_handler.delete_file_from_cloudinary(existing_question.media_url)
                        existing_question.media_url = q_data['media_url'] # Use provided URL directly
                else:
                    new_question = QuizQuestion(
                        chapter_id=chapter.id,
                        question_text=q_data['question_text'],
                        option1=q_data['option1'],
                        option2=q_data['option2'],
                        option3=q_data['option3'],
                        option4=q_data['option4'],
                        correct_option_number=q_data['correct_option_number'],
                        point_value=q_data['point_value'],
                        negative_mark=q_data['negative_mark'],
                        media_url=q_data['media_url']
                        # difficulty (from excel or default?) - needs decision if from excel
                        # Default difficulty as 'সহজ' for new questions
                        # or you can add a difficulty column to Excel
                    )
                    db.session.add(new_question)
            
            db.session.commit()
            flash(f'{len(questions_data)} টি প্রশ্ন সফলভাবে আপলোড করা হয়েছে!', 'success')

        except Exception as e:
            db.session.rollback() # Rollback changes on error
            flash(f'প্রশ্ন আপলোডে ত্রুটি: {e}', 'danger')
        finally:
            # Clean up temporary local file
            if os.path.exists(temp_filepath):
                os.remove(temp_filepath)
            
            return redirect(url_for('admin.upload_quiz'))

    return render_template('admin/upload_quiz.html', form=form)

# --- Site Settings (Notice & Theme) ---
@admin_bp.route('/site_settings', methods=['GET', 'POST'])
@login_required
def site_settings():
    if not is_admin(): return redirect(url_for('auth.login'))
    
    form = SiteSettingForm()
    
    # Load current settings for GET request
    notice_setting = SiteSetting.query.filter_by(setting_key='homepage_notice').first()
    theme_setting = SiteSetting.query.filter_by(setting_key='default_theme').first()

    if request.method == 'GET':
        if notice_setting: form.homepage_notice.data = notice_setting.setting_value
        if theme_setting: form.theme_setting.data = theme_setting.setting_value
    
    if form.validate_on_submit():
        # Update Homepage Notice
        if notice_setting:
            notice_setting.setting_value = form.homepage_notice.data
        else:
            new_notice_setting = SiteSetting(setting_key='homepage_notice', setting_value=form.homepage_notice.data)
            db.session.add(new_notice_setting)
        
        # Update Default Theme
        if theme_setting:
            theme_setting.setting_value = form.theme_setting.data
        else:
            new_theme_setting = SiteSetting(setting_key='default_theme', setting_value=form.theme_setting.data)
            db.session.add(new_theme_setting)
        
        db.session.commit()
        flash('সাইট সেটিংস সফলভাবে আপডেট করা হয়েছে!', 'success')
        return redirect(url_for('admin.site_settings'))
            
    return render_template('admin/site_settings.html', form=form)

# --- User Management (Placeholder, similar to subject/chapter) ---
@admin_bp.route('/users')
@login_required
def manage_users():
    if not is_admin(): return redirect(url_for('auth.login'))
    
    users = User.query.all()
    return render_template('admin/manage_users.html', users=users)

# Add routes for add/edit/delete individual questions if needed (not from excel)
# @admin_bp.route('/questions') ...
# @admin_bp.route('/questions/add') ...
# @admin_bp.route('/questions/edit/<int:question_id>') ...
# @admin_bp.route('/questions/delete/<int:question_id>') ...