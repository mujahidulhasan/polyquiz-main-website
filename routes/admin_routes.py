import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user 
from models import AdminUser, Subject, Chapter, QuizQuestion, SiteSetting, User 
from database import db
from forms import SubjectForm, ChapterForm, QuizUploadForm, QuestionForm, SiteSettingForm 
from utils.excel_parser import parse_quiz_excel
from utils import file_upload_handler 
from werkzeug.utils import secure_filename
import logging 

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__)

# --- Helper function to check if current user is admin ---
# TEMPORARILY DISABLED for direct access. RE-ENABLE FOR SECURITY!
# def is_admin():
#    return current_user.is_authenticated and isinstance(current_user, AdminUser)

# --- Admin Dashboard and Root of Admin Blueprint ---
@admin_bp.route('/') 
@admin_bp.route('/dashboard') 
# @login_required 
def dashboard():
    return render_template('admin/admin_dashboard.html')

# --- Admin Login Route (Redirects to main login) ---
@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    return redirect(url_for('auth.login'))

# --- Subject Management ---
@admin_bp.route('/subjects', methods=['GET', 'POST'])
# @login_required 
def manage_subjects():
    form = SubjectForm()
    if form.validate_on_submit():
        subject_name = form.name.data
        is_active = form.is_active.data
        image_file = form.image_file.data # Get file from form

        existing_subject = Subject.query.filter_by(name=subject_name).first()
        if existing_subject:
            flash('এই বিষয় ইতিমধ্যে বিদ্যমান।', 'danger')
        else:
            image_url = None
            if image_file and file_upload_handler.allowed_file(image_file.filename):
                image_url = file_upload_handler.upload_file_to_cloudinary(image_file, folder_name='subject_icons')
                if not image_url:
                    flash('ছবি আপলোডে ত্রুটি।', 'danger')
                    return render_template('admin/manage_subjects.html', subjects=Subject.query.all(), form=form)

            new_subject = Subject(name=subject_name, is_active=is_active, image_url=image_url) # Save URL
            db.session.add(new_subject)
            db.session.commit()
            flash('বিষয় সফলভাবে যোগ করা হয়েছে!', 'success')
            return redirect(url_for('admin.manage_subjects'))
    
    subjects = Subject.query.all()
    return render_template('admin/manage_subjects.html', subjects=subjects, form=form)

@admin_bp.route('/subjects/edit/<int:subject_id>', methods=['GET', 'POST'])
# @login_required 
def edit_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    form = SubjectForm(obj=subject) 
    
    if form.validate_on_submit():
        subject.name = form.name.data
        subject.is_active = form.is_active.data
        image_file = form.image_file.data # Get file from form

        if image_file and file_upload_handler.allowed_file(image_file.filename):
            # Delete old image from Cloudinary if it exists
            if subject.image_url:
                file_upload_handler.delete_file_from_cloudinary(subject.image_url)
            
            new_image_url = file_upload_handler.upload_file_to_cloudinary(image_file, folder_name='subject_icons')
            if not new_image_url:
                flash('নতুন ছবি আপলোডে ত্রুটি।', 'danger')
                return render_template('admin/edit_subject.html', form=form, subject=subject)
            subject.image_url = new_image_url # Save new URL
        elif 'remove_image' in request.form and request.form['remove_image'] == 'true': # Option to remove existing image
            if subject.image_url:
                file_upload_handler.delete_file_from_cloudinary(subject.image_url)
            subject.image_url = None
        
        db.session.commit()
        flash('বিষয় সফলভাবে আপডেট করা হয়েছে!', 'success')
        return redirect(url_for('admin.manage_subjects'))
    
    return render_template('admin/edit_subject.html', form=form, subject=subject)

@admin_bp.route('/subjects/delete/<int:subject_id>', methods=['POST'])
# @login_required 
def delete_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    if subject.image_url: # Delete image from Cloudinary
        file_upload_handler.delete_file_from_cloudinary(subject.image_url)
    
    db.session.delete(subject)
    db.session.commit()
    flash('বিষয় সফলভাবে মুছে ফেলা হয়েছে!', 'info')
    return redirect(url_for('admin.manage_subjects'))

