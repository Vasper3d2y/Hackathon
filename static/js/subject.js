const API_BASE = (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1")
    ? (window.location.port === "5050" ? "" : "http://127.0.0.1:5050")
    : "https://hackathon-in7t.onrender.com";


// Display Student Name
const studentName = localStorage.getItem("studentName") || "Student";
const welcomeEl = document.getElementById("welcome");
const userBadge = document.getElementById("userBadge");

if (welcomeEl) {
    welcomeEl.innerHTML = `Welcome, ${escapeHtml(studentName)} 👋`;
}

if (userBadge && studentName !== "Student") {
    userBadge.textContent = studentName;
}

function selectSubject(subjectName) {
    localStorage.setItem("subject", subjectName);
    
    if (window.location.pathname.endsWith(".html") || window.location.protocol === "file:") {
        window.location.href = "quiz.html";
    } else {
        window.location.href = "/quiz";
    }
}

// Global Logout helper
window.logoutUser = function() {
    localStorage.clear();
    if (window.location.pathname.endsWith(".html") || window.location.protocol === "file:") {
        window.location.href = "index.html";
    } else {
        window.location.href = "/";
    }
};

function escapeHtml(str) {
    if (!str) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// DYNAMIC SUBJECTS LOADING
const subjectGrid = document.getElementById("subjectGrid");

async function loadSubjects() {
    if (!subjectGrid) return;

    try {
        let response;
        try {
            response = await fetch(`${API_BASE}/api/subjects`);
        } catch (err) {
            response = await fetch(`http://127.0.0.1:5050/api/subjects`);
        }

        const data = await response.json();

        if (response.ok && data.status === "success" && data.subjects && data.subjects.length > 0) {
            renderSubjectsGrid(data.subjects);
        } else {
            renderFallbackSubjects();
        }
    } catch (err) {
        console.warn("Could not fetch subjects from backend, using fallback subjects:", err);
        renderFallbackSubjects();
    }
}

function renderSubjectsGrid(subjects) {
    subjectGrid.innerHTML = "";

    subjects.forEach(s => {
        const card = document.createElement("div");
        card.className = "subject-card";
        card.setAttribute("data-subject", s.name);

        const icon = s.icon || "📚";
        const badge = s.badge || "Flashcard Quiz";
        const qCount = s.question_count || 5;

        card.innerHTML = `
            <div class="card-icon">${icon}</div>
            <div class="card-badge">${escapeHtml(badge)}</div>
            <h2>${escapeHtml(s.name.toUpperCase())}</h2>
            <p>${escapeHtml(s.description)}</p>
            <div class="card-footer">
                <span class="q-count">${qCount} Questions</span>
                <button class="select-btn">Start Quiz →</button>
            </div>
        `;

        card.addEventListener("click", () => selectSubject(s.name));
        subjectGrid.appendChild(card);
    });

    // Append "Create Custom Quiz" Action Card inside Grid
    const createCard = document.createElement("div");
    createCard.className = "subject-card create-quiz-card-item";
    createCard.innerHTML = `
        <div class="card-icon" style="font-size: 42px; margin-bottom: 8px;">✨</div>
        <h2 style="font-size: 20px; color: var(--primary);">Create Custom Quiz</h2>
        <p style="font-size: 13px; color: #64748b; margin-bottom: 16px;">Build your own subject & add 5 flashcard questions</p>
        <button class="create-quiz-trigger-btn" style="padding: 8px 18px; font-size: 14px;">+ Add Quiz</button>
    `;
    createCard.addEventListener("click", openCreatorModal);
    subjectGrid.appendChild(createCard);
}

function renderFallbackSubjects() {
    renderSubjectsGrid([
        {
            name: "Web Hosting",
            description: "Shared, VPS, Dedicated Hosting, FTP & Domain Protocols",
            icon: "🌐",
            badge: "Server & Cloud",
            question_count: 5
        },
        {
            name: "C programming",
            description: "Pointers, Bitwise Operators, Memory & Standard Libraries",
            icon: "💻",
            badge: "Core Concepts",
            question_count: 5
        }
    ]);
}

// CREATOR MODAL & 5-QUESTION BUILDER LOGIC
const creatorModal = document.getElementById("creatorModal");
const openCreateBtn = document.getElementById("openCreateBtn");
const closeCreateBtn = document.getElementById("closeCreateBtn");
const createQuizForm = document.getElementById("createQuizForm");
const creatorFeedback = document.getElementById("creatorFeedback");

const newSubjectName = document.getElementById("newSubjectName");
const newSubjectDesc = document.getElementById("newSubjectDesc");
const newSubjectIcon = document.getElementById("newSubjectIcon");

const qTabs = document.querySelectorAll(".q-tab");
const currentQNumEl = document.getElementById("currentQNum");
const qCountBadge = document.getElementById("qCountBadge");

const qTextInput = document.getElementById("qText");
const optAInput = document.getElementById("optA");
const optBInput = document.getElementById("optB");
const optCInput = document.getElementById("optC");
const optDInput = document.getElementById("optD");
const correctOptionSelect = document.getElementById("correctOption");

const prevQBtn = document.getElementById("prevQBtn");
const nextQBtn = document.getElementById("nextQBtn");
const saveQuizBtn = document.getElementById("saveQuizBtn");

// 5 Questions State Array (Strict Limit: 5)
let activeQIndex = 0;
let questionsState = Array.from({ length: 5 }, () => ({
    question_text: "",
    option_a: "",
    option_b: "",
    option_c: "",
    option_d: "",
    correct_index: 0
}));

function openCreatorModal() {
    resetCreatorForm();
    if (creatorModal) creatorModal.style.display = "flex";
}

function closeCreatorModal() {
    if (creatorModal) creatorModal.style.display = "none";
}

if (openCreateBtn) openCreateBtn.addEventListener("click", openCreatorModal);
if (closeCreateBtn) closeCreateBtn.addEventListener("click", closeCreatorModal);

if (creatorModal) {
    creatorModal.addEventListener("click", (e) => {
        if (e.target === creatorModal) closeCreatorModal();
    });
}

function saveCurrentQuestionFormState() {
    if (!questionsState[activeQIndex]) return;

    questionsState[activeQIndex].question_text = qTextInput ? qTextInput.value.trim() : "";
    questionsState[activeQIndex].option_a = optAInput ? optAInput.value.trim() : "";
    questionsState[activeQIndex].option_b = optBInput ? optBInput.value.trim() : "";
    questionsState[activeQIndex].option_c = optCInput ? optCInput.value.trim() : "";
    questionsState[activeQIndex].option_d = optDInput ? optDInput.value.trim() : "";
    questionsState[activeQIndex].correct_index = correctOptionSelect ? parseInt(correctOptionSelect.value, 10) || 0 : 0;

    updateTabsUI();
}

function loadQuestionIntoForm(index) {
    saveCurrentQuestionFormState();

    activeQIndex = index;
    const q = questionsState[activeQIndex];

    if (currentQNumEl) currentQNumEl.textContent = activeQIndex + 1;
    if (qTextInput) qTextInput.value = q.question_text;
    if (optAInput) optAInput.value = q.option_a;
    if (optBInput) optBInput.value = q.option_b;
    if (optCInput) optCInput.value = q.option_c;
    if (optDInput) optDInput.value = q.option_d;
    if (correctOptionSelect) correctOptionSelect.value = q.correct_index;

    if (prevQBtn) prevQBtn.disabled = (activeQIndex === 0);
    if (nextQBtn) nextQBtn.disabled = (activeQIndex === 4);

    updateTabsUI();
}

function updateTabsUI() {
    let filledCount = 0;

    questionsState.forEach((q, idx) => {
        const isFilled = (q.question_text && q.option_a && q.option_b && q.option_c && q.option_d);
        if (isFilled) filledCount++;

        const tabBtn = document.querySelector(`.q-tab[data-qindex="${idx}"]`);
        if (tabBtn) {
            tabBtn.classList.toggle("active", idx === activeQIndex);
            tabBtn.classList.toggle("filled", Boolean(isFilled));
        }
    });

    if (qCountBadge) qCountBadge.textContent = `${filledCount}/5`;
}

// Tab Click Handlers
qTabs.forEach(tab => {
    tab.addEventListener("click", () => {
        const targetIdx = parseInt(tab.getAttribute("data-qindex"), 10);
        loadQuestionIntoForm(targetIdx);
    });
});

if (prevQBtn) {
    prevQBtn.addEventListener("click", () => {
        if (activeQIndex > 0) loadQuestionIntoForm(activeQIndex - 1);
    });
}

if (nextQBtn) {
    nextQBtn.addEventListener("click", () => {
        if (activeQIndex < 4) loadQuestionIntoForm(activeQIndex + 1);
    });
}

function showCreatorFeedback(msg, type = "error") {
    if (!creatorFeedback) return;
    creatorFeedback.style.display = "block";
    creatorFeedback.textContent = msg;
    creatorFeedback.className = `feedback-msg ${type}`;
}

function resetCreatorForm() {
    activeQIndex = 0;
    questionsState = Array.from({ length: 5 }, () => ({
        question_text: "",
        option_a: "",
        option_b: "",
        option_c: "",
        option_d: "",
        correct_index: 0
    }));

    if (newSubjectName) newSubjectName.value = "";
    if (newSubjectDesc) newSubjectDesc.value = "";
    if (newSubjectIcon) newSubjectIcon.value = "⚡";
    if (creatorFeedback) creatorFeedback.style.display = "none";

    loadQuestionIntoForm(0);
}

// FORM SUBMISSION
if (createQuizForm) {
    createQuizForm.addEventListener("submit", async function(e) {
        e.preventDefault();
        saveCurrentQuestionFormState();

        const sName = newSubjectName ? newSubjectName.value.trim() : "";
        const sDesc = newSubjectDesc ? newSubjectDesc.value.trim() : "";
        const sIcon = newSubjectIcon ? newSubjectIcon.value : "⚡";

        if (!sName) {
            showCreatorFeedback("Please enter a Subject Name.");
            if (newSubjectName) newSubjectName.focus();
            return;
        }

        if (!sDesc) {
            showCreatorFeedback("Please enter a Subject Description.");
            if (newSubjectDesc) newSubjectDesc.focus();
            return;
        }

        // Validate all 5 questions
        for (let i = 0; i < 5; i++) {
            const q = questionsState[i];
            if (!q.question_text || !q.option_a || !q.option_b || !q.option_c || !q.option_d) {
                loadQuestionIntoForm(i);
                showCreatorFeedback(`Question ${i + 1} is incomplete! All 5 questions must have question text and Options A-D filled.`);
                return;
            }
        }

        saveQuizBtn.disabled = true;
        saveQuizBtn.innerHTML = "<span>Publishing Quiz...</span>";
        showCreatorFeedback("Saving custom quiz to database...", "success");

        try {
            const payload = {
                name: sName,
                description: sDesc,
                icon: sIcon,
                badge: "Custom Quiz",
                creator: studentName,
                questions: questionsState
            };

            let response;
            try {
                response = await fetch(`${API_BASE}/api/quiz/create`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
            } catch (netErr) {
                response = await fetch(`http://127.0.0.1:5050/api/quiz/create`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
            }

            const data = await response.json();

            if (response.ok && data.status === "success") {
                showCreatorFeedback(`Quiz "${sName}" created successfully!`, "success");

                setTimeout(() => {
                    closeCreatorModal();
                    loadSubjects();
                }, 800);
            } else {
                saveQuizBtn.disabled = false;
                saveQuizBtn.innerHTML = "Save & Publish Quiz 🚀";
                showCreatorFeedback(data.message || "Failed to create quiz.");
            }

        } catch (err) {
            saveQuizBtn.disabled = false;
            saveQuizBtn.innerHTML = "Save & Publish Quiz 🚀";
            console.error("Error creating quiz:", err);
            showCreatorFeedback("Could not connect to database server. Please try again.");
        }
    });
}

// Load subjects on page load
document.addEventListener("DOMContentLoaded", function() {
    loadSubjects();
    document.querySelectorAll(".logout-btn").forEach(btn => {
        btn.addEventListener("click", function(e) {
            e.preventDefault();
            window.logoutUser();
        });
    });
});

window.logoutUser = function() {
    localStorage.clear();
    sessionStorage.clear();
    window.location.href = "index.html";
};