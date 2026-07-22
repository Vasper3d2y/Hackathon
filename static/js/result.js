const studentName = localStorage.getItem("studentName") || "Student";
const rollNumber = localStorage.getItem("rollNumber") || "";
const subject = localStorage.getItem("subject") || "Quiz";
const score = parseInt(localStorage.getItem("quizScore") || "0", 10);
const total = parseInt(localStorage.getItem("quizTotal") || "5", 10);
const details = JSON.parse(localStorage.getItem("quizDetails") || "[]");

const API_BASE = (window.location.port === "5050") ? "" : "http://127.0.0.1:5050";

const resStudentBadge = document.getElementById("resStudentBadge");
const resultTitle = document.getElementById("resultTitle");
const subjectSubtitle = document.getElementById("subjectSubtitle");
const scoreNum = document.getElementById("scoreNum");
const totalNum = document.getElementById("totalNum");
const percentageText = document.getElementById("percentageText");
const performanceBadge = document.getElementById("performanceBadge");
const reviewContainer = document.getElementById("reviewContainer");

const retakeBtn = document.getElementById("retakeBtn");
const changeSubjectBtn = document.getElementById("changeSubjectBtn");

if (resStudentBadge) resStudentBadge.textContent = studentName;
if (resultTitle) resultTitle.textContent = `Great Job, ${studentName}!`;
if (subjectSubtitle) subjectSubtitle.textContent = `Assessment Summary for ${subject}`;
if (scoreNum) scoreNum.textContent = score;
if (totalNum) totalNum.textContent = total;

const percentage = total > 0 ? Math.round((score / total) * 100) : 0;
if (percentageText) percentageText.textContent = `${percentage}% Score`;

if (performanceBadge) {
    if (percentage >= 80) {
        performanceBadge.textContent = "🏆 Excellent Performance";
        performanceBadge.className = "result-badge badge-excellent";
    } else if (percentage >= 60) {
        performanceBadge.textContent = "👍 Good Effort";
        performanceBadge.className = "result-badge badge-good";
    } else {
        performanceBadge.textContent = "📖 Keep Practicing";
        performanceBadge.className = "result-badge badge-needs-work";
    }
}

// Render Detailed Review
if (reviewContainer && details.length > 0) {
    reviewContainer.innerHTML = "";
    const labels = ['A', 'B', 'C', 'D'];

    details.forEach((item, idx) => {
        const reviewItem = document.createElement("div");
        reviewItem.className = `review-card ${item.isCorrect ? 'correct-card' : 'wrong-card'}`;

        let statusText = item.isCorrect ? "✓ Correct" : "✗ Incorrect";

        let optionsHtml = item.options.map((opt, optIdx) => {
            let itemClass = "review-opt";
            if (optIdx === item.correctIndex) {
                itemClass += " correct-opt";
            } else if (optIdx === item.userChoice && !item.isCorrect) {
                itemClass += " user-wrong-opt";
            }

            return `
                <div class="${itemClass}">
                    <span class="opt-label">${labels[optIdx]}</span>
                    <span>${escapeHtml(opt)}</span>
                    ${optIdx === item.correctIndex ? '<span class="badge-correct">Correct Answer</span>' : ''}
                    ${optIdx === item.userChoice && !item.isCorrect ? '<span class="badge-wrong">Your Choice</span>' : ''}
                </div>
            `;
        }).join("");

        reviewItem.innerHTML = `
            <div class="review-header">
                <h3>Question ${idx + 1}</h3>
                <span class="status-tag ${item.isCorrect ? 'tag-correct' : 'tag-wrong'}">${statusText}</span>
            </div>
            <p class="review-question">${escapeHtml(item.question)}</p>
            <div class="review-options">
                ${optionsHtml}
            </div>
        `;

        reviewContainer.appendChild(reviewItem);
    });
}

// Fetch Previous Quiz Attempts History from Database
async function fetchUserHistory() {
    const historyContainer = document.getElementById("historyContainer");
    if (!historyContainer || !rollNumber) {
        if (historyContainer) historyContainer.innerHTML = "<p style='color: #64748b; text-align: center; padding: 20px;'>No student roll number found.</p>";
        return;
    }

    try {
        let response;
        try {
            response = await fetch(`${API_BASE}/api/results/${encodeURIComponent(rollNumber)}`);
        } catch (netErr) {
            response = await fetch(`http://127.0.0.1:5050/api/results/${encodeURIComponent(rollNumber)}`);
        }
        const data = await response.json();

        if (response.ok && data.status === "success" && data.history && data.history.length > 0) {
            historyContainer.innerHTML = "";
            data.history.forEach((attempt) => {
                const item = document.createElement("div");
                item.className = "review-card";
                item.style.marginBottom = "12px";
                item.style.padding = "16px 20px";
                item.style.display = "flex";
                item.style.justifyContent = "space-between";
                item.style.alignItems = "center";
                item.style.flexWrap = "wrap";
                item.style.gap = "10px";

                const isPassed = attempt.percentage >= 60;
                const statusBadge = isPassed 
                    ? `<span class="tag-correct" style="padding: 4px 12px; border-radius: 20px; font-weight: 600; font-size: 13px;">Passed (${attempt.percentage}%)</span>`
                    : `<span class="tag-wrong" style="padding: 4px 12px; border-radius: 20px; font-weight: 600; font-size: 13px;">Needs Practice (${attempt.percentage}%)</span>`;

                item.innerHTML = `
                    <div>
                        <h4 style="margin: 0 0 4px 0; font-size: 16px; color: var(--text-dark, #0f172a);">${escapeHtml(attempt.subject)}</h4>
                        <span style="font-size: 13px; color: #64748b;">Roll: <strong>${escapeHtml(attempt.roll_number)}</strong> • Date: ${attempt.submitted_at ? attempt.submitted_at : 'Recent'}</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 16px;">
                        <span style="font-size: 16px; font-weight: 700;">${attempt.score} / ${attempt.total}</span>
                        ${statusBadge}
                    </div>
                `;
                historyContainer.appendChild(item);
            });
        } else {
            historyContainer.innerHTML = "<p style='color: #64748b; text-align: center; padding: 20px;'>No previous quiz history recorded in database for Roll #" + escapeHtml(rollNumber) + " yet.</p>";
        }
    } catch (e) {
        console.error("Error fetching history:", e);
        if (historyContainer) {
            historyContainer.innerHTML = "<p style='color: #ef4444; text-align: center; padding: 20px;'>Could not load quiz history from database server.</p>";
        }
    }
}

function escapeHtml(str) {
    return str
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

if (retakeBtn) {
    retakeBtn.addEventListener("click", () => {
        if (window.location.pathname.endsWith(".html") || window.location.protocol === "file:") {
            window.location.href = "quiz.html";
        } else {
            window.location.href = "/quiz";
        }
    });
}

if (changeSubjectBtn) {
    changeSubjectBtn.addEventListener("click", () => {
        if (window.location.pathname.endsWith(".html") || window.location.protocol === "file:") {
            window.location.href = "subjects.html";
        } else {
            window.location.href = "/subjects";
        }
    });
}

document.addEventListener("DOMContentLoaded", fetchUserHistory);

// Global Logout helper
window.logoutUser = function() {
    localStorage.clear();
    if (window.location.pathname.endsWith(".html") || window.location.protocol === "file:") {
        window.location.href = "index.html";
    } else {
        window.location.href = "/";
    }
};
