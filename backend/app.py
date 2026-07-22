import sqlite3
import os
from flask import Flask, render_template, request, jsonify, send_from_directory
from backend.ai_service import make_request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', 'static'))
TEMPLATES_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', 'templates'))

app = Flask(__name__, static_folder=STATIC_DIR, template_folder=TEMPLATES_DIR)

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    return response

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "database")
DB_NAME = os.path.join(DB_DIR, "quiz.db")

def get_db_connection():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create users table for login page
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT NOT NULL,
            roll_number TEXT NOT NULL CHECK (length(roll_number) = 3 AND roll_number GLOB '[0-9][0-9][0-9]'),
            email TEXT,
            year TEXT NOT NULL,
            batch TEXT NOT NULL,
            login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Ensure email column exists if users table was created earlier without it
    cursor.execute("PRAGMA table_info(users)")
    columns = [col['name'] for col in cursor.fetchall()]
    if 'email' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")

    # Remove any existing duplicate emails, keeping the latest user row per email
    cursor.execute('''
        DELETE FROM users
        WHERE id NOT IN (
            SELECT MAX(id)
            FROM users
            WHERE email IS NOT NULL AND email != ''
            GROUP BY LOWER(email)
        ) AND email IS NOT NULL AND email != ''
    ''')

    # Create unique index on email to enforce uniqueness at database level
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users(LOWER(email));")
    
    # Create quiz results table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT NOT NULL,
            roll_number TEXT NOT NULL CHECK (length(roll_number) = 3 AND roll_number GLOB '[0-9][0-9][0-9]'),
            subject TEXT NOT NULL,
            score INTEGER NOT NULL,
            total INTEGER NOT NULL,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create questions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject VARCHAR(50) NOT NULL,
            question_text VARCHAR(500) NOT NULL,
            option_a VARCHAR(100) NOT NULL,
            option_b VARCHAR(100) NOT NULL,
            option_c VARCHAR(100) NOT NULL,
            option_d VARCHAR(100) NOT NULL,
            correct_index INT NOT NULL
        )
    ''')
    
    # Create subjects table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(50) NOT NULL UNIQUE,
            description VARCHAR(200) NOT NULL,
            icon VARCHAR(10) DEFAULT '📚',
            badge VARCHAR(30) DEFAULT 'Custom Quiz',
            created_by VARCHAR(100) DEFAULT 'User',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Seed default subjects if empty
    cursor.execute("SELECT COUNT(*) FROM subjects")
    if cursor.fetchone()[0] == 0:
        cursor.executemany('''
            INSERT INTO subjects (name, description, icon, badge, created_by)
            VALUES (?, ?, ?, ?, ?)
        ''', [
            ('Web Hosting', 'Shared, VPS, Dedicated Hosting, FTP & Domain Protocols', '🌐', 'Server & Cloud', 'System'),
            ('C programming', 'Pointers, Bitwise Operators, Memory & Standard Libraries', '💻', 'Core Concepts', 'System')
        ])

    # Check if questions table is empty, if so import from questions.sql
    cursor.execute("SELECT COUNT(*) FROM questions")
    count = cursor.fetchone()[0]
    
    sql_path = os.path.join(DB_DIR, "questions.sql")
    if count == 0 and os.path.exists(sql_path):
        print("Initializing database from questions.sql...")
        with open(sql_path, "r", encoding="utf-8") as f:
            sql_script = f.read()
            cursor.executescript(sql_script)
    
    conn.commit()
    conn.close()

# HTML URL Routing & Aliases
@app.route('/')
@app.route('/index.html')
def index_page():
    return render_template('index.html')

@app.route('/subjects')
@app.route('/subjects.html')
def subjects_page():
    return render_template('subjects.html')

@app.route('/quiz')
@app.route('/quiz.html')
def quiz_page():
    return render_template('quiz.html')

@app.route('/result')
@app.route('/result.html')
def result_page():
    return render_template('result.html')

@app.route('/profile')
@app.route('/profile.html')
def profile_page():
    return render_template('profile.html')

# Fallback route for static assets
@app.route('/<path:filename>')
def serve_static(filename):
    if filename.endswith('.css'):
        return send_from_directory('static/css', filename)
    elif filename.endswith('.js'):
        return send_from_directory('static/js', filename)
    return send_from_directory('static', filename)

import re

# API Endpoints
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    mode = data.get('mode', 'login').strip() # 'login' or 'register'
    student_name = data.get('studentName', '').strip()
    roll_number = data.get('rollNumber', '').strip()
    email = data.get('email', '').strip()
    year = data.get('year', '').strip()
    batch = data.get('batch', '').strip()

    if not email:
        return jsonify({'status': 'error', 'message': 'Email address is required.'}), 400

    if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email):
        return jsonify({'status': 'error', 'message': 'Please enter a valid email address.'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if a user with this email already exists
    cursor.execute('SELECT * FROM users WHERE LOWER(email) = LOWER(?)', (email,))
    existing_user = cursor.fetchone()

    # --- MODE 1: LOGIN MODE ---
    if mode == 'login':
        if not existing_user:
            conn.close()
            return jsonify({
                'status': 'error',
                'message': 'Account does not exist. Please check your email or click "Create Account" to register.'
            }), 404

        u_dict = dict(existing_user)
        db_name = u_dict.get('student_name', '').strip()

        # Check if student name matches database record
        if student_name and db_name and student_name.lower() != db_name.lower():
            conn.close()
            return jsonify({
                'status': 'error',
                'message': f'Account does not exist for "{student_name}". Student Name does not match our registered records.'
            }), 400

        # Update login timestamp
        cursor.execute('UPDATE users SET login_time = CURRENT_TIMESTAMP WHERE id = ?', (u_dict['id'],))
        conn.commit()
        conn.close()

        return jsonify({
            'status': 'success',
            'message': 'Logged in successfully!',
            'user': {
                'id': u_dict['id'],
                'studentName': u_dict.get('student_name', student_name),
                'rollNumber': u_dict.get('roll_number', '101'),
                'email': u_dict.get('email', email),
                'year': u_dict.get('year', 'First Year'),
                'batch': u_dict.get('batch', 'A')
            }
        })

    # --- MODE 2: CREATE ACCOUNT / REGISTER MODE ---
    if not student_name or not roll_number or not year or not batch:
        conn.close()
        return jsonify({'status': 'error', 'message': 'All fields (Name, Roll Number, Email, Year, and Batch) are compulsory to create an account.'}), 400

    if not re.match(r'^\d{3}$', roll_number):
        conn.close()
        return jsonify({'status': 'error', 'message': 'Roll number must be exactly 3 digits (e.g. 101).'}), 400

    if existing_user:
        user_id = existing_user['id']
        cursor.execute(
            '''UPDATE users 
               SET student_name = ?, roll_number = ?, year = ?, batch = ?, login_time = CURRENT_TIMESTAMP 
               WHERE id = ?''',
            (student_name, roll_number, year, batch, user_id)
        )
    else:
        cursor.execute(
            '''INSERT INTO users (student_name, roll_number, email, year, batch) VALUES (?, ?, ?, ?, ?)''',
            (student_name, roll_number, email, year, batch)
        )
        user_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return jsonify({
        'status': 'success',
        'message': 'Account registered successfully!',
        'user': {
            'id': user_id,
            'studentName': student_name,
            'rollNumber': roll_number,
            'email': email,
            'year': year,
            'batch': batch
        }
    })

@app.route('/api/subjects', methods=['GET'])
def api_get_subjects():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT s.id, s.name, s.description, s.icon, s.badge, s.created_by,
               (SELECT COUNT(*) FROM questions q WHERE LOWER(q.subject) = LOWER(s.name)) as question_count
        FROM subjects s
        ORDER BY s.id ASC
    ''')
    rows = cursor.fetchall()
    conn.close()

    subjects_list = []
    for row in rows:
        subjects_list.append({
            'id': row['id'],
            'name': row['name'],
            'description': row['description'],
            'icon': row['icon'] or '📚',
            'badge': row['badge'] or 'Flashcard Quiz',
            'created_by': row['created_by'],
            'question_count': row['question_count'] or 5
        })

    return jsonify({'status': 'success', 'subjects': subjects_list})

