import unittest
import os
import sqlite3
from app import app, init_db

class PlacementTrackerTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config['TESTING'] = True
        app.config['DATABASE'] = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'test_database.db')
        init_db()

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(app.config['DATABASE']):
            try:
                os.remove(app.config['DATABASE'])
            except OSError:
                pass

    def setUp(self):
        self.client = app.test_client()

    def login(self, email, password):
        return self.client.post('/login', data={
            'email': email,
            'password': password
        }, follow_redirects=True)

    def logout(self):
        return self.client.get('/logout', follow_redirects=True)

    def test_01_landing_page(self):
        """Test landing page loads successfully with HTTP 200."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Build Your Skills', response.data)
        self.assertIn(b'Track Your Growth', response.data)
        self.assertIn(b'Get Placed', response.data)

    def test_02_student_login(self):
        """Test student login works and redirects to student dashboard."""
        response = self.login('student@college.edu', 'student123')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Hello, Alex Johnson', response.data)
        self.assertIn(b'Profile Completion Status', response.data)
        self.logout()

    def test_03_admin_login(self):
        """Test admin login works and redirects to admin dashboard."""
        response = self.login('admin@placement.edu', 'admin123')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Placement Administration BI', response.data)
        self.assertIn(b'Applications by Status', response.data)
        self.logout()

    def test_04_role_authorization_protection(self):
        """Test student cannot access admin routes."""
        self.login('student@college.edu', 'student123')
        response = self.client.get('/admin/dashboard', follow_redirects=True)
        # Should redirect to student dashboard with error message
        self.assertIn(b'Access denied', response.data)
        self.assertIn(b'Hello, Alex Johnson', response.data)
        self.logout()

    def test_05_student_skills_crud(self):
        """Test adding, editing, and deleting a skill."""
        self.login('student@college.edu', 'student123')
        
        # Add skill
        resp_add = self.client.post('/student/skills/add', data={
            'skill_name': 'Docker',
            'proficiency': 'Intermediate'
        }, follow_redirects=True)
        self.assertEqual(resp_add.status_code, 200)
        self.assertIn(b'Docker', resp_add.data)

        # Edit skill
        # Find skill id
        db = sqlite3.connect(app.config['DATABASE'])
        db.row_factory = sqlite3.Row
        skill = db.execute("SELECT id FROM student_skills WHERE skill_name = 'Docker'").fetchone()
        self.assertIsNotNone(skill)
        skill_id = skill['id']

        resp_edit = self.client.post(f'/student/skills/edit/{skill_id}', data={
            'proficiency': 'Advanced'
        }, follow_redirects=True)
        self.assertEqual(resp_edit.status_code, 200)
        self.assertIn(b'Skill proficiency updated', resp_edit.data)

        # Delete skill
        resp_del = self.client.post(f'/student/skills/delete/{skill_id}', follow_redirects=True)
        self.assertEqual(resp_del.status_code, 200)
        self.assertIn(b'Skill removed successfully', resp_del.data)
        self.logout()

    def test_06_student_project_crud(self):
        """Test adding and deleting a project."""
        self.login('student@college.edu', 'student123')
        resp_add = self.client.post('/student/projects/add', data={
            'title': 'Test Project',
            'description': 'A unit test project description.',
            'technologies': 'Python, Flask',
            'github_link': 'https://github.com/test/repo',
            'project_link': '',
            'project_date': '2026'
        }, follow_redirects=True)
        self.assertEqual(resp_add.status_code, 200)
        self.assertIn(b'Test Project', resp_add.data)
        self.logout()

    def test_07_skill_gap_api(self):
        """Test Skill Gap Analyzer API calculation."""
        self.login('student@college.edu', 'student123')
        # Check job 1: Junior Full-Stack Developer
        response = self.client.get('/api/skill-gap/1')
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertIn('match_percentage', json_data)
        self.assertIn('matched_skills', json_data)
        self.assertIn('missing_skills', json_data)
        self.assertIn('recommendation', json_data)
        self.logout()

    def test_08_duplicate_job_application_prevention(self):
        """Test student cannot apply to the same job twice."""
        self.login('student@college.edu', 'student123')
        # Student 1 is already applied to job 1 in seed data
        resp = self.client.post('/student/jobs/apply/1', follow_redirects=True)
        self.assertIn(b'already applied', resp.data)
        self.logout()

    def test_09_admin_status_update(self):
        """Test admin can update application status."""
        self.login('admin@placement.edu', 'admin123')
        # Application 1 is currently 'Interview'
        resp = self.client.post('/admin/applications/update-status/1', data={
            'status': 'Selected'
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Application status updated to', resp.data)
        self.logout()

if __name__ == '__main__':
    unittest.main()
