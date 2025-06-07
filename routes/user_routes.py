from flask import Blueprint, render_template, redirect, url_for, flash, session, request, jsonify 
from flask_login import login_required, current_user
from models import User, AdminUser, Subject, Chapter, QuizQuestion, UserQuizAttempt, db
import json
from sqlalchemy import func
from datetime import datetime
import logging 
from flask_wtf.csrf import generate_csrf 

logger = logging.getLogger(__name__)

user_bp = Blueprint('user', __name__)

@user_bp.route('/dashboard')
@login_required # Requires user to be logged in
def dashboard():
    logger.info("Attempting to access user dashboard.")
    if isinstance(current_user, AdminUser):
        flash('অ্যাডমিন ড্যাশবোর্ডে প্রবেশ করুন।', 'info')
        logger.warning(f"Admin user {current_user.username} tried to access user dashboard. Redirecting.")
        return redirect(url_for('admin.dashboard')) 

    user_subjects = []
    user_chapters = []

    if current_user.selected_class:
        user_chapters = Chapter.query.filter_by(for_class=current_user.selected_class, is_active=True).all()
        
        seen_subject_ids = set()
        for chapter in user_chapters:
            if chapter.subject and chapter.subject.is_active and chapter.subject.id not in seen_subject_ids:
                user_subjects.append(chapter.subject)
                seen_subject_ids.add(chapter.subject.id)
    
    logger.info(f"User {current_user.username} dashboard loaded. Class: {current_user.selected_class}, Subjects found: {len(user_subjects)}")
    return render_template('user_dashboard.html', user_subjects=user_subjects, user_chapters=user_chapters)

@user_bp.route('/select_chapter/<int:subject_id>')
def select_chapter(subject_id):
    logger.info(f"Attempting to select chapter for subject ID: {subject_id}")
    subject = Subject.query.get_or_404(subject_id)
    
    chapters = Chapter.query.filter_by(subject_id=subject.id, is_active=True).order_by(Chapter.name).all()
    
    logger.info(f"Found {len(chapters)} chapters for subject {subject.name}.")
    return render_template('chapter_selection.html', subject=subject, chapters=chapters)

@user_bp.route('/play_quiz/<int:chapter_id>')
# @login_required # Temporarily disabled for easier testing
def play_quiz(chapter_id):
    logger.info(f"Attempting to play quiz for chapter ID: {chapter_id}")
    chapter = Chapter.query.get_or_404(chapter_id)
    
    questions = QuizQuestion.query.filter_by(chapter_id=chapter.id).order_by(func.random()).limit(10).all()

    if not questions:
        logger.info(f"No questions found for chapter ID: {chapter_id}. Redirecting.")
        flash(f'দুঃখিত, "{chapter.name}" অধ্যায়ের জন্য কোনো প্রশ্ন উপলব্ধ নেই। অ্যাডমিনকে প্রশ্ন যোগ করতে বলুন।', 'no-question-notice') 
        return redirect(url_for('user.select_chapter', subject_id=chapter.subject.id))
    
    logger.info(f"Found {len(questions)} questions for chapter ID: {chapter_id}. Starting quiz.")

    quiz_data_for_session = []
    for q in questions:
        quiz_data_for_session.append({
            'id': q.id,
            'question_text': q.question_text,
            'option1': q.option1,
            'option2': q.option2,
            'option3': q.option3,
            'option4': q.option4,
            'correct_option_number': q.correct_option_number,
            'point_value': q.point_value,
            'negative_mark': q.negative_mark,
            'media_url': q.media_url,
            'difficulty': q.difficulty
        })
    
    session['current_quiz'] = quiz_data_for_session
    session['current_question_index'] = 0
    session['user_answers'] = []
    session['quiz_chapter_id'] = chapter.id
    session['quiz_total_score'] = 0.0

    csrf_token = generate_csrf() 
    
    return render_template('quiz_play.html', chapter=chapter, csrf_token=csrf_token)

