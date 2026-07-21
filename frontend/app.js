const messagesEl = document.getElementById("messages");
const chatForm = document.getElementById("chatForm");
const queryInput = document.getElementById("queryInput");
const sendButton = document.getElementById("sendButton");
const maskToggle = document.getElementById("maskToggle");
const clearChatButton = document.getElementById("clearChat");
const statusLabel = document.getElementById("statusLabel");
const chunkCount = document.getElementById("chunkCount");
const statusPill = document.getElementById("statusPill");
const promptChips = document.getElementById("promptChips");

const PROMPT_MAP = {
  Doctrine: "Explain the military chain of command",
  Summary: "Summarize the indexed documents",
  Guide: "What can I ask?",
};

function autoResize(textarea) {
  textarea.style.height = "auto";
  textarea.style.height = `${Math.min(textarea.scrollHeight, 120)}px`;
}

function renderAnswer(text) {
  const blocks = text.split("\n\n");
  const html = blocks
    .map((block) => {
      const trimmed = block.trim();
      if (trimmed.startsWith("•")) {
        const items = trimmed
          .split("\n")
          .map((line) => line.replace(/^•\s*/, "").trim())
          .filter(Boolean);
        return `<ul>${items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`;
      }
      return `<p>${escapeHtml(trimmed).replace(/\n/g, "<br>")}</p>`;
    })
    .join("");
  return html;
}

function escapeHtml(value) {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function createMessage(role, text, sources = []) {
  const message = document.createElement("article");
  message.className = `message ${role}`;

  const avatar = document.createElement("div");
  avatar.className = `avatar ${role === "user" ? "user-avatar" : "bot-avatar"}`;
  if (role === "user") {
    avatar.textContent = "YOU";
  } else {
    avatar.innerHTML = '<svg viewBox="0 0 24 24"><path d="M12 3c-4 0-7 2.5-7 6v2c0 3.5 3 6 7 6s7-2.5 7-6V9c0-3.5-3-6-7-6z" fill="currentColor"/></svg>';
  }

  const bubble = document.createElement("div");
  bubble.className = `bubble ${role === "user" ? "user-bubble" : "bot-bubble"}`;

  const label = document.createElement("div");
  label.className = "bubble-label";
  label.textContent = role === "user" ? "You" : "Assistant";

  const body = document.createElement("div");
  body.className = "bubble-body";

  if (role === "user") {
    body.textContent = text;
  } else {
    body.innerHTML = renderAnswer(text);
  }

  bubble.appendChild(label);
  bubble.appendChild(body);

  if (role === "bot" && sources.length > 0) {
    const sourcesWrap = document.createElement("div");
    sourcesWrap.className = "sources";

    const toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "sources-btn";
    toggle.textContent = `View ${sources.length} source${sources.length > 1 ? "s" : ""}`;

    const list = document.createElement("div");
    list.className = "source-list";

    sources.forEach((source) => {
      const card = document.createElement("div");
      card.className = "source-card";
      card.innerHTML = `
        <strong>${escapeHtml(source.source)}${source.page ? ` · page ${source.page}` : ""}</strong>
        <p>${escapeHtml(source.content.slice(0, 260))}</p>
      `;
      list.appendChild(card);
    });

    toggle.addEventListener("click", () => {
      const open = list.classList.toggle("open");
      toggle.textContent = open
        ? `Hide ${sources.length} source${sources.length > 1 ? "s" : ""}`
        : `View ${sources.length} source${sources.length > 1 ? "s" : ""}`;
    });

    sourcesWrap.appendChild(toggle);
    sourcesWrap.appendChild(list);
    bubble.appendChild(sourcesWrap);
  }

  message.appendChild(avatar);
  message.appendChild(bubble);
  messagesEl.appendChild(message);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return message;
}

function createTypingMessage() {
  const message = createMessage("bot", "");
  const body = message.querySelector(".bubble-body");
  body.innerHTML = '<div class="typing"><span></span><span></span><span></span></div>';
  message.dataset.loading = "true";
  return message;
}

async function sendQuery(query) {
  createMessage("user", query);
  sendButton.disabled = true;

  const loadingNode = createTypingMessage();

  try {
    const response = await fetch("/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query,
        mask_sensitive: maskToggle.checked,
      }),
    });

    const data = await response.json();
    loadingNode.remove();

    if (!response.ok) {
      createMessage("bot", data.detail || "Something went wrong while processing your request.");
      return;
    }

    createMessage("bot", data.answer, data.sources || []);
    refreshHealth();
  } catch (error) {
    loadingNode.remove();
    createMessage("bot", `Network error: ${error.message}`);
  } finally {
    sendButton.disabled = false;
    queryInput.focus();
  }
}

async function refreshHealth() {
  try {
    const response = await fetch("/health");
    const data = await response.json();
    statusLabel.textContent = "Online";
    chunkCount.textContent = `${data.indexed_chunks} chunks`;
    statusPill.classList.add("online");
    statusPill.textContent = "Backend connected · Local RAG active";
  } catch (_error) {
    statusLabel.textContent = "Offline";
    chunkCount.textContent = "—";
    statusPill.classList.remove("online");
    statusPill.textContent = "Start server: uvicorn backend.main:app --reload";
  }
}

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const query = queryInput.value.trim();
  if (!query) return;
  queryInput.value = "";
  autoResize(queryInput);
  await sendQuery(query);
});

promptChips.addEventListener("click", (event) => {
  const card = event.target.closest(".prompt-card");
  if (!card) return;
  const tag = card.querySelector(".prompt-tag")?.textContent;
  queryInput.value = PROMPT_MAP[tag] || card.textContent.trim();
  autoResize(queryInput);
  chatForm.requestSubmit();
});

clearChatButton.addEventListener("click", () => {
  messagesEl.innerHTML = "";
  createMessage(
    "bot",
    "Conversation reset.\n\nAsk a specific question about doctrine, summaries, skills, or standards in your indexed files."
  );
});

queryInput.addEventListener("input", () => autoResize(queryInput));

queryInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    chatForm.requestSubmit();
  }
});

refreshHealth();
