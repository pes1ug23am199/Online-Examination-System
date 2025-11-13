from flask import Flask, render_template, request, redirect, url_for, session, flash
import pymysql
pymysql.install_as_MySQLdb()
from flask_mysqldb import MySQL
import MySQLdb
import MySQLdb.cursors
from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config.from_pyfile('config.py')
app.secret_key = app.config.get('SECRET_KEY', 'dev')

mysql = MySQL(app)

# --------- Helpers ---------

def get_cursor():
    return mysql.connection.cursor(MySQLdb.cursors.DictCursor)


def verify_password(stored_value: str, submitted: str) -> bool:
    """Accepts either hashed (Werkzeug) or legacy plaintext passwords."""
    if not stored_value:
        return False
    # Werkzeug hashes usually start with 'pbkdf2:' prefix
    if stored_value.startswith('pbkdf2:') or stored_value.startswith('scrypt:'):
        try:
            return check_password_hash(stored_value, submitted)
        except Exception:
            return False
    # fallback plaintext compare
    return stored_value == submitted

# --------- Routes ---------

@app.route('/')
def index():
    return redirect(url_for('student_login'))

# ---- Student ----
@app.route('/student/signup', methods=['GET', 'POST'])
def student_signup():
    if request.method == 'POST':
        usn = request.form.get('usn')
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        department = request.form.get('department')
        semester = request.form.get('semester', type=int)
        if not (usn and name and email and password and semester):
            flash('Please fill all required fields', 'error')
            return render_template('student_signup.html')
        cur = get_cursor()
        try:
            cur.execute(
                "INSERT INTO Student (usn, name, email, password, department, semester) VALUES (%s,%s,%s,%s,%s,%s)",
                (usn, name, email, generate_password_hash(password), department, semester)
            )
            mysql.connection.commit()
            flash('Account created. Please log in.', 'success')
            return redirect(url_for('student_login'))
        except MySQLdb.IntegrityError:
            mysql.connection.rollback()
            flash('Email or USN already exists', 'error')
        except MySQLdb.DatabaseError as e:
            mysql.connection.rollback()
            msg = (e.args[1] if hasattr(e, 'args') and len(e.args) > 1 else str(e))
            flash(msg, 'error')
        finally:
            cur.close()
    return render_template('student_signup.html')


@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember')
        try:
            cur = get_cursor()
            cur.execute("SELECT student_id, name, password FROM Student WHERE email=%s", (email,))
            user = cur.fetchone()
            cur.close()
        except MySQLdb.OperationalError as e:
            app.logger.error(f"DB error during student_login: {e}")
            flash(f'Database connection failed: {getattr(e, "args", [None, str(e)])[1] if getattr(e, "args", None) else str(e)}', 'error')
            return render_template('student_login.html')
        if user and verify_password(user.get('password'), password):
            session['student_id'] = user['student_id']
            session['student_name'] = user['name']
            session.permanent = bool(remember)
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
    # Available quizzes with subject
    cur.execute("""
        SELECT q.quiz_id, q.quiz_title, q.date, sub.subject_name
        FROM Quiz q
        JOIN Subject sub ON q.subject_id = sub.subject_id
        ORDER BY q.date DESC
    """)
    quizzes = cur.fetchall()
    # Subjects with quiz counts (no explicit enrollment table in schema)
    cur.execute("""
        SELECT s.subject_id, s.subject_name, COUNT(q.quiz_id) AS quiz_count
        FROM Subject s
        LEFT JOIN Quiz q ON q.subject_id = s.subject_id
        GROUP BY s.subject_id, s.subject_name
        ORDER BY s.subject_name
    """)
    subjects = cur.fetchall()
    cur.close()
    return render_template('student_dashboard.html', quizzes=quizzes, subjects=subjects, student_name=session.get('student_name'))

@app.route('/student/quiz/<int:quiz_id>', methods=['GET', 'POST'])
def student_quiz(quiz_id):
    if 'student_id' not in session:
        return redirect(url_for('student_login'))
    cur = get_cursor()
    if request.method == 'POST':
        student_id = session['student_id']
        try:
            # Short-circuit if already submitted (better UX); DB trigger also enforces this
            cur.execute("SELECT 1 FROM Score WHERE student_id=%s AND quiz_id=%s LIMIT 1", (student_id, quiz_id))
            if cur.fetchone():
                flash('You have already submitted this exam.', 'error')
                cur.close()
                return redirect(url_for('student_result', quiz_id=quiz_id))
            # Insert answers
            cur.execute("SELECT question_id FROM Question WHERE quiz_id=%s", (quiz_id,))
            qids = [row['question_id'] for row in cur.fetchall()]
            for qid in qids:
                choice = request.form.get(f'q_{qid}')
                if choice in ('A','B','C','D'):
                    cur.execute(
                        """
                        INSERT INTO Answer (question_id, student_id, chosen_option)
                        VALUES (%s,%s,%s)
                        ON DUPLICATE KEY UPDATE chosen_option=VALUES(chosen_option)
                        """,
                        (qid, student_id, choice)
                    )
            mysql.connection.commit()
        except MySQLdb.DatabaseError as e:
            mysql.connection.rollback()
            msg = (e.args[1] if hasattr(e, 'args') and len(e.args) > 1 else str(e))
            if 'Duplicate submission' in msg:
                flash('You have already submitted this exam.', 'error')
                cur.close()
                return redirect(url_for('student_result', quiz_id=quiz_id))
            flash('Failed to submit answers: ' + msg, 'error')
            cur.close()
            return redirect(url_for('student_quiz', quiz_id=quiz_id))
        cur.close()
        return redirect(url_for('student_result', quiz_id=quiz_id))