@user_bp.route('/save_quiz_progress', methods=['POST'])
# @login_required # Temporarily disabled for easier testing
def save_quiz_progress():
    logger.info("Received request to save quiz progress.")
    # Verify CSRF token manually as it's an AJAX request
    if not request.headers.get('X-CSRFToken'):
        logger.warning("CSRF token missing in AJAX request headers.")
        return jsonify({'status': 'error', 'message': 'CSRF টoken অনুপস্থিত।'}), 403 
    
    try: 
        data = request.get_json()
        
        quiz_data = session.get('current_quiz')
        current_question_index = session.get('current_question_index')
        user_answers = session.get('user_answers')
        quiz_total_score = session.get('quiz_total_score', 0.0)

        if not quiz_data or current_question_index is None or user_answers is None:
            logger.error("save_quiz_progress: Quiz data not found in session or invalid state.")
            return jsonify({'status': 'error', 'message': 'কুইজ ডেটা সেশনে পাওয়া যায়নি বা সেশন মেয়াদোত্তীর্ণ।'}), 400

        question_id = data.get('question_id')
        user_choice = data.get('user_choice')
        
        if current_question_index >= len(quiz_data) or quiz_data[current_question_index]['id'] != question_id:
            logger.error(f"save_quiz_progress: Session question ID mismatch. Expected {quiz_data[current_question_index]['id']}, Got {question_id}. Current index {current_question_index}.")
            return jsonify({'status': 'error', 'message': 'সেশনের প্রশ্ন আইডি মিলছে না। সম্ভবত ব্রাউজার রিলোড হয়েছে।'}), 400

        question_details = quiz_data[current_question_index]
        is_correct = (user_choice == question_details['correct_option_number']) if user_choice is not None else False
        
        points_earned = 0.0
        if is_correct:
            points_earned = question_details['point_value']
        elif user_choice is not None:
            points_earned = -question_details['negative_mark']
        
        quiz_total_score += points_earned
        
        user_answers.append({
            'question_id': question_details['id'],
            'question_text': question_details['question_text'],
            'options': [question_details['option1'], question_details['option2'], question_details['option3'], question_details['option4']],
            'user_choice': user_choice,
            'correct_option_number': question_details['correct_option_number'],
            'is_correct': is_correct, 
            'points_earned': points_earned,
            'media_url': question_details['media_url']
        })

        session['user_answers'] = user_answers
        session['current_question_index'] = current_question_index + 1
        session['quiz_total_score'] = quiz_total_score

        new_user_total_points = None
        new_user_level = None

        if current_user.is_authenticated and isinstance(current_user, User):
            current_user.total_points += points_earned
            
            new_level = int(current_user.total_points / 100) + 1
            if new_level > current_user.current_level:
                current_user.current_level = new_level
                flash(f'অভিনন্দন! আপনি এখন লেভেল {current_user.current_level} এ উন্নীত হয়েছেন!', 'info')

            db.session.commit()
            new_user_total_points = current_user.total_points
            new_user_level = current_user.current_level
        
        return jsonify({ 
            'status': 'success', 
            'message': 'প্রগতি সেভ করা হয়েছে।', 
            'new_total_points': new_user_total_points, 
            'new_level': new_user_level,
            'quiz_finished': session['current_question_index'] >= len(quiz_data)
        }), 200

    except Exception as e: 
        db.session.rollback() 
        logger.exception("Error during save_quiz_progress processing:") 
        return jsonify({'status': 'error', 'message': f'সার্ভার প্রক্রিয়াকরণে ত্রুটি: {str(e)}'}), 500

@user_bp.route('/quiz_result/<int:chapter_id>')
def quiz_result(chapter_id):
    logger.info(f"Accessing quiz results for chapter ID: {chapter_id}")
    chapter = Chapter.query.get_or_404(chapter_id)
    
    user_answers = session.pop('user_answers', [])
    quiz_total_score = session.pop('quiz_total_score', 0.0)
    
    session.pop('current_quiz', None)
    session.pop('current_question_index', None)
    session.pop('quiz_chapter_id', None)
    session.pop('quiz_total_score', None)
    
    return render_template('quiz_result.html', 
                           chapter=chapter, 
                           answer_sheet=user_answers,
                           quiz_total_score=quiz_total_score,
                           total_questions_attempted=len(user_answers))