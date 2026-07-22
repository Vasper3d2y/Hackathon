const API_BASE = (window.location.port === "5050") ? "" : "http://127.0.0.1:5050";

const rollNumber = localStorage.getItem("rollNumber") || "";
const localName = localStorage.getItem("studentName") || "Student";
const localEmail = localStorage.getItem("email") || "Not Provided";
const localYear = localStorage.getItem("year") || "N/A";
const localBatch = localStorage.getItem("batch") || "N/A";

const avatarInitials = document.getElementById("avatarInitials");
const profStudentName = document.getElementById("profStudentName");
const profEmail = document.getElementById("profEmail");
const profRoll = document.getElementById("profRoll");
const profYear = document.getElementById("profYear");
const profBatch = document.getElementById("profBatch");

const statTotalTests = document.getElementById("statTotalTests");
const statAvgScore = document.getElementById("statAvgScore");
const statPassCount = document.getElementById("statPassCount");
const historyContainer = document.getElementById("profileHistoryContainer");

const userIdentifier = (localEmail && localEmail !== "Not Provided") ? localEmail : rollNumber;

// Set initial fallback values from local storage
if (profStudentName) profStudentName.textContent = localName;
if (profEmail && localEmail !== "Not Provided") profEmail.textContent = localEmail;
if (profRoll) profRoll.textContent = rollNumber || "000";
if (profYear) profYear.textContent = localYear;
if (profBatch) profBatch.textContent = localBatch;

if (avatarInitials) {
    const parts = localName.trim().split(" ");
    const initials = parts.length > 1 ? (parts[0][0] + parts[1][0]) : (parts[0][0] || "ST");
    avatarInitials.textContent = initials.toUpperCase();
}

