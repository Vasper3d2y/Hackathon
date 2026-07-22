import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY

def create_pdf(output_filename="USER_FLOW_AND_WORKFLOW.pdf"):
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom Color Palette
    PRIMARY = colors.HexColor("#1e1b4b")       # Deep Indigo
    SECONDARY = colors.HexColor("#2563eb")     # Electric Blue
    ACCENT = colors.HexColor("#7c3aed")        # Royal Purple
    TEXT_DARK = colors.HexColor("#0f172a")     # Dark Slate
    BG_LIGHT = colors.HexColor("#f8fafc")      # Light Slate Background
    BORDER_COLOR = colors.HexColor("#e2e8f0")  # Soft Border

    # Custom Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=PRIMARY,
        alignment=TA_LEFT,
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=SECONDARY,
        alignment=TA_LEFT,
        spaceAfter=15
    )

    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=PRIMARY,
        spaceBefore=14,
        spaceAfter=8
    )

    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=ACCENT,
        spaceBefore=10,
        spaceAfter=4
    )

    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=TEXT_DARK,
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        'BulletCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=TEXT_DARK,
        leftIndent=15,
        spaceAfter=4
    )

    code_style = ParagraphStyle(
        'CodeBlockCustom',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#1e293b"),
        backColor=colors.HexColor("#f1f5f9"),
        borderColor=colors.HexColor("#cbd5e1"),
        borderWidth=0.5,
        borderPadding=6,
        spaceBefore=4,
        spaceAfter=6
    )

    story = []

    # Title & Header Banner
    story.append(Paragraph("User Flow & Technical Workflow Specification", title_style))
    story.append(Paragraph("<b>Project</b>: Adaptive AI-Tutor & Interactive Assessment Platform | <b>Team</b>: Purple Hue (Ayush, Kunal, Abhishek)", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=SECONDARY, spaceBefore=0, spaceAfter=15))

    # SECTION 1: USER FLOW
    story.append(Paragraph("1. Complete User Flow Architecture", h1_style))
    story.append(Paragraph("The user flow guides students seamlessly from initial onboarding to interactive assessment, performance analytics, and on-demand AI tutoring.", body_style))

    user_flow_steps = [
        ("Step 1: Student Onboarding", "Student opens index page (`/`). Enters Name, 3-digit Roll Number, Email, Year, and Batch. Client validates fields, submits `POST /api/login`, saves attributes to `localStorage`, and logs in."),
        ("Step 2: Subject Dashboard & Creator", "Student arrives at `/subjects`. Chooses preset cards (Web Hosting, C Programming, Python) or opens '+ Add Custom Quiz' modal to author custom subjects and flashcard questions."),
        ("Step 3: Interactive Quiz Engine", "Student takes quiz at `/quiz`. Questions loaded dynamically via `GET /api/questions/<subject>`. Options highlighted in real time with progress bar tracking."),
        ("Step 4: Score Review & Analytics", "On submission (`POST /api/submit`), student views `/result` with performance badges (Excellent, Good, Practice), question breakdowns, and historical DB attempts."),
        ("Step 5: Profile Dashboard", "Student visits `/profile` to view aggregate performance metrics (total tests, pass rate, average score) and complete test history."),
        ("Step 6: AI-Tutor Side Assistant", "At any point, student clicks the compact right-edge arrow tab handle (`◀`). Opens right-side chat drawer with live subject context, quick suggestion chips, and chemical/math formula subscript rendering.")
    ]

    for step_title, step_desc in user_flow_steps:
        story.append(Paragraph(f"• <b>{step_title}</b>", h2_style))
        story.append(Paragraph(step_desc, bullet_style))

    story.append(Spacer(1, 10))

    # User Flow Table Summary
    uf_table_data = [
        [Paragraph("<b>User Action</b>", body_style), Paragraph("<b>Frontend Screen / Trigger</b>", body_style), Paragraph("<b>Backend API / System Action</b>", body_style)],
        [Paragraph("Submit Login Details", body_style), Paragraph("`index.html` -> `app.js`", body_style), Paragraph("`POST /api/login` -> Insert user into SQLite", body_style)],
        [Paragraph("Create Custom Quiz", body_style), Paragraph("`subjects.html` -> `subject.js`", body_style), Paragraph("`POST /api/quiz/create` -> Insert questions into DB", body_style)],
        [Paragraph("Take Practice Quiz", body_style), Paragraph("`quiz.html` -> `quiz.js`", body_style), Paragraph("`GET /api/questions/<subject>` -> Query DB", body_style)],
        [Paragraph("Submit Quiz Answers", body_style), Paragraph("`quiz.html` -> `submitBtn`", body_style), Paragraph("`POST /api/submit` -> Record score attempt", body_style)],
        [Paragraph("Ask AI Tutor Question", body_style), Paragraph("Right Sidebar Drawer (`◀`)", body_style), Paragraph("`POST /api/tutor/chat` -> Gemini API / Fallback", body_style)],
    ]

    t_uf = Table(uf_table_data, colWidths=[130, 160, 230])
    t_uf.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BG_LIGHT),
        ('TEXTCOLOR', (0, 0), (-1, 0), PRIMARY),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_uf)

    story.append(PageBreak())

    # SECTION 2: TECHNICAL WORKFLOW
    story.append(Paragraph("2. Technical System Workflow & ADK 2.0 Architecture", h1_style))
    story.append(Paragraph("The technical workflow integrates Flask REST routes, SQLite database storage, Gemini 2.0 LLM reasoning, and Google ADK 2.0 Graph Workflow nodes.", body_style))

    story.append(Paragraph("ADK 2.0 Graph Workflow Node Execution Topology", h2_style))
    graph_text = """START Event -> parse_submission -> validate_and_sanitize_payload
                                   |-- (Security Gate 1 Fail: XSS/SQLi) --> quarantine_node
                                   |-- (valid & difficulty < 3) ----------> auto_grade_node
                                   +-- (valid & difficulty >= 3) ---------> prompt_guard_node
                                                                               |-- (Security Gate 2 Fail) --> quarantine_node
                                                                               +-- (clean payload) ---------> llm_review_node -> tutor_verification_node (HITL)"""
    story.append(Paragraph(graph_text.replace('\n', '<br/>').replace(' ', '&nbsp;'), code_style))

    tech_workflow_steps = [
        ("Phase 1: Flask Web Server Routing (`backend/app.py`)", "Serves static assets, HTML templates, and REST API endpoints with CORS headers enabled. Auto-initializes SQLite database (`init_db()`) and seeds initial questions if empty."),
        ("Phase 2: Pre-Ingestion Security Boundary (`validate_and_sanitize_payload`)", "Validates schema types, escapes script tags to block XSS, and strips SQL injection patterns (`UNION SELECT`, `; --`). Diverts malicious payloads to `quarantine_node`."),
        ("Phase 3: Pre-LLM Prompt Guard Boundary (`prompt_guard_node`)", "Scans text for prompt injection and jailbreaks (`ignore system instructions`, `DAN mode`). Short-circuits malicious inputs to `quarantine_node` before invoking Gemini."),
        ("Phase 4: Adaptive Dual-Path Evaluation", "• <b>Fast Path (< 3)</b>: Pure Python deterministic auto-grading.<br/>• <b>AI Path (≥ 3)</b>: Gemini 2.0 essay evaluation on 100-point rubric + `RequestInput` Human-in-the-Loop tutor approval."),
        ("Phase 5: AI Tutor Right-Edge Drawer (`POST /api/tutor/chat`)", "Receives student message and active subject context. Executes `make_request(prompt, model='gemini-2.0-flash')` with 10s deadline. Formats output with HTML subscripts (H₂O, CO₂)."),
        ("Phase 6: Quota Resilience & Fallback Engine", "If Google AI Studio free tier rate limit (`429 RESOURCE_EXHAUSTED`) is hit, `backend/ai_service.py` returns instant, structured educational study notes.")
    ]

    for phase_title, phase_desc in tech_workflow_steps:
        story.append(Paragraph(f"• <b>{phase_title}</b>", h2_style))
        story.append(Paragraph(phase_desc, bullet_style))

    story.append(Spacer(1, 10))

    # Technical API Summary Table
    tech_table_data = [
        [Paragraph("<b>API Endpoint</b>", body_style), Paragraph("<b>Method</b>", body_style), Paragraph("<b>Payload / Parameters</b>", body_style), Paragraph("<b>Response Output</b>", body_style)],
        [Paragraph("`/api/login`", body_style), Paragraph("POST", body_style), Paragraph("`{ studentName, rollNumber, email, year, batch }`", body_style), Paragraph("`{ status: 'success', user }`", body_style)],
        [Paragraph("`/api/questions/<subject>`", body_style), Paragraph("GET", body_style), Paragraph("Subject path parameter", body_style), Paragraph("`{ status: 'success', questions }`", body_style)],
        [Paragraph("`/api/quiz/create`", body_style), Paragraph("POST", body_style), Paragraph("`{ subject, description, questions }`", body_style), Paragraph("`{ status: 'success' }`", body_style)],
        [Paragraph("`/api/submit`", body_style), Paragraph("POST", body_style), Paragraph("`{ studentName, rollNumber, subject, score, total }`", body_style), Paragraph("`{ status: 'success', result_id }`", body_style)],
        [Paragraph("`/api/results/<roll>`", body_style), Paragraph("GET", body_style), Paragraph("Roll number parameter", body_style), Paragraph("`{ status: 'success', history }`", body_style)],
        [Paragraph("`/api/user/<roll>`", body_style), Paragraph("GET", body_style), Paragraph("Roll number parameter", body_style), Paragraph("`{ status: 'success', user, metrics }`", body_style)],
        [Paragraph("`/api/tutor/chat`", body_style), Paragraph("POST", body_style), Paragraph("`{ message, subject, student_name }`", body_style), Paragraph("`{ status: 'success', response }`", body_style)],
    ]

    t_tech = Table(tech_table_data, colWidths=[110, 50, 180, 180])
    t_tech.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BG_LIGHT),
        ('TEXTCOLOR', (0, 0), (-1, 0), PRIMARY),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_tech)

    # Footer Note
    story.append(Spacer(1, 15))
    story.append(HRFlowable(width="100%", thickness=1, color=BORDER_COLOR, spaceBefore=10, spaceAfter=8))
    story.append(Paragraph("<i>Specification Document compiled for Team Purple Hue | Hackathon 2026</i>", ParagraphStyle('FooterStyle', parent=styles['Normal'], fontName='Helvetica-Oblique', fontSize=8, textColor=colors.HexColor("#64748b"), alignment=TA_CENTER)))

    doc.build(story)
    print(f"Successfully generated PDF: {output_filename}")

if __name__ == "__main__":
    create_pdf()
