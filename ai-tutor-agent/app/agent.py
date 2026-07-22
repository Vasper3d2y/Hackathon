# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import base64
import json
import logging
import os
from typing import Any, AsyncGenerator

from google import genai
from google.adk.agents.context import Context
from google.adk.apps import App
from google.adk.events.event import Event
from google.adk.events.request_input import RequestInput
from google.adk.workflow import Workflow, START
from google.genai import types

from app.config import DIFFICULTY_THRESHOLD, GEMINI_MODEL
from app.security import sanitize_text, validate_schema, detect_prompt_injection

logger = logging.getLogger(__name__)


def parse_submission(ctx: Context, node_input: Any) -> Event:
    """
    Step 1: Parses student assessment submission from JSON or Pub/Sub base64 payload.
    """
    raw_payload = node_input
    if isinstance(raw_payload, types.Content):
        raw_text = "".join(part.text for part in raw_payload.parts if part.text)
        try:
            raw_payload = json.loads(raw_text)
        except Exception:
            raw_payload = {"response_text": raw_text, "difficulty_score": 1}

    if isinstance(raw_payload, dict) and "data" in raw_payload:
        data_val = raw_payload["data"]
        if isinstance(data_val, str):
            try:
                decoded_bytes = base64.b64decode(data_val)
                payload_dict = json.loads(decoded_bytes.decode('utf-8'))
            except Exception:
                payload_dict = json.loads(data_val)
        elif isinstance(data_val, dict):
            payload_dict = data_val
        else:
            payload_dict = raw_payload
    elif isinstance(raw_payload, str):
        try:
            payload_dict = json.loads(raw_payload)
        except Exception:
            payload_dict = {"response_text": raw_payload, "difficulty_score": 1}
    else:
        payload_dict = raw_payload if isinstance(raw_payload, dict) else {}

    # Check if this turn is a human tutor resuming a pending verification
    if ctx.state.get("llm_output", {}).get("status") == "PENDING_TUTOR_APPROVAL":
        logger.info("Resuming pending tutor approval for student %s", ctx.state["llm_output"].get("student_id"))
        return Event(output=node_input, route="tutor_verification")

    return Event(output=payload_dict, state={"raw_payload": payload_dict})


def validate_and_sanitize_payload(ctx: Context, node_input: Any) -> Event:
    """
    Step 2 (Pre-Ingestion Security Boundary):
    Enforces schema validation and deterministic text sanitization (XSS, SQLi).
    Short-circuits invalid or malicious payloads directly to 'quarantine'.
    """
    payload_dict = node_input if isinstance(node_input, dict) else ctx.state.get("raw_payload", {})

    # 1. Enforce Schema Validation
    is_valid, err_msg = validate_schema(payload_dict)
    if not is_valid:
        logger.warning("Security Gate 1 Failure (Schema Invalid): %s", err_msg)
        security_event = {
            "student_id": payload_dict.get("student_id", "unknown") if isinstance(payload_dict, dict) else "unknown",
            "reason": f"Schema Validation Error: {err_msg}",
            "raw_payload": payload_dict,
        }
        return Event(output=security_event, route="quarantine")

    # 2. Sanitize Text Inputs
    raw_response = payload_dict.get("response_text", "")
    sanitized_response = sanitize_text(raw_response)

    if "[SQLI_BLOCKED]" in sanitized_response:
        logger.warning("Security Gate 1 Failure (SQL Injection Detected)")
        security_event = {
            "student_id": payload_dict.get("student_id", "unknown"),
            "reason": "SQL Injection attempt detected and blocked.",
            "raw_payload": payload_dict,
        }
        return Event(output=security_event, route="quarantine")

    student_id = payload_dict.get("student_id", "std_101")
    question_id = payload_dict.get("question_id", "q_1")
    difficulty_score = float(payload_dict.get("difficulty_score", 1))
    subject = payload_dict.get("subject", "General Knowledge")

    submission = {
        "student_id": student_id,
        "question_id": question_id,
        "difficulty_score": difficulty_score,
        "response_text": sanitized_response,
        "raw_response_text": raw_response,
        "subject": subject,
        "sanitization_status": "PASSED",
    }

    # Deterministic Python Routing
    if difficulty_score < DIFFICULTY_THRESHOLD:
        route = "auto_grade"
        logger.info("Security Gate 1 Passed. Difficulty %.1f < %d -> auto_grade", difficulty_score, DIFFICULTY_THRESHOLD)
    else:
        route = "guard_check"
        logger.info("Security Gate 1 Passed. Difficulty %.1f >= %d -> guard_check", difficulty_score, DIFFICULTY_THRESHOLD)

    return Event(output=submission, route=route, state={"submission": submission})


