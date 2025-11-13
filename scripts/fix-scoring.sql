-- Fix scoring and grading logic: recalc from answers and question count
USE online_exam_system;

-- Drop old triggers if they exist
DROP TRIGGER IF EXISTS trg_calculate_score;
DROP TRIGGER IF EXISTS trg_generate_result;
DROP TRIGGER IF EXISTS trg_score_after_answer_ins;
DROP TRIGGER IF EXISTS trg_score_after_answer_upd;
DROP TRIGGER IF EXISTS trg_score_after_answer_del;
DROP TRIGGER IF EXISTS trg_result_after_score_ins;
DROP TRIGGER IF EXISTS trg_result_after_score_upd;

DELIMITER //

-- Recalculate Score on INSERT/UPDATE/DELETE of Answer
CREATE TRIGGER trg_score_after_answer_ins
AFTER INSERT ON Answer
FOR EACH ROW
BEGIN
  DECLARE qz INT;
  SELECT quiz_id INTO qz FROM Question WHERE question_id = NEW.question_id;
  REPLACE INTO Score (student_id, quiz_id, marks_obtained, total_marks)
  SELECT NEW.student_id, qz,
         SUM(a.chosen_option = q.correct_option),
         COUNT(*)
    FROM Question q
    LEFT JOIN Answer a ON a.question_id = q.question_id AND a.student_id = NEW.student_id
   WHERE q.quiz_id = qz;
END;//

CREATE TRIGGER trg_score_after_answer_upd
AFTER UPDATE ON Answer
FOR EACH ROW
BEGIN
  DECLARE qz INT;
  SELECT quiz_id INTO qz FROM Question WHERE question_id = NEW.question_id;
  REPLACE INTO Score (student_id, quiz_id, marks_obtained, total_marks)
  SELECT NEW.student_id, qz,
         SUM(a.chosen_option = q.correct_option),
         COUNT(*)
    FROM Question q
    LEFT JOIN Answer a ON a.question_id = q.question_id AND a.student_id = NEW.student_id
   WHERE q.quiz_id = qz;
END;//

CREATE TRIGGER trg_score_after_answer_del
AFTER DELETE ON Answer
FOR EACH ROW
BEGIN
  DECLARE qz INT;
  SELECT quiz_id INTO qz FROM Question WHERE question_id = OLD.question_id;
  REPLACE INTO Score (student_id, quiz_id, marks_obtained, total_marks)
  SELECT OLD.student_id, qz,
         SUM(a.chosen_option = q.correct_option),
         COUNT(*)
    FROM Question q
    LEFT JOIN Answer a ON a.question_id = q.question_id AND a.student_id = OLD.student_id
   WHERE q.quiz_id = qz;
END;//

-- Keep Result in sync on INSERT/UPDATE of Score
CREATE TRIGGER trg_result_after_score_ins
AFTER INSERT ON Score
FOR EACH ROW
BEGIN
  INSERT INTO Result (student_id, quiz_id, grade)
  VALUES (NEW.student_id, NEW.quiz_id, get_grade(NEW.marks_obtained, NEW.total_marks))
  ON DUPLICATE KEY UPDATE grade = VALUES(grade);
END;//

CREATE TRIGGER trg_result_after_score_upd
AFTER UPDATE ON Score
FOR EACH ROW
BEGIN
  INSERT INTO Result (student_id, quiz_id, grade)
  VALUES (NEW.student_id, NEW.quiz_id, get_grade(NEW.marks_obtained, NEW.total_marks))
  ON DUPLICATE KEY UPDATE grade = VALUES(grade);
END;//

DELIMITER ;
