# polyquiz/models.py

from datetime import datetime
from database import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    current_level = db.Column(db.Integer, default=1)
    total_points = db.Column(db.Float, default=0.0)
    selected_class = db.Column(db.String(50), nullable=True)

    attempts = db.relationship('UserQuizAttempt', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username}>"

class AdminUser(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property 
    def is_admin(self):
        return True

    def __repr__(self):
        return f"<AdminUser {self.username}>"

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    image_url = db.Column(db.String(500), nullable=True) 
    chapters = db.relationship('Chapter', backref='subject', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Subject {self.name}>"

class Chapter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    for_class = db.Column(db.String(50), nullable=True) 
    is_active = db.Column(db.Boolean, default=True)
    image_url = db.Column(db.String(500), nullable=True) 
    questions = db.relationship('QuizQuestion', backref='chapter', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Chapter {self.name} ({self.subject.name})>"

class QuizQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    option1 = db.Column(db.String(255), nullable=False)
    option2 = db.Column(db.String(255), nullable=False)
    option3 = db.Column(db.String(255), nullable=False)
    option4 = db.Column(db.String(255), nullable=False)
    correct_option_number = db.Column(db.Integer, nullable=False)
    point_value = db.Column(db.Float, default=1.0)
    negative_mark = db.Column(db.Float, default=0.0)
    media_url = db.Column(db.String(500), nullable=True)
    difficulty = db.Column(db.String(20), default='সহজ')

    def __repr__(self):
        return f"<QuizQuestion {self.question_text[:30]}>"

class SiteSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(100), unique=True, nullable=False)
    setting_value = db.Column(db.Text, nullable=True)
    
    # ADDED: For footer/developer info (confirm these are present and correct)
    developer_name_text = db.Column(db.String(255), nullable=True) 
    developer_image_url = db.Column(db.String(500), nullable=True) 
    facebook_link = db.Column(db.String(500), nullable=True)
    instagram_link = db.Column(db.String(500), nullable=True)

    def __repr__(self):
        return f"<SiteSetting {self.setting_key}>"

class UserQuizAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id'), nullable=False)
    score = db.Column(db.Float, nullable=False)
    total_questions = db.Column(db.Integer, nullable=False)
    attempt_date = db.Column(db.DateTime, default=datetime.utcnow)
    answered_questions_data = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<Attempt User:{self.user_id} Chapter:{self.chapter_id} Score:{self.score}>"