# GET -> render questions and quiz meta
    cur.execute("""
        SELECT q.question_id, q.question_text, q.option_a, q.option_b, q.option_c, q.option_d
        FROM Question q WHERE q.quiz_id=%s
    """, (quiz_id,))
    questions = cur.fetchall()
    cur.execute("""
        SELECT z.quiz_title, z.duration_minutes, s.subject_name
        FROM Quiz z JOIN Subject s ON z.subject_id = s.subject_id
        WHERE z.quiz_id=%s
    """, (quiz_id,))
    quiz_meta = cur.fetchone() or {"quiz_title": "Quiz", "duration_minutes": 0, "subject_name": ""}
    cur.close()
    return render_template('quiz.html', questions=questions, quiz_id=quiz_id, quiz=quiz_meta)

@app.route('/student/result/<int:quiz_id>')
def student_result(quiz_id):
    if 'student_id' not in session:
        return redirect(url_for('student_login'))
    cur = get_cursor()
    # Compute marks and total directly from Questions and Answers for correctness
    cur.execute(
        """
        SELECT 
          SUM(CASE WHEN a.chosen_option = q.correct_option THEN 1 ELSE 0 END) AS marks_obtained,
          COUNT(*) AS total_marks
        FROM Question q
        LEFT JOIN Answer a ON a.question_id = q.question_id AND a.student_id = %s
        WHERE q.quiz_id = %s
        """,
        (session['student_id'], quiz_id),
    )
    scores = cur.fetchone() or {"marks_obtained": 0, "total_marks": 0}
    marks = int(scores.get("marks_obtained") or 0)
    total = int(scores.get("total_marks") or 0)
    # Meta for display
    cur.execute("""
        SELECT z.quiz_title, s.subject_name
        FROM Quiz z JOIN Subject s ON z.subject_id = s.subject_id
        WHERE z.quiz_id=%s
    """, (quiz_id,))
    meta = cur.fetchone() or {"quiz_title": "Quiz", "subject_name": ""}
    # Compute grade in app
    pct = (marks / total) * 100 if total else 0
    if pct >= 90:
        grade = 'A+'
    elif pct >= 75:
        grade = 'A'
    elif pct >= 60:
        grade = 'B+'
    elif pct >= 50:
        grade = 'B'
    else:
        grade = 'F'
    # Persist into Score and Result (idempotent upsert)
    try:
        cur.execute(
            """
            INSERT INTO Score (student_id, quiz_id, marks_obtained, total_marks)
            VALUES (%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE marks_obtained=VALUES(marks_obtained), total_marks=VALUES(total_marks)
            """,
            (session['student_id'], quiz_id, marks, total),
        )
        cur.execute(
            """
            INSERT INTO Result (student_id, quiz_id, grade)
            VALUES (%s,%s,%s)
            ON DUPLICATE KEY UPDATE grade=VALUES(grade)
            """,
            (session['student_id'], quiz_id, grade),
        )
        mysql.connection.commit()
    except Exception:
        mysql.connection.rollback()
    finally:
        cur.close()
    result_payload = {"marks_obtained": marks, "total_marks": total, "grade": grade, "quiz_title": meta.get('quiz_title'), "subject_name": meta.get('subject_name')}
    return render_template('result.html', result=result_payload, quiz_id=quiz_id)

# ---- Staff ----
@app.route('/staff/signup', methods=['GET', 'POST'])
def staff_signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        department = request.form.get('department')
        if not (name and email and password):
            flash('Please fill all required fields', 'error')
            return render_template('staff_signup.html')
        cur = get_cursor()
        try:
            cur.execute(
                "INSERT INTO Staff (name, email, password, department) VALUES (%s,%s,%s,%s)",
                (name, email, generate_password_hash(password), department)
            )
            mysql.connection.commit()
            flash('Staff account created. Please log in.', 'success')
            return redirect(url_for('staff_login'))
        except MySQLdb.IntegrityError as e:
            mysql.connection.rollback()
            flash('Email already exists', 'error')
        finally:
            cur.close()
    return render_template('staff_signup.html')


