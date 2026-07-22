# 🗺️ User Flow & Technical Workflow Specification
## Project: Adaptive AI-Tutor & Interactive Assessment Platform
**Team Name**: Purple Hue  
**Team Members**: Ayush (Full-Stack Lead), Kunal (Backend & AI Integration), Abhishek (Frontend & UI/UX Design)

---

## 📌 1. Complete User Flow Architecture

The user flow guides students seamlessly from initial onboarding to interactive assessment, performance analytics, and on-demand AI tutoring.

```mermaid
flowchart TD
    A[index.html: Student Login] -->|Submit Roll Number & Details| B[subjects.html: Subject Dashboard]
    B -->|Select Preset Subject| C[quiz.html: Take Quiz]
    B -->|Click '+ Add Custom Quiz'| D[Custom Quiz Modal]
    D -->|Define Subject & Questions| B
    C -->|Answer Questions & Submit| E[result.html: Score Review & Solution Breakdown]
    E -->|Click 'View Profile'| F[profile.html: Performance Analytics & History]
    
    subgraph AI Tutor Interaction (Available on Every Screen)
        G[Click Right-Edge Side Tab Handle ◀] --> H[Slide-Out AI Tutor Chat Drawer]
        H -->|Ask Concept Query or Click Chip| I[Receive Formatted AI Hint / Study Guide]
    end
```

### Step-by-Step User Journey

1. **Step 1: Student Onboarding (`templates/index.html` & `static/js/app.js`)**
   - Student opens the portal and enters Name, 3-digit Roll Number, Email, Academic Year, and Batch.
   - Client validates fields and sends `POST /api/login`.
   - User profile is saved to SQLite `users` table and session attributes stored in browser `localStorage`.

2. **Step 2: Subject Selection & Custom Quiz Builder (`templates/subjects.html` & `static/js/subject.js`)**
   - Student lands on the dashboard displaying preset subject cards (*Web Hosting*, *C Programming*, *Python*).
   - **Custom Quiz Builder**: Student clicks "+ Add Custom Quiz" to open a glassmorphic modal where they define custom subjects and 5 multi-choice questions with designated correct answers.

3. **Step 3: Interactive Quiz Engine (`templates/quiz.html` & `static/js/quiz.js`)**
   - Questions loaded dynamically via `GET /api/questions/<subject>`.
   - Real-time progress bar, option selection highlighting (`A`, `B`, `C`, `D`), and option navigation (`Next Question` / `Prev Question`).
   - Final score calculated automatically upon submission.

4. **Step 4: Score Review & Solution Breakdown (`templates/result.html` & `static/js/result.js`)**
   - Submits result via `POST /api/submit`.
   - Displays final score percentage, performance grade badges (*Excellent 🌟*, *Good Effort 👍*, *Needs Practice 📖*), question-by-question solution breakdowns, and DB attempt count.

5. **Step 5: Profile Dashboard & Performance Analytics (`templates/profile.html` & `static/js/profile.js`)**
   - Fetches history via `GET /api/results/<rollNumber>` and user metrics via `GET /api/user/<rollNumber>`.
   - Displays aggregate metrics (Total Quizzes Completed, Average Score, Passed Rate) and full historical attempt logs.

6. **Step 6: AI-Tutor Side Assistant Widget (`static/js/ai-tutor-widget.js`)**
   - A compact, glassmorphic side handle tab (`◀`) fixed to the far-right edge of the screen (`position: fixed; right: 0; top: 50%`).
   - Clicking opens a slide-out right drawer overlay auto-detecting the page context (`📚 Context: Web Development`).
   - Offers quick suggestion chips (`💡 Give me a hint`, `📖 Explain concept`, `❓ Practice Question`).
   - Automatically formats chemical and mathematical equations into clean HTML subscripts (e.g. H₂O, CO₂, C₆H₁₂O₆).

---

## 🛠️ 2. Technical System Workflow & Architecture

The technical workflow integrates Flask REST routes, SQLite database storage, Gemini 2.0 LLM reasoning, and Google ADK 2.0 Graph Workflow nodes.

### ADK 2.0 Graph Workflow Node Execution Topology

