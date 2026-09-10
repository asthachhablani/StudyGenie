"""
Full Flask integration test for SQLite migration.
Run: python tests/validate_flask.py
"""
import os, sys, json, tempfile, shutil
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

tmp_dir = tempfile.mkdtemp()
db_path = os.path.join(tmp_dir, 'test.db')
os.environ['SECRET_KEY'] = 'a' * 32
os.environ['DATABASE_PATH'] = db_path

from app import create_app
app = create_app()
client = app.test_client()

print('=== Flask Integration Tests (SQLite) ===')

# Health
resp = client.get('/api/health')
data = resp.get_json()
assert resp.status_code == 200 and data['database'] == 'connected', f'Health failed: {data}'
print('[PASS] GET /api/health — database: connected')

assert client.get('/').status_code == 200
assert client.get('/login').status_code == 200
assert client.get('/register').status_code == 200
print('[PASS] Landing, login, register pages load')

for path in ['/api/subjects', '/api/documents', '/api/quizzes', '/api/dashboard', '/api/ai/status']:
    r = client.get(path)
    assert r.status_code == 401, f'{path} returned {r.status_code}'
print('[PASS] Protected routes return 401 without auth')

# Register
payload = json.dumps({'name':'Test User','email':'test@sg.test','password':'securepass123','confirm_password':'securepass123'})
resp = client.post('/api/auth/register', data=payload, content_type='application/json')
assert resp.status_code == 201, f'Register failed: {resp.get_json()}'
token = resp.get_json()['token']
user_id = resp.get_json()['user']['id']
print('[PASS] POST /api/auth/register')

auth = {'Authorization': f'Bearer {token}'}

# Duplicate registration
resp2 = client.post('/api/auth/register', data=payload, content_type='application/json')
assert resp2.status_code == 409
print('[PASS] Duplicate registration rejected (409)')

# Login
resp = client.post('/api/auth/login', data=json.dumps({'email':'test@sg.test','password':'securepass123'}), content_type='application/json')
assert resp.status_code == 200
print('[PASS] POST /api/auth/login')

# Me
resp = client.get('/api/auth/me', headers=auth)
assert resp.status_code == 200 and resp.get_json()['user']['email'] == 'test@sg.test'
print('[PASS] GET /api/auth/me')

# Subject CRUD
resp = client.post('/api/subjects', data=json.dumps({'name':'DBMS','description':'DB'}), content_type='application/json', headers=auth)
assert resp.status_code == 201
sub_id = resp.get_json()['subject']['id']
print('[PASS] POST /api/subjects — create')

resp = client.get('/api/subjects', headers=auth)
assert resp.status_code == 200 and len(resp.get_json()['subjects']) == 1
print('[PASS] GET /api/subjects — list')

resp = client.get(f'/api/subjects/{sub_id}', headers=auth)
assert resp.status_code == 200
print('[PASS] GET /api/subjects/<id>')

resp = client.put(f'/api/subjects/{sub_id}', data=json.dumps({'name':'DBMS v2','description':'Updated'}), content_type='application/json', headers=auth)
assert resp.status_code == 200
print('[PASS] PUT /api/subjects/<id>')

# Dashboard
resp = client.get('/api/dashboard', headers=auth)
assert resp.status_code == 200
d = resp.get_json()
assert 'stats' in d and d['stats']['total_subjects'] == 1
print('[PASS] GET /api/dashboard — stats correct')

# Quiz list (empty)
resp = client.get('/api/quizzes', headers=auth)
assert resp.status_code == 200 and resp.get_json()['quizzes'] == []
print('[PASS] GET /api/quizzes — empty list')

# Planner list (empty)
resp = client.get('/api/planner', headers=auth)
assert resp.status_code == 200
print('[PASS] GET /api/planner — empty list')

# Set exam date
resp = client.post('/api/dashboard/exam-date', data=json.dumps({'subject_name':'DBMS','exam_date':'2025-06-01'}), content_type='application/json', headers=auth)
assert resp.status_code == 200
print('[PASS] POST /api/dashboard/exam-date')

# Logout
resp = client.post('/api/auth/logout', headers=auth)
assert resp.status_code == 200
print('[PASS] POST /api/auth/logout')

# Delete subject
resp = client.delete(f'/api/subjects/{sub_id}', headers=auth)
assert resp.status_code == 200
print('[PASS] DELETE /api/subjects/<id>')

# Verify isolation — other user cannot see first user's subjects
payload2 = json.dumps({'name':'Other','email':'other@sg.test','password':'securepass123','confirm_password':'securepass123'})
resp = client.post('/api/auth/register', data=payload2, content_type='application/json')
token2 = resp.get_json()['token']
auth2 = {'Authorization': f'Bearer {token2}'}
resp = client.get('/api/subjects', headers=auth2)
assert len(resp.get_json()['subjects']) == 0
print('[PASS] User isolation — other user sees no subjects')

shutil.rmtree(tmp_dir)
print()
print('=== ALL FLASK INTEGRATION TESTS PASSED ===')
