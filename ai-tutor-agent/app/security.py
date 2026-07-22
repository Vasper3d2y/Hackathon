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

import re
import html

# SQL Injection signature patterns
SQLI_PATTERNS = [
    r"(?i)\bUNION\b\s+\bSELECT\b",
    r"(?i)\bDROP\b\s+\bTABLE\b",
    r"(?i)\bINSERT\b\s+\bINTO\b",
    r"(?i)\bDELETE\b\s+\bFROM\b",
    r"(?i)\bEXEC\b\s*\(",
    r";\s*--",
]

# Prompt Injection & Jailbreak signature patterns
INJECTION_PATTERNS = [
    r"(?i)ignore\s+(all\s+)?(previous|prior)\s+instructions",
    r"(?i)disregard\s+(all\s+)?(previous|prior)\s+(rules|directions|instructions)",
    r"(?i)forget\s+(all\s+)?(previous|prior)\s+instructions",
    r"(?i)you\s+are\s+now\s+a\b",
    r"(?i)system\s+prompt\b",
    r"(?i)override\s+system",
    r"(?i)DAN\s+mode",
    r"(?i)new\s+system\s+directive",
    r"(?i)print\s+(the\s+)?system\s+instructions",
]


def sanitize_text(text: str) -> str:
    """
    Sanitizes raw text strings by escaping HTML/script tags and stripping dangerous SQLi patterns.
    """
    if not text:
        return ""

    # Escape HTML to prevent XSS (<script>, <iframe>, etc.)
    clean = html.escape(str(text))

    # Strip null bytes and control characters
    clean = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", clean)

    # Check for SQL injection signatures
    for pattern in SQLI_PATTERNS:
        if re.search(pattern, clean):
            clean = re.sub(pattern, "[SQLI_BLOCKED]", clean)

    return clean.strip()


def validate_schema(payload: dict) -> tuple[bool, str]:
    """
    Enforces schema validation on extracted submission payload.
    """
    if not isinstance(payload, dict):
        return False, "Payload must be a valid JSON dictionary."

    required_fields = ["student_id", "question_id", "difficulty_score", "response_text"]
    for field in required_fields:
        if field not in payload or payload[field] is None:
            return False, f"Missing required field: '{field}'."

    # Validate data types
    try:
        float(payload["difficulty_score"])
    except (ValueError, TypeError):
        return False, "Field 'difficulty_score' must be a numeric value."

    if not isinstance(payload.get("response_text"), str):
        return False, "Field 'response_text' must be a string."

    return True, "Valid Schema"


def detect_prompt_injection(text: str) -> tuple[bool, float, str]:
    """
    Scans student response text for prompt injection, jailbreak attempts, or hostile directives.
    Returns (is_injection_detected, risk_score, reason).
    """
    if not text:
        return False, 0.0, "Clean Payload"

    raw_text = str(text)
    risk_score = 0.0
    matched_reasons = []

    for pattern in INJECTION_PATTERNS:
        match = re.search(pattern, raw_text)
        if match:
            risk_score += 0.8
            matched_reasons.append(f"Matched pattern: '{match.group(0)}'")

    if risk_score > 0.5:
        reason = "Prompt Injection Attack Detected: " + "; ".join(matched_reasons)
        return True, min(risk_score, 1.0), reason

    return False, 0.0, "Clean Payload"
