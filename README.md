
# Online Examination System

A complete Online Examination System built using **Flask**, **MySQL**, **HTML/CSS/JS**, and **Bootstrap**.  
This project allows students to take quizzes online and lets staff manage courses, questions, and results.  
It also includes MySQL triggers for automatic evaluation and result generation.

---

## 🚀 Features

### 👨‍🎓 Student Module
- Login & authentication  
- View available quizzes  
- Attempt multiple–choice exams  
- Automatic scoring  
- View results instantly  

### 👨‍🏫 Staff Module
- Login & authentication  
- Add, edit, and delete questions  
- Create quizzes  
- View student submissions  
- Manage exam categories  

---

## 🗂️ Project Structure

```
online-examination-system/
│── app.py                  # Main Flask application
│── config.py               # DB credentials & app configurations
│── miniproject.sql         # Database structure + triggers
│── requirements.txt        # Python dependencies
│── static/                 # CSS, JS, images
│── templates/              # HTML Pages (Flask Jinja2)
│── scripts/                # Helper / DB scripts
└── venv/                   # Virtual environment (should be excluded in deployment)
```

---

## 🛠️ Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/pes1ug23am199/Online-Examination-System.git
cd online-examination-system
```

### 2. Create & Activate a Virtual Environment
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 🗄️ Database Setup (MySQL)

### 1. Create a Database
```sql
CREATE DATABASE online_exam_system;
```

### 2. Import the SQL Dump
Use either:
- MySQL Workbench  
- phpMyAdmin  
- MySQL CLI  

```bash
mysql -u root -p exam_system < miniproject.sql
```

The SQL file contains:
- Tables (students, staff, quizzes, questions, results)
- Stored procedures
- Triggers for auto-evaluation

---

## ⚙️ Configure Application

Edit **config.py**:

```python
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "yourpassword"
DB_NAME = "online_exam_system"
SECRET_KEY = "supersecretkey"
```

---

## ▶️ Running the Application

```bash
python app.py
```

App starts at:

```
http://127.0.0.1:5000/
```

---

## 🔐 Default Routes

### Student  
| Feature | Route |
|--------|--------|
| Login | `/student/login` |
| Dashboard | `/student/dashboard` |
| Attempt Quiz | `/student/quiz/<quiz_id>` |
| View Result | `/student/result/<result_id>` |

### Staff  
| Feature | Route |
|--------|--------|
| Login | `/staff/login` |
| Dashboard | `/staff/dashboard` |
| Add Questions | `/staff/add_question` |

---

## 📌 Future Enhancements
- Timer-based exam  
- Randomized question ordering  
- Email notifications  
- Admin panel for system monitoring  
- Export results to PDF  

---

## 📜 License
This project is developed for educational purposes as part of the PES University UE23CS351A curriculum.

