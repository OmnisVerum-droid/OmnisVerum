const API = "https://omnisverum.onrender.com";
let currentUser = null;
let currentServer = null;
const THEMES = ["dark", "light", "aurora"];
const THEME_LABELS = {
    dark: "Dark",
    light: "Light",
    aurora: "Aurora"
};

// --- APP FEEDBACK ---
function showAppMessage(text, type = "info") {
    const box = document.getElementById("app-message");
    if (!box) return;
    box.textContent = `Omnisverum: ${text}`;
    box.classList.remove("hidden", "app-message-success", "app-message-error", "app-message-info");
    box.classList.add(`app-message-${type}`);
    clearTimeout(showAppMessage.timer);
    showAppMessage.timer = setTimeout(() => box.classList.add("hidden"), 4200);
}

function escapeHtml(value) {
    return String(value || "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

function escapeHtmlWithBreaks(value) {
    return escapeHtml(value).replace(/\n/g, "<br>");
}

async function readJsonResponse(res) {
    const text = await res.text();
    if (!text) return {};
    try {
        return JSON.parse(text);
    } catch {
        return { detail: text || res.statusText };
    }
}

function formatApiDetail(detail) {
    if (detail == null) return "";
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
        return detail.map(d => (d && typeof d === "object" && d.msg) ? d.msg : String(d)).join(" ");
    }
    return String(detail);
}

async function apiFetch(path, options = {}) {
    const { auth = true, ...rest } = options;
    const headers = { ...(rest.headers || {}) };
    let body = rest.body;
    if (body && typeof body === "object" && !(body instanceof FormData)) {
        body = JSON.stringify(body);
        headers["Content-Type"] = "application/json";
    }
    if (auth !== false && currentUser && currentUser.token) {
        headers["Authorization"] = `Bearer ${currentUser.token}`;
    }
    const res = await fetch(`${API}${path}`, { ...rest, headers, body });
    if (res.status === 401) {
        localStorage.removeItem("omnisverum_user");
        currentUser = null;
        currentServer = null;
        showAppMessage("Session expired. Please login again.", "error");
        if (document.getElementById("landing")) {
            showLanding();
        } else if (document.getElementById("frontpage")) {
            showFrontpage();
        }
        throw new Error("Unauthorized");
    }
    return res;
}

// --- THEMES ---
function applyTheme(themeName) {
    const selected = THEMES.includes(themeName) ? themeName : "dark";
    document.body.classList.remove("theme-dark", "theme-light", "theme-aurora");
    document.body.classList.add(`theme-${selected}`);
    localStorage.setItem("omnisverum_theme", selected);

    const button = document.getElementById("theme-toggle");
    if (button) {
        button.textContent = `Theme: ${THEME_LABELS[selected]}`;
    }
}

function cycleTheme() {
    const current = localStorage.getItem("omnisverum_theme") || "dark";
    const idx = THEMES.indexOf(current);
    const next = THEMES[(idx + 1) % THEMES.length];
    applyTheme(next);
    showAppMessage(`Switched to ${THEME_LABELS[next]} mode.`, "info");
}

// --- NAVIGATION ---
function showFrontpage() {
    hideAll();
    window.scrollTo(0, 0);
    const frontpage = document.getElementById("frontpage");
    if (frontpage) frontpage.classList.remove("hidden");
}

function goToAuthPage() {
    window.location.href = "auth.html";
}

function showLanding() {
    hideAll();
    window.scrollTo(0, 0);
    const landing = document.getElementById("landing");
    if (landing) landing.classList.remove("hidden");
}

function showRegister() {
    hideAll();
    window.scrollTo(0, 0);
    const register = document.getElementById("register");
    if (register) register.classList.remove("hidden");
}

function showLogin() {
    hideAll();
    window.scrollTo(0, 0);
    const login = document.getElementById("login");
    if (login) login.classList.remove("hidden");
}

function showDashboard() {
    hideAll();
    window.scrollTo(0, 0);
    const dashboard = document.getElementById("dashboard");
    if (dashboard) dashboard.classList.remove("hidden");
    const userInfo = document.getElementById("user-info");
    if (userInfo && currentUser) {
        userInfo.textContent = `${currentUser.displayName || currentUser.username} | Rep: ${currentUser.reputation} | ${currentUser.tier}`;
    }
}

function hideAll() {
    ["frontpage", "landing", "register", "login", "dashboard"].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.classList.add("hidden");
    });
}

