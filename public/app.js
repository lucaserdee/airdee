// Elementen
const form = document.getElementById("chat-form");
const input = document.getElementById("question");
const sendBtn = document.getElementById("send-btn");
const chatLog = document.getElementById("chat-log");
const newChat = document.getElementById("new-chat");
const menuBtn = document.getElementById("menu-btn");
const dropdown = document.getElementById("dropdown");
const settingsBtn = document.getElementById("open-settings");
const settingsModal = document.getElementById("settings-modal");
const closeSettings = document.getElementById("close-settings");
const themeSelect = document.getElementById("theme-select");

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

// ===== Nieuwe chat =====
newChat.addEventListener("click", () => {
  chatLog.innerHTML = "";
  input.value = "";
  sendBtn.disabled = true;
  sendBtn.classList.remove("enabled");
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

// - Markdown linkjes [titel](url)
// - Kale url's
// - Lege regel → nieuwe paragraaf
// - Regels die beginnen met "- " → lijstitems
function renderMessageHtml(text) {
  let t = String(text ?? "");
  // normaliseer CRLF
  t = t.replace(/\r\n/g, "\n");

  // mark down links
  t = t.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, (_, a, url) =>
    `<a href="${url}" target="_blank" rel="noopener noreferrer">${escapeHtml(a)}</a>`
  );

  // autolink kale urls
  t = t.replace(/(^|[\s(])((https?:\/\/[^\s<)]+))/g, '$1<a href="$2" target="_blank" rel="noopener noreferrer">$2</a>');

  // splits op dubbele newline in paragrafen of lijsten
  const blocks = t.split(/\n{2,}/).map(block => {
    // lijst?
    if (/^\s*[-•]\s+/m.test(block)) {
      const items = block
        .split(/\n/)
        .filter(line => /^\s*[-•]\s+/.test(line))
        .map(line => `<li>${escapeHtml(line.replace(/^\s*[-•]\s+/, ""))}</li>`)
        .join("");
      return `<ul>${items}</ul>`;
    }
    // gewone paragraaf: behoud enkelvoudige nieuwe regels als <br>
    const safe = escapeHtml(block).replace(/\n/g, "<br>");
    return `<p>${safe}</p>`;
  });

  // extra: zorg voor visuele scheiding tussen bronnen door lege regels te bewaren
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

// Loader
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
    // LET OP: pas de endpoint aan indien nodig
    const resp = await fetch("http://172.28.128.188:5678/webhook/ai-chatbot", {
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