@app.route('/api/quiz/create', methods=['POST'])
def api_create_quiz():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    icon = data.get('icon', '⚡').strip() or '⚡'
    badge = data.get('badge', 'Custom Quiz').strip() or 'Custom Quiz'
    creator = data.get('creator', 'User').strip() or 'User'
    questions = data.get('questions', [])

    if not name:
        return jsonify({'status': 'error', 'message': 'Subject name is required.'}), 400

    if not description:
        return jsonify({'status': 'error', 'message': 'Subject description is required.'}), 400

    if not isinstance(questions, list) or len(questions) == 0:
        return jsonify({'status': 'error', 'message': 'At least 1 question is required.'}), 400

    # Limit to maximum 5 questions
    if len(questions) > 5:
        return jsonify({'status': 'error', 'message': 'Maximum limit is 5 questions per quiz.'}), 400

    # Validate each question
    for idx, q in enumerate(questions):
        q_text = q.get('question_text', '').strip()
        opt_a = q.get('option_a', '').strip()
        opt_b = q.get('option_b', '').strip()
        opt_c = q.get('option_c', '').strip()
        opt_d = q.get('option_d', '').strip()
        correct_idx = q.get('correct_index', 0)

        if not q_text or not opt_a or not opt_b or not opt_c or not opt_d:
            return jsonify({
                'status': 'error',
                'message': f'Question {idx + 1} is incomplete. All fields (question text & options A-D) are required.'
            }), 400

        try:
            correct_idx = int(correct_idx)
            if correct_idx < 0 or correct_idx > 3:
                correct_idx = 0
        except (ValueError, TypeError):
            correct_idx = 0

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Check if subject exists, or insert new
        cursor.execute('SELECT id FROM subjects WHERE LOWER(name) = LOWER(?)', (name,))
        existing = cursor.fetchone()

        if existing:
            cursor.execute('''
                UPDATE subjects SET description = ?, icon = ?, badge = ? WHERE id = ?
            ''', (description, icon, badge, existing['id']))
        else:
            cursor.execute('''
                INSERT INTO subjects (name, description, icon, badge, created_by)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, description, icon, badge, creator))

        # Delete old questions for this subject if re-creating
        cursor.execute('DELETE FROM questions WHERE LOWER(subject) = LOWER(?)', (name,))

        # Insert questions
        for q in questions:
            cursor.execute('''
                INSERT INTO questions (subject, question_text, option_a, option_b, option_c, option_d, correct_index)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                name,
                q.get('question_text', '').strip(),
                q.get('option_a', '').strip(),
                q.get('option_b', '').strip(),
                q.get('option_c', '').strip(),
                q.get('option_d', '').strip(),
                int(q.get('correct_index', 0))
            ))

        conn.commit()
        conn.close()

        return jsonify({
            'status': 'success',
            'message': f'Quiz "{name}" created successfully with {len(questions)} questions!',
            'subject': name
        })

    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'status': 'error', 'message': f'Database error: {str(e)}'}), 500

