# Online Examination System (Flask + MySQL)

Simple, functional DBMS mini-project using Flask and MySQL.

## Setup
1. Ensure Python and MySQL are installed.
2. Create DB and objects:
   - Import `miniproject.sql` into MySQL (e.g., via MySQL Workbench or CLI).
3. Configure app:
   - Edit `config.py` with your MySQL credentials and secret key.
4. Install deps:
   ```bash
   pip install -r requirements.txt
   ```
5. Run app:
   ```bash
   python app.py
   ```

## Notes
- Default routes:
  - Student: `/student/login`, dashboard `/student/dashboard`, quiz `/student/quiz/<id>`, result `/student/result/<id>`
  - Staff: `/staff/login`, dashboard `/staff/dashboard` (add question)
- Uses MySQL triggers/functions to score and generate results automatically.
