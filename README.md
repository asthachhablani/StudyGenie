# StudyGenie AI 🎓
## Personalized Study & Exam Preparation Assistant

> **Database:** SQLite (built-in Python) — no database server required. The database file `studygenie.db` is created automatically on first startup.

> **Final Year Project** — Demonstrates an agentic AI architecture for intelligent, personalized learning, addressing the **Smart Study Generator Agent** problem statement.

---

## Problem Statement

Students struggle to efficiently process large volumes of study material, identify weak areas, and plan targeted revision before exams. Traditional studying is passive and generic. StudyGenie AI solves this with a multi-agent AI system that makes study material interactive, generates practice content, and builds personalized study plans.

---

## Features

| Feature | Description |
|---|---|
| 🔐 Authentication | Register, login, JWT + session-based auth, password hashing |
| 📚 Subject Management | Create, edit, delete subjects with per-subject resources |
| 📤 PDF Upload | Upload, validate, securely store PDF study notes |
| ⚙️ Document Processing | Extract text, chunk, generate embeddings, index in ChromaDB |
| 🔍 RAG Q&A | Ask questions — get answers from your own study material |
| 📋 Smart Summaries | Short, detailed, key points, exam-focus, definitions |
| 🃏 Flashcards | AI-generated Q&A flashcards with flip-card UI |
| ✏️ MCQ Quizzes | AI-generated quizzes with scoring, explanations, topic analysis |
| 🎯 Weak Area Analysis | Identify weak topics from quiz history |
| 📅 Study Planner | Personalized day-by-day study plans prioritizing weak topics |
| 🔄 Revision Material | Targeted revision notes for weak topics |
| 🤖 Study Assistant | Conversational AI that routes to the right agent |
| 📊 Dashboard | Progress overview, scores, countdown, task tracking |

---

## Technology Stack

**Backend:** Python 3.11+ · Flask 3.0
**Database:** SQLite (built-in Python — no server needed)
**AI:** IBM watsonx.ai (Granite models) · Groq (LLaMA3)  
**RAG:** sentence-transformers · ChromaDB · PyMuPDF  
**Auth:** PyJWT · bcrypt · Flask sessions  
**Frontend:** HTML5 · CSS3 · Vanilla JavaScript  

---

## Architecture

```
Student Request
      ↓
Flask Route  →  Study Assistant Agent
                      ↓
          Intent Detection (pattern matching)
                      ↓
    ┌─────────────────────────────────────┐
    │  Knowledge  │  Summary  │  Quiz     │
    │  Agent      │  Agent    │  Agent    │
    ├─────────────────────────────────────┤
    │  Flashcard  │  Planner  │  Revision │
    │  Agent      │  Agent    │  Agent    │
    ├─────────────────────────────────────┤
    │  Document   │  Weak     │           │
    │  Agent      │  Area     │           │
    └─────────────────────────────────────┘
          ↓                   ↓
    RAG Pipeline          AI Models
    (ChromaDB)         (IBM / Groq)
          ↓
       Response
```

### RAG Pipeline
```
PDF Upload
    ↓ PyMuPDF text extraction
    ↓ Text cleaning + chunking (500 words / 50 overlap)
    ↓ Embeddings (sentence-transformers/all-MiniLM-L6-v2)
    ↓ ChromaDB vector store (per-subject collection)
    ↓ Cosine similarity search (top-k retrieval)
    ↓ Context + question → IBM Granite / Groq LLaMA3
    ↓ Context-grounded answer + source citations
```

---

## Folder Structure