@app.route('/api/questions/<subject>', methods=['GET'])
def api_get_questions(subject):
    # Normalize subject name matching
    target_subject = subject.strip()
    if target_subject.lower() in ['webhosting', 'web hosting', 'web technology', 'webtech']:
        target_subject = 'Web Hosting'
    elif target_subject.lower() in ['c programming', 'c', 'c-programming']:
        target_subject = 'C programming'

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT * FROM questions WHERE LOWER(subject) = LOWER(?)',
        (target_subject,)
    )
    rows = cursor.fetchall()
    conn.close()

    questions = []
    for row in rows:
        questions.append({
            'id': row['id'],
            'subject': row['subject'],
            'question_text': row['question_text'],
            'options': [row['option_a'], row['option_b'], row['option_c'], row['option_d']],
            'correct_index': row['correct_index']
        })

    return jsonify({'status': 'success', 'subject': target_subject, 'questions': questions})

@app.route('/api/submit', methods=['POST'])
def api_submit_result():
    data = request.get_json() or {}
    student_name = data.get('studentName', 'Anonymous').strip()
    roll_number = data.get('rollNumber', 'N/A').strip()
    subject = data.get('subject', 'General').strip()
    score = data.get('score', 0)
    total = data.get('total', 0)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        '''INSERT INTO results (student_name, roll_number, subject, score, total) VALUES (?, ?, ?, ?, ?)''',
        (student_name, roll_number, subject, score, total)
    )
    conn.commit()
    result_id = cursor.lastrowid
    conn.close()

    return jsonify({
        'status': 'success',
        'message': 'Quiz result saved to database!',
        'result_id': result_id
    })

@app.route('/api/results/<roll_number>', methods=['GET'])
def api_get_user_results(roll_number):
    roll_number = roll_number.strip()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id, student_name, roll_number, subject, score, total, submitted_at FROM results WHERE roll_number = ? ORDER BY id DESC',
        (roll_number,)
    )
    rows = cursor.fetchall()
    conn.close()

    history = []
    for row in rows:
        history.append({
            'id': row['id'],
            'student_name': row['student_name'],
            'roll_number': row['roll_number'],
            'subject': row['subject'],
            'score': row['score'],
            'total': row['total'],
            'percentage': round((row['score'] / row['total']) * 100) if row['total'] > 0 else 0,
            'submitted_at': row['submitted_at']
        })

    return jsonify({'status': 'success', 'roll_number': roll_number, 'history': history})