async function loadProfileData() {
    if (!userIdentifier) {
        if (historyContainer) {
            historyContainer.innerHTML = `
                <div style="text-align: center; padding: 40px; background: white; border-radius: 16px; border: 1px solid var(--border);">
                    <p style="color: #64748b; font-weight: 600;">No student details found. Please log in first.</p>
                    <button onclick="window.location.href='index.html'" class="primary-btn" style="width: auto; padding: 10px 24px; margin-top: 16px;">Go to Login Page 🔑</button>
                </div>
            `;
        }
        return;
    }

    try {
        let response;
        try {
            response = await fetch(`${API_BASE}/api/user/${encodeURIComponent(userIdentifier)}`);
        } catch (netErr) {
            // Fallback attempt to http://127.0.0.1:5050 if relative fetch failed
            response = await fetch(`http://127.0.0.1:5050/api/user/${encodeURIComponent(userIdentifier)}`);
        }
        const data = await response.json();

        if (response.ok && data.status === "success") {
            const u = data.user || {};
            const m = data.metrics || {};
            const history = data.history || [];

            // Populate User Information safely preserving student name and email
            const activeName = (u.studentName && u.studentName.trim() && u.studentName !== "Student") 
                ? u.studentName 
                : (localName && localName !== "Student" ? localName : (u.studentName || localName || "Student"));
            
            const activeEmail = (u.email && u.email.trim() && u.email !== "Not Provided")
                ? u.email
                : (localEmail && localEmail !== "Not Provided" ? localEmail : "");

            if (profStudentName) profStudentName.textContent = activeName;
            if (profEmail && activeEmail) profEmail.textContent = activeEmail;
            if (u.rollNumber) profRoll.textContent = u.rollNumber;
            if (u.year) profYear.textContent = u.year; else if (localYear) profYear.textContent = localYear;
            if (u.batch) profBatch.textContent = u.batch; else if (localBatch) profBatch.textContent = localBatch;

            if (avatarInitials && activeName) {
                const parts = activeName.trim().split(" ");
                const initials = parts.length > 1 ? (parts[0][0] + parts[1][0]) : (parts[0][0] || "ST");
                avatarInitials.textContent = initials.toUpperCase();
            }

            // Populate Stats Cards
            if (statTotalTests) statTotalTests.textContent = m.total_tests || 0;
            if (statAvgScore) statAvgScore.textContent = `${m.avg_percentage || 0}%`;
            if (statPassCount) statPassCount.textContent = m.passed_tests || 0;

            // Render Attempt History List Cards
            if (historyContainer) {
                if (history.length === 0) {
                    historyContainer.innerHTML = `
                        <div style="text-align: center; padding: 36px; background: white; border-radius: 16px; border: 1px solid var(--border);">
                            <p style="font-size: 16px; color: #64748b; margin-bottom: 12px;">No quiz attempts recorded yet.</p>
                            <button onclick="window.location.href='subjects.html'" class="primary-btn" style="width: auto; padding: 10px 24px;">Start Your First Quiz ⚡</button>
                        </div>
                    `;
                    return;
                }

                historyContainer.innerHTML = "";
                history.forEach((attempt, index) => {
                    const card = document.createElement("div");
                    card.className = "review-card";
                    card.style.display = "flex";
                    card.style.justifyContent = "space-between";
                    card.style.alignItems = "center";
                    card.style.flexWrap = "wrap";
                    card.style.gap = "14px";
                    card.style.padding = "20px 24px";
                    card.style.borderRadius = "14px";
                    card.style.background = "#ffffff";
                    card.style.border = "1px solid var(--border)";

                    const isPassed = attempt.percentage >= 60;
                    card.className = `review-card ${isPassed ? 'correct-card' : 'wrong-card'}`;

                    const statusTag = isPassed
                        ? `<span class="tag-correct" style="padding: 6px 14px; border-radius: 20px; font-weight: 700; font-size: 13px;">Passed (${attempt.percentage}%)</span>`
                        : `<span class="tag-wrong" style="padding: 6px 14px; border-radius: 20px; font-weight: 700; font-size: 13px;">Needs Improvement (${attempt.percentage}%)</span>`;

                    card.innerHTML = `
                        <div>
                            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
                                <span style="font-size: 12px; font-weight: 800; background: #e2e8f0; color: #334155; padding: 2px 8px; border-radius: 6px;">Test #${history.length - index}</span>
                                <h3 style="margin: 0; font-size: 18px; font-weight: 800; color: var(--text-main);">${escapeHtml(attempt.subject)}</h3>
                            </div>
                            <span style="font-size: 13px; color: #64748b;">Completed on: <strong>${attempt.submitted_at ? attempt.submitted_at : 'Recent'}</strong></span>
                        </div>
                        <div style="display: flex; align-items: center; gap: 20px;">
                            <div style="text-align: right;">
                                <div style="font-size: 20px; font-weight: 900; color: var(--text-main);">${attempt.score} / ${attempt.total}</div>
                                <div style="font-size: 12px; color: #64748b;">Score</div>
                            </div>
                            ${statusTag}
                        </div>
                    `;
                    historyContainer.appendChild(card);
                });
            }

        } else {
            showErrorState("Unable to load profile data from backend database.");
        }

    } catch (err) {
        console.error("Error loading user profile:", err);
        showErrorState("Could not connect to database server.");
    }
}

function showErrorState(msg) {
    if (historyContainer) {
        historyContainer.innerHTML = `
            <div style="text-align: center; padding: 30px; background: white; border-radius: 16px; border: 1px solid var(--border);">
                <p style="color: #ef4444; font-weight: 700; margin-bottom: 10px;">⚠️ ${msg}</p>
                <button onclick="loadProfileData()" class="secondary-btn" style="width: auto; padding: 8px 20px;">Retry Connection 🔄</button>
            </div>
        `;
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

document.addEventListener("DOMContentLoaded", loadProfileData);

// Global Logout helper
window.logoutUser = function() {
    localStorage.clear();
    if (window.location.pathname.endsWith(".html") || window.location.protocol === "file:") {
        window.location.href = "index.html";
    } else {
        window.location.href = "/";
    }
};