function logout() {
    currentUser = null;
    currentServer = null;
    localStorage.removeItem('omnisverum_user');
    if (document.getElementById("frontpage")) {
        showFrontpage();
    } else if (document.getElementById("landing")) {
        showLanding();
    }
    showAppMessage("You have logged out.", "info");
}

// --- AUTH ---
async function register() {
    const username = document.getElementById("reg-username").value;
    const password = document.getElementById("reg-password").value;
    const ageConfirmed = document.getElementById("age-confirm").checked;
    const tosAgreed = document.getElementById("tos-agree").checked;

    const ageError = document.getElementById("age-error");
    const tosError = document.getElementById("tos-error");
    const regError = document.getElementById("reg-error");

    ageError.classList.add("hidden");
    tosError.classList.add("hidden");
    regError.classList.add("hidden");

    let hasError = false;

    if (!username || !password) {
        regError.classList.remove("hidden");
        hasError = true;
    }
    if (!ageConfirmed) {
        ageError.classList.remove("hidden");
        hasError = true;
    }
    if (!tosAgreed) {
        tosError.classList.remove("hidden");
        hasError = true;
    }
    if (hasError) return;

    const res = await apiFetch("/register", {
        method: "POST",
        auth: false,
        body: {
            username,
            password,
            age_confirmed: ageConfirmed,
            tos_agreed: tosAgreed,
        },
    });
    const data = await readJsonResponse(res);
    if (res.ok && data.token) {
        showAppMessage("Account created. Please login to continue.", "success");
        showLogin();
    } else {
        regError.textContent = "⚠ " + (formatApiDetail(data.detail) || "Registration failed");
        regError.classList.remove("hidden");
        showAppMessage(data.detail || "Registration failed.", "error");
    }
}

async function login() {
    const username = document.getElementById("login-username").value;
    const password = document.getElementById("login-password").value;

    const res = await apiFetch("/login", {
        method: "POST",
        auth: false,
        body: { username, password },
    });
    const data = await readJsonResponse(res);
    if (res.ok && data.token) {
        const payload = JSON.parse(atob(data.token.split(".")[1]));
        currentUser = {
            id: payload.sub,
            username: username,
            displayName: data.display_name || username,
            bio: data.bio || "",
            isAnonymous: !!data.is_anonymous,
            token: data.token,
            reputation: data.reputation,
            tier: getTier(data.reputation)
        };
        showDashboard();
        showServers();
        loginSuccess();
        showAppMessage(`Welcome back, ${currentUser.displayName}.`, "success");
    } else {
        showAppMessage(formatApiDetail(data.detail) || "Login failed.", "error");
    }
}

function getTier(rep) {
    if (rep >= 1000) return "Authority";
    if (rep >= 501) return "Verified";
    if (rep >= 201) return "Trusted";
    if (rep >= 51) return "Member";
    if (rep >= 0) return "Newcomer";
    if (rep >= -50) return "Flagged";
    return "Locked";
}

// --- SERVERS ---
async function showServers() {
    const res = await apiFetch("/servers", { auth: false });
    const servers = await readJsonResponse(res);
    let html = `<h2 style="letter-spacing:3px;margin-bottom:20px;">PUBLIC SERVERS</h2>`;
    if (servers.length === 0) {
        html += `<p style="color:#555">No public servers yet.</p>`;
    }
    servers.forEach(s => {
        html += `
        <div class="server-card" onclick="enterServer('${s.id}', ${JSON.stringify(s.name)})">
            <strong>${escapeHtml(s.name)}</strong>
            <p style="color:#555;font-size:13px;margin-top:6px;">${escapeHtml(s.description)}</p>
            ${s.invite_only ? '<span style="color:#555;font-size:11px;">🔒 Invite Only</span>' : ''}
        </div>`;
    });
    html += `<button onclick="showCreateServer()" style="margin-top:20px;">+ Create Server</button>`;
    document.getElementById("main-content").innerHTML = html;
}