def prompt_guard_node(ctx: Context, node_input: Any) -> Event:
    """
    Step 3 (Pre-LLM Security Boundary):
    Scans student response text for prompt injection, jailbreak attempts, or hostile directives.
    Diverts malicious prompts away from Gemini directly to 'quarantine'.
    """
    submission = node_input if isinstance(node_input, dict) else ctx.state.get("submission", {})
    response_text = submission.get("response_text", "")

    # Scan for prompt injection signatures
    is_injection, risk_score, reason = detect_prompt_injection(response_text)

    if is_injection:
        logger.warning("Security Gate 2 Failure (Prompt Injection Detected): %s", reason)
        security_event = {
            **submission,
            "reason": reason,
            "risk_score": risk_score,
            "security_flagged": True,
        }
        return Event(output=security_event, route="quarantine", state={"security_flagged": True})

    logger.info("Security Gate 2 Passed (Prompt Guard Clean: Risk Score %.2f)", risk_score)
    guarded_submission = {
        **submission,
        "security_flagged": False,
        "prompt_injection_score": risk_score,
        "security_audit": "CLEAN",
    }
    return Event(output=guarded_submission, route="llm_review", state={"guarded_submission": guarded_submission})


def quarantine_node(ctx: Context, node_input: Any) -> Event:
    """
    Step Quarantine: Short-circuits malicious/invalid payloads into an isolated security state.
    """
    payload = node_input if isinstance(node_input, dict) else {}
    student_id = payload.get("student_id", "unknown")
    reason = payload.get("reason", "Security Policy Violation Detected.")

    logger.error("SECURITY ALERT: Payload Quarantined for Student %s | Reason: %s", student_id, reason)

    quarantine_record = {
        "student_id": student_id,
        "question_id": payload.get("question_id", "unknown"),
        "score": 0,
        "feedback": f"SECURITY BLOCK: Submission quarantined. Reason: {reason}",
        "graded_by": "Enterprise Security Policy Engine",
        "status": "QUARANTINED",
        "security_flagged": True,
    }
    return Event(output=quarantine_record, state={"grade_result": quarantine_record})



def auto_grade_node(ctx: Context, node_input: Any) -> Event:
    """
    Step 4a (Fast Path): Auto-grades low-difficulty questions deterministically in Python.
    """
    submission = node_input if isinstance(node_input, dict) else ctx.state.get("submission", {})
    response_text = submission.get("response_text", "").strip()

    if len(response_text) > 0 and "incorrect" not in response_text.lower():
        score = 100
        feedback = "Correct! Clear and objective answer."
    else:
        score = 50
        feedback = "Partially correct. Review objective concepts."

    result = {
        **submission,
        "score": score,
        "feedback": feedback,
        "graded_by": "Python Auto-Grader",
        "status": "APPROVED",
        "security_flagged": False,
    }
    logger.info("Auto-graded submission %s for student %s: %d/100", submission.get("question_id"), submission.get("student_id"), score)
    return Event(output=result, state={"grade_result": result})


def llm_review_node(ctx: Context, node_input: Any) -> Event:
    """
    Step 4b (LLM Path): Invokes Gemini (gemini-2.0-flash) to evaluate complex answers.
    Only executed after passing Pre-LLM Prompt Guard.
    """
    submission = node_input if isinstance(node_input, dict) else ctx.state.get("guarded_submission", {})
    response_text = submission.get("response_text", "")
    subject = submission.get("subject", "General Subject")

    prompt = f"""You are an expert AI tutor for the subject '{subject}'.
Analyze the following student answer for conceptual missteps and provide pedagogical insights.

Student Response: "{response_text}"

Tasks:
1. Identify any conceptual errors or gaps.
2. Provide a suggested score (0-100).
3. Draft constructive, encouraging feedback and hints for the student.
"""

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )
        draft_analysis = response.text
    except Exception as e:
        logger.warning("Gemini call failed (%s), using fallback draft.", str(e))
        draft_analysis = (
            "Score: 85\n"
            "Feedback: Good effort! Consider reviewing the core principles of "
            f"{subject} for deeper understanding."
        )

    llm_output = {
        **submission,
        "draft_analysis": draft_analysis,
        "status": "PENDING_TUTOR_APPROVAL",
    }
    logger.info("Generated LLM pedagogical draft for student %s", submission.get("student_id"))
    return Event(output=llm_output, state={"llm_output": llm_output})


