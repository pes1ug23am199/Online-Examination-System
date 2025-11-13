CREATE DATABASE online_exam_system;
USE online_exam_system;

CREATE TABLE Student (
    student_id INT AUTO_INCREMENT PRIMARY KEY,
    usn VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(100) NOT NULL,
    department VARCHAR(100),
    semester INT CHECK (semester BETWEEN 1 AND 8)
);

CREATE TABLE Staff (
    staff_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(100) NOT NULL,
    department VARCHAR(100)
);

CREATE TABLE Subject (
    subject_id INT AUTO_INCREMENT PRIMARY KEY,
    subject_code VARCHAR(20) UNIQUE NOT NULL,
    subject_name VARCHAR(100) NOT NULL,
    staff_id INT,
    FOREIGN KEY (staff_id) REFERENCES Staff(staff_id)
        ON DELETE SET NULL ON UPDATE CASCADE
);

CREATE TABLE Quiz (
    quiz_id INT AUTO_INCREMENT PRIMARY KEY,
    subject_id INT NOT NULL,
    quiz_title VARCHAR(100),
    date DATE,
    duration_minutes INT CHECK (duration_minutes > 0),
    FOREIGN KEY (subject_id) REFERENCES Subject(subject_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE Question (
    question_id INT AUTO_INCREMENT PRIMARY KEY,
    quiz_id INT NOT NULL,
    question_text TEXT NOT NULL,
    option_a VARCHAR(255) NOT NULL,
    option_b VARCHAR(255) NOT NULL,
    option_c VARCHAR(255) NOT NULL,
    option_d VARCHAR(255) NOT NULL,
    correct_option CHAR(1) CHECK (correct_option IN ('A','B','C','D')),
    FOREIGN KEY (quiz_id) REFERENCES Quiz(quiz_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE Answer (
    answer_id INT AUTO_INCREMENT PRIMARY KEY,
    question_id INT NOT NULL,
    student_id INT NOT NULL,
    chosen_option CHAR(1) CHECK (chosen_option IN ('A','B','C','D')),
    FOREIGN KEY (question_id) REFERENCES Question(question_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (student_id) REFERENCES Student(student_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE Score (
    score_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    quiz_id INT NOT NULL,
    marks_obtained INT CHECK (marks_obtained >= 0),
    total_marks INT CHECK (total_marks > 0),
    FOREIGN KEY (student_id) REFERENCES Student(student_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (quiz_id) REFERENCES Quiz(quiz_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE Result (
    result_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    quiz_id INT NOT NULL,
    grade VARCHAR(5),
    FOREIGN KEY (student_id) REFERENCES Student(student_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (quiz_id) REFERENCES Quiz(quiz_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);


INSERT INTO Student (usn, name, email, password, department, semester)
VALUES
('PES1UG23AM199', 'P Pavan Shanbhag', 'pavan@pes.edu', 'pavan123', 'CSE (AI & ML)', 5),
('PES1UG23AM210', 'Prarthan H A', 'prarthan@pes.edu', 'prarthan123', 'CSE (AI & ML)', 5),
('PES1UG23AM205', 'Rohan M', 'rohan@pes.edu', 'rohan123', 'CSE (AI & ML)', 5),
('PES1UG23AM201', 'Sneha S', 'sneha@pes.edu', 'sneha123', 'CSE (AI & ML)', 5),
('PES1UG23AM202', 'Arjun K', 'arjun@pes.edu', 'arjun123', 'CSE (AI & ML)', 5);

INSERT INTO Staff (name, email, password, department)
VALUES
('Dr. Ramesh Kumar', 'ramesh@pes.edu', 'ramesh123', 'CSE (AI & ML)'),
('Prof. Priya Desai', 'priya@pes.edu', 'priya123', 'CSE (AI & ML)'),
('Dr. Manjunath Rao', 'manjunath@pes.edu', 'manju123', 'CSE'),
('Prof. Kavya N', 'kavya@pes.edu', 'kavya123', 'CSE'),
('Dr. Vinod P', 'vinod@pes.edu', 'vinod123', 'CSE');

INSERT INTO Subject (subject_code, subject_name, staff_id)
VALUES
('DBMS501', 'Database Management Systems', 1),
('AIML502', 'Artificial Intelligence', 2),
('CN503', 'Computer Networks', 3),
('OS504', 'Operating Systems', 4),
('SE505', 'Software Engineering', 5);

INSERT INTO Quiz (subject_id, quiz_title, date, duration_minutes)
VALUES
(1, 'DBMS Mid-Sem Exam', '2025-10-10', 60),
(2, 'AI Basics Test', '2025-10-15', 45),
(3, 'Networks Quiz', '2025-10-18', 30),
(4, 'OS Fundamentals', '2025-10-20', 50),
(5, 'Software Design Quiz', '2025-10-25', 40);

INSERT INTO Question (quiz_id, question_text, option_a, option_b, option_c, option_d, correct_option)
VALUES
(1, 'Which SQL command is used to remove a table?', 'DELETE', 'DROP', 'REMOVE', 'ERASE', 'B'),
(1, 'What is a primary key?', 'Unique identifier', 'Foreign key', 'Duplicate key', 'Null key', 'A'),
(2, 'Which algorithm is used for classification?', 'K-Means', 'KNN', 'Apriori', 'DBSCAN', 'B'),
(3, 'Which layer is responsible for routing?', 'Application', 'Transport', 'Network', 'Data Link', 'C'),
(4, 'Which scheduling algorithm uses time slices?', 'FCFS', 'SJF', 'Round Robin', 'Priority', 'C');

INSERT INTO Answer (question_id, student_id, chosen_option)
VALUES
(1, 1, 'B'),
(2, 1, 'A'),
(3, 2, 'B'),
(4, 3, 'C'),
(5, 4, 'C');

INSERT INTO Score (student_id, quiz_id, marks_obtained, total_marks)
VALUES
(1, 1, 20, 20),
(2, 2, 18, 20),
(3, 3, 14, 20),
(4, 4, 17, 20),
(5, 5, 15, 20);

INSERT INTO Result (student_id, quiz_id, grade)
VALUES
(1, 1, 'A+'),
(2, 2, 'A'),
(3, 3, 'B+'),
(4, 4, 'A'),
(5, 5, 'B');

USE online_exam_system;
ALTER TABLE Score
ADD CONSTRAINT unique_student_quiz_score UNIQUE (student_id, quiz_id);

ALTER TABLE Result
ADD CONSTRAINT unique_student_quiz_result UNIQUE (student_id, quiz_id);

ALTER TABLE Answer
ADD CONSTRAINT unique_student_question_answer UNIQUE (student_id, question_id);

-- Enforce question uniqueness per quiz at the database level
-- Normalized column for case/whitespace-insensitive comparison
ALTER TABLE Question
  ADD COLUMN question_text_norm VARCHAR(1024)
    GENERATED ALWAYS AS (LOWER(TRIM(question_text))) STORED,
  ADD UNIQUE KEY uniq_quiz_question_text_norm (quiz_id, question_text_norm);

--Trigger 1: Automatically calculate and insert Score after all answers are submitted

DELIMITER //
-- Drop all existing related triggers to reset
DROP TRIGGER IF EXISTS trg_calculate_score;
DROP TRIGGER IF EXISTS trg_generate_result;
DROP TRIGGER IF EXISTS trg_score_after_answer_ins;
DROP TRIGGER IF EXISTS trg_score_after_answer_upd;
DROP TRIGGER IF EXISTS trg_score_after_answer_del;
DROP TRIGGER IF EXISTS trg_result_after_score_ins;
DROP TRIGGER IF EXISTS trg_result_after_score_upd;
DROP TRIGGER IF EXISTS trg_prevent_duplicate_submission;
DROP TRIGGER IF EXISTS trg_student_non_empty_name;

-- Trigger 1: Prevent duplicate exam submissions
CREATE TRIGGER trg_prevent_duplicate_submission
BEFORE INSERT ON Answer
FOR EACH ROW
BEGIN
  DECLARE qz INT;
  SELECT quiz_id INTO qz FROM Question WHERE question_id = NEW.question_id;
  IF EXISTS (SELECT 1 FROM Score WHERE student_id = NEW.student_id AND quiz_id = qz) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Duplicate submission: You have already submitted this exam.';
  END IF;
END;//

-- Trigger 2: Prevent duplicate question in the same quiz
-- Clean up any prior trigger-2 variants
DROP TRIGGER IF EXISTS trg_student_non_empty_name;
DROP TRIGGER IF EXISTS trg_student_required_fields_ins;
DROP TRIGGER IF EXISTS trg_staff_required_fields_ins;
DROP TRIGGER IF EXISTS trg_prevent_duplicate_question;

CREATE TRIGGER trg_prevent_duplicate_question
BEFORE INSERT ON Question
FOR EACH ROW
BEGIN
    IF EXISTS (
        SELECT 1
        FROM Question
        WHERE quiz_id = NEW.quiz_id
          AND TRIM(LOWER(question_text)) = TRIM(LOWER(NEW.question_text))
    ) THEN
        SIGNAL SQLSTATE '45000'
        SET MYSQL_ERRNO = 1644,
            MESSAGE_TEXT = 'Duplicate question detected: This question already exists in the selected quiz.';
    END IF;
END;//
DELIMITER ;

--Trigger 2: Automatically generate Result after Score update


--Function 1: Calculate grade directly

DELIMITER //
CREATE FUNCTION get_grade(marks INT, total INT)
RETURNS VARCHAR(5)
DETERMINISTIC
BEGIN
    DECLARE percentage DECIMAL(5,2);
    DECLARE grade VARCHAR(5);

    SET percentage = (marks / total) * 100;

    IF percentage >= 90 THEN
        SET grade = 'A+';
    ELSEIF percentage >= 75 THEN
        SET grade = 'A';
    ELSEIF percentage >= 60 THEN
        SET grade = 'B+';
    ELSEIF percentage >= 50 THEN
        SET grade = 'B';
    ELSE
        SET grade = 'F';
    END IF;

    RETURN grade;
END;
//
DELIMITER ;

--Function 2: Get total marks obtained by a student

DELIMITER //
CREATE FUNCTION total_marks_student(stu_id INT)
RETURNS INT
DETERMINISTIC
BEGIN
    DECLARE total INT;
    SELECT SUM(marks_obtained) INTO total
    FROM Score
    WHERE student_id = stu_id;
    RETURN IFNULL(total, 0);
END;
//
DELIMITER ;


--Procedure 1: Display result summary for a student

DELIMITER //
CREATE PROCEDURE get_student_results(IN stu_id INT)
BEGIN
    SELECT s.name AS Student_Name,
           sub.subject_name,
           q.quiz_title,
           sc.marks_obtained,
           sc.total_marks,
           r.grade
    FROM Result r
    JOIN Student s ON r.student_id = s.student_id
    JOIN Quiz q ON r.quiz_id = q.quiz_id
    JOIN Subject sub ON q.subject_id = sub.subject_id
    JOIN Score sc ON s.student_id = sc.student_id AND q.quiz_id = sc.quiz_id
    WHERE s.student_id = stu_id;
END;
//
DELIMITER ;

--Procedure 2: Add a new question safely
DELIMITER //
CREATE PROCEDURE add_question(
    IN quizId INT,
    IN qText TEXT,
    IN optA VARCHAR(255),
    IN optB VARCHAR(255),
    IN optC VARCHAR(255),
    IN optD VARCHAR(255),
    IN correct CHAR(1)
)
BEGIN
    INSERT INTO Question (quiz_id, question_text, option_a, option_b, option_c, option_d, correct_option)
    VALUES (quizId, qText, optA, optB, optC, optD, correct);
END;
//
DELIMITER ;