function showCreateServer() {
    document.getElementById("main-content").innerHTML = `
        <h2 style="letter-spacing:3px;margin-bottom:20px;">CREATE SERVER</h2>
        <input type="text" id="server-name" placeholder="Server name">
        <input type="text" id="server-desc" placeholder="Description">
        <label>Server Type:</label>
        <select id="server-type" style="width:100%;background:#111;color:#fff;border:1px solid #333;padding:10px;margin-bottom:12px;font-family:Georgia,serif;">
            <option value="public">Public — anyone can join</option>
            <option value="invite">Invite Only — link required</option>
            <option value="private">Private — hidden from list</option>
        </select>
        <button onclick="createServer()">Create</button>
        <button onclick="showServers()" style="margin-top:10px;">Cancel</button>
    `;
}

async function createServer() {
    const name = document.getElementById("server-name").value;
    const desc = document.getElementById("server-desc").value;
    const type = document.getElementById("server-type").value;

    const isPublic = type === "public";
    const inviteOnly = type === "invite";

    const res = await apiFetch(
        `/servers/create?name=${encodeURIComponent(name)}&description=${encodeURIComponent(desc)}&is_public=${isPublic}&invite_only=${inviteOnly}`,
        { method: "POST" }
    );
    const data = await readJsonResponse(res);
    if (data.server_id) {
        showAppMessage("Server created successfully.", "success");
        showServers();
    } else {
        showAppMessage(data.detail || "Failed to create server.", "error");
    }
}

async function enterServer(serverId, serverName) {
    currentServer = { id: serverId, name: serverName };
    const res = await apiFetch(`/servers/join?server_id=${encodeURIComponent(serverId)}`, { method: "POST" });
    if (res.ok) {
        showServerPage();
        return;
    }
    const err = await readJsonResponse(res);
    const detail = typeof err.detail === "string" ? err.detail : "";
    if (res.status === 400 && detail.toLowerCase().includes("already")) {
        showServerPage();
        return;
    }
    showAppMessage(detail || "Could not join server.", "error");
}

function showServerPage() {
    document.getElementById("main-content").innerHTML = `
        <h2 style="letter-spacing:3px;margin-bottom:20px;">${escapeHtml(currentServer.name)}</h2>
        <div style="display:flex;gap:10px;margin-bottom:20px;flex-wrap:wrap;">
            <button onclick="showUploads()">Uploads</button>
            <button onclick="showAsk()">Ask AI</button>
            <button onclick="showUploadForm()">+ Upload</button>
            <button onclick="generateInvite()">Invite Link</button>
            <button onclick="showServers()">← Back</button>
        </div>
        <div id="server-content"></div>
    `;
    showUploads();
}

// --- INVITE ---
async function generateInvite() {
    const hours = prompt("Invite expiry in hours? (Leave blank for no expiry)");
    let path = `/servers/invite/create?server_id=${encodeURIComponent(currentServer.id)}`;
    if (hours) path += `&expires_hours=${encodeURIComponent(hours)}`;
    const res = await apiFetch(path, { method: "POST" });
    const data = await readJsonResponse(res);
    if (data.invite_link) {
        prompt(`Copy your invite link (expires: ${data.expires}):`, data.invite_link);
        showAppMessage("Invite link generated.", "success");
    } else {
        showAppMessage(data.detail || "Failed to generate invite.", "error");
    }
}