# --- Chapter Management ---
@admin_bp.route('/chapters', methods=['GET', 'POST'])
# @login_required 
def manage_chapters():
    form = ChapterForm()
    form.subject_id.choices = [(s.id, s.name) for s in Subject.query.order_by(Subject.name).all()]
    form.subject_id.choices.insert(0, (0, 'একটি বিষয় নির্বাচন করুন')) # Add a default placeholder

    if form.validate_on_submit():
        chapter_name = form.name.data
        subject_id = form.subject_id.data
        #for_class = form.for_class.data
        is_active = form.is_active.data
        image_file = form.image_file.data # Get file from form

        existing_chapter = Chapter.query.filter_by(name=chapter_name, subject_id=subject_id, for_class=for_class).first()
        if existing_chapter:
            flash('এই অধ্যায়টি এই বিষয়ে এবং ক্লাসে ইতিমধ্যে বিদ্যমান।', 'danger')
        else:
            image_url = None
            if image_file and file_upload_handler.allowed_file(image_file.filename):
                image_url = file_upload_handler.upload_file_to_cloudinary(image_file, folder_name='chapter_icons')
                if not image_url:
                    flash('অধ্যায়ের ছবি আপলোডে ত্রুটি।', 'danger')
                    return render_template('admin/manage_chapters.html', chapters=Chapter.query.all(), form=form, subjects=Subject.query.all()) # ADDED subjects here
            new_chapter = Chapter(name=chapter_name, subject_id=subject_id, for_class=for_class, is_active=is_active, image_url=image_url)
            db.session.add(new_chapter)
            db.session.commit()
            flash('অধ্যায় সফলভাবে যোগ করা হয়েছে!', 'success')
            return redirect(url_for('admin.manage_chapters'))
    
    chapters = Chapter.query.order_by(Chapter.subject_id, Chapter.name).all()
    subjects = Subject.query.all() # ADDED: Query all subjects
    return render_template('admin/manage_chapters.html', chapters=chapters, form=form, subjects=subjects) # CHANGED: Pass subjects

