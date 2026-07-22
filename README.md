# 🎓 Interactive Flashcard, Quiz & ADK 2.0 AI-Tutor Platform

An intelligent, responsive web platform for student learning, automated assessment, and real-time AI tutoring. Built with a **Python Flask** web backend, **SQLite** database, **Vanilla JavaScript**, modern **CSS3 Glassmorphic Design System**, and an **ADK 2.0 Graph Workflow AI Agent** (`ai-tutor-agent`).

---

## 🏗️ Architecture Overview

The platform consists of two integrated components:
1. **Web Portal & Backend**: Flask web app providing quiz management, flashcards, student dashboards, custom quiz builders, and a right-side AI Tutor Chat widget.
2. **ADK 2.0 AI-Tutor Graph Workflow Agent (`ai-tutor-agent/`)**: Enterprise security-hardened ADK 2.0 Graph Workflow with pre-ingestion payload sanitization, pre-LLM prompt injection guardrails, deterministic auto-grading, Gemini AI review, and Human-in-the-Loop (`RequestInput`) verification.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                     Browser Client                                     │
│  HTML Templates (index, subjects, quiz, result, profile) | CSS3 | Vanilla JS Engines    │
│  🤖 Right-Side AI Tutor Chat Drawer (static/js/ai-tutor-widget.js)                      │
└────────────┬──────────────────────────────────────────────────────────────┬────────────┘
             │                                                              │
   HTTP Page Routes / REST APIs                                    AI Tutor Chat API
(GET /, GET /quiz, POST /api/login)                                (POST /api/tutor/chat)
             │                                                              │
             ▼                                                              ▼
┌───────────────────────────┐    REST Interop      ┌─────────────────────────────────────┐
│       Flask Backend       │ ◄──────────────────► │    ADK 2.0 AI-Tutor Agent Graph    │
│ (app.py, ai_service.py)   │                      │    (ai-tutor-agent/app/agent.py)   │
└────────────┬──────────────┘                      └──────────────────┬──────────────────┘
             │                                                        │
    Database Queries                                          Security Policy Engine
             ▼                                                        ▼
┌───────────────────────────┐                      ┌─────────────────────────────────────┐
│  SQLite DB (quiz.db)      │                      │  • Gate 1: XSS / SQLi Sanitization  │
│  (users, results, etc.)   │                      │  • Gate 2: Prompt Injection Guard   │
└───────────────────────────┘                      │  • HITL RequestInput Audit Context  │
                                                   └─────────────────────────────────────┘
```

---

## 📁 Repository Structure

```
Hackathon/
├── run.py                          # Launcher script for the Flask Web Server
├── README.md                       # Complete platform documentation & system overview
├── CODE_FLOW.md                    # Detailed code execution & data flow guide
├── backend/                        # Backend implementation & database models
│   ├── __init__.py                 # Package initializer
│   ├── app.py                      # Main Flask application, routes & REST APIs
│   ├── ai_service.py               # Gemini API client with fallback model chain & smart fallback
│   └── database/                   # SQLite database storage & SQL schemas
│       ├── questions.sql           # Initial question bank seed data
│       └── quiz.db                 # SQLite runtime database file
├── ai-tutor-agent/                 # ADK 2.0 Graph Workflow AI Agent
│   ├── agents-cli-manifest.yaml    # Agents CLI manifest file
│   ├── pyproject.toml              # Dependencies & ADK 2.0 configuration
│   ├── app/
│   │   ├── agent.py                # ADK 2.0 Graph Workflow topology & node functions
│   │   ├── security.py             # Pre-ingestion sanitization & prompt injection guard
│   │   ├── config.py               # Model thresholds & configuration settings
│   │   └── fast_api_app.py         # FastAPI runner for ADK server & A2A protocol
│   └── tests/                      # Unit & integration test suites for AI agent
├── static/                         # Static web assets
│   ├── css/
│   │   └── style.css               # Global glassmorphism design system & widget styles
│   └── js/                         # Modular JavaScript engines
│       ├── app.js                  # Student login & authentication engine
│       ├── subject.js              # Subject card selection & custom quiz creator modal
│       ├── quiz.js                 # Interactive quiz renderer & option selection
│       ├── result.js               # Score reviewer & past attempts history renderer
│       ├── profile.js              # Profile dashboard & analytics summary engine
│       └── ai-tutor-widget.js      # Right-side AI Tutor floating sidebar chat drawer
└── templates/                      # Frontend HTML templates
    ├── index.html                  # Student login portal template
    ├── subjects.html               # Subject dashboard & custom quiz builder template
    ├── quiz.html                   # Interactive quiz test template
    ├── result.html                 # Score result review & solution breakdown template
    └── profile.html                # Student profile & performance analytics template
