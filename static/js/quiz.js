let questions = [];
let currentIndex = 0;
let userAnswers = {};
let currentSubject = localStorage.getItem("subject") || "C programming";
let studentName = localStorage.getItem("studentName") || "Student";
let rollNumber = localStorage.getItem("rollNumber") || "00000";

// Handle dynamic port or static preview URL
const API_BASE = (window.location.port === "5050") ? "" : "http://127.0.0.1:5050";

const subjectBadge = document.getElementById("quizSubjectBadge");
const subjectTag = document.getElementById("subjectNameTag");
const counterEl = document.getElementById("questionCounter");
const progressFill = document.getElementById("progressFill");
const loadingState = document.getElementById("loadingState");
const questionContent = document.getElementById("questionContent");
const questionTextEl = document.getElementById("questionText");
const optionsContainer = document.getElementById("optionsContainer");

const prevBtn = document.getElementById("prevBtn");
const nextBtn = document.getElementById("nextBtn");
const submitBtn = document.getElementById("submitBtn");

if (subjectBadge) subjectBadge.textContent = studentName;
if (subjectTag) subjectTag.textContent = currentSubject;

async function fetchQuestions() {
    try {
        let response;
        try {
            response = await fetch(`${API_BASE}/api/questions/${encodeURIComponent(currentSubject)}`);
        } catch (netErr) {
            response = await fetch(`http://127.0.0.1:5050/api/questions/${encodeURIComponent(currentSubject)}`);
        }
        const data = await response.json();

        if (response.ok && data.status === 'success' && data.questions && data.questions.length > 0) {
            questions = data.questions;
            renderQuestion(0);
        } else {
            showError("No questions found in database for " + currentSubject);
        }
    } catch (err) {
        console.warn("Backend server offline or static hosting, using client fallback question sets:", err);
        const FALLBACK_QUESTION_SETS = {
            "C programming": [
                { id: 1, question_text: "Which keyword is used to declare an integer variable in C?", options: ["int", "float", "string", "var"], correct_option: 0 },
                { id: 2, question_text: "Which symbol is used for dereferencing a pointer in C?", options: ["&", "*", "->", "%"], correct_option: 1 },
                { id: 3, question_text: "What does the printf() function do in C?", options: ["Takes user input", "Prints output to console", "Allocates memory", "Terminates program"], correct_option: 1 },
                { id: 4, question_text: "Which header file is used for standard input/output?", options: ["<conio.h>", "<stdlib.h>", "<stdio.h>", "<string.h>"], correct_option: 2 },
                { id: 5, question_text: "What is the return type of the main() function in C?", options: ["void", "int", "char", "float"], correct_option: 1 }
            ],
            "Web hosting": [
                { id: 1, question_text: "What protocol is used to transfer files to a web host?", options: ["HTTP", "SFTP / FTP", "DNS", "SMTP"], correct_option: 1 },
                { id: 2, question_text: "What does DNS stand for in web hosting?", options: ["Digital Network System", "Domain Name System", "Direct Node Server", "Data Network Storage"], correct_option: 1 },
                { id: 3, question_text: "Which hosting type shares server hardware with multiple sites?", options: ["Dedicated Hosting", "VPS Hosting", "Shared Hosting", "Colocation"], correct_option: 2 },
                { id: 4, question_text: "What is an SSL certificate used for?", options: ["Speeding up website load time", "Encrypting HTTP traffic (HTTPS)", "Managing domain registration", "Storing database records"], correct_option: 1 },
                { id: 5, question_text: "Which port is used by default for HTTP traffic?", options: ["443", "21", "80", "22"], correct_option: 2 }
            ],
            "Python": [
                { id: 1, question_text: "Which data type is immutable in Python?", options: ["List", "Dictionary", "Tuple", "Set"], correct_option: 2 },
                { id: 2, question_text: "How do you define a function in Python?", options: ["def myFunc():", "function myFunc()", "func myFunc()", "define myFunc()"], correct_option: 0 },
                { id: 3, question_text: "What is the output of print(type([])) in Python?", options: ["<class 'tuple'>", "<class 'list'>", "<class 'dict'>", "<class 'array'>"], correct_option: 1 },
                { id: 4, question_text: "Which library is commonly used for data manipulation in Python?", options: ["pandas", "requests", "flask", "pytest"], correct_option: 0 },
                { id: 5, question_text: "What does list comprehension provide in Python?", options: ["A concise way to create lists", "A way to encrypt data", "A database connection tool", "A multi-threading library"], correct_option: 0 }
            ]
        };

        const fallback = FALLBACK_QUESTION_SETS[currentSubject] || FALLBACK_QUESTION_SETS["Python"] || FALLBACK_QUESTION_SETS["C programming"];
        questions = fallback;
        renderQuestion(0);
    }
}


