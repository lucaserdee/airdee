// Elementen
const form = document.getElementById("chat-form");
const input = document.getElementById("question");
const sendBtn = document.getElementById("send-btn");
const chatLog = document.getElementById("chat-log");
const newChat = document.getElementById("new-chat");
const mobileNewChat = document.getElementById("mobile-new-chat");
const menuBtn = document.getElementById("menu-btn");
const dropdown = document.getElementById("dropdown");
const settingsBtn = document.getElementById("open-settings");
const settingsModal = document.getElementById("settings-modal");
const closeSettings = document.getElementById("close-settings");
const themeSelect = document.getElementById("theme-select");
const emgLogo = document.getElementById("emg-logo");

// ====================================
// 1. EMG LOGO → maak klikbaar (desktop + mobiel)
// ====================================
if (emgLogo) {
  emgLogo.addEventListener("click", () => {
    window.location.href = "https://www.emg.nl";   // Pas de URL aan indien nodig
  });
}

// ====================================
// 2. Voeg het ChatGPT-stijl nieuwe-chat icoontje toe
// ====================================
if (newChat) {
  newChat.innerHTML = `
    <span class="newchat-icon">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
        <rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" stroke-width="2"/>
        <path d="M8 16l1-4 7-7 3 3-7 7-4 1z" stroke="currentColor" stroke-width="2" fill="none"/>
      </svg>
    </span>
    <span>Nieuwe chat</span>
  `;
}

// ===== Thema instellen =====
function applyTheme(theme) {
  if (theme === "system") {
    document.body.removeAttribute("data-theme");
  } else {
    document.body.setAttribute("data-theme", theme);
  }
  localStorage.setItem("airdee-theme", theme);
}
const savedTheme = localStorage.getItem("airdee-theme") || "system";
applyTheme(savedTheme);
if (themeSelect) themeSelect.value = savedTheme;

// ===== Menu =====
menuBtn.addEventListener("click", (e) => {
  e.stopPropagation();
  dropdown.classList.toggle("hidden");
});
document.addEventListener("click", () => dropdown.classList.add("hidden"));

settingsBtn?.addEventListener("click", () => {
  settingsModal.classList.remove("hidden");
  dropdown.classList.add("hidden");
});
closeSettings?.addEventListener("click", () => settingsModal.classList.add("hidden"));
settingsModal.addEventListener("click", (e) => {
  if (e.target === settingsModal) settingsModal.classList.add("hidden");
});
themeSelect?.addEventListener("change", (e) => applyTheme(e.target.value));

// ====================================
// 3. Nieuwe chat werkend maken (ook op mobiel)
// ====================================
function resetChat() {
  chatLog.innerHTML = "";
  input.value = "";
  sendBtn.disabled = true;
  sendBtn.classList.remove("enabled");
}

newChat?.addEventListener("click", (e) => {
  e.preventDefault();
  e.stopPropagation();
  resetChat();
});

mobileNewChat?.addEventListener("click", () => {
  resetChat();
});

// ===== Input enable/disable send knop =====
input.addEventListener("input", () => {
  const hasText = input.value.trim().length > 0;
  sendBtn.disabled = !hasText;
  sendBtn.classList.toggle("enabled", hasText);
});

// ===== Tekst naar veilige, nette HTML =====
function escapeHtml(s) {
  return s
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function renderMessageHtml(text) {
  let t = String(text ?? "");
  t = t.replace(/\r\n/g, "\n");

  // Escape eerst alle HTML behalve voor links
  function esc(s) {
    return s.replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;");
  }

  t = esc(t);

  // 1️⃣ Markdown formaat: [titel](url)
  t = t.replace(
    /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g,
    `<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>`
  );

  t = t.replace(
    /([^()\n]+)\s*\((https?:\/\/[^\s)]+)\)/g,
    (m, title, url) => {
      const cleanTitle = title.trim();
      return `<a href="${url}" target="_blank" rel="noopener noreferrer">${cleanTitle}</a>`;
    }
  );

  // Paragrafen + linebreaks
  const blocks = t.split(/\n{2,}/).map(block =>
    `<p>${block.replace(/\n/g, "<br>")}</p>`
  );

  return blocks.join("\n");
}

function addMessage(role, text) {
  const div = document.createElement("div");
  div.className = `message ${role}`;
  if (role === "assistant") {
    div.innerHTML = renderMessageHtml(text);
  } else {
    div.textContent = text;
  }
  chatLog.appendChild(div);
  chatLog.scrollTop = chatLog.scrollHeight;
}

function showLoader() {
  const div = document.createElement("div");
  div.id = "loader";
  div.className = "message assistant";
  div.innerHTML = `<span class="loader"><span class="gear"></span> Aan het nadenken…</span>`;
  chatLog.appendChild(div);
  chatLog.scrollTop = chatLog.scrollHeight;
}
function hideLoader() {
  document.getElementById("loader")?.remove();
}

// ===== Verzenden =====
form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const question = input.value.trim();
  if (!question) return;

  addMessage("user", question);
  input.value = "";
  sendBtn.disabled = true;
  sendBtn.classList.remove("enabled");

  showLoader();

  try {
    const resp = await fetch("https://airdee.erdee.nl/webhook/ai-chatbot", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question })
    });
    const text = await resp.text();
    hideLoader();
    if (!resp.ok) {
      addMessage("assistant", "Er ging iets mis bij het ophalen van het antwoord.");
      return;
    }
    addMessage("assistant", text || "—");
  } catch (err) {
    hideLoader();
    console.error(err);
    addMessage("assistant", "Er trad een netwerkfout op. Probeer het opnieuw.");
  }
});