```

---

## ⭐ Core Features & Capabilities

### 1. Student Portal & Authentication (`templates/index.html` & `static/js/app.js`)
- Collects Student Name, Roll Number (3-digit), Email, Academic Year, and Batch.
- Persists session attributes in browser `localStorage` and records user logins in SQLite.

### 2. Subject Dashboard & Custom Quiz Creator (`templates/subjects.html` & `static/js/subject.js`)
- Choose from preset subjects (*Web Hosting*, *C Programming*, *Python*, etc.).
- **Custom Quiz Builder**: Create custom subjects and define new multi-choice questions dynamically via modal interface.

### 3. Interactive Quiz Engine (`templates/quiz.html` & `static/js/quiz.js`)
- Dynamic question fetching from database (`GET /api/questions/<subject>`).
- Real-time progress bar, option selection highlighting, option navigation, and automatic score calculation.

### 4. AI Tutor Right-Side Chat Sidebar (`static/js/ai-tutor-widget.js` & `backend/app.py`)
- Floating **🤖 AI Tutor** button in the bottom-right corner across all pages.
- Right-side slide-out glassmorphic drawer overlay.
- **Context-Aware**: Auto-detects active subject context (e.g. `📚 Context: Web Development`).
- **Pedagogical AI**: Powered by Gemini (`gemini-2.0-flash`) via `POST /api/tutor/chat`.
- **Subscript & Math Renderer**: Automatically formats chemical formulas (`H₂O`, `CO₂`, `C₆H₁₂O<sub>6</sub>`) and LaTeX arrows without displaying raw code symbols.
- **Quick Suggestion Chips**: `💡 Give me a hint`, `📖 Explain concept`, and `❓ Practice Question`.
- **Smart Fallback Engine**: Generates instant, formatted study guides during free-tier API rate limit periods.

### 5. ADK 2.0 Graph Workflow Agent (`ai-tutor-agent/`)
- Built using ADK 2.0 Graph Workflow API (`from google.adk.workflow import Workflow`).
- **Dual-Path Routing**:
  - *Fast Path (`difficulty_score < 3`)*: Deterministic Python auto-grading node.
  - *AI Review Path (`difficulty_score ≥ 3`)*: Gemini LLM evaluation + `RequestInput` Human-in-the-Loop tutor verification.
- **Enterprise Security Layer**:
  - *Security Gate 1 (`validate_and_sanitize_payload`)*: Schema validation and XSS/SQLi sanitization.
  - *Security Gate 2 (`prompt_guard_node`)*: Pre-LLM prompt injection scanning (`"ignore system instructions"`, `"DAN mode"`). Diverts malicious inputs to `quarantine_node` before invoking Gemini.
  - *HITL Audit Context*: Displays sanitization and injection risk metadata in `RequestInput` message.

---

## ⚡ How to Run Locally

### 1. Running the Web Application
```bash
# Launch Flask Web Server
python3 run.py
```
Open your browser at **`http://127.0.0.1:5050/`**.

---

### 2. Interacting with ADK 2.0 AI-Tutor Agent via CLI
```bash
cd ai-tutor-agent

# Run agent via CLI with JSON payload
agents-cli run '{"student_id": "std_100", "question_id": "q1", "difficulty_score": 1, "response_text": "Python variables store references.", "subject": "Python"}'
```

---

### 3. Launching ADK Web Playground
```bash
cd ai-tutor-agent

# Launch ADK Web Playground UI for visual graph debugging
agents-cli playground
```
Open your browser at **`http://localhost:8000/`**.