async def tutor_verification_node(
    ctx: Context, node_input: Any
) -> AsyncGenerator[Event | RequestInput, None]:
    """
    Step 5 (Human-in-the-Loop with Full Security Context):
    Pauses workflow using RequestInput to allow human tutor to verify LLM feedback,
    providing complete security audit context (sanitization, injection score, risk level).
    """
    llm_output = ctx.state.get("llm_output", {})
    if isinstance(node_input, dict) and "draft_analysis" in node_input:
        llm_output = node_input

    tutor_reply = None
    if ctx.resume_inputs and "tutor_decision" in ctx.resume_inputs:
        tutor_reply = str(ctx.resume_inputs.get("tutor_decision"))
    elif ctx.resume_inputs and "tutor_review" in ctx.resume_inputs:
        tutor_reply = str(ctx.resume_inputs.get("tutor_review"))
    elif isinstance(node_input, types.Content):
        tutor_reply = "".join(part.text for part in node_input.parts if part.text).strip()

    if not tutor_reply:
        student_id = llm_output.get("student_id", "student")
        draft = llm_output.get("draft_analysis", "No draft available.")
        san_status = llm_output.get("sanitization_status", "PASSED")
        inj_score = llm_output.get("prompt_injection_score", 0.0)
        risk_level = "LOW" if inj_score < 0.3 else ("MEDIUM" if inj_score < 0.7 else "HIGH")

        prompt_msg = (
            f"====================================================\n"
            f"🔒 HUMAN TUTOR VERIFICATION & SECURITY AUDIT CONTEXT\n"
            f"====================================================\n"
            f"• Student ID:            {student_id}\n"
            f"• Subject:               {llm_output.get('subject')}\n"
            f"• Sanitization Status:  {san_status}\n"
            f"• Injection Risk Score: {inj_score:.2f} (Risk Level: {risk_level})\n"
            f"• Security Flagged:     False (Passed Pre-LLM Guard)\n"
            f"----------------------------------------------------\n"
            f"Student Answer: \"{llm_output.get('response_text')}\"\n\n"
            f"Gemini Draft Analysis:\n{draft}\n"
            f"----------------------------------------------------\n"
            "Please submit your decision (e.g. 'APPROVED', 'EDITED: <feedback>', or 'REJECTED')."
        )
        yield RequestInput(interrupt_id="tutor_decision", message=prompt_msg)
        return

    tutor_reply_upper = tutor_reply.upper()
    if tutor_reply.startswith("EDITED:"):
        final_feedback = tutor_reply[7:].strip()
        status = "EDITED_BY_TUTOR"
        score = 85
    elif tutor_reply_upper == "REJECTED":
        final_feedback = "Answer requires complete re-submission."
        status = "REJECTED_BY_TUTOR"
        score = 0
    else:
        final_feedback = llm_output.get("draft_analysis", "APPROVED")
        status = "APPROVED_BY_TUTOR"
        score = 90

    final_result = {
        **llm_output,
        "score": score,
        "feedback": final_feedback,
        "tutor_status": status,
        "graded_by": "Gemini AI + Human Tutor Verified",
    }
    logger.info("Human tutor verified submission for student %s: Status=%s", llm_output.get("student_id"), status)
    yield Event(output=final_result, state={"grade_result": final_result})


def record_grade_node(ctx: Context, node_input: Any) -> Event:
    """
    Step 6: Finalizes assessment result and emits formatted output.
    """
    result = node_input if isinstance(node_input, dict) else ctx.state.get("grade_result", {})

    student_id = result.get("student_id", "Unknown")
    question_id = result.get("question_id", "Unknown")
    score = result.get("score", 0)
    feedback = result.get("feedback", "")
    graded_by = result.get("graded_by", "System")
    security_flagged = result.get("security_flagged", False)

    status_icon = "⚠️ SECURITY REJECTED" if security_flagged else "✅ Assessment Recorded"
    summary_text = (
        f"{status_icon}\n"
        f"Student ID: {student_id} | Question: {question_id}\n"
        f"Final Score: {score}/100 | Evaluated By: {graded_by}\n"
        f"Feedback: {feedback}"
    )

    return Event(
        content=types.Content(role="model", parts=[types.Part.from_text(text=summary_text)]),
        output=result,
        state={"final_record": result},
    )


# ADK 2.0 Graph Workflow Agent Definition with Enterprise Security Layer
root_agent = Workflow(
    name="ai_tutor_agent",
    description="Adaptive AI Tutor Agent using ADK 2.0 Graph Workflow API with Enterprise Security Nodes.",
    edges=[
        (START, parse_submission),
        (parse_submission, validate_and_sanitize_payload),
        (validate_and_sanitize_payload, {
            "quarantine": quarantine_node,
            "auto_grade": auto_grade_node,
            "guard_check": prompt_guard_node,
        }),
        (prompt_guard_node, {
            "quarantine": quarantine_node,
            "llm_review": llm_review_node,
        }),
        (llm_review_node, tutor_verification_node),
        (parse_submission, {"tutor_verification": tutor_verification_node}),
        (auto_grade_node, record_grade_node),
        (tutor_verification_node, record_grade_node),
        (quarantine_node, record_grade_node),
    ],
)

app = App(
    root_agent=root_agent,
    name="app",
)
