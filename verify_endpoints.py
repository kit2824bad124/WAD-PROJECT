import urllib.request
import http.cookiejar
import urllib.parse
import json

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

def get(url):
    req = urllib.request.Request(url)
    with opener.open(req) as resp:
        return resp.status, resp.read().decode('utf-8')

def post(url, data):
    encoded = urllib.parse.urlencode(data).encode('utf-8')
    req = urllib.request.Request(url, data=encoded)
    with opener.open(req) as resp:
        return resp.status, resp.read().decode('utf-8')

print("Starting live end-to-end endpoint verification...")

status, html = get('http://127.0.0.1:5000/')
assert status == 200 and 'Build Your Skills' in html, 'Landing page failed'
print('[PASS] 1. Landing Page (HTTP 200)')

status, html = post('http://127.0.0.1:5000/login', {'email': 'student@college.edu', 'password': 'student123'})
assert status == 200 and 'Hello, Alex Johnson' in html, 'Student login failed'
print('[PASS] 2. Student Login (Welcome Alex Johnson)')

# 3. Student Routes
student_routes = [
    '/student/dashboard',
    '/student/profile',
    '/student/skills',
    '/student/certifications',
    '/student/projects',
    '/student/jobs',
    '/student/applications',
    '/student/skill-gap',
    '/student/resume'
]
for path in student_routes:
    s, h = get('http://127.0.0.1:5000' + path)
    assert s == 200, f'Failed {path}'
    print(f'[PASS] 3. Student Route: {path} (HTTP 200)')

# 4. Skill Gap API
s, h = get('http://127.0.0.1:5000/api/skill-gap/1')
gap_data = json.loads(h)
pct = gap_data['match_percentage']
job = gap_data['job_title']
print(f'[PASS] 4. Skill Gap API: {pct}% match computed for "{job}"')

# 5. Student Logout
status, html = get('http://127.0.0.1:5000/logout')
print('[PASS] 5. Student Logout')

# 6. Admin Login
status, html = post('http://127.0.0.1:5000/login', {'email': 'admin@placement.edu', 'password': 'admin123'})
assert status == 200 and 'Placement Administration BI' in html, 'Admin login failed'
print('[PASS] 6. Admin Login (Placement Administration BI)')

# 7. Admin Routes
admin_routes = [
    '/admin/dashboard',
    '/admin/students',
    '/admin/student/2',
    '/admin/jobs',
    '/admin/applications'
]
for path in admin_routes:
    s, h = get('http://127.0.0.1:5000' + path)
    assert s == 200, f'Failed {path}'
    print(f'[PASS] 7. Admin Route: {path} (HTTP 200)')

# 8. Admin Logout
status, html = get('http://127.0.0.1:5000/logout')
print('[PASS] 8. Admin Logout')

print("\n------------------------------------------------------------")
print("ALL LIVE APPLICATION ENDPOINTS FULLY OPERATIONAL AND VERIFIED!")
print("------------------------------------------------------------")
