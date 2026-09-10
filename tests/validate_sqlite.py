"""
Quick SQLite migration validation script.
Run: python tests/validate_sqlite.py
"""
import os, sys, json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ['SECRET_KEY'] = 'test-secret-key-abc'
os.environ['DATABASE_PATH'] = 'studygenie_test_validation.db'

print('=== SQLite Migration Validation ===')

from models.db import init_db, get_db_connection
init_db()

conn = get_db_connection()
tables = [r[0] for r in conn.execute(
    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
).fetchall()]
conn.close()
print('Tables:', tables)

expected = {'users','subjects','documents','quizzes','quiz_attempts','progress','study_plans','flashcards','chat_history'}
missing = expected - set(tables)
if missing:
    raise AssertionError(f'MISSING TABLES: {missing}')
print('[PASS] All 9 tables present')

# User
from models.user_model import create_user, find_user_by_email, verify_password
user = create_user('Alice', 'alice@test.com', 'password123')
assert user['id'] is not None
found = find_user_by_email('alice@test.com')
assert found is not None
assert verify_password('password123', found['password_hash'])
print('[PASS] User create + find + verify')

# Duplicate email
try:
    create_user('Alice2', 'alice@test.com', 'password123')
    raise AssertionError('Should have rejected duplicate email')
except Exception as e:
    if 'UNIQUE' in str(e) or 'already exists' in str(e):
        print('[PASS] Duplicate email rejected correctly')
    else:
        raise

# Subject CRUD
from models.subject_model import create_subject, get_subjects_for_user, update_subject, delete_subject
sub = create_subject(user['id'], 'DBMS', 'Database Management')
assert sub['name'] == 'DBMS'
subs = get_subjects_for_user(user['id'])
assert len(subs) == 1
ok = update_subject(sub['id'], user['id'], 'DBMS Updated', 'Desc')
assert ok
updated_subs = get_subjects_for_user(user['id'])
assert updated_subs[0]['name'] == 'DBMS Updated'
print('[PASS] Subject create + list + update')

# Document
from models.document_model import create_document, get_document, update_document_status, delete_document, serialize_document
doc = create_document(user['id'], sub['id'], 'notes.pdf', '/uploads/notes.pdf')
assert doc['status'] == 'uploaded'
update_document_status(doc['id'], 'processed', {'page_count': 10, 'chunk_count': 50})
updated_doc = get_document(doc['id'], user['id'])
assert updated_doc['status'] == 'processed'
assert updated_doc['page_count'] == 10
print('[PASS] Document create + status update')

# Progress
from models.progress_model import upsert_topic_progress, get_weak_topics, get_strong_topics
upsert_topic_progress(user['id'], sub['id'], 'Normalization', 40.0, 'weak')
upsert_topic_progress(user['id'], sub['id'], 'SQL Joins', 85.0, 'strong')
upsert_topic_progress(user['id'], sub['id'], 'Normalization', 45.0, 'weak')  # upsert
weak = get_weak_topics(user['id'])
strong = get_strong_topics(user['id'])
assert 'Normalization' in weak
assert 'SQL Joins' in strong
print('[PASS] Progress upsert + weak/strong query')

# Quiz
from models.quiz_model import create_quiz, get_quiz, save_quiz_attempt, get_attempts_for_user, serialize_quiz
questions = [{'question':'Q1','options':['A','B','C','D'],'correct_answer':'A','explanation':'','topic':'Normalization','difficulty':'easy'}]
quiz = create_quiz(user['id'], sub['id'], 'Normalization', questions)
assert quiz is not None
assert len(quiz['questions']) == 1
retrieved = get_quiz(quiz['id'], user['id'])
assert retrieved['topic'] == 'Normalization'
answers_detail = [{'question_index': 0, 'is_correct': True, 'topic': 'Normalization'}]
attempt = save_quiz_attempt(user['id'], quiz['id'], 1, 1, answers_detail, [])
assert attempt['score'] == 1
assert attempt['percentage'] == 100.0
print('[PASS] Quiz create + retrieve + attempt save')

# Study plan
from models.study_plan_model import create_study_plan, get_latest_plan, serialize_plan
tasks = [{'day': 1, 'tasks': [{'subject': 'DBMS', 'topic': 'Normalization', 'duration_minutes': 60, 'completed': False}]}]
plan = create_study_plan(user['id'], sub['id'], tasks, 7, '2025-06-01')
latest = get_latest_plan(user['id'])
assert latest is not None
assert latest['duration_days'] == 7
assert isinstance(latest['tasks'], list)
print('[PASS] Study plan create + retrieve')

# JWT + auth
from models.auth import generate_token, decode_token
token = generate_token(str(user['id']), user['email'])
payload = decode_token(token)
assert payload['user_id'] == str(user['id'])
print('[PASS] JWT generate + decode')

# Delete subject (cascade should not error)
ok = delete_subject(sub['id'], user['id'])
assert ok
remaining = get_subjects_for_user(user['id'])
assert len(remaining) == 0
print('[PASS] Subject delete')

print()
print('=== ALL VALIDATION CHECKS PASSED ===')

# Cleanup
os.remove('studygenie_test_validation.db')
print('Test database cleaned up.')