@app.route('/staff/login', methods=['GET', 'POST'])
def staff_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember')
        try:
            cur = get_cursor()
            cur.execute("SELECT staff_id, name, password FROM Staff WHERE email=%s", (email,))
            user = cur.fetchone()
            cur.close()
        except MySQLdb.OperationalError as e:
            app.logger.error(f"DB error during staff_login: {e}")
            flash(f'Database connection failed: {getattr(e, "args", [None, str(e)])[1] if getattr(e, "args", None) else str(e)}', 'error')
            return render_template('staff_login.html')
        if user and verify_password(user.get('password'), password):
            session['staff_id'] = user['staff_id']
            session['staff_name'] = user['name']
            session.permanent = bool(remember)
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
    # subjects for creating quizzes
    cur.execute("SELECT subject_id, subject_name FROM Subject ORDER BY subject_name")
    subjects = cur.fetchall()
    # list of quizzes for adding questions
    cur.execute("SELECT quiz_id, quiz_title FROM Quiz ORDER BY quiz_id DESC")
    quizzes = cur.fetchall()
    # detailed quizzes list for display
    cur.execute("""
        SELECT q.quiz_id, q.quiz_title, q.date, q.duration_minutes, s.subject_name
        FROM Quiz q JOIN Subject s ON q.subject_id = s.subject_id
        ORDER BY q.quiz_id DESC
    """)
    quizzes_full = cur.fetchall()
    cur.close()
    return render_template('staff_dashboard.html', subjects=subjects, quizzes=quizzes, quizzes_full=quizzes_full, staff_name=session.get('staff_name'))

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
        except MySQLdb.IntegrityError as e:
            mysql.connection.rollback()
            code = (e.args[0] if hasattr(e, 'args') and len(e.args) > 0 else None)
            if code == 1062:
                flash('This question already exists in the selected quiz.', 'error')
            else:
                flash('Failed to add question', 'error')
        except MySQLdb.DatabaseError as e:
            mysql.connection.rollback()
            code = (e.args[0] if hasattr(e, 'args') and len(e.args) > 0 else None)
            msg = (e.args[1] if hasattr(e, 'args') and len(e.args) > 1 else str(e))
            if code == 1644 or 'Duplicate question detected' in msg:
                flash('This question already exists in the selected quiz.', 'error')
            else:
                flash(msg, 'error')
        except Exception:
            mysql.connection.rollback()
            flash('Failed to add question', 'error')
        finally:
            cur.close()
    else:
        flash('Please fill all fields correctly', 'error')
    return redirect(url_for('staff_dashboard'))


@app.route('/student/results')
def student_results_overview():
    if 'student_id' not in session:
        return redirect(url_for('student_login'))
    cur = get_cursor()
    # Use stored procedure to fetch results summary
    cur.execute("CALL get_student_results(%s)", (session['student_id'],))
    rows = cur.fetchall()
    # Ensure we close any additional result sets
    try:
        while cur.nextset():
            pass
    except Exception:
        pass
    cur.close()
    return render_template('student_results.html', rows=rows)

# ---- Staff: Create quiz and view results ----
@app.route('/staff/create_quiz', methods=['POST'])
def staff_create_quiz():
    if 'staff_id' not in session:
        return redirect(url_for('staff_login'))
    subject_id = request.form.get('subject_id', type=int)
    title = request.form.get('quiz_title')
    date = request.form.get('date')
    duration = request.form.get('duration_minutes', type=int)
    if not (subject_id and title and date and duration and duration > 0):
        flash('Please provide subject, title, date, and a positive duration.', 'error')
        return redirect(url_for('staff_dashboard'))
    cur = get_cursor()
    try:
        cur.execute(
            "INSERT INTO Quiz (subject_id, quiz_title, date, duration_minutes) VALUES (%s,%s,%s,%s)",
            (subject_id, title, date, duration),
        )
        mysql.connection.commit()
        flash('Quiz created.', 'success')
    except Exception:
        mysql.connection.rollback()
        flash('Failed to create quiz.', 'error')
    finally:
        cur.close()
    return redirect(url_for('staff_dashboard'))

@app.route('/staff/results')
def staff_results():
    if 'staff_id' not in session:
        return redirect(url_for('staff_login'))
    quiz_id = request.args.get('quiz_id', type=int)
    cur = get_cursor()
    cur.execute("SELECT quiz_id, quiz_title FROM Quiz ORDER BY quiz_id DESC")
    quizzes = cur.fetchall()
    rows = []
    meta = None
    if quiz_id:
        cur.execute(
            """
            SELECT st.usn, st.name, sc.marks_obtained, sc.total_marks, r.grade
            FROM Score sc
            JOIN Student st ON st.student_id = sc.student_id
            LEFT JOIN Result r ON r.student_id=sc.student_id AND r.quiz_id=sc.quiz_id
            WHERE sc.quiz_id=%s
            ORDER BY sc.marks_obtained DESC
            """,
            (quiz_id,),
        )
        rows = cur.fetchall()
        cur.execute("SELECT q.quiz_title, s.subject_name FROM Quiz q JOIN Subject s ON q.subject_id=s.subject_id WHERE q.quiz_id=%s", (quiz_id,))
        meta = cur.fetchone()
    cur.close()
    return render_template('staff_results.html', quizzes=quizzes, rows=rows, meta=meta, selected_quiz_id=quiz_id)

if __name__ == '__main__':
    app.run(debug=True)
