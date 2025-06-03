import pandas as pd
import math

def parse_quiz_excel(file_path):
    """
    Parses an Excel file to extract quiz question data without a header row.
    Assumes fixed column order as per user's requirement.
    """
    try:
        # Read Excel without header, assign column names manually
        # Column order: Question Text, Option1, Option2, Option3, Option4, Correct Option Number, Negative Mark, Point, Media URL
        df = pd.read_excel(file_path, header=None, names=[
            'question_text', 'option1', 'option2', 'option3', 'option4',
            'correct_option_number', 'negative_mark', 'point_value', 'media_url' # Assuming media_url is the last column
        ])
        
        questions_data = []
        
        for index, row in df.iterrows():
            # Basic validation: ensure essential columns are not empty
            if pd.isna(row['question_text']) or pd.isna(row['option1']) or \
               pd.isna(row['correct_option_number']) or pd.isna(row['point_value']) or \
               pd.isna(row['negative_mark']):
                print(f"Skipping row {index + 1} due to missing essential data.")
                continue # Skip rows with incomplete essential data

            # Handle optional media_url column
            media_url_val = row.get('media_url')
            if pd.isna(media_url_val):
                media_url_val = None
            else:
                media_url_val = str(media_url_val).strip()

            question = {
                'question_text': str(row['question_text']),
                'option1': str(row['option1']),
                'option2': str(row['option2']), # Even if empty in sheet, will be 'nan' then str
                'option3': str(row['option3']),
                'option4': str(row['option4']),
                'correct_option_number': int(row['correct_option_number']),
                'negative_mark': float(row['negative_mark']),
                'point_value': float(row['point_value']),
                'media_url': media_url_val
            }
            
            # Validation for correct_option_number
            if not (1 <= question['correct_option_number'] <= 4):
                raise ValueError(
                    f"Invalid correct option number in row {index + 1}. "
                    f"Must be between 1 and 4. Found: {question['correct_option_number']}"
                )
            
            questions_data.append(question)
        return questions_data
    except Exception as e:
        print(f"Error parsing Excel file (no header mode): {e}")
        raise e