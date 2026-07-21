const messagesEl = document.getElementById("messages");
const chatForm = document.getElementById("chatForm");
const queryInput = document.getElementById("queryInput");
const sendButton = document.getElementById("sendButton");
const maskToggle = document.getElementById("maskToggle");
const clearChatButton = document.getElementById("clearChat");
const statusCard = document.getElementById("statusCard");
const statusLabel = document.getElementById("statusLabel");
const statusDetail = document.getElementById("statusDetail");
const promptChips = document.getElementById("promptChips");

function autoResize(textarea) {
  textarea.style.height = "auto";
  textarea.style.height = `${Math.min(textarea.scrollHeight, 140)}px`;
}

function createMessage(role, text, sources = []) {
  const msg = document.createElement("div");
  msg.className = `msg ${role}`;

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = role === "user" ? "You" : "AI";

  const content = document.createElement("div");
  content.className = "content";

  const textEl = document.createElement("div");
  textEl.className = "text";
  textEl.textContent = text;
  content.appendChild(textEl);

  if (role === "assistant" && sources.length > 0) {
    const wrap = document.createElement("div");
    wrap.className = "sources-wrap";

    const toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "sources-toggle";
    toggle.textContent = `Show ${sources.length} source${sources.length > 1 ? "s" : ""}`;

    const list = document.createElement("div");
    list.className = "sources-list";

    sources.forEach((source) => {
      const item = document.createElement("div");
      item.className = "source-item";

      const title = document.createElement("strong");
      title.textContent = `${source.source}${source.page ? ` · page ${source.page}` : ""}`;

      const body = document.createElement("p");
      body.textContent = source.content.slice(0, 280);

      item.appendChild(title);
      item.appendChild(body);
      list.appendChild(item);
    });

    toggle.addEventListener("click", () => {
      const open = list.classList.toggle("open");
      toggle.textContent = open
        ? `Hide ${sources.length} source${sources.length > 1 ? "s" : ""}`
        : `Show ${sources.length} source${sources.length > 1 ? "s" : ""}`;
    });

    wrap.appendChild(toggle);
    wrap.appendChild(list);
    content.appendChild(wrap);
  }

  msg.appendChild(avatar);
  msg.appendChild(content);
  messagesEl.appendChild(msg);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return msg;
}

async function sendQuery(query) {
  createMessage("user", query);
  sendButton.disabled = true;

  const loadingNode = createMessage("assistant", "Searching your documents...");
  loadingNode.classList.add("loading");

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
      createMessage("assistant", data.detail || "Something went wrong.");
      return;
    }

    createMessage("assistant", data.answer, data.sources || []);
    refreshHealth();
  } catch (error) {
    loadingNode.remove();
    createMessage("assistant", `Network error: ${error.message}`);
  } finally {
    sendButton.disabled = false;
    queryInput.focus();
  }
}

async function refreshHealth() {
  try {
    const response = await fetch("/health");
    const data = await response.json();
    statusCard.classList.add("online");
    statusCard.classList.remove("offline");
    statusLabel.textContent = "Ready";
    statusDetail.textContent = `${data.indexed_chunks} chunks indexed`;
  } catch (_error) {
    statusCard.classList.add("offline");
    statusCard.classList.remove("online");
    statusLabel.textContent = "Offline";
    statusDetail.textContent = "Run uvicorn backend.main:app --reload";
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
  const chip = event.target.closest(".chip");
  if (!chip) return;
  queryInput.value = chip.textContent;
  autoResize(queryInput);
  chatForm.requestSubmit();
});

clearChatButton.addEventListener("click", () => {
  messagesEl.innerHTML = "";
  createMessage(
    "assistant",
    "Chat cleared. Ask a specific question about your documents, or use a suggested prompt."
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
