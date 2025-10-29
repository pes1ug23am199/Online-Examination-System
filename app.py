from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
import MySQLdb.cursors
from datetime import datetime

app = Flask(__name__)
app.config.from_pyfile('config.py')
app.secret_key = app.config.get('SECRET_KEY', 'dev')

mysql = MySQL(app)

# --------- Helpers ---------

def get_cursor():
    return mysql.connection.cursor(MySQLdb.cursors.DictCursor)

# --------- Routes ---------

@app.route('/')
def index():
    return redirect(url_for('student_login'))

# ---- Student ----
@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        cur = get_cursor()
        cur.execute("SELECT student_id, name FROM Student WHERE email=%s AND password=%s", (email, password))
        user = cur.fetchone()
        cur.close()
        if user:
            session['student_id'] = user['student_id']
            session['student_name'] = user['name']
            return redirect(url_for('student_dashboard'))
        flash('Invalid credentials', 'error')
    return render_template('student_login.html')

@app.route('/student/logout')
def student_logout():
    session.pop('student_id', None)
    session.pop('student_name', None)
    return redirect(url_for('student_login'))

@app.route('/student/dashboard')
def student_dashboard():
    if 'student_id' not in session:
        return redirect(url_for('student_login'))
    cur = get_cursor()
    cur.execute("""
        SELECT q.quiz_id, q.quiz_title, q.date, sub.subject_name
        FROM Quiz q
        JOIN Subject sub ON q.subject_id = sub.subject_id
        ORDER BY q.date DESC
    """)
    quizzes = cur.fetchall()
    cur.close()
    return render_template('student_dashboard.html', quizzes=quizzes, student_name=session.get('student_name'))

@app.route('/student/quiz/<int:quiz_id>', methods=['GET', 'POST'])
def student_quiz(quiz_id):
    if 'student_id' not in session:
        return redirect(url_for('student_login'))
    cur = get_cursor()
    if request.method == 'POST':
        student_id = session['student_id']
        # Insert answers (ignore duplicates so re-submits don't double count)
        cur.execute("SELECT question_id FROM Question WHERE quiz_id=%s", (quiz_id,))
        qids = [row['question_id'] for row in cur.fetchall()]
        for qid in qids:
            choice = request.form.get(f'q_{qid}')
            if choice in ('A','B','C','D'):
                cur.execute(
                    "INSERT IGNORE INTO Answer (question_id, student_id, chosen_option) VALUES (%s,%s,%s)",
                    (qid, student_id, choice)
                )
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('student_result', quiz_id=quiz_id))
    # GET -> render questions
    cur.execute("""
        SELECT q.question_id, q.question_text, q.option_a, q.option_b, q.option_c, q.option_d
        FROM Question q WHERE q.quiz_id=%s
    """, (quiz_id,))
    questions = cur.fetchall()
    cur.close()
    return render_template('quiz.html', questions=questions, quiz_id=quiz_id)

@app.route('/student/result/<int:quiz_id>')
def student_result(quiz_id):
    if 'student_id' not in session:
        return redirect(url_for('student_login'))
    cur = get_cursor()
    cur.execute("""
        SELECT sc.marks_obtained, sc.total_marks, r.grade
        FROM Score sc
        LEFT JOIN Result r ON r.student_id=sc.student_id AND r.quiz_id=sc.quiz_id
        WHERE sc.student_id=%s AND sc.quiz_id=%s
    """, (session['student_id'], quiz_id))
    row = cur.fetchone()
    cur.close()
    return render_template('result.html', result=row, quiz_id=quiz_id)

# ---- Staff ----
@app.route('/staff/login', methods=['GET', 'POST'])
def staff_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        cur = get_cursor()
        cur.execute("SELECT staff_id, name FROM Staff WHERE email=%s AND password=%s", (email, password))
        user = cur.fetchone()
        cur.close()
        if user:
            session['staff_id'] = user['staff_id']
            session['staff_name'] = user['name']
            return redirect(url_for('staff_dashboard'))
        flash('Invalid credentials', 'error')
    return render_template('staff_login.html')

@app.route('/staff/logout')
def staff_logout():
    session.pop('staff_id', None)
    session.pop('staff_name', None)
    return redirect(url_for('staff_login'))

@app.route('/staff/dashboard', methods=['GET', 'POST'])
def staff_dashboard():
    if 'staff_id' not in session:
        return redirect(url_for('staff_login'))
    cur = get_cursor()
    # simple list of quizzes for adding questions
    cur.execute("SELECT quiz_id, quiz_title FROM Quiz ORDER BY quiz_id DESC")
    quizzes = cur.fetchall()
    cur.close()
    return render_template('staff_dashboard.html', quizzes=quizzes, staff_name=session.get('staff_name'))

@app.route('/staff/add_question', methods=['POST'])
def staff_add_question():
    if 'staff_id' not in session:
        return redirect(url_for('staff_login'))
    quiz_id = request.form.get('quiz_id', type=int)
    qText = request.form.get('question_text')
    optA = request.form.get('option_a')
    optB = request.form.get('option_b')
    optC = request.form.get('option_c')
    optD = request.form.get('option_d')
    correct = request.form.get('correct_option')
    if quiz_id and qText and optA and optB and optC and optD and correct in ('A','B','C','D'):
        cur = get_cursor()
        try:
            cur.execute("CALL add_question(%s,%s,%s,%s,%s,%s,%s)", (quiz_id, qText, optA, optB, optC, optD, correct))
            mysql.connection.commit()
            flash('Question added', 'success')
        except Exception as e:
            mysql.connection.rollback()
            flash('Failed to add question', 'error')
        finally:
            cur.close()
    else:
        flash('Please fill all fields correctly', 'error')
    return redirect(url_for('staff_dashboard'))


if __name__ == '__main__':
    app.run(debug=True)