// --- UPLOADS ---
async function showUploads() {
    const res = await apiFetch(`/uploads/${encodeURIComponent(currentServer.id)}`, { auth: false });
    const uploads = await readJsonResponse(res);
    let html = `<h3 style="letter-spacing:2px;margin-bottom:16px;">UPLOADS</h3>`;
    if (uploads.length === 0) {
        html += `<p style="color:#555">No uploads yet.</p>`;
    }
    uploads.forEach(u => {
        html += `
        <div class="upload-card">
            <div class="author">${escapeHtml(u.display_name)} • ${escapeHtml(u.timestamp)}</div>
            <div>${escapeHtmlWithBreaks(u.content)}</div>
            <button onclick="reportUpload('${u.id}')" style="margin-top:8px;font-size:11px;padding:4px 10px;">Report</button>
        </div>`;
    });
    document.getElementById("server-content").innerHTML = html;
}

function showUploadForm() {
    document.getElementById("server-content").innerHTML = `
        <h3 style="letter-spacing:2px;margin-bottom:16px;">UPLOAD INFO</h3>
        <textarea id="upload-content" placeholder="Enter information..."></textarea>
        <label><input type="checkbox" id="upload-anon"> Post anonymously</label>
        <button onclick="uploadText()" style="margin-top:10px;">Upload</button>
    `;
}

async function uploadText() {
    const content = document.getElementById("upload-content").value;
    const isAnon = document.getElementById("upload-anon").checked;

    const res = await apiFetch(
        `/upload?server_id=${encodeURIComponent(currentServer.id)}&content=${encodeURIComponent(content)}&is_anonymous=${isAnon}`,
        { method: "POST" }
    );
    const data = await readJsonResponse(res);
    if (data.upload_id) {
        showAppMessage("Upload posted successfully.", "success");
        showUploads();
    } else {
        showAppMessage(data.detail || "Upload failed.", "error");
    }
}

// --- ASK AI ---
function showAsk() {
    document.getElementById("server-content").innerHTML = `
        <h3 style="letter-spacing:2px;margin-bottom:16px;">ASK OMNISVERUM</h3>
        <textarea id="question" placeholder="Ask anything..."></textarea>
        <label><input type="checkbox" id="want-sources"> Suggest external sources</label>
        <button onclick="askAI()" style="margin-top:10px;">Ask</button>
        <div id="answer-box"></div>
    `;
}

async function askAI() {
    const question = document.getElementById("question").value;
    const wantSources = document.getElementById("want-sources").checked;

    document.getElementById("answer-box").innerHTML = `<div class="answer-box">Thinking...</div>`;

    const res = await apiFetch(
        `/ask?server_id=${encodeURIComponent(currentServer.id)}&question=${encodeURIComponent(question)}&want_other_sources=${wantSources}`,
        { method: "POST" }
    );
    const data = await readJsonResponse(res);
    const answer = res.ok && data.answer != null ? escapeHtmlWithBreaks(data.answer) : escapeHtml(data.detail || "Could not get an answer.");
    document.getElementById("answer-box").innerHTML = `<div class="answer-box">${answer}</div>`;
}

// --- REPORT ---
async function reportUpload(uploadId) {
    const reason = prompt("Why are you reporting this?");
    if (!reason) return;
    const res = await apiFetch(
        `/report?upload_id=${encodeURIComponent(uploadId)}&reason=${encodeURIComponent(reason)}`,
        { method: "POST" }
    );
    const data = await readJsonResponse(res);
    showAppMessage(data.message || data.detail || "Report submitted.", "info");
}

