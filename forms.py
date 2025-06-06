# polyquiz/forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, IntegerField, SelectField, BooleanField, FloatField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange
from flask_wtf.file import FileField, FileAllowed

# from wtforms import FieldList, FormField # এই দুটি এখন আর দরকার নেই, তাই সরিয়ে দেওয়া হয়েছে

class LoginForm(FlaskForm):
    username = StringField('ইউজারনেম', validators=[DataRequired(), Length(min=2, max=80)])
    password = PasswordField('পাসওয়ার্ড', validators=[DataRequired()])
    submit = SubmitField('লগইন করুন')

class RegistrationForm(FlaskForm):
    username = StringField('ইউজারনেম', validators=[DataRequired(), Length(min=2, max=80)])
    email = StringField('ইমেইল', validators=[DataRequired(), Email()])
    password = PasswordField('পাসওয়ার্ড', validators=[DataRequired()])
    confirm_password = PasswordField('পাসওয়ার্ড নিশ্চিত করুন', validators=[DataRequired(), EqualTo('password')])
    selected_class = SelectField('ক্লাস নির্বাচন করুন', choices=[
        ('Class 8', 'অষ্টম শ্রেণি'),
        ('Class 9', 'নবম শ্রেণি'),
        ('Class 10', 'দশম শ্রেণি'),
        ('Class 11', 'একাদশ শ্রেণি'),
        ('Class 12', 'দ্বাদশ শ্রেণি')
    ], validators=[DataRequired()])
    submit = SubmitField('রেজিস্টার করুন')

# --- Admin Panel Forms ---

class SubjectForm(FlaskForm):
    name = StringField('বিষয় এর নাম', validators=[DataRequired(), Length(max=100)])
    is_active = BooleanField('সক্রিয় আছে?')
    image_file = FileField('বিষয় এর আইকন/ছবি আপলোড করুন', validators=[FileAllowed(['png', 'jpg', 'jpeg', 'gif'])])
    submit = SubmitField('সেভ করুন')

class ChapterForm(FlaskForm):
    name = StringField('অধ্যায় এর নাম', validators=[DataRequired(), Length(max=100)])
    subject_id = SelectField('বিষয় নির্বাচন করুন', coerce=int, validators=[DataRequired()])
    for_class = SelectField('ক্লাস নির্বাচন করুন', choices=[
        ('', 'নির্বাচন করুন'),
        ('Class 8', 'অষ্টম শ্রেণি'),
        ('Class 9', 'নবম শ্রেণি'),
        ('Class 10', 'দশম শ্রেণি'),
        ('Class 11', 'একাদশ শ্রেণি'),
        ('Class 12', 'দ্বাদশ শ্রেণি')
    ], validators=[DataRequired()])
    is_active = BooleanField('সক্রিয় আছে?')
    image_file = FileField('অধ্যায় এর আইকন/ছবি আপলোড করুন', validators=[FileAllowed(['png', 'jpg', 'jpeg', 'gif'])])
    submit = SubmitField('সেভ করুন')

# --- Quiz Upload Form (for Excel files) ---
class QuizUploadForm(FlaskForm): 
    subject_id = SelectField('বিষয় নির্বাচন করুন', coerce=int, validators=[DataRequired()])
    chapter_id = SelectField('অধ্যায় নির্বাচন করুন', coerce=int, validators=[DataRequired()])
    excel_file = FileField('এক্সেল ফাইল আপলোড করুন (.xlsx)', validators=[FileAllowed(['xlsx'])])
    submit = SubmitField('আপলোড করুন')

# QuestionForm (if you still need individual question editing routes)
class QuestionForm(FlaskForm): # For individual question management/editing later
    question_text = TextAreaField('প্রশ্ন', validators=[DataRequired()])
    option1 = StringField('অপশন ১', validators=[DataRequired()])
    option2 = StringField('অপশন ২', validators=[DataRequired()])
    option3 = StringField('অপশন ৩', validators=[DataRequired()])
    option4 = StringField('অপশন ৪', validators=[DataRequired()])
    correct_option_number = SelectField('সঠিক অপশন', choices=[
        ('1', 'অপশন ১'), ('2', 'অপশন ২'), ('3', 'অপশন ৩'), ('4', 'অপশন ৪')
    ], validators=[DataRequired()], coerce=int)
    point_value = FloatField('পয়েন্ট ভ্যালু', validators=[DataRequired(), NumberRange(min=0.1)])
    negative_mark = FloatField('নেগেটিভ মার্ক', validators=[DataRequired(), NumberRange(min=0.0)])
    media_file = FileField('ছবি/ভিডিও আপলোড করুন', validators=[FileAllowed(['png', 'jpg', 'jpeg', 'gif', 'mp4', 'webm'])])
    difficulty = SelectField('কঠিনতার স্তর', choices=[
        ('সহজ', 'সহজ'), ('কঠিন', 'কঠিন'), ('অধিক কঠিন', 'অধিক কঠিন')
    ], validators=[DataRequired()])
    submit = SubmitField('সেভ করুন')

class SiteSettingForm(FlaskForm):
    homepage_notice = TextAreaField('হোমপেজ নোটিশ', render_kw={"rows": 5})
    theme_setting = SelectField('ওয়েবসাইট থিম', choices=[('default', 'ডিফল্ট'), ('dark', 'ডার্ক')], validators=[DataRequired()])
    developer_name_text = StringField('ডেভেলপার নাম টেক্সট', validators=[Length(max=255)])
    developer_image_file = FileField('ডেভেলপার ছবি আপলোড করুন', validators=[FileAllowed(['png', 'jpg', 'jpeg', 'gif'])])
    facebook_link = StringField('ফেসবুক লিংক')
    instagram_link = StringField('ইনস্টাগ্রাম লিংক')
    submit = SubmitField('সেভ করুন')