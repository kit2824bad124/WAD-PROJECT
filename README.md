# Student Skill & Placement Tracker 🎓💼

A modern, clean, responsive, and fully functional full-stack web application designed for college **Web Application Development (WAD)** projects.

Built with **Python Flask**, **SQLite3**, and **Bootstrap 5**, this portal connects aspiring students with campus placement opportunities, provides automated **Skill Gap Analysis**, digital portfolio tracking, and gives placement officers real-time analytics and application management tools.

---

## 🌟 Key Features

### 👨‍🎓 1. Student Portal
* **Student Registration & Secure Authentication**: Password hashing via `werkzeug.security` with session management.
* **Smart Dashboard**:
  - Profile completion progress meter (0–100%).
  - 5 KPI summary cards: Total Skills, Certifications, Projects, Applications, and Placed Offers.
  - Recent application status updates.
* **Comprehensive Profile Management**:
  - Roll/Register Number, Phone, Department, Year, CGPA, Location, Placement Bio, and Profile Photo upload with preview.
* **Skills Module (with Proficiency Levels)**:
  - Add, edit, and delete technical competencies.
  - Proficiency tagging: `Beginner`, `Intermediate`, `Advanced`.
  - Visual mastery indicators for each skill.
* **Certifications Tracker**:
  - Record external credentials (AWS, Oracle, Coursera, Meta, NPTEL) with verification links and certificate IDs.
* **Projects Portfolio**:
  - Highlight academic and capstone software projects with tech stack badges, GitHub repository links, and live demo links.
* **Job Opportunities**:
  - Filter by role type (Full-Time / Internship), location, and required skills.
  - 1-Click application with duplicate submission protection.
* **Application Tracking ("My Applications")**:
  - Color-coded status badges: `Applied`, `Shortlisted`, `Interview`, `Selected` (Placed), and `Rejected`.
* **Interactive Skill Gap Analyzer**:
  - Compares the student's current skills against the job's required skills.
  - Calculates real-time **Skill Match Percentage** (e.g. 80%).
  - Identifies matched skills (✓) and missing competencies (✗).
  - Delivers tailored preparation recommendations.
* **Resume Management**:
  - Upload PDF resume with strict file-type validation.
  - View, replace, or delete resume anytime.

---

### 🛡️ 2. Placement Officer / Admin Portal
* **Placement BI Dashboard**:
  - Metric counters: Total Registered Students, Total Drives, Total Applications, and Total Placed Candidates.
  - **Chart.js Visualizations**:
    1. *Applications by Status* (Doughnut Chart: Applied, Shortlisted, Interview, Selected, Rejected).
    2. *Students by Department* (Bar Chart distribution).
* **Student Directory**:
  - Search candidates by name, roll number, or email.
  - Filter candidates by engineering department.
  - Deep candidate profile inspection (skills, projects, certifications, resume PDF viewer).
* **Job Opportunity Management**:
  - Post new campus recruitment drives with deadlines, required skills, package/stipend, and descriptions.
  - Edit existing drives or delete expired listings.
  - View applicant count per posting.
* **Application & Candidate Pipeline Management**:
  - Filter all incoming applications by job posting or status.
  - In-place status updates (`Applied` ➔ `Shortlisted` ➔ `Interview` ➔ `Selected` ➔ `Rejected`).

---

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | HTML5, CSS3, JavaScript (ES6) | Structure, custom modern styling, and client-side interactions |
| **UI Framework** | Bootstrap 5.3 | Responsive grid layout, modals, navigation, and cards |
| **Icons** | Font Awesome 6 | Vector iconography |
| **Charts** | Chart.js | Interactive dashboard analytics for placement officers |
| **Backend** | Python 3 (Flask) | Lightweight, readable WSGI web server and REST/route logic |
| **Database** | SQLite3 | Native relational database, zero-configuration, ACID compliant |
| **Security** | Werkzeug Security | SHA-256 password hashing, secure file upload sanitization |

---

## 🔑 Default Demo Login Credentials

The database is automatically initialized and pre-seeded on first run with rich sample records:

| Role | Email | Password | Details |
| :--- | :--- | :--- | :--- |
| **Placement Officer (Admin)** | `admin@placement.edu` | `admin123` | Full administrative & placement BI access |
| **Student** | `student@college.edu` | `student123` | Alex Johnson (CSE, 4th Year, 8.85 CGPA, sample skills & resume) |
| **Student (Alternative)** | `priya@college.edu` | `student123` | Priya Sharma (IT, 4th Year, 9.15 CGPA) |

> 💡 **Viva Tip**: On the `/login` page, you can click the **"Student Demo"** or **"Admin Demo"** quick-fill buttons to automatically insert these credentials!

---

## 🚀 Installation & Running Instructions (Windows)

### Prerequisites
* Windows 10/11
* Python 3.9 or higher

### Step 1: Clone or Navigate to the Project Directory
```powershell
cd "c:\Users\Raj priyan\OneDrive\Desktop\WAD proj"
```

### Step 2: Install Dependencies
```powershell
pip install -r requirements.txt
```
*(If using the included virtual environment: `.\venv\Scripts\pip.exe install -r requirements.txt`)*

