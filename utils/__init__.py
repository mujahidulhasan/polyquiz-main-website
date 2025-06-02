import pandas as pd

def parse_quiz_excel(file_path):
    try:
        df = pd.read_excel(file_path)
        questions_data = []
        for index, row in df.iterrows():
            # Validate required columns
            if not all(col in row for col in ['প্রশ্ন', 'অপশন ১', 'অপশন ২', 'অপশন ৩', 'অপশন ৪', 'সঠিক অপশন নাম্বার', 'পয়েন্ট', 'নেগেটিভ মার্ক']):
                raise ValueError(f"Missing required columns in row {index + 2}. Required: প্রশ্ন, অপশন ১-৪, সঠিক অপশন নাম্বার, পয়েন্ট, নেগেটিভ মার্ক")

            question = {
                'question_text': str(row['প্রশ্ন']),
                'option1': str(row['অপশন ১']),
                'option2': str(row['অপশন ২']),
                'option3': str(row['অপশন ৩']),
                'option4': str(row['অপশন ৪']),
                'correct_option_number': int(row['সঠিক অপশন নাম্বার']),
                'point_value': float(row['পয়েন্ট']),
                'negative_mark': float(row['নেগেটিভ মার্ক']),
                'media_url': str(row.get('ভিডিও/ছবি লিঙ্ক', '')).strip() if pd.notna(row.get('ভিডিও/ছবি লিঙ্ক')) else None
            }
            # Basic validation for correct_option_number
            if not (1 <= question['correct_option_number'] <= 4):
                raise ValueError(f"Invalid correct option number in row {index + 2}. Must be between 1 and 4.")
            questions_data.append(question)
        return questions_data
    except Exception as e:
        print(f"Error parsing Excel file: {e}")
        raise e