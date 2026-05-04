const API = "https://omnisverum.onrender.com";
let currentUser = null;
let currentServer = null;

// --- NAVIGATION ---
function showLanding() {
    hideAll();
    document.getElementById("landing").classList.remove("hidden");
    document.getElementById("frontpage").classList.add("hidden");
}

function showRegister() {
    hideAll();
    document.getElementById("register").classList.remove("hidden");
}

function showLogin() {
    hideAll();
    document.getElementById("login").classList.remove("hidden");
}

function showDashboard() {
    hideAll();
    document.getElementById("dashboard").classList.remove("hidden");
    document.getElementById("user-info").textContent = `${currentUser.username} | Rep: ${currentUser.reputation} | ${currentUser.tier}`;
}

function hideAll() {
    ["landing", "register", "login", "dashboard"].forEach(id => {
        document.getElementById(id).classList.add("hidden");
    });
}

function logout() {
    currentUser = null;
    currentServer = null;
    showLanding();
    localStorage.removeItem('omnisverum_user');
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

    const res = await fetch(`${API}/register?username=${username}&password=${password}&age_confirmed=${ageConfirmed}&tos_agreed=${tosAgreed}`, {
        method: "POST"
    });
    const data = await res.json();
    if (data.token) {
        alert("Account created! Please login.");
        showLogin();
    } else {
        regError.textContent = "⚠ " + (data.detail || "Registration failed");
        regError.classList.remove("hidden");
    }
}

async function login() {
    const username = document.getElementById("login-username").value;
    const password = document.getElementById("login-password").value;

    const res = await fetch(`${API}/login?username=${username}&password=${password}`, {
        method: "POST"
    });
    const data = await res.json();
    if (data.token) {
        const payload = JSON.parse(atob(data.token.split(".")[1]));
        currentUser = {
            id: payload.sub,
            username: username,
            token: data.token,
            reputation: data.reputation,
            tier: getTier(data.reputation)
        };
        showDashboard();
        showServers();
        loginSuccess();
    } else {
        alert(data.detail || "Login failed");
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
    const res = await fetch(`${API}/servers`);
    const servers = await res.json();
    let html = `<h2 style="letter-spacing:3px;margin-bottom:20px;">PUBLIC SERVERS</h2>`;
    if (servers.length === 0) {
        html += `<p style="color:#555">No public servers yet.</p>`;
    }
    servers.forEach(s => {
        html += `
        <div class="server-card" onclick="enterServer('${s.id}', '${s.name}')">
            <strong>${s.name}</strong>
            <p style="color:#555;font-size:13px;margin-top:6px;">${s.description}</p>
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

    const res = await fetch(`${API}/servers/create?name=${name}&description=${desc}&is_public=${isPublic}&invite_only=${inviteOnly}&owner_id=${currentUser.id}`, {
        method: "POST"
    });
    const data = await res.json();
    if (data.server_id) {
        alert("Server created!");
        showServers();
    } else {
        alert(data.detail || "Failed to create server");
    }
}

async function enterServer(serverId, serverName) {
    currentServer = { id: serverId, name: serverName };
    await fetch(`${API}/servers/join?server_id=${serverId}&user_id=${currentUser.id}`, { method: "POST" });
    showServerPage();
}

function showServerPage() {
    document.getElementById("main-content").innerHTML = `
        <h2 style="letter-spacing:3px;margin-bottom:20px;">${currentServer.name}</h2>
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
    let url = `${API}/servers/invite/create?server_id=${currentServer.id}&user_id=${currentUser.id}`;
    if (hours) url += `&expires_hours=${hours}`;
    const res = await fetch(url, { method: "POST" });
    const data = await res.json();
    if (data.invite_link) {
        prompt(`Copy your invite link (expires: ${data.expires}):`, data.invite_link);
    } else {
        alert(data.detail || "Failed to generate invite");
    }
}

// --- UPLOADS ---
async function showUploads() {
    const res = await fetch(`${API}/uploads/${currentServer.id}`);
    const uploads = await res.json();
    let html = `<h3 style="letter-spacing:2px;margin-bottom:16px;">UPLOADS</h3>`;
    if (uploads.length === 0) {
        html += `<p style="color:#555">No uploads yet.</p>`;
    }
    uploads.forEach(u => {
        html += `
        <div class="upload-card">
            <div class="author">${u.display_name} • ${u.timestamp}</div>
            <div>${u.content}</div>
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

    const res = await fetch(`${API}/upload?server_id=${currentServer.id}&user_id=${currentUser.id}&content=${encodeURIComponent(content)}&is_anonymous=${isAnon}`, {
        method: "POST"
    });
    const data = await res.json();
    if (data.upload_id) {
        alert("Uploaded successfully!");
        showUploads();
    } else {
        alert(data.detail || "Upload failed");
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

    const res = await fetch(`${API}/ask?server_id=${currentServer.id}&question=${encodeURIComponent(question)}&want_other_sources=${wantSources}`, {
        method: "POST"
    });
    const data = await res.json();
    document.getElementById("answer-box").innerHTML = `<div class="answer-box">${data.answer}</div>`;
}

// --- REPORT ---
async function reportUpload(uploadId) {
    const reason = prompt("Why are you reporting this?");
    if (!reason) return;
    const res = await fetch(`${API}/report?reported_by=${currentUser.id}&upload_id=${uploadId}&reason=${encodeURIComponent(reason)}`, {
        method: "POST"
    });
    const data = await res.json();
    alert(data.message || data.detail);
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
    const res = await fetch(`${API}/wiki?query=${encodeURIComponent(query)}`);
    const data = await res.json();
    document.getElementById("wiki-result").innerHTML = `
        <div class="wiki-result">
            <h3>${data.title}</h3>
            <p>${data.summary}</p>
        </div>
    `;
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
    document.getElementById("reg-username").addEventListener("keydown", function(e) {
        if (e.key === "Enter") document.getElementById("reg-password").focus();
    });
    document.getElementById("reg-password").addEventListener("keydown", function(e) {
        if (e.key === "Enter") register();
    });
    document.getElementById("login-username").addEventListener("keydown", function(e) {
        if (e.key === "Enter") document.getElementById("login-password").focus();
    });
    document.getElementById("login-password").addEventListener("keydown", function(e) {
        if (e.key === "Enter") login();
    });

    showLanding();
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
    const question = input.value.toLowerCase().trim();
    if (!question) return;

    const messagesDiv = document.getElementById("chatbot-messages");
    
    messagesDiv.innerHTML += `<div class="chatbot-message user">${question}</div>`;
    
    let answer = omnisInfo["default"];
    for (let key in omnisInfo) {
        if (question.includes(key)) {
            answer = omnisInfo[key];
            break;
        }
    }
    
    messagesDiv.innerHTML += `<div class="chatbot-message bot">${answer}</div>`;
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    input.value = "";
}

// --- AUTO LOGIN ---
window.addEventListener('load', function() {
    const saved = localStorage.getItem('omnisverum_user');
    if (saved) {
        currentUser = JSON.parse(saved);
        showDashboard();
        showServers();
    }
});

// Save user on login
function loginSuccess() {
    localStorage.setItem('omnisverum_user', JSON.stringify(currentUser));
}


