const nameInput = document.getElementById("studentName");
const rollInput = document.getElementById("rollNumber");
const emailInput = document.getElementById("studentEmail");
const yearInput = document.getElementById("year");
const batchInput = document.getElementById("batch");
const loginBtn = document.getElementById("loginBtn");
const feedbackEl = document.getElementById("loginFeedback");

const API_BASE = (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1")
    ? (window.location.port === "5050" ? "" : "http://127.0.0.1:5050")
    : "";



// ENTER KEY NAVIGATION
if (nameInput) {
    nameInput.addEventListener("keydown", function(e){
        if(e.key === "Enter") rollInput.focus();
    });
}

if (rollInput) {
    rollInput.addEventListener("keydown", function(e){
        if(e.key === "Enter" && emailInput) emailInput.focus();
        else if(e.key === "Enter") yearInput.focus();
    });
}

if (emailInput) {
    emailInput.addEventListener("keydown", function(e){
        if(e.key === "Enter") yearInput.focus();
    });
}

if (yearInput) {
    yearInput.addEventListener("keydown", function(e){
        if(e.key === "Enter") batchInput.focus();
    });
}

if (batchInput) {
    batchInput.addEventListener("keydown", function(e){
        if(e.key === "Enter") loginBtn.click();
    });
}

function showFeedback(msg, type = "error") {
    if(!feedbackEl) return;
    feedbackEl.textContent = msg;
    feedbackEl.className = `feedback-msg ${type}`;
}

function redirectNextPage() {
    const studentCard = document.querySelector(".student-card");
    const container = document.querySelector("main.container");

    if (studentCard) studentCard.classList.add("login-exit");
    if (container) container.classList.add("login-exit");

    setTimeout(() => {
        if (studentCard) studentCard.style.display = "none";
        if (container) container.style.display = "none";

        if (window.location.pathname.endsWith(".html") || window.location.protocol === "file:") {
            window.location.href = "subjects.html";
        } else {
            window.location.href = "/subjects";
        }
    }, 400);
}

function resetFieldStyles() {
    [nameInput, rollInput, emailInput, yearInput, batchInput].forEach(el => {
        if (el) el.style.borderColor = "";
    });
}

function markFieldInvalid(el, msg) {
    resetFieldStyles();
    if (el) {
        el.style.borderColor = "#ef4444";
        el.focus();
    }
    showFeedback(msg);
}

let currentMode = "login"; // Default mode

const tabLogin = document.getElementById("tabLogin");
const tabRegister = document.getElementById("tabRegister");
const cardTitle = document.getElementById("cardTitle");
const cardSubtitle = document.getElementById("cardSubtitle");
const btnText = document.getElementById("btnText");
const rollGroup = document.getElementById("rollGroup");
const academicRow = document.getElementById("academicRow");

function setMode(mode) {
    currentMode = mode;
    resetFieldStyles();
    if (feedbackEl) feedbackEl.textContent = "";

    if (mode === "login") {
        if (tabLogin) tabLogin.classList.add("active");
        if (tabRegister) tabRegister.classList.remove("active");
        if (cardTitle) cardTitle.textContent = "Log In to Portal";
        if (cardSubtitle) cardSubtitle.textContent = "Enter your Name and Email Address to log in";
        if (btnText) btnText.textContent = "Log In to Portal";
        if (rollGroup) rollGroup.style.display = "none";
        if (academicRow) academicRow.style.display = "none";
    } else {
        if (tabRegister) tabRegister.classList.add("active");
        if (tabLogin) tabLogin.classList.remove("active");
        if (cardTitle) cardTitle.textContent = "Create New Account";
        if (cardSubtitle) cardSubtitle.textContent = "Enter all compulsory details to register as a new student";
        if (btnText) btnText.textContent = "Create Account & Enter";
        if (rollGroup) rollGroup.style.display = "block";
        if (academicRow) academicRow.style.display = "flex";
    }
}

if (tabLogin) tabLogin.addEventListener("click", () => setMode("login"));
if (tabRegister) tabRegister.addEventListener("click", () => setMode("register"));

// Initialize default mode
setMode("login");

// VALIDATION AND DATABASE LOGIN INTEGRATION
if (loginBtn) {
    loginBtn.addEventListener("click", async function(e){
        e.preventDefault();
        resetFieldStyles();
        
        const name = nameInput ? nameInput.value.trim().toUpperCase() : "";
        const roll = rollInput ? rollInput.value.trim().toUpperCase() : "";
        const email = emailInput ? emailInput.value.trim().toLowerCase() : "";
        const year = yearInput ? yearInput.value : "";
        const batch = batchInput ? batchInput.value : "";

        if (currentMode === "login") {
            if (!name) {
                markFieldInvalid(nameInput, "Please enter your Student Name.");
                return;
            }
            if (!email) {
                markFieldInvalid(emailInput, "Please enter your Email Address.");
                return;
            }
            if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
                markFieldInvalid(emailInput, "Please enter a valid email address (e.g. student@example.com).");
                return;
            }

            loginBtn.disabled = true;
            loginBtn.innerHTML = "<span>Logging In...</span>";
            showFeedback("Checking account details...", "success");

            try {
                const payload = { mode: "login", studentName: name, email: email };
                let response;
                try {
                    response = await fetch(`${API_BASE}/api/login`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    });
                } catch (netErr) {
                    response = await fetch(`http://127.0.0.1:5050/api/login`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    });
                }

                const data = await response.json();

                if (response.ok && data.status === 'success') {
                    const u = data.user || {};
                    localStorage.setItem("studentName", u.studentName || name);
                    localStorage.setItem("rollNumber", u.rollNumber || "101");
                    localStorage.setItem("email", u.email || email);
                    if (u.year) localStorage.setItem("year", u.year);
                    if (u.batch) localStorage.setItem("batch", u.batch);

                    showFeedback("Logged In Successfully!", "success");
                    setTimeout(redirectNextPage, 300);
                } else {
                    loginBtn.disabled = false;
                    loginBtn.innerHTML = '<span id="btnText">Log In to Portal</span> →';
                    markFieldInvalid(emailInput, data.message || "Account does not exist. Please check your credentials or click 'Create Account' to register.");
                }
            } catch (err) {
                console.warn("Backend server offline or static hosting, falling back to local session:", err);
                localStorage.setItem("studentName", name);
                localStorage.setItem("rollNumber", "101");
                localStorage.setItem("email", email);
                showFeedback("Logged In Successfully!", "success");
                setTimeout(redirectNextPage, 300);
            }


        } else {
            // Mode is "register": Validate ALL compulsory fields
            if (!name) {
                markFieldInvalid(nameInput, "All fields are required. Please enter your Student Name.");
                return;
            }

            if (!email) {
                markFieldInvalid(emailInput, "All fields are required. Please enter your Email Address.");
                return;
            }

            if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
                markFieldInvalid(emailInput, "Please enter a valid email address (e.g. student@example.com).");
                return;
            }

            if (!roll) {
                markFieldInvalid(rollInput, "All fields are required. Please enter your Roll Number.");
                return;
            }

            if (!/^\d{3}$/.test(roll)) {
                markFieldInvalid(rollInput, "Roll number must be exactly 3 numeric digits (e.g. 101, 007).");
                return;
            }

            if (!year) {
                markFieldInvalid(yearInput, "All fields are required. Please select your Academic Year.");
                return;
            }

            if (!batch) {
                markFieldInvalid(batchInput, "All fields are required. Please select your Batch.");
                return;
            }

            // Save local session state immediately
            localStorage.setItem("studentName", name);
            localStorage.setItem("rollNumber", roll);
            localStorage.setItem("email", email);
            localStorage.setItem("year", year);
            localStorage.setItem("batch", batch);

            loginBtn.disabled = true;
            loginBtn.innerHTML = "<span>Registering Account...</span>";
            showFeedback("Registering account...", "success");

            try {
                const payload = {
                    mode: "register",
                    studentName: name,
                    rollNumber: roll,
                    email: email,
                    year: year,
                    batch: batch
                };
                let response;
                try {
                    response = await fetch(`${API_BASE}/api/login`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    });
                } catch (netErr) {
                    response = await fetch(`http://127.0.0.1:5050/api/login`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    });
                }

                const data = await response.json();

                if (response.ok && data.status === 'success') {
                    showFeedback("Account Registered Successfully!", "success");
                }
            } catch (err) {
                console.error("Backend registration network notice:", err);
            }

            // Immediately transition to subjects page
            setTimeout(redirectNextPage, 200);
        }
    });
}

// Global logout function
window.logoutUser = function() {
    localStorage.removeItem("studentName");
    localStorage.removeItem("rollNumber");
    localStorage.removeItem("email");
    localStorage.removeItem("year");
    localStorage.removeItem("batch");
    localStorage.removeItem("subject");
    localStorage.removeItem("quizScore");
    localStorage.removeItem("quizTotal");
    localStorage.removeItem("quizDetails");

    if (window.location.pathname.endsWith(".html") || window.location.protocol === "file:") {
        window.location.href = "index.html";
    } else {
        window.location.href = "/";
    }
};

// Auto check existing session on login page load
document.addEventListener("DOMContentLoaded", () => {
    const existingEmail = localStorage.getItem("email");
    const existingName = localStorage.getItem("studentName");

    // If already logged in, hide login page immediately and redirect to subjects
    if (existingEmail || (existingName && existingName !== "Student")) {
        const studentCard = document.querySelector(".student-card");
        const container = document.querySelector("main.container");
        if (studentCard) studentCard.style.display = "none";
        if (container) container.style.display = "none";
        
        if (window.location.pathname.endsWith(".html") || window.location.protocol === "file:") {
            window.location.href = "subjects.html";
        } else {
            window.location.href = "/subjects";
        }
    }
});

