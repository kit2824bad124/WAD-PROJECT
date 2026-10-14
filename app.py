import os
import sqlite3
from functools import wraps
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, g, jsonify, send_from_directory, abort
)

# Initialize Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'wad-placement-tracker-secret-key-2026'
app.config['DATABASE'] = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'database.db')
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload size

ALLOWED_RESUME_EXTENSIONS = {'pdf'}
ALLOWED_PHOTO_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

# Ensure upload directories exist
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'resumes'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'photos'), exist_ok=True)


# ==============================================================================
# DATABASE HELPERS
# ==============================================================================

def get_db():
    """Opens a new database connection if there is none yet for the current application context."""
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """Initializes the database schema and seeds initial demo data if empty."""
    db = sqlite3.connect(app.config['DATABASE'])
    db.row_factory = sqlite3.Row
    cursor = db.cursor()

    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")

    # 1. Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('student', 'admin')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Student Profiles table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS student_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE NOT NULL,
        register_no TEXT,
        phone TEXT,
        department TEXT,
        year TEXT,
        cgpa REAL,
        location TEXT,
        about_me TEXT,
        profile_photo TEXT DEFAULT 'default_avatar.png',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );
    """)

    # 3. Master Skills table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS skills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        category TEXT
    );
    """)

    # 4. Student Skills table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS student_skills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        skill_name TEXT NOT NULL,
        proficiency TEXT NOT NULL CHECK(proficiency IN ('Beginner', 'Intermediate', 'Advanced')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES users (id) ON DELETE CASCADE,
        UNIQUE (student_id, skill_name)
    );
    """)

    # 5. Certifications table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS certifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        organization TEXT NOT NULL,
        issue_date TEXT NOT NULL,
        certificate_id TEXT,
        certificate_link TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES users (id) ON DELETE CASCADE
    );
    """)

    # 6. Projects table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        technologies TEXT NOT NULL,
        github_link TEXT,
        project_link TEXT,
        project_date TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES users (id) ON DELETE CASCADE
    );
    """)

    # 7. Jobs table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        company TEXT NOT NULL,
        location TEXT NOT NULL,
        job_type TEXT NOT NULL,
        required_skills TEXT NOT NULL,
        salary TEXT NOT NULL,
        deadline TEXT NOT NULL,
        description TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 8. Job Applications table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS job_applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER NOT NULL,
        student_id INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'Applied' CHECK(status IN ('Applied', 'Shortlisted', 'Interview', 'Selected', 'Rejected')),
        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (job_id) REFERENCES jobs (id) ON DELETE CASCADE,
        FOREIGN KEY (student_id) REFERENCES users (id) ON DELETE CASCADE,
        UNIQUE(job_id, student_id)
    );
    """)

    # 9. Resumes table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS resumes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER UNIQUE NOT NULL,
        filename TEXT NOT NULL,
        original_filename TEXT NOT NULL,
        upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES users (id) ON DELETE CASCADE
    );
    """)

    db.commit()

    # Seed initial demo data if users table is empty
    cursor.execute("SELECT COUNT(*) as count FROM users")
    if cursor.fetchone()['count'] == 0:
        seed_demo_data(cursor, db)

    db.close()

def seed_demo_data(cursor, db):
    """Populates rich sample data for viva demonstration."""
    # 1. Master skills
    skills_list = [
        ('Python', 'Programming'), ('Java', 'Programming'), ('C', 'Programming'),
        ('C++', 'Programming'), ('HTML', 'Web Development'), ('CSS', 'Web Development'),
        ('JavaScript', 'Web Development'), ('SQL', 'Database'), ('React', 'Frontend'),
        ('Machine Learning', 'AI/Data Science'), ('Node.js', 'Backend'),
        ('Git', 'Tools'), ('Docker', 'DevOps'), ('MongoDB', 'Database')
    ]
    for skill, cat in skills_list:
        cursor.execute("INSERT OR IGNORE INTO skills (name, category) VALUES (?, ?)", (skill, cat))

    # 2. Admin User
    admin_pw = generate_password_hash('admin123')
    cursor.execute("""
        INSERT INTO users (name, email, password_hash, role)
        VALUES (?, ?, ?, ?)
    """, ('Prof. Placement Officer', 'admin@placement.edu', admin_pw, 'admin'))

    # 3. Student 1: Alex Johnson
    student1_pw = generate_password_hash('student123')
    cursor.execute("""
        INSERT INTO users (name, email, password_hash, role)
        VALUES (?, ?, ?, ?)
    """, ('Alex Johnson', 'student@college.edu', student1_pw, 'student'))
    s1_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO student_profiles (user_id, register_no, phone, department, year, cgpa, location, about_me)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (s1_id, '717822P101', '+91 98765 43210', 'Computer Science and Engineering', '4th Year', 8.85, 'Chennai, India',
          'Passionate aspiring full-stack software engineer with strong fundamentals in Python, Web Development, and Database Systems.'))

    # Skills for Student 1
    s1_skills = [
        (s1_id, 'Python', 'Advanced'),
        (s1_id, 'HTML', 'Advanced'),
        (s1_id, 'CSS', 'Intermediate'),
        (s1_id, 'JavaScript', 'Intermediate'),
        (s1_id, 'SQL', 'Advanced'),
        (s1_id, 'Git', 'Intermediate')
    ]
    cursor.executemany("INSERT INTO student_skills (student_id, skill_name, proficiency) VALUES (?, ?, ?)", s1_skills)

    # Certifications for Student 1
    cursor.execute("""
        INSERT INTO certifications (student_id, name, organization, issue_date, certificate_id, certificate_link)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (s1_id, 'Full Stack Web Development with Python', 'Coursera - Meta', '2025-08-15', 'META-FS-8921', 'https://coursera.org/verify/sample'))

    cursor.execute("""
        INSERT INTO certifications (student_id, name, organization, issue_date, certificate_id, certificate_link)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (s1_id, 'Database Foundations: SQL', 'Oracle University', '2025-11-10', 'ORCL-DB-4432', 'https://oracle.com/verify/sample'))

    # Projects for Student 1
    cursor.execute("""
        INSERT INTO projects (student_id, title, description, technologies, github_link, project_link, project_date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (s1_id, 'Campus Event Hub', 'A centralized portal for university clubs to schedule workshops, register attendees, and track feedback.',
          'Python, Flask, SQLite, Bootstrap 5', 'https://github.com/example/campus-hub', 'https://campus-hub.demo.app', '2025-10'))

    cursor.execute("""
        INSERT INTO projects (student_id, title, description, technologies, github_link, project_link, project_date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (s1_id, 'Smart Expense Tracker', 'Interactive financial planning tool with budget forecasting and visual spending analytics.',
          'JavaScript, HTML5, CSS3, Chart.js', 'https://github.com/example/expense-tracker', 'https://expense.demo.app', '2025-12'))

    # 4. Student 2: Priya Sharma
    cursor.execute("""
        INSERT INTO users (name, email, password_hash, role)
        VALUES (?, ?, ?, ?)
    """, ('Priya Sharma', 'priya@college.edu', student1_pw, 'student'))
    s2_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO student_profiles (user_id, register_no, phone, department, year, cgpa, location, about_me)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (s2_id, '717822P205', '+91 94441 23456', 'Information Technology', '4th Year', 9.15, 'Bengaluru, India',
          'Data science enthusiast and machine learning practitioner exploring predictive modeling and analytics.'))

    s2_skills = [
        (s2_id, 'Python', 'Advanced'),
        (s2_id, 'Machine Learning', 'Intermediate'),
        (s2_id, 'SQL', 'Intermediate'),
        (s2_id, 'C++', 'Beginner')
    ]
    cursor.executemany("INSERT INTO student_skills (student_id, skill_name, proficiency) VALUES (?, ?, ?)", s2_skills)

    # 5. Student 3: Rahul Verma (ECE)
    cursor.execute("""
        INSERT INTO users (name, email, password_hash, role)
        VALUES (?, ?, ?, ?)
    """, ('Rahul Verma', 'rahul@college.edu', student1_pw, 'student'))
    s3_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO student_profiles (user_id, register_no, phone, department, year, cgpa, location, about_me)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (s3_id, '717822P312', '+91 91234 56789', 'Electronics and Communication', '3rd Year', 8.40, 'Hyderabad, India',
          'Hardware-software co-design and embedded programming enthusiast.'))

    # 6. Sample Jobs
    jobs_data = [
        ('Junior Full-Stack Developer', 'TechNova Solutions', 'Chennai / Hybrid', 'Full-Time',
         'Python, HTML, CSS, JavaScript, SQL, React', '6.5 - 8.5 LPA', '2026-10-30',
         'Looking for enthusiastic freshers to join our product engineering team. You will build user-facing web portals and REST APIs using modern frameworks.'),
        ('Data Analyst Graduate Trainee', 'Apex Analytics Group', 'Bengaluru', 'Full-Time',
         'Python, SQL, Machine Learning', '5.5 - 7.0 LPA', '2026-11-15',
         'Join our business intelligence division to extract actionable insights from client datasets, build executive dashboards, and automate SQL reporting pipelines.'),
        ('Frontend Software Intern', 'CloudScale Inc', 'Remote', 'Internship',
         'HTML, CSS, JavaScript, React', '25,000 / month', '2026-10-25',
         '6-month paid internship with potential PPO. Hands-on experience developing high-performance responsive web applications with modern component libraries.'),
        ('Python Backend Developer', 'Zoho Systems', 'Chennai', 'Full-Time',
         'Python, SQL, Git', '7.0 - 9.0 LPA', '2026-11-05',
         'Develop scalable microservices, manage relational database transactions, and collaborate closely with cross-functional product squads.'),
        ('Cloud & DevOps Associate', 'Stratum Cloudworks', 'Hyderabad', 'Full-Time',
         'Python, Git, Docker', '6.0 - 8.0 LPA', '2026-11-20',
         'Help build continuous integration and continuous deployment pipelines, manage containerized environments, and support cloud infrastructure.')
    ]

    cursor.executemany("""
        INSERT INTO jobs (title, company, location, job_type, required_skills, salary, deadline, description)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, jobs_data)

    # 7. Sample Applications
    cursor.execute("""
        INSERT INTO job_applications (job_id, student_id, status, applied_at)
        VALUES (1, ?, 'Interview', '2026-09-12 10:30:00')
    """, (s1_id,))

    cursor.execute("""
        INSERT INTO job_applications (job_id, student_id, status, applied_at)
        VALUES (4, ?, 'Selected', '2026-09-10 14:15:00')
    """, (s1_id,))

    cursor.execute("""
        INSERT INTO job_applications (job_id, student_id, status, applied_at)
        VALUES (3, ?, 'Applied', '2026-09-18 09:00:00')
    """, (s1_id,))

    cursor.execute("""
        INSERT INTO job_applications (job_id, student_id, status, applied_at)
        VALUES (2, ?, 'Shortlisted', '2026-09-15 16:45:00')
    """, (s2_id,))

    cursor.execute("""
        INSERT INTO job_applications (job_id, student_id, status, applied_at)
        VALUES (1, ?, 'Rejected', '2026-09-08 11:20:00')
    """, (s3_id,))

    # 8. Sample Resume for Student 1
    sample_resume_name = 'sample_resume_alex.pdf'
    resume_path = os.path.join(app.config['UPLOAD_FOLDER'], 'resumes', sample_resume_name)
    minimal_pdf = b'%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000052 00000 n\n0000000101 00000 n\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n178\n%%EOF\n'
    try:
        with open(resume_path, 'wb') as f:
            f.write(minimal_pdf)
        cursor.execute("""
            INSERT INTO resumes (student_id, filename, original_filename)
            VALUES (?, ?, ?)
        """, (s1_id, sample_resume_name, 'Alex_Johnson_Resume.pdf'))
    except OSError:
        pass

    db.commit()



# ==============================================================================
# AUTHENTICATION HELPERS & DECORATORS
# ==============================================================================

def login_required(f):
    """Requires user to be logged in."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def student_required(f):
    """Requires logged in user to have the 'student' role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('login'))
        if session.get('role') != 'student':
            flash('Access denied. Student portal only.', 'danger')
            return redirect(url_for('admin_dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Requires logged in user to have the 'admin' role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in as an administrator.', 'warning')
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            flash('Access denied. Administrator privileges required.', 'danger')
            return redirect(url_for('student_dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def calculate_profile_completion(profile, skills_count, certs_count, projects_count, resume_exists):
    """Calculates student profile completion percentage based on multiple criteria."""
    score = 0
    total = 100

    # Basic info
    if profile:
        if profile['register_no']: score += 10
        if profile['phone']: score += 10
        if profile['department']: score += 10
        if profile['year']: score += 5
        if profile['cgpa']: score += 10
        if profile['about_me']: score += 10
        if profile['profile_photo'] and profile['profile_photo'] != 'default_avatar.png': score += 5
    
    # Skills
    if skills_count >= 3: score += 15
    elif skills_count >= 1: score += 10

    # Certifications
    if certs_count >= 1: score += 10

    # Projects
    if projects_count >= 1: score += 10

    # Resume
    if resume_exists: score += 5

    return min(score, 100)


# ==============================================================================
# PUBLIC ROUTES
# ==============================================================================

@app.route('/')
def index():
    """Landing Page with Hero, Features, Statistics, and CTAs."""
    db = get_db()
    # Placement Highlights / Statistics
    total_students = db.execute("SELECT COUNT(*) as count FROM users WHERE role = 'student'").fetchone()['count']
    total_jobs = db.execute("SELECT COUNT(*) as count FROM jobs").fetchone()['count']
    total_applications = db.execute("SELECT COUNT(*) as count FROM job_applications").fetchone()['count']
    total_placed = db.execute("SELECT COUNT(DISTINCT student_id) as count FROM job_applications WHERE status = 'Selected'").fetchone()['count']
    recent_jobs = db.execute("SELECT * FROM jobs ORDER BY id DESC LIMIT 3").fetchall()

    return render_template('index.html',
                           total_students=total_students,
                           total_jobs=total_jobs,
                           total_applications=total_applications,
                           total_placed=total_placed,
                           recent_jobs=recent_jobs)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login handler for both Students and Admins."""
    if 'user_id' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('student_dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()

        if not email or not password:
            flash('Please provide both email and password.', 'warning')
            return render_template('login.html', email=email)

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE LOWER(email) = ?", (email,)).fetchone()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['name'] = user['name']
            session['email'] = user['email']
            session['role'] = user['role']
            flash(f"Welcome back, {user['name']}!", 'success')

            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('student_dashboard'))
        else:
            flash('Invalid email or password. Please check your credentials.', 'danger')
            return render_template('login.html', email=email)

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Student Registration."""
    if 'user_id' in session:
        return redirect(url_for('student_dashboard'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        register_no = request.form.get('register_no', '').strip()
        department = request.form.get('department', '').strip()

        # Validation
        if not name or not email or not password:
            flash('Please fill in all mandatory fields.', 'warning')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html', name=name, email=email, register_no=register_no, department=department)

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'warning')
            return render_template('register.html', name=name, email=email, register_no=register_no, department=department)

        db = get_db()
        # Check existing user
        existing_user = db.execute("SELECT id FROM users WHERE LOWER(email) = ?", (email,)).fetchone()
        if existing_user:
            flash('Email is already registered. Please log in.', 'warning')
            return redirect(url_for('login'))

        password_hash = generate_password_hash(password)
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO users (name, email, password_hash, role)
            VALUES (?, ?, ?, 'student')
        """, (name, email, password_hash))
        new_user_id = cursor.lastrowid

        # Create associated student profile
        cursor.execute("""
            INSERT INTO student_profiles (user_id, register_no, department)
            VALUES (?, ?, ?)
        """, (new_user_id, register_no, department))

        db.commit()

        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    """Logs out user and clears session."""
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))


# ==============================================================================
# STUDENT PORTAL ROUTES
# ==============================================================================

@app.route('/student/dashboard')
@student_required
def student_dashboard():
    """Student Dashboard with summary metrics and recent activity."""
    student_id = session['user_id']
    db = get_db()

    profile = db.execute("SELECT * FROM student_profiles WHERE user_id = ?", (student_id,)).fetchone()
    skills_count = db.execute("SELECT COUNT(*) as count FROM student_skills WHERE student_id = ?", (student_id,)).fetchone()['count']
    certs_count = db.execute("SELECT COUNT(*) as count FROM certifications WHERE student_id = ?", (student_id,)).fetchone()['count']
    projects_count = db.execute("SELECT COUNT(*) as count FROM projects WHERE student_id = ?", (student_id,)).fetchone()['count']
    apps_count = db.execute("SELECT COUNT(*) as count FROM job_applications WHERE student_id = ?", (student_id,)).fetchone()['count']
    selected_count = db.execute("SELECT COUNT(*) as count FROM job_applications WHERE student_id = ? AND status = 'Selected'", (student_id,)).fetchone()['count']
    resume = db.execute("SELECT * FROM resumes WHERE student_id = ?", (student_id,)).fetchone()

    # Calculate profile completion
    completion_pct = calculate_profile_completion(profile, skills_count, certs_count, projects_count, resume is not None)

    # Recent applications
    recent_apps = db.execute("""
        SELECT a.*, j.title as job_title, j.company, j.location, j.job_type
        FROM job_applications a
        JOIN jobs j ON a.job_id = j.id
        WHERE a.student_id = ?
        ORDER BY a.applied_at DESC LIMIT 5
    """, (student_id,)).fetchall()

    # Recommended jobs
    recommended_jobs = db.execute("SELECT * FROM jobs ORDER BY id DESC LIMIT 3").fetchall()

    return render_template('student_dashboard.html',
                           profile=profile,
                           skills_count=skills_count,
                           certs_count=certs_count,
                           projects_count=projects_count,
                           apps_count=apps_count,
                           selected_count=selected_count,
                           completion_pct=completion_pct,
                           recent_apps=recent_apps,
                           recommended_jobs=recommended_jobs,
                           resume=resume)

@app.route('/student/profile', methods=['GET', 'POST'])
@student_required
def profile():
    """Student Profile View and Update."""
    student_id = session['user_id']
    db = get_db()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        register_no = request.form.get('register_no', '').strip()
        phone = request.form.get('phone', '').strip()
        department = request.form.get('department', '').strip()
        year = request.form.get('year', '').strip()
        cgpa_str = request.form.get('cgpa', '').strip()
        location = request.form.get('location', '').strip()
        about_me = request.form.get('about_me', '').strip()

        cgpa = None
        if cgpa_str:
            try:
                cgpa = float(cgpa_str)
            except ValueError:
                flash('Please enter a valid numeric CGPA.', 'warning')
                return redirect(url_for('profile'))

        # Update User Name
        db.execute("UPDATE users SET name = ? WHERE id = ?", (name, student_id))
        session['name'] = name

        # Handle Profile Photo Upload if present
        photo_filename = None
        if 'profile_photo' in request.files:
            file = request.files['profile_photo']
            if file and file.filename != '':
                ext = file.filename.rsplit('.', 1)[-1].lower()
                if ext in ALLOWED_PHOTO_EXTENSIONS:
                    photo_filename = f"user_{student_id}_{int(datetime.now().timestamp())}.{ext}"
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'photos', photo_filename)
                    file.save(filepath)
                else:
                    flash('Invalid image format. Allowed: PNG, JPG, JPEG, WEBP.', 'warning')

        # Check existing profile
        existing_profile = db.execute("SELECT * FROM student_profiles WHERE user_id = ?", (student_id,)).fetchone()
        if existing_profile:
            if photo_filename:
                db.execute("""
                    UPDATE student_profiles
                    SET register_no = ?, phone = ?, department = ?, year = ?, cgpa = ?,
                        location = ?, about_me = ?, profile_photo = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (register_no, phone, department, year, cgpa, location, about_me, photo_filename, student_id))
            else:
                db.execute("""
                    UPDATE student_profiles
                    SET register_no = ?, phone = ?, department = ?, year = ?, cgpa = ?,
                        location = ?, about_me = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (register_no, phone, department, year, cgpa, location, about_me, student_id))
        else:
            db.execute("""
                INSERT INTO student_profiles (user_id, register_no, phone, department, year, cgpa, location, about_me, profile_photo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (student_id, register_no, phone, department, year, cgpa, location, about_me, photo_filename or 'default_avatar.png'))

        db.commit()
        flash('Your profile has been updated successfully!', 'success')
        return redirect(url_for('profile'))

    user = db.execute("SELECT * FROM users WHERE id = ?", (student_id,)).fetchone()
    profile_data = db.execute("SELECT * FROM student_profiles WHERE user_id = ?", (student_id,)).fetchone()
    return render_template('profile.html', user=user, profile=profile_data)

@app.route('/student/skills')
@student_required
def skills():
    """Skills Module: list current skills, add new skill modal/form."""
    student_id = session['user_id']
    db = get_db()
    student_skills = db.execute("SELECT * FROM student_skills WHERE student_id = ? ORDER BY id DESC", (student_id,)).fetchall()
    master_skills = db.execute("SELECT name FROM skills ORDER BY name ASC").fetchall()
    return render_template('skills.html', student_skills=student_skills, master_skills=master_skills)

@app.route('/student/skills/add', methods=['POST'])
@student_required
def add_skill():
    """Adds a new skill with proficiency level."""
    student_id = session['user_id']
    skill_name = request.form.get('skill_name', '').strip()
    proficiency = request.form.get('proficiency', 'Beginner').strip()

    if not skill_name:
        flash('Skill name cannot be empty.', 'warning')
        return redirect(url_for('skills'))

    if proficiency not in ('Beginner', 'Intermediate', 'Advanced'):
        proficiency = 'Beginner'

    db = get_db()
    try:
        db.execute("""
            INSERT INTO student_skills (student_id, skill_name, proficiency)
            VALUES (?, ?, ?)
        """, (student_id, skill_name, proficiency))
        db.commit()
        flash(f'Skill "{skill_name}" added successfully!', 'success')
    except sqlite3.IntegrityError:
        flash(f'You have already added the skill "{skill_name}". You can edit its proficiency level.', 'warning')

    return redirect(url_for('skills'))

@app.route('/student/skills/edit/<int:skill_id>', methods=['POST'])
@student_required
def edit_skill(skill_id):
    """Updates proficiency of an existing skill."""
    student_id = session['user_id']
    proficiency = request.form.get('proficiency', 'Intermediate').strip()

    if proficiency in ('Beginner', 'Intermediate', 'Advanced'):
        db = get_db()
        db.execute("""
            UPDATE student_skills
            SET proficiency = ?
            WHERE id = ? AND student_id = ?
        """, (proficiency, skill_id, student_id))
        db.commit()
        flash('Skill proficiency updated successfully!', 'success')
    else:
        flash('Invalid proficiency level selected.', 'warning')

    return redirect(url_for('skills'))

@app.route('/student/skills/delete/<int:skill_id>', methods=['POST'])
@student_required
def delete_skill(skill_id):
    """Deletes a skill from student profile."""
    student_id = session['user_id']
    db = get_db()
    db.execute("DELETE FROM student_skills WHERE id = ? AND student_id = ?", (skill_id, student_id))
    db.commit()
    flash('Skill removed successfully.', 'info')
    return redirect(url_for('skills'))

@app.route('/student/certifications')
@student_required
def certifications():
    """Certifications Module: list certifications and add new."""
    student_id = session['user_id']
    db = get_db()
    certs = db.execute("SELECT * FROM certifications WHERE student_id = ? ORDER BY id DESC", (student_id,)).fetchall()
    return render_template('certifications.html', certifications=certs)

@app.route('/student/certifications/add', methods=['POST'])
@student_required
def add_certification():
    """Adds a new certification."""
    student_id = session['user_id']
    name = request.form.get('name', '').strip()
    organization = request.form.get('organization', '').strip()
    issue_date = request.form.get('issue_date', '').strip()
    certificate_id = request.form.get('certificate_id', '').strip()
    certificate_link = request.form.get('certificate_link', '').strip()

    if not name or not organization or not issue_date:
        flash('Please fill in Certification Name, Issuing Organization, and Issue Date.', 'warning')
        return redirect(url_for('certifications'))

    db = get_db()
    db.execute("""
        INSERT INTO certifications (student_id, name, organization, issue_date, certificate_id, certificate_link)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (student_id, name, organization, issue_date, certificate_id, certificate_link))
    db.commit()

    flash(f'Certification "{name}" added successfully!', 'success')
    return redirect(url_for('certifications'))

@app.route('/student/certifications/delete/<int:cert_id>', methods=['POST'])
@student_required
def delete_certification(cert_id):
    """Deletes a certification."""
    student_id = session['user_id']
    db = get_db()
    db.execute("DELETE FROM certifications WHERE id = ? AND student_id = ?", (cert_id, student_id))
    db.commit()
    flash('Certification deleted successfully.', 'info')
    return redirect(url_for('certifications'))

@app.route('/student/projects')
@student_required
def projects():
    """Projects Module: list projects and add new."""
    student_id = session['user_id']
    db = get_db()
    projects_list = db.execute("SELECT * FROM projects WHERE student_id = ? ORDER BY id DESC", (student_id,)).fetchall()
    return render_template('projects.html', projects=projects_list)

@app.route('/student/projects/add', methods=['POST'])
@student_required
def add_project():
    """Adds a new project."""
    student_id = session['user_id']
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    technologies = request.form.get('technologies', '').strip()
    github_link = request.form.get('github_link', '').strip()
    project_link = request.form.get('project_link', '').strip()
    project_date = request.form.get('project_date', '').strip()

    if not title or not description or not technologies:
        flash('Please fill in Project Title, Description, and Technologies Used.', 'warning')
        return redirect(url_for('projects'))

    db = get_db()
    db.execute("""
        INSERT INTO projects (student_id, title, description, technologies, github_link, project_link, project_date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (student_id, title, description, technologies, github_link, project_link, project_date))
    db.commit()

    flash(f'Project "{title}" added successfully!', 'success')
    return redirect(url_for('projects'))

@app.route('/student/projects/delete/<int:project_id>', methods=['POST'])
@student_required
def delete_project(project_id):
    """Deletes a project."""
    student_id = session['user_id']
    db = get_db()
    db.execute("DELETE FROM projects WHERE id = ? AND student_id = ?", (project_id, student_id))
    db.commit()
    flash('Project removed successfully.', 'info')
    return redirect(url_for('projects'))

@app.route('/student/jobs')
@student_required
def jobs():
    """Job Opportunities listing with search, filtering, and apply action."""
    student_id = session['user_id']
    db = get_db()

    search_query = request.args.get('search', '').strip()
    job_type = request.args.get('type', '').strip()

    sql = "SELECT * FROM jobs WHERE 1=1"
    params = []

    if search_query:
        sql += " AND (title LIKE ? OR company LIKE ? OR required_skills LIKE ? OR location LIKE ?)"
        term = f"%{search_query}%"
        params.extend([term, term, term, term])

    if job_type:
        sql += " AND job_type = ?"
        params.append(job_type)

    sql += " ORDER BY id DESC"
    all_jobs = db.execute(sql, params).fetchall()

    # Get set of jobs already applied for by this student
    applied_rows = db.execute("SELECT job_id, status FROM job_applications WHERE student_id = ?", (student_id,)).fetchall()
    applied_job_map = {row['job_id']: row['status'] for row in applied_rows}

    return render_template('jobs.html', jobs=all_jobs, applied_job_map=applied_job_map,
                           search_query=search_query, job_type=job_type)

@app.route('/student/jobs/apply/<int:job_id>', methods=['POST'])
@student_required
def apply_job(job_id):
    """Applies for a job. Prevents duplicate applications."""
    student_id = session['user_id']
    db = get_db()

    # Check if job exists
    job = db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if not job:
        flash('Job not found.', 'danger')
        return redirect(url_for('jobs'))

    # Check for duplicate application
    existing = db.execute("SELECT * FROM job_applications WHERE job_id = ? AND student_id = ?", (job_id, student_id)).fetchone()
    if existing:
        flash(f'You have already applied for the position "{job["title"]}" at {job["company"]}.', 'warning')
        return redirect(url_for('applications'))

    try:
        db.execute("""
            INSERT INTO job_applications (job_id, student_id, status)
            VALUES (?, ?, 'Applied')
        """, (job_id, student_id))
        db.commit()
        flash(f'Application submitted successfully for "{job["title"]}" at {job["company"]}!', 'success')
    except sqlite3.IntegrityError:
        flash('You have already applied for this job.', 'warning')

    return redirect(url_for('applications'))

@app.route('/student/applications')
@student_required
def applications():
    """Application Tracking: View all jobs applied by the student and their status."""
    student_id = session['user_id']
    db = get_db()
    apps = db.execute("""
        SELECT a.*, j.title as job_title, j.company, j.location, j.job_type, j.salary, j.deadline
        FROM job_applications a
        JOIN jobs j ON a.job_id = j.id
        WHERE a.student_id = ?
        ORDER BY a.applied_at DESC
    """, (student_id,)).fetchall()
    return render_template('applications.html', applications=apps)

@app.route('/student/skill-gap')
@student_required
def skill_gap():
    """Interactive Skill Gap Analyzer."""
    student_id = session['user_id']
    db = get_db()

    selected_job_id = request.args.get('job_id', type=int)
    all_jobs = db.execute("SELECT id, title, company, required_skills FROM jobs ORDER BY id DESC").fetchall()
    student_skills = [row['skill_name'].strip() for row in db.execute("SELECT skill_name FROM student_skills WHERE student_id = ?", (student_id,)).fetchall()]

    return render_template('skill_gap.html',
                           jobs=all_jobs,
                           student_skills=student_skills,
                           selected_job_id=selected_job_id)

@app.route('/api/skill-gap/<int:job_id>')
@student_required
def api_skill_gap(job_id):
    """API endpoint that compares student skills against a job's requirements."""
    student_id = session['user_id']
    db = get_db()

    job = db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if not job:
        return jsonify({'error': 'Job not found'}), 404

    # Extract required skills (comma-separated)
    required_skills_raw = [s.strip() for s in job['required_skills'].split(',') if s.strip()]
    
    # Get student skills
    student_skills_rows = db.execute("SELECT skill_name, proficiency FROM student_skills WHERE student_id = ?", (student_id,)).fetchall()
    student_skills_map = {row['skill_name'].lower().strip(): row['proficiency'] for row in student_skills_rows}

    matched_skills = []
    missing_skills = []

    for req in required_skills_raw:
        req_clean = req.lower()
        if req_clean in student_skills_map:
            matched_skills.append({
                'name': req,
                'proficiency': student_skills_map[req_clean]
            })
        else:
            missing_skills.append(req)

    total_req = len(required_skills_raw)
    match_percentage = int((len(matched_skills) / total_req * 100)) if total_req > 0 else 100

    # Generate custom recommendation
    if match_percentage == 100:
        recommendation = f"Outstanding match! Your skill set aligns 100% with the requirements for {job['title']} at {job['company']}. You are strongly encouraged to apply!"
    elif match_percentage >= 70:
        recommendation = f"Strong match ({match_percentage}%). Consider polishing: {', '.join(missing_skills)} to maximize your chances."
    elif match_percentage >= 40:
        recommendation = f"Moderate match ({match_percentage}%). Focus on learning: {', '.join(missing_skills)} through certifications or hands-on mini projects before your interview."
    else:
        recommendation = f"Significant skill gap ({match_percentage}% match). Priority skills to acquire: {', '.join(missing_skills)}."

    return jsonify({
        'job_id': job['id'],
        'job_title': job['title'],
        'company': job['company'],
        'required_skills': required_skills_raw,
        'matched_skills': matched_skills,
        'missing_skills': missing_skills,
        'match_percentage': match_percentage,
        'recommendation': recommendation
    })

@app.route('/student/resume')
@student_required
def resume():
    """Resume management: View current resume, upload or replace PDF."""
    student_id = session['user_id']
    db = get_db()
    current_resume = db.execute("SELECT * FROM resumes WHERE student_id = ?", (student_id,)).fetchone()
    return render_template('resume.html', resume=current_resume)

@app.route('/student/resume/upload', methods=['POST'])
@student_required
def upload_resume():
    """Uploads or replaces PDF resume with strict file type validation."""
    student_id = session['user_id']

    if 'resume_file' not in request.files:
        flash('No file selected.', 'warning')
        return redirect(url_for('resume'))

    file = request.files['resume_file']
    if file.filename == '':
        flash('Please choose a file to upload.', 'warning')
        return redirect(url_for('resume'))

    # Extension validation
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext != 'pdf':
        flash('Invalid file format. Only PDF files (.pdf) are allowed for resumes.', 'danger')
        return redirect(url_for('resume'))

    orig_filename = secure_filename(file.filename) or 'resume.pdf'
    unique_filename = f"resume_student_{student_id}_{int(datetime.now().timestamp())}.pdf"
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], 'resumes', unique_filename)
    file.save(save_path)

    db = get_db()
    # Check if student already has a resume record
    existing = db.execute("SELECT * FROM resumes WHERE student_id = ?", (student_id,)).fetchone()
    if existing:
        # Delete old file from disk if it exists
        old_path = os.path.join(app.config['UPLOAD_FOLDER'], 'resumes', existing['filename'])
        if os.path.exists(old_path):
            try:
                os.remove(old_path)
            except OSError:
                pass

        db.execute("""
            UPDATE resumes
            SET filename = ?, original_filename = ?, upload_date = CURRENT_TIMESTAMP
            WHERE student_id = ?
        """, (unique_filename, orig_filename, student_id))
        flash('Resume replaced successfully!', 'success')
    else:
        db.execute("""
            INSERT INTO resumes (student_id, filename, original_filename)
            VALUES (?, ?, ?)
        """, (student_id, unique_filename, orig_filename))
        flash('Resume uploaded successfully!', 'success')

    db.commit()
    return redirect(url_for('resume'))

@app.route('/student/resume/delete', methods=['POST'])
@student_required
def delete_resume():
    """Deletes uploaded resume."""
    student_id = session['user_id']
    db = get_db()
    res = db.execute("SELECT * FROM resumes WHERE student_id = ?", (student_id,)).fetchone()
    if res:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'resumes', res['filename'])
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass
        db.execute("DELETE FROM resumes WHERE student_id = ?", (student_id,))
        db.commit()
        flash('Resume deleted successfully.', 'info')
    else:
        flash('No resume found to delete.', 'warning')
    return redirect(url_for('resume'))


# ==============================================================================
# ADMIN PORTAL ROUTES
# ==============================================================================

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Admin Dashboard with Placement KPI metrics and Chart.js analytics."""
    db = get_db()

    total_students = db.execute("SELECT COUNT(*) as count FROM users WHERE role = 'student'").fetchone()['count']
    total_jobs = db.execute("SELECT COUNT(*) as count FROM jobs").fetchone()['count']
    total_applications = db.execute("SELECT COUNT(*) as count FROM job_applications").fetchone()['count']
    total_placed = db.execute("SELECT COUNT(DISTINCT student_id) as count FROM job_applications WHERE status = 'Selected'").fetchone()['count']

    # Application status distribution
    status_counts_rows = db.execute("""
        SELECT status, COUNT(*) as count
        FROM job_applications
        GROUP BY status
    """).fetchall()
    status_map = {'Applied': 0, 'Shortlisted': 0, 'Interview': 0, 'Selected': 0, 'Rejected': 0}
    for row in status_counts_rows:
        status_map[row['status']] = row['count']

    # Students by department
    dept_rows = db.execute("""
        SELECT COALESCE(NULLIF(department, ''), 'Unassigned') as dept, COUNT(*) as count
        FROM student_profiles
        GROUP BY dept
        ORDER BY count DESC
    """).fetchall()
    dept_labels = [row['dept'] for row in dept_rows]
    dept_counts = [row['count'] for row in dept_rows]

    # Recent applications
    recent_applications = db.execute("""
        SELECT a.*, u.name as student_name, u.email as student_email, j.title as job_title, j.company
        FROM job_applications a
        JOIN users u ON a.student_id = u.id
        JOIN jobs j ON a.job_id = j.id
        ORDER BY a.applied_at DESC LIMIT 6
    """).fetchall()

    return render_template('admin_dashboard.html',
                           total_students=total_students,
                           total_jobs=total_jobs,
                           total_applications=total_applications,
                           total_placed=total_placed,
                           status_map=status_map,
                           dept_labels=dept_labels,
                           dept_counts=dept_counts,
                           recent_applications=recent_applications)

@app.route('/admin/students')
@admin_required
def admin_students():
    """Admin: View and search students, filter by department."""
    db = get_db()

    search = request.args.get('search', '').strip()
    dept_filter = request.args.get('department', '').strip()

    sql = """
        SELECT u.id, u.name, u.email, u.created_at,
               p.register_no, p.department, p.year, p.cgpa, p.phone, p.location,
               (SELECT COUNT(*) FROM student_skills WHERE student_id = u.id) as skill_count,
               (SELECT COUNT(*) FROM job_applications WHERE student_id = u.id AND status = 'Selected') as is_placed,
               (SELECT filename FROM resumes WHERE student_id = u.id) as resume_file
        FROM users u
        LEFT JOIN student_profiles p ON u.id = p.user_id
        WHERE u.role = 'student'
    """
    params = []

    if search:
        sql += " AND (u.name LIKE ? OR u.email LIKE ? OR p.register_no LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term])

    if dept_filter:
        sql += " AND p.department = ?"
        params.append(dept_filter)

    sql += " ORDER BY u.id DESC"
    students_list = db.execute(sql, params).fetchall()

    # Get distinct departments for filter dropdown
    departments = db.execute("SELECT DISTINCT department FROM student_profiles WHERE department IS NOT NULL AND department != ''").fetchall()

    return render_template('students.html', students=students_list, departments=departments,
                           search=search, dept_filter=dept_filter)

@app.route('/admin/student/<int:user_id>')
@admin_required
def admin_student_detail(user_id):
    """Admin: View detailed student profile (skills, certs, projects, resume)."""
    db = get_db()
    student = db.execute("SELECT * FROM users WHERE id = ? AND role = 'student'", (user_id,)).fetchone()
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('admin_students'))

    profile_data = db.execute("SELECT * FROM student_profiles WHERE user_id = ?", (user_id,)).fetchone()
    skills_list = db.execute("SELECT * FROM student_skills WHERE student_id = ? ORDER BY proficiency DESC", (user_id,)).fetchall()
    certs = db.execute("SELECT * FROM certifications WHERE student_id = ? ORDER BY issue_date DESC", (user_id,)).fetchall()
    projects_list = db.execute("SELECT * FROM projects WHERE student_id = ? ORDER BY id DESC", (user_id,)).fetchall()
    resume_file = db.execute("SELECT * FROM resumes WHERE student_id = ?", (user_id,)).fetchone()
    student_apps = db.execute("""
        SELECT a.*, j.title as job_title, j.company, j.location, j.salary
        FROM job_applications a
        JOIN jobs j ON a.job_id = j.id
        WHERE a.student_id = ?
        ORDER BY a.applied_at DESC
    """, (user_id,)).fetchall()

    return render_template('student_detail.html',
                           student=student,
                           profile=profile_data,
                           skills=skills_list,
                           certifications=certs,
                           projects=projects_list,
                           resume=resume_file,
                           applications=student_apps)

@app.route('/admin/jobs')
@admin_required
def admin_jobs():
    """Admin: Job Management (Add, View, Edit, Delete)."""
    db = get_db()
    all_jobs = db.execute("""
        SELECT j.*, (SELECT COUNT(*) FROM job_applications WHERE job_id = j.id) as applicants_count
        FROM jobs j
        ORDER BY j.id DESC
    """).fetchall()
    return render_template('admin_jobs.html', jobs=all_jobs)

@app.route('/admin/jobs/add', methods=['POST'])
@admin_required
def admin_add_job():
    """Admin: Create new job posting."""
    title = request.form.get('title', '').strip()
    company = request.form.get('company', '').strip()
    location = request.form.get('location', '').strip()
    job_type = request.form.get('job_type', 'Full-Time').strip()
    required_skills = request.form.get('required_skills', '').strip()
    salary = request.form.get('salary', '').strip()
    deadline = request.form.get('deadline', '').strip()
    description = request.form.get('description', '').strip()

    if not title or not company or not required_skills or not deadline:
        flash('Please fill in Job Title, Company, Required Skills, and Deadline.', 'warning')
        return redirect(url_for('admin_jobs'))

    db = get_db()
    db.execute("""
        INSERT INTO jobs (title, company, location, job_type, required_skills, salary, deadline, description)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (title, company, location, job_type, required_skills, salary, deadline, description))
    db.commit()

    flash(f'Job posting for "{title}" at {company} created successfully!', 'success')
    return redirect(url_for('admin_jobs'))

@app.route('/admin/jobs/edit/<int:job_id>', methods=['POST'])
@admin_required
def admin_edit_job(job_id):
    """Admin: Update existing job posting."""
    title = request.form.get('title', '').strip()
    company = request.form.get('company', '').strip()
    location = request.form.get('location', '').strip()
    job_type = request.form.get('job_type', 'Full-Time').strip()
    required_skills = request.form.get('required_skills', '').strip()
    salary = request.form.get('salary', '').strip()
    deadline = request.form.get('deadline', '').strip()
    description = request.form.get('description', '').strip()

    db = get_db()
    db.execute("""
        UPDATE jobs
        SET title = ?, company = ?, location = ?, job_type = ?,
            required_skills = ?, salary = ?, deadline = ?, description = ?
        WHERE id = ?
    """, (title, company, location, job_type, required_skills, salary, deadline, description, job_id))
    db.commit()

    flash('Job updated successfully!', 'success')
    return redirect(url_for('admin_jobs'))

@app.route('/admin/jobs/delete/<int:job_id>', methods=['POST'])
@admin_required
def admin_delete_job(job_id):
    """Admin: Delete job posting."""
    db = get_db()
    db.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
    db.commit()
    flash('Job deleted successfully.', 'info')
    return redirect(url_for('admin_jobs'))

@app.route('/admin/applications')
@admin_required
def admin_applications():
    """Admin: View and manage all student job applications."""
    db = get_db()

    status_filter = request.args.get('status', '').strip()
    job_filter = request.args.get('job_id', type=int)

    sql = """
        SELECT a.*, u.name as student_name, u.email as student_email,
               p.department, p.register_no, p.cgpa,
               j.title as job_title, j.company, j.location,
               r.filename as resume_file
        FROM job_applications a
        JOIN users u ON a.student_id = u.id
        LEFT JOIN student_profiles p ON u.id = p.user_id
        JOIN jobs j ON a.job_id = j.id
        LEFT JOIN resumes r ON u.id = r.student_id
        WHERE 1=1
    """
    params = []

    if status_filter:
        sql += " AND a.status = ?"
        params.append(status_filter)

    if job_filter:
        sql += " AND a.job_id = ?"
        params.append(job_filter)

    sql += " ORDER BY a.applied_at DESC"
    all_applications = db.execute(sql, params).fetchall()
    all_jobs = db.execute("SELECT id, title, company FROM jobs ORDER BY id DESC").fetchall()

    return render_template('admin_applications.html',
                           applications=all_applications,
                           jobs=all_jobs,
                           status_filter=status_filter,
                           job_filter=job_filter)

@app.route('/admin/applications/update-status/<int:app_id>', methods=['POST'])
@admin_required
def admin_update_application_status(app_id):
    """Admin: Updates an application status (Applied, Shortlisted, Interview, Selected, Rejected)."""
    new_status = request.form.get('status', '').strip()
    valid_statuses = ('Applied', 'Shortlisted', 'Interview', 'Selected', 'Rejected')

    if new_status not in valid_statuses:
        flash('Invalid status value provided.', 'danger')
        return redirect(request.referrer or url_for('admin_applications'))

    db = get_db()
    db.execute("UPDATE job_applications SET status = ? WHERE id = ?", (new_status, app_id))
    db.commit()

    flash(f'Application status updated to "{new_status}"!', 'success')
    return redirect(request.referrer or url_for('admin_applications'))


# ==============================================================================
# SECURE FILE SERVING
# ==============================================================================

@app.route('/uploads/resumes/<path:filename>')
@login_required
def view_resume_file(filename):
    """Serves resume PDFs securely for authenticated students and admins."""
    folder = os.path.join(app.config['UPLOAD_FOLDER'], 'resumes')
    return send_from_directory(folder, filename)

@app.route('/uploads/photos/<path:filename>')
def view_photo_file(filename):
    """Serves uploaded profile photos."""
    folder = os.path.join(app.config['UPLOAD_FOLDER'], 'photos')
    return send_from_directory(folder, filename)


# ==============================================================================
# APPLICATION ENTRYPOINT
# ==============================================================================

if __name__ == '__main__':
    # Initialize DB and seed demo data on first start
    init_db()
    print("=" * 60)
    print(" Student Skill & Placement Tracker")
    print(" Server running on: http://127.0.0.1:5000")
    print(" Demo Admin:   admin@placement.edu  | Password: admin123")
    print(" Demo Student: student@college.edu  | Password: student123")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)