```
START Event -> parse_submission -> validate_and_sanitize_payload
                                      ├─► (Security Gate 1 Fail: XSS/SQLi) ──► quarantine_node
                                      ├─► (valid & difficulty < 3) ────────────► auto_grade_node
                                      └─► (valid & difficulty >= 3) ───────────► prompt_guard_node
                                                                                    ├─► (Security Gate 2 Fail: Injection) ──► quarantine_node
                                                                                    └─► (clean payload) ────────────────────► llm_review_node ──► tutor_verification_node (HITL)
```

### Step-by-Step Technical Execution Sequence

1. **Phase 1: Web Server Initialization (`backend/app.py` & `run.py`)**
   - Flask server starts on port `5050` with CORS headers enabled (`Access-Control-Allow-Origin: *`).
   - Auto-initializes SQLite database (`init_db()`) and seeds initial questions if empty.

2. **Phase 2: Security Gate 1 — Pre-Ingestion Payload Boundary (`validate_and_sanitize_payload`)**
   - Validates JSON schema types.
   - Escapes script tags (`<script>`) to block Cross-Site Scripting (XSS).
   - Strips SQL injection patterns (`UNION SELECT`, `DROP TABLE`, `; --`).
   - Diverts invalid or malicious payloads to `quarantine_node`.

3. **Phase 3: Security Gate 2 — Pre-LLM Prompt Injection Scanner (`prompt_guard_node`)**
   - Scans text for jailbreaks (`"ignore system instructions"`, `"DAN mode"`).
   - Diverts attack payloads directly to `quarantine_node` **before** calling Gemini, preventing LLM exploitation.

4. **Phase 4: Adaptive Dual-Path Evaluation**
   - **Fast Path (`difficulty < 3`)**: Pure Python deterministic grading node (0ms latency, $0 cost).
   - **AI Path (`difficulty ≥ 3`)**: Routes to `llm_review_node` using Gemini (`gemini-2.0-flash`) for essay evaluation on a 100-point rubric scale, followed by `tutor_verification_node` (**Human-in-the-Loop `RequestInput`** verification).

5. **Phase 5: AI Tutor Chat Drawer Endpoint (`POST /api/tutor/chat`)**
   - Handles student questions sent via the right-side chat widget.
   - Executes `make_request(prompt, model='gemini-2.0-flash')` with a 10-second timeout.
   - Automatically formats chemical and math formulas into clean HTML subscript tags (`H<sub>2</sub>O`, `CO<sub>2</sub>`).

6. **Phase 6: Quota Resilience & Smart Fallback Engine**
   - If Google AI Studio free tier rate limit (`429 RESOURCE_EXHAUSTED`) is hit, `backend/ai_service.py` returns instant, structured educational study notes for topics like Photosynthesis, Carbon Crystals, JavaScript Promises, Recursion, Arrays, and Essays.

---

## 📡 3. Complete REST API Reference Table

| API Endpoint | HTTP Method | Request Body / Parameters | Response Output Summary |
| :--- | :--- | :--- | :--- |
| `/` | `GET` | None | Renders Login Portal (`index.html`) |
| `/subjects` | `GET` | None | Renders Subject Dashboard (`subjects.html`) |
| `/quiz` | `GET` | None | Renders Quiz Interface (`quiz.html`) |
| `/result` | `GET` | None | Renders Score Review Page (`result.html`) |
| `/profile` | `GET` | None | Renders Student Analytics Page (`profile.html`) |
| `/api/login` | `POST` | `{ studentName, rollNumber, email, year, batch }` | `{ status: 'success', user: {...} }` |
| `/api/questions/<subject>` | `GET` | Subject path parameter | `{ status: 'success', questions: [...] }` |
| `/api/quiz/create` | `POST` | `{ subject, description, questions: [...] }` | `{ status: 'success', message: '...' }` |
| `/api/submit` | `POST` | `{ studentName, rollNumber, subject, score, total }` | `{ status: 'success', result_id: 12 }` |
| `/api/results/<rollNumber>` | `GET` | Roll number path parameter | `{ status: 'success', history: [...] }` |
| `/api/user/<rollNumber>` | `GET` | Roll number path parameter | `{ status: 'success', user: {...}, metrics: {...} }` |
| `/api/tutor/chat` | `POST` | `{ message, subject, student_name }` | `{ status: 'success', response: '...' }` |