### Step 3: Start the Flask Application
Run either:
```powershell
python app.py
```
Or simply double-click the **`run.bat`** file in the project folder!

### Step 4: Access in Your Browser
Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 📁 Project Directory Structure

```
student-placement-tracker/
│
├── app.py                      # Core Flask backend, route controllers, and SQLite database helpers
├── database.db                 # SQLite database file (created automatically)
├── requirements.txt            # Python dependencies (Flask, Werkzeug)
├── run.bat                     # 1-Click Windows execution script
├── README.md                   # Complete documentation & viva guide
│
├── templates/                  # Jinja2 HTML templates
│   ├── base.html               # Master layout with navbar, alerts, and footer
│   ├── index.html              # Modern landing page with hero, stats, and workflow
│   ├── login.html              # Authentication sign-in with quick-fill demo buttons
│   ├── register.html           # Student registration form
│   ├── student_sidebar.html    # Reusable student navigation sidebar
│   ├── student_dashboard.html  # Student dashboard with completion meter & KPI cards
│   ├── profile.html            # Profile editor with photo upload & preview
│   ├── skills.html             # Technical skills CRUD with proficiency tags
│   ├── certifications.html     # Certifications showcase
│   ├── projects.html           # Projects portfolio with GitHub/live links
│   ├── jobs.html               # Campus drives listing with search and 1-click apply
│   ├── applications.html       # Application tracking with status badges
│   ├── skill_gap.html          # Interactive Skill Gap Analyzer
│   ├── resume.html             # PDF resume upload, replace, and preview
│   ├── admin_sidebar.html      # Reusable admin navigation sidebar
│   ├── admin_dashboard.html    # Placement BI with Chart.js status & department charts
│   ├── students.html           # Admin candidate directory with search and filters
│   ├── student_detail.html     # Admin deep-dive candidate inspection page
│   ├── admin_jobs.html         # Admin job posting CRUD
│   └── admin_applications.html # Admin application review and status updater
│
└── static/
    ├── css/
    │   └── style.css           # Custom design system, badges, and responsive tweaks
    ├── js/
    │   └── script.js           # Interactive skill gap logic, file validation, and auto-dismiss
    └── uploads/
        ├── photos/             # Uploaded student profile avatars
        └── resumes/            # Uploaded student PDF resumes
```

---

## 🗄️ Database Schema Details

The SQLite database (`database.db`) consists of 9 normalized tables:
1. `users`: Core credentials, names, emails, role (`student` or `admin`), and password hashes.
2. `student_profiles`: Academic metadata (Register No, Department, Year, CGPA, Phone, Location, Bio, Profile Photo).
3. `skills`: Master skills library.
4. `student_skills`: Student competencies with proficiency (`Beginner`, `Intermediate`, `Advanced`).
5. `certifications`: External credentials (Name, Organization, Issue Date, ID, Verification Link).
6. `projects`: Showcase items (Title, Description, Technologies, GitHub URL, Demo URL, Date).
7. `jobs`: Recruitment drives (Title, Company, Location, Type, Required Skills, Salary, Deadline, Description).
8. `job_applications`: Application mapping (`job_id`, `student_id`, `status`, `applied_at`) with unique constraints.
9. `resumes`: Secure PDF resume mapping (`filename`, `original_filename`, `upload_date`).

---

## 🎓 College Viva Q&A Cheat Sheet

**Q1: What architecture does this application follow?**
> *Answer*: It follows the **Model-View-Controller (MVC)** architectural pattern. SQLite represents the Model layer, HTML/Jinja2 templates form the View layer, and Flask route handlers in `app.py` act as Controllers handling business logic and HTTP requests.

**Q2: How is security handled in this project?**
> *Answer*:
> 1. Passwords are never stored as plain text; they are hashed using `generate_password_hash` (PBKDF2 with SHA-256) and verified using `check_password_hash`.
> 2. Session cookies authenticate requests.
> 3. Custom Python decorators (`@login_required`, `@student_required`, `@admin_required`) prevent unauthorized access between roles.
> 4. File uploads are validated server-side for file extensions (`.pdf` for resumes, `.png/.jpg` for avatars) and sanitized with `secure_filename`.

**Q3: How does the Skill Gap Analyzer work?**
> *Answer*:
> The system takes the comma-separated required skills of a job posting and compares them against the student's verified skills list. Case-insensitive matching computes the intersection (matched skills) and the difference (missing skills). The match percentage is calculated as:
> $$\text{Match Percentage} = \left(\frac{\text{Matched Skills Count}}{\text{Total Required Skills}}\right) \times 100$$
> Dynamic recommendations are then generated based on the threshold (e.g. $\ge 70\%$ is a strong match; $<70\%$ highlights specific missing skills to learn).

**Q4: How does the database automatically create itself?**
> *Answer*: In `app.py`, `init_db()` is called on server startup. It executes `CREATE TABLE IF NOT EXISTS` DDL statements and checks if any users exist; if empty, it seeds realistic initial records so the app is immediately demonstrable.