function showError(msg) {
    if (loadingState) {
        loadingState.innerHTML = `
            <div style="text-align: center; padding: 20px;">
                <p style="color: #ef4444; font-weight: 700; font-size: 16px; margin-bottom: 12px;">⚠️ ${msg}</p>
                <button onclick="fetchQuestions()" class="primary-btn" style="width: auto; padding: 8px 20px; margin-top: 10px;">Retry Connection 🔄</button>
            </div>
        `;
    }
}

function renderQuestion(index) {
    if (questions.length === 0) return;

    currentIndex = index;
    const q = questions[currentIndex];

    // Hide loader, show content
    if (loadingState) loadingState.style.display = "none";
    if (questionContent) questionContent.style.display = "block";

    // Update Counter & Progress
    if (counterEl) counterEl.textContent = `Question ${currentIndex + 1} of ${questions.length}`;
    if (progressFill) {
        const percent = ((currentIndex + 1) / questions.length) * 100;
        progressFill.style.width = `${percent}%`;
    }

    // Set Question Text
    if (questionTextEl) questionTextEl.textContent = `${currentIndex + 1}. ${q.question_text}`;

    // Render Options
    if (optionsContainer) {
        optionsContainer.innerHTML = "";
        const labels = ['A', 'B', 'C', 'D'];

        q.options.forEach((opt, optIdx) => {
            const optionBtn = document.createElement("button");
            optionBtn.className = "option-btn";
            if (userAnswers[currentIndex] === optIdx) {
                optionBtn.classList.add("selected");
            }

            optionBtn.innerHTML = `
                <span class="option-prefix">${labels[optIdx]}</span>
                <span class="option-text">${escapeHtml(opt)}</span>
            `;

            optionBtn.addEventListener("click", () => selectOption(optIdx));
            optionsContainer.appendChild(optionBtn);
        });
    }

    // Update Action Buttons
    if (prevBtn) prevBtn.disabled = (currentIndex === 0);

    if (currentIndex === questions.length - 1) {
        if (nextBtn) nextBtn.style.display = "none";
        if (submitBtn) submitBtn.style.display = "inline-flex";
    } else {
        if (nextBtn) nextBtn.style.display = "inline-flex";
        if (submitBtn) submitBtn.style.display = "none";
    }
}

function selectOption(optIdx) {
    userAnswers[currentIndex] = optIdx;
    renderQuestion(currentIndex);
}

function escapeHtml(str) {
    return str
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Button Events
if (prevBtn) {
    prevBtn.addEventListener("click", () => {
        if (currentIndex > 0) renderQuestion(currentIndex - 1);
    });
}

if (nextBtn) {
    nextBtn.addEventListener("click", () => {
        if (currentIndex < questions.length - 1) renderQuestion(currentIndex + 1);
    });
}

if (submitBtn) {
    submitBtn.addEventListener("click", async () => {
        // Calculate Score
        let score = 0;
        const details = [];

        questions.forEach((q, idx) => {
            const userChoice = userAnswers[idx];
            const isCorrect = (userChoice === q.correct_index);
            if (isCorrect) score++;

            details.push({
                question: q.question_text,
                options: q.options,
                userChoice: userChoice !== undefined ? userChoice : -1,
                correctIndex: q.correct_index,
                isCorrect: isCorrect
            });
        });

        // Submit result to database API
        try {
            await fetch(`${API_BASE}/api/submit`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    studentName: studentName,
                    rollNumber: rollNumber,
                    subject: currentSubject,
                    score: score,
                    total: questions.length
                })
            });
        } catch (e) {
            console.error("Error saving result to DB:", e);
        }

        // Save detailed results locally for results page
        localStorage.setItem("quizScore", score);
        localStorage.setItem("quizTotal", questions.length);
        localStorage.setItem("quizDetails", JSON.stringify(details));

        // Navigate to result page
        if (window.location.pathname.endsWith(".html") || window.location.protocol === "file:") {
            window.location.href = "result.html";
        } else {
            window.location.href = "/result";
        }
    });
}

// Initialize on page load
document.addEventListener("DOMContentLoaded", fetchQuestions);

// Global Logout helper
window.logoutUser = function() {
    localStorage.clear();
    if (window.location.pathname.endsWith(".html") || window.location.protocol === "file:") {
        window.location.href = "index.html";
    } else {
        window.location.href = "/";
    }
};