```
studygenie/
├── app.py                  # Flask application factory
├── config.py               # Configuration from environment variables
├── requirements.txt        # Python dependencies
├── seed.py                 # Optional demo data seeder
├── .env.example            # Environment variable template
├── routes/                 # Flask blueprints
│   ├── auth_routes.py
│   ├── subject_routes.py
│   ├── document_routes.py
│   ├── ai_routes.py
│   ├── quiz_routes.py
│   ├── planner_routes.py
│   ├── dashboard_routes.py
│   └── page_routes.py
├── models/                 # SQLite data helpers
│   ├── db.py
│   ├── auth.py
│   ├── user_model.py
│   ├── subject_model.py
│   ├── document_model.py
│   ├── quiz_model.py
│   ├── progress_model.py
│   └── study_plan_model.py
├── services/               # Core service layer
│   ├── pdf_service.py
│   ├── embedding_service.py
│   ├── vector_service.py
│   ├── rag_service.py
│   ├── ibm_service.py
│   └── groq_service.py
├── agents/                 # Specialized AI agents
│   ├── document_agent.py
│   ├── knowledge_agent.py
│   ├── summary_agent.py
│   ├── flashcard_agent.py
│   ├── quiz_agent.py
│   ├── study_planner_agent.py
│   ├── weak_area_agent.py
│   ├── revision_agent.py
│   └── study_assistant_agent.py
├── templates/              # Jinja2 HTML pages
├── static/                 # CSS, JS, images
├── uploads/                # Uploaded PDFs (git-ignored)
├── vector_store/           # ChromaDB data (git-ignored)
└── tests/                  # Pytest test suite
```

---

## Installation

### Prerequisites
- Python 3.11+
- Groq API key (free at console.groq.com)
- IBM watsonx.ai credentials (optional — app works without them)

> **No database server required.** SQLite is built into Python. The database file `studygenie.db` is created automatically on first run.

### 1. Clone / Navigate to project
```bash
cd studygenie
```

### 2. Create and activate virtual environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
```bash
cp .env.example .env
# Edit .env with your credentials
```

### 5. Run the application
```bash
python app.py
```

Open: http://127.0.0.1:5000/

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | ✅ | Flask session secret key |
| `DATABASE_PATH` | No | SQLite file path (default: `studygenie.db`) |
| `GROQ_API_KEY` | ✅ for AI | Groq API key from console.groq.com |
| `GROQ_MODEL` | No | Default: llama3-8b-8192 |
| `IBM_WATSONX_URL` | Optional | IBM watsonx.ai endpoint |
| `IBM_WATSONX_API_KEY` | Optional | IBM API key |
| `IBM_PROJECT_ID` | Optional | IBM project ID |
| `IBM_MODEL_ID` | Optional | e.g. ibm/granite-13b-instruct-v2 |
| `IBM_ORCHESTRATE_URL` | Optional | IBM Orchestrate endpoint |
| `IBM_ORCHESTRATE_API_KEY` | Optional | IBM Orchestrate key |
| `PORT` | No | Default: 5000 |

---

## Groq Setup

1. Visit https://console.groq.com/keys
2. Create a free API key
3. Add to `.env`: `GROQ_API_KEY=your_key_here`

---

## IBM watsonx.ai Setup

1. Create an account at https://cloud.ibm.com/
2. Create a watsonx.ai project
3. Generate an API key at https://cloud.ibm.com/iam/apikeys
4. Find your project ID in the watsonx.ai project settings
5. Add to `.env`:
   ```
   IBM_WATSONX_URL=https://us-south.ml.cloud.ibm.com
   IBM_WATSONX_API_KEY=your_key_here
   IBM_PROJECT_ID=your_project_id
   IBM_MODEL_ID=ibm/granite-13b-instruct-v2
   ```

**The application works without IBM credentials.** Groq is used as the fallback AI provider.

---

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|---|---|---|
| POST | /api/auth/register | Create account |
| POST | /api/auth/login | Login |
| POST | /api/auth/logout | Logout |
| GET | /api/auth/me | Current user |

### Subjects
| Method | Endpoint | Description |
|---|---|---|
| GET | /api/subjects | List subjects |
| POST | /api/subjects | Create subject |
| GET | /api/subjects/\<id\> | Get subject details |
| PUT | /api/subjects/\<id\> | Update subject |
| DELETE | /api/subjects/\<id\> | Delete subject |

### Documents
| Method | Endpoint | Description |
|---|---|---|
| POST | /api/documents/upload | Upload PDF |
| GET | /api/documents | List documents |
| DELETE | /api/documents/\<id\> | Delete document |
| POST | /api/documents/\<id\>/process | Trigger processing |