@admin_bp.route('/chapters/edit/<int:chapter_id>', methods=['GET', 'POST'])
# @login_required 
def edit_chapter(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    form = ChapterForm(obj=chapter)
    form.subject_id.choices = [(s.id, s.name) for s in Subject.query.order_by(Subject.name).all()]
    
    if form.validate_on_submit():
        chapter.name = form.name.data
        chapter.subject_id = form.subject_id.data
        #chapter.for_class = form.for_class.data
        chapter.is_active = form.is_active.data
        image_file = form.image_file.data

        if image_file and file_upload_handler.allowed_file(image_file.filename):
            if chapter.image_url:
                file_upload_handler.delete_file_from_cloudinary(chapter.image_url)
            
            new_image_url = file_upload_handler.upload_file_to_cloudinary(image_file, folder_name='chapter_icons')
            if not new_image_url:
                flash('নতুন অধ্যায়ের ছবি আপloade ত্রুটি।', 'danger')
                return render_template('admin/edit_chapter.html', form=form, chapter=chapter, subjects=Subject.query.all()) # ADDED subjects here
            chapter.image_url = new_image_url
        elif 'remove_image' in request.form and request.form['remove_image'] == 'true':
            if chapter.image_url:
                file_upload_handler.delete_file_from_cloudinary(chapter.image_url)
            chapter.image_url = None
        
        db.session.commit()
        flash('অধ্যায় সফলভাবে আপডেট করা হয়েছে!', 'success')
        return redirect(url_for('admin.manage_chapters'))
    
    return render_template('admin/edit_chapter.html', form=form, chapter=chapter, subjects=Subject.query.all()) # CHANGED: Pass subjects

@admin_bp.route('/chapters/delete/<int:chapter_id>', methods=['POST'])
# @login_required 
def delete_chapter(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    if chapter.image_url:
        file_upload_handler.delete_file_from_cloudinary(chapter.image_url)
    
    db.session.delete(chapter)
    db.session.commit()
    flash('অধ্যায় সফলভাবে মুছে ফেলা হয়েছে!', 'info')
    return redirect(url_for('admin.manage_chapters'))

# --- Quiz Upload (Excel File Upload) ---
@admin_bp.route('/quiz_upload', methods=['GET', 'POST']) 
# @login_required 
def upload_quiz(): 
    form = QuizUploadForm()
    form.subject_id.choices = [(s.id, s.name) for s in Subject.query.order_by(Subject.name).all()]
    form.chapter_id.choices = [(c.id, c.name) for c in Chapter.query.order_by(Chapter.name).all()]
    
    if form.validate_on_submit():
        subject = Subject.query.get(form.subject_id.data)
        chapter = Chapter.query.get(form.chapter_id.data)

        if not subject or not chapter:
            flash('বৈধ বিষয় বা অধ্যায় নির্বাচন করুন।', 'danger')
            return render_template('admin/quiz_upload.html', form=form)
        
        excel_file = form.excel_file.data
        if not excel_file:
            flash('কোনো ফাইল নির্বাচন করা হয়নি।', 'danger')
            return render_template('admin/quiz_upload.html', form=form)
        
        if not file_upload_handler.allowed_file(excel_file.filename):
            flash('শুধুমাত্র .xlsx ফাইল অনুমোদিত।', 'danger')
            return render_template('admin/quiz_upload.html', form=form)

        try:
            from werkzeug.utils import secure_filename
            temp_filepath = os.path.join(current_app.root_path, current_app.config['UPLOAD_FOLDER'], secure_filename(excel_file.filename))
            excel_file.save(temp_filepath)
            
            questions_data = parse_quiz_excel(temp_filepath)
            
            questions_added_count = 0
            for q_data in questions_data:
                if not q_data.get('question_text') or q_data.get('correct_option_number') is None:
                    flash(f"এক্সেল রোতে প্রশ্ন বা সঠিক অপশন অনুপস্থিত। রো নম্বর {q_data.get('quiz_number', 'অজ্ঞাত')}.", 'warning')
                    continue

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
                    media_url=q_data['media_url'], 
                    difficulty='সহজ'
                )
                db.session.add(new_question)
                questions_added_count += 1
            
            db.session.commit()
            flash(f'{questions_added_count} টি প্রশ্ন সফলভাবে আপলোড করা হয়েছে!', 'success')
            return redirect(url_for('admin.upload_quiz'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'প্রশ্ন আপলোডে ত্রুটি: {e}', 'danger')

    return render_template('admin/quiz_upload.html', form=form)


# --- Site Settings (Notice & Theme) ---
@admin_bp.route('/site_settings', methods=['GET', 'POST'])
# @login_required 
def site_settings():
    form = SiteSettingForm()
    
    notice_setting = SiteSetting.query.filter_by(setting_key='homepage_notice').first()
    theme_setting = SiteSetting.query.filter_by(setting_key='default_theme').first()
    
    developer_name_setting = SiteSetting.query.filter_by(setting_key='developer_name_text').first() 
    developer_image_setting = SiteSetting.query.filter_by(setting_key='developer_image_url').first()
    facebook_link_setting = SiteSetting.query.filter_by(setting_key='facebook_link').first()
    instagram_link_setting = SiteSetting.query.filter_by(setting_key='instagram_link').first()


    if request.method == 'GET':
        if notice_setting: form.homepage_notice.data = notice_setting.setting_value
        if theme_setting: form.theme_setting.data = theme_setting.setting_value
        if developer_name_setting: form.developer_name_text.data = developer_name_setting.setting_value
        if facebook_link_setting: form.facebook_link.data = facebook_link_setting.setting_value
        if instagram_link_setting: form.instagram_link.data = instagram_link_setting.setting_value
        
    if form.validate_on_submit():
        if notice_setting:
            notice_setting.setting_value = form.homepage_notice.data
        else:
            new_notice_setting = SiteSetting(setting_key='homepage_notice', setting_value=form.homepage_notice.data)
            db.session.add(new_notice_setting)
        
        if theme_setting:
            theme_setting.setting_value = form.theme_setting.data
        else:
            new_theme_setting = SiteSetting(setting_key='default_theme', setting_value=form.theme_setting.data)
            db.session.add(new_theme_setting)
        
        if developer_name_setting:
            developer_name_setting.setting_value = form.developer_name_text.data
        else:
            new_dev_name_setting = SiteSetting(setting_key='developer_name', setting_value=form.developer_name_text.data)
            db.session.add(new_dev_name_setting)
        
        developer_image_file = form.developer_image_file.data
        if developer_image_file and file_upload_handler.allowed_file(developer_image_file.filename):
            if developer_image_setting and developer_image_setting.setting_value: 
                file_upload_handler.delete_file_from_cloudinary(developer_image_setting.setting_value)
            new_image_url = file_upload_handler.upload_file_to_cloudinary(developer_image_file, folder_name='developer_image')
            if new_image_url:
                if developer_image_setting:
                    developer_image_setting.setting_value = new_image_url
                else:
                    db.session.add(SiteSetting(setting_key='developer_image_url', setting_value=new_image_url))
            else:
                flash('ডেভেলপার ছবি আপলোডে ত্রুটি।', 'danger')
        elif 'remove_developer_image' in request.form and request.form['remove_developer_image'] == 'true':
            if developer_image_setting and developer_image_setting.setting_value:
                file_upload_handler.delete_file_from_cloudinary(developer_image_setting.setting_value)
                developer_image_setting.setting_value = None 
        
        if facebook_link_setting:
            facebook_link_setting.setting_value = form.facebook_link.data
        else:
            new_fb_link_setting = SiteSetting(setting_key='facebook_link', setting_value=form.facebook_link.data)
            db.session.add(new_fb_link_setting)

        if instagram_link_setting:
            instagram_link_setting.setting_value = form.instagram_link.data
        else:
            new_insta_link_setting = SiteSetting(setting_key='instagram_link', setting_value=form.instagram_link.data)
            db.session.add(new_insta_link_setting)
            
        db.session.commit()
        flash('সাইট সেটিংস সফলভাবে আপডেট করা হয়েছে!', 'success')
        return redirect(url_for('admin.site_settings'))
            
    return render_template('admin/site_settings.html', form=form)

# --- User Management (Placeholder, similar to subject/chapter) ---
@admin_bp.route('/users')
# @login_required 
def manage_users():
    users = User.query.all()
    return render_template('admin/manage_users.html', users=users)

# Add routes for add/edit/delete individual questions if needed (not from excel)
# @admin_bp.route('/questions') ...
# @admin_bp.route('/questions/add') ...
# @admin_bp.route('/questions/edit/<int:question_id>') ...
# @admin_bp.route('/questions/delete/<int:question_id>') ...