@app.route('/api/user/<identifier>', methods=['GET'])
def api_get_user_profile(identifier):
    target = identifier.strip()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM users 
        WHERE LOWER(email) = LOWER(?) OR roll_number = ? 
        ORDER BY id DESC LIMIT 1
    ''', (target, target))
    user_row = cursor.fetchone()
    u_dict = dict(user_row) if user_row else {}
    
    roll = u_dict.get('roll_number', target)
    cursor.execute('''
        SELECT id, student_name, roll_number, subject, score, total, submitted_at 
        FROM results 
        WHERE roll_number = ? OR LOWER(student_name) = LOWER(?) 
        ORDER BY id DESC
    ''', (roll, u_dict.get('student_name', '')))
    result_rows = cursor.fetchall()
    conn.close()

    user_info = {
        'studentName': u_dict.get('student_name', ''),
        'rollNumber': u_dict.get('roll_number', target if not '@' in target else '101'),
        'email': u_dict.get('email', target if '@' in target else ''),
        'year': u_dict.get('year', ''),
        'batch': u_dict.get('batch', ''),
        'login_time': u_dict.get('login_time', '')
    }

    history = []
    total_tests = len(result_rows)
    total_score = 0
    total_possible = 0
    passed_tests = 0

    for row in result_rows:
        pct = round((row['score'] / row['total']) * 100) if row['total'] > 0 else 0
        total_score += row['score']
        total_possible += row['total']
        if pct >= 60:
            passed_tests += 1

        history.append({
            'id': row['id'],
            'student_name': row['student_name'],
            'roll_number': row['roll_number'],
            'subject': row['subject'],
            'score': row['score'],
            'total': row['total'],
            'percentage': pct,
            'submitted_at': row['submitted_at']
        })

    avg_percentage = round((total_score / total_possible) * 100) if total_possible > 0 else 0

    return jsonify({
        'status': 'success',
        'user': user_info,
        'metrics': {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'avg_percentage': avg_percentage,
            'total_score': total_score,
            'total_possible': total_possible
        },
        'history': history
    })

@app.route('/api/ai/generate', methods=['POST'])
def api_ai_generate():
    data = request.get_json() or {}
    prompt = data.get('prompt', '').strip()
    model = data.get('model', 'gemini-2.0-flash').strip()

    if not prompt:
        return jsonify({'status': 'error', 'message': 'Prompt is required.'}), 400

    try:
        generated_text = make_request(prompt=prompt, model=model)
        return jsonify({'status': 'success', 'response': generated_text})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/tutor/chat', methods=['POST'])
def api_tutor_chat():
    data = request.get_json() or {}
    message = data.get('message', '').strip()
    subject = data.get('subject', 'General Learning').strip()
    student_name = data.get('student_name', 'Student').strip()

    if not message:
        return jsonify({'status': 'error', 'message': 'Message is required.'}), 400

    tutor_prompt = f"""You are an encouraging, expert AI Tutor helping a student named '{student_name}'.
Current Subject Context: '{subject}'.

Student Question/Request: "{message}"

Instructions:
1. Provide a friendly, clear, and pedagogical explanation or hint.
2. Keep explanations concise, structured, and easy for a student to digest.
3. Use bold formatting (e.g., **Key Concept**) for important terms.
4. For chemical or mathematical formulas, use clean HTML subscript tags (e.g., H<sub>2</sub>O, CO<sub>2</sub>) or Unicode subscripts (H₂O, CO₂). Do NOT output raw LaTeX math symbols like $H_2O$.
"""



    try:
        response_text = make_request(prompt=tutor_prompt, model='gemini-2.0-flash')
        return jsonify({'status': 'success', 'response': response_text})
    except Exception as e:
        return jsonify({
            'status': 'success',
            'response': "💡 **Study Note**: The Gemini API free tier rate limit was briefly reached. Please wait 15–30 seconds and ask your question again!"
        })



if __name__ == '__main__':


    init_db()
    print("Server running at http://127.0.0.1:5050/")
    app.run(debug=True, host='127.0.0.1', port=5050)