### AI
| Method | Endpoint | Description |
|---|---|---|
| POST | /api/ai/ask | RAG question answering |
| POST | /api/ai/summary | Generate summary |
| POST | /api/ai/flashcards | Generate flashcards |
| POST | /api/ai/revision | Generate revision material |
| POST | /api/ai/chat | Study Assistant chat |
| GET | /api/ai/chat/history | Chat history |
| GET | /api/ai/status | AI service status |

### Quizzes
| Method | Endpoint | Description |
|---|---|---|
| GET | /api/quizzes | List quizzes |
| POST | /api/quizzes/generate | Generate quiz |
| GET | /api/quizzes/\<id\> | Get quiz |
| POST | /api/quizzes/\<id\>/submit | Submit answers |
| GET | /api/quizzes/attempts | Quiz attempts |
| GET | /api/quizzes/weak-areas | Weak area analysis |

### Planner
| Method | Endpoint | Description |
|---|---|---|
| POST | /api/planner/generate | Generate study plan |
| GET | /api/planner | List plans |
| GET | /api/planner/latest | Latest plan |
| POST | /api/planner/\<id\>/task/\<n\>/complete | Mark task done |

### Dashboard
| Method | Endpoint | Description |
|---|---|---|
| GET | /api/dashboard | Dashboard stats |
| GET | /api/dashboard/progress | Progress data |
| POST | /api/dashboard/exam-date | Set exam date |

### Health
| Method | Endpoint | Description |
|---|---|---|
| GET | /api/health | Health check |

---

## Database Collections

| Collection | Purpose |
|---|---|
| users | User accounts |
| subjects | Student subjects |
| documents | Uploaded PDF metadata |
| chunks | Extracted text chunks |
| quizzes | Generated quizzes |
| quiz_attempts | Quiz results |
| progress | Topic performance |
| study_plans | Generated study plans |
| flashcards | Generated flashcard sets |
| chat_history | AI conversation history |

---

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pip install pytest-cov
pytest tests/ --cov=. --cov-report=term-missing
```

Tests use a temporary SQLite database. External AI API calls are not made during tests.

---

## Demo Workflow

1. **Register** at /register
2. **Login** at /login
3. **Create subject** "DBMS" at /subjects
4. **Upload PDF** (DBMS notes) at /upload — select the DBMS subject
5. **Process document** — click Process button
6. **Ask a question** at /study-assistant: *"Explain normalization in simple language"*
7. **Generate summary** at /summary: topic = "Normalization", type = "exam"
8. **Generate flashcards** at /flashcards: topic = "Normalization"
9. **Take quiz** at /quiz: topic = "Normalization", 10 questions, medium
10. **Submit quiz** and view topic-wise results
11. **View weak areas** — dashboard shows weak topics
12. **Generate study plan** at /study-plan — 7 days
13. **Generate revision** at /revision — auto-targets weak topics
14. **Dashboard** shows updated progress

---

## Model Selection Strategy

| Task | Model |
|---|---|
| RAG / document-grounded answers | IBM Granite (if configured) → Groq fallback |
| Quiz generation | Groq (fast, structured JSON) |
| Flashcard generation | Groq |
| Summary generation | Groq |
| Study plan generation | Groq |
| Revision material | Groq |

---

## Security Notes

- Passwords hashed with bcrypt (cost factor 12)
- JWT tokens with 24-hour expiry
- File validation: PDF only, 50 MB max, safe filenames
- API keys read from environment variables only
- No credentials in frontend JavaScript
- SQLite parameterized queries (no SQL injection)
- Sessions: HttpOnly, SameSite=Lax cookies

---

## Future Improvements

- IBM watsonx Orchestrate full agent orchestration
- Spaced repetition for flashcard scheduling
- Voice-to-text question input
- Collaborative study groups
- Export study plans to calendar (iCal)
- Mobile app (React Native)
- Support for image-based PDFs (OCR)
- Multi-language support

---

*Built as a final year Computer Science project demonstrating real-world agentic AI architecture.*
