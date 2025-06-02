import pandas as pd
import math # Import math for checking NaN

def parse_quiz_excel(file_path):
    try:
        df = pd.read_excel(file_path)
        questions_data = []
        for index, row in df.iterrows():
            # Validate required columns
            required_cols = ['কুইজ নাম্বার', 'প্রশ্ন', 'অপশন ১', 'অপশন ২', 'অপশন ৩', 'অপশন ৪', 'সঠিক অপশন নাম্বার', 'নেগেটিভ মার্ক', 'পয়েন্ট']
            if not all(col in df.columns for col in required_cols):
                raise ValueError(f"Missing one or more required columns in the Excel sheet. Required: {', '.join(required_cols)}")
            
            # Use .get() and check for NaN for optional/nullable fields
            media_url_val = row.get('ভিডিও/ছবি লিঙ্ক')
            if pd.isna(media_url_val): # Check if it's NaN (Not a Number) from pandas
                media_url_val = None
            else:
                media_url_val = str(media_url_val).strip() # Convert to string if not NaN

            question = {
                'quiz_number': int(row['কুইজ নাম্বার']), # Assuming this is quiz ID or just a serial
                'question_text': str(row['প্রশ্ন']),
                'option1': str(row['অপশন ১']),
                'option2': str(row['অপশন ২']),
                'option3': str(row['অপশন ৩']),
                'option4': str(row['অপশন ৪']),
                'correct_option_number': int(row['সঠিক অপশন নাম্বার']),
                'point_value': float(row['পয়েন্ট']),
                'negative_mark': float(row['নেগেটিভ মার্ক']),
                'media_url': media_url_val
            }
            # Basic validation for correct_option_number
            if not (1 <= question['correct_option_number'] <= 4):
                raise ValueError(f"Invalid correct option number in row {index + 2} (Quiz Number {question.get('quiz_number', 'N/A')}). Must be between 1 and 4.")
            questions_data.append(question)
        return questions_data
    except Exception as e:
        print(f"Error parsing Excel file: {e}")
        raise e