// --- PROFILE ---
async function showProfile() {
    if (!currentUser) {
        showAppMessage("Please login to manage your profile.", "error");
        return;
    }

    let profile = {
        username: currentUser.username,
        display_name: currentUser.displayName || currentUser.username,
        bio: currentUser.bio || "",
        is_anonymous: !!currentUser.isAnonymous,
        reputation: currentUser.reputation
    };

    try {
        const res = await apiFetch("/profile");
        const data = await readJsonResponse(res);
        if (res.ok) profile = data;
    } catch (_) {
        // Keep local fallback profile when backend is temporarily unavailable.
    }

    document.getElementById("main-content").innerHTML = `
        <h2 style="letter-spacing:3px;margin-bottom:20px;">YOUR PROFILE</h2>
        <div class="profile-card">
            <p><strong>Username:</strong> ${escapeHtml(profile.username)}</p>
            <p><strong>Reputation:</strong> ${escapeHtml(profile.reputation)} (${escapeHtml(getTier(profile.reputation))})</p>
            <label for="profile-display-name">Display Name</label>
            <input type="text" id="profile-display-name" maxlength="40" value="${escapeHtml(profile.display_name)}" placeholder="How your name appears">
            <label for="profile-bio">Bio</label>
            <textarea id="profile-bio" maxlength="280" placeholder="Tell your community who you are...">${escapeHtml(profile.bio)}</textarea>
            <label><input type="checkbox" id="profile-anonymous" ${profile.is_anonymous ? "checked" : ""}> Default to anonymous posting</label>
            <div class="auth-buttons">
                <button onclick="updateProfile()">Save Profile</button>
                <button onclick="showServers()">Back to Servers</button>
            </div>
        </div>
    `;
}

async function updateProfile() {
    if (!currentUser) return;
    const displayName = document.getElementById("profile-display-name").value.trim();
    const bio = document.getElementById("profile-bio").value.trim();
    const isAnonymous = document.getElementById("profile-anonymous").checked;

    if (!displayName) {
        showAppMessage("Display name cannot be empty.", "error");
        return;
    }

    const res = await apiFetch("/profile", {
        method: "PUT",
        body: {
            display_name: displayName,
            bio,
            is_anonymous: isAnonymous,
        },
    });
    const data = await readJsonResponse(res);

    if (!res.ok) {
        showAppMessage(data.detail || "Failed to update profile.", "error");
        return;
    }

    currentUser.displayName = displayName;
    currentUser.bio = bio;
    currentUser.isAnonymous = isAnonymous;
    loginSuccess();
    showDashboard();
    showProfile();
    showAppMessage("Profile updated successfully.", "success");
}

// --- WIKI ---
function showWiki() {
    document.getElementById("main-content").innerHTML = `
        <h2 style="letter-spacing:3px;margin-bottom:20px;">KNOWLEDGE BASE</h2>
        <input type="text" id="wiki-query" placeholder="Search anything...">
        <button onclick="searchWiki()" style="margin-top:10px;">Search</button>
        <div id="wiki-result"></div>
    `;
}

async function searchWiki() {
    const query = document.getElementById("wiki-query").value;
    document.getElementById("wiki-result").innerHTML = `<div class="wiki-result">Searching...</div>`;
    const res = await apiFetch(`/wiki?query=${encodeURIComponent(query)}`, { auth: false });
    const data = await readJsonResponse(res);
    const err = data.error ? escapeHtml(String(data.error)) : "";
    const body = err
        ? `<p class="error">${err}</p>`
        : `<h3>${escapeHtml(data.title)}</h3><p>${escapeHtmlWithBreaks(data.summary || "")}</p>`;
    document.getElementById("wiki-result").innerHTML = `<div class="wiki-result">${body}</div>`;
}

// --- MODALS ---
function openModal(id) {
    document.getElementById(id).classList.remove("hidden");
}

function closeModal(id) {
    document.getElementById(id).classList.add("hidden");
}

// --- PASSWORD TOGGLE ---
function togglePassword(id, el) {
    const input = document.getElementById(id);
    if (input.type === "password") {
        input.type = "text";
        el.textContent = "Hide";
    } else {
        input.type = "password";
        el.textContent = "Show";
    }
}

// --- ENTER KEY ---
document.addEventListener("DOMContentLoaded", function() {
    applyTheme(localStorage.getItem("omnisverum_theme") || "dark");

    const regUsername = document.getElementById("reg-username");
    const regPassword = document.getElementById("reg-password");
    const loginUsername = document.getElementById("login-username");
    const loginPassword = document.getElementById("login-password");

    if (regUsername && regPassword) {
        regUsername.addEventListener("keydown", function(e) {
            if (e.key === "Enter") regPassword.focus();
        });
    }

    if (regPassword) {
        regPassword.addEventListener("keydown", function(e) {
            if (e.key === "Enter") register();
        });
    }

    if (loginUsername && loginPassword) {
        loginUsername.addEventListener("keydown", function(e) {
            if (e.key === "Enter") loginPassword.focus();
        });
    }

    if (loginPassword) {
        loginPassword.addEventListener("keydown", function(e) {
            if (e.key === "Enter") login();
        });
    }

    if (document.getElementById("frontpage")) {
        showFrontpage();
    } else if (document.getElementById("landing")) {
        showLanding();
    }
});

const omnisInfo = {
    "what is omnisverum": "Omnisverum is a crowd-sourced knowledge platform where users create servers, upload information, and an AI answers questions based on that data. Tagline: Upload truth. Ask anything. Trust the crowd.",
    "how does it work": "Users create isolated knowledge servers, upload text information, and others ask questions. The AI uses semantic search (RAG) to understand questions and find relevant uploaded content, then answers intelligently even if wording doesn't exactly match.",
    "what is a server": "A server is an isolated knowledge base. You create one, invite people to join, and together you build a shared knowledge repository. Servers can be public (anyone joins), invite-only (need link), or private (hidden).",
    "reputation system": "Your reputation increases when your uploads are useful. Higher reputation (1000+) gives you more permissions like posting bounties and moderating. Negative reputation locks your account.",
    "can i be anonymous": "Yes! When uploading or posting, you can choose anonymous or named. Your identity is always stored privately for safety, but you control what others see.",
    "what is a bounty": "Post a question with a reputation point reward. The first person to upload verified information wins the bounty points.",
    "how is it different from wikipedia": "Wikipedia stores facts. Omnisverum stores any information communities want to share — opinions, experiences, discussions. It's crowd-sourced with trust weighting.",
    "is it safe": "Yes. The system has reputation weighting (trusted users' info trusted more), moderation, reporting, blacklists, and admin controls. Illegal content is instantly removed.",
    "can i delete my account": "Yes, you can request full data deletion which removes your account and uploads.",
    "what are the tiers": "Newcomer (0-50 rep, read only), Member (51-200, upload+vote), Trusted (201-500), Verified (501-1000, can post bounties), Authority (1000+, can moderate). Negative rep locks you.",
    "how do i report content": "Click the Report button on any upload and explain why. Our moderation system reviews reports.",
    "what happens to my data": "Your username and uploads are stored. Your password is encrypted. Your user ID is never publicly shown. You can request deletion anytime.",
    "default": "I'm here to help explain Omnisverum! Ask about servers, reputation, safety, bounties, or how it works.",
};

function openChatbot() {
    document.getElementById("info-chatbot").classList.remove("hidden");
    document.getElementById("chatbot-question").focus();
}

function closeChatbot() {
    document.getElementById("info-chatbot").classList.add("hidden");
}

function askChatbot() {
    const input = document.getElementById("chatbot-question");
    const raw = input.value.trim();
    const question = raw.toLowerCase();
    if (!question) return;

    const messagesDiv = document.getElementById("chatbot-messages");
    
    messagesDiv.innerHTML += `<div class="chatbot-message user">${escapeHtml(raw)}</div>`;
    
    let answer = omnisInfo["default"];
    for (let key in omnisInfo) {
        if (question.includes(key)) {
            answer = omnisInfo[key];
            break;
        }
    }
    
    messagesDiv.innerHTML += `<div class="chatbot-message bot">${escapeHtml(answer)}</div>`;
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    input.value = "";
}

// --- AUTO LOGIN ---
window.addEventListener('load', function() {
    if (document.getElementById("frontpage")) {
        // Keep index focused on onboarding; do not auto-open auth/dashboard.
        showFrontpage();
        return;
    }

    const saved = localStorage.getItem('omnisverum_user');
    if (saved) {
        currentUser = JSON.parse(saved);
        currentUser.displayName = currentUser.displayName || currentUser.username;
        showDashboard();
        showServers();
    }
});

// Save user on login
function loginSuccess() {
    localStorage.setItem('omnisverum_user', JSON.stringify(currentUser));
}


