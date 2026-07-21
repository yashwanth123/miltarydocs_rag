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
const fileInput = document.getElementById("fileInput");
const uploadZone = document.getElementById("uploadZone");
const fileList = document.getElementById("fileList");
const uploadStatus = document.getElementById("uploadStatus");
const branchFilter = document.getElementById("branchFilter");

async function fetchWithRetry(url, options = {}, retries = 5, timeoutMs = 90000) {
  let lastError;
  for (let attempt = 0; attempt < retries; attempt += 1) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
      });
      clearTimeout(timer);
      return response;
    } catch (error) {
      clearTimeout(timer);
      lastError = error;
      if (attempt < retries - 1) {
        await new Promise((resolve) => setTimeout(resolve, 1500 * (attempt + 1)));
      }
    }
  }
  throw lastError;
}

function autoResize(textarea) {
  textarea.style.height = "auto";
  textarea.style.height = `${Math.min(textarea.scrollHeight, 120)}px`;
}

function escapeHtml(value) {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function renderAnswer(text) {
  const blocks = text.split("\n\n");
  return blocks
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
}

function createMessage(role, text, sources = []) {
  const message = document.createElement("article");
  message.className = `message ${role}`;

  const avatar = document.createElement("div");
  avatar.className = `avatar ${role === "user" ? "user-avatar" : "bot-avatar"}`;
  avatar.textContent = role === "user" ? "YOU" : "";
  if (role === "bot") {
    avatar.innerHTML = '<svg viewBox="0 0 24 24"><path d="M12 3c-4 0-7 2.5-7 6v2c0 3.5 3 6 7 6s7-2.5 7-6V9c0-3.5-3-6-7-6z" fill="currentColor"/></svg>';
  }

  const bubble = document.createElement("div");
  bubble.className = `bubble ${role === "user" ? "user-bubble" : "bot-bubble"}`;

  const label = document.createElement("div");
  label.className = "bubble-label";
  label.textContent = role === "user" ? "You" : "Assistant";

  const body = document.createElement("div");
  body.className = "bubble-body";
  body.innerHTML = role === "user" ? `<p>${escapeHtml(text)}</p>` : renderAnswer(text);

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
        <strong>${escapeHtml(source.title || source.source)}${source.page ? ` · page ${source.page}` : ""}${source.branch ? ` · ${escapeHtml(source.branch)}` : ""}</strong>
        ${source.source_url ? `<a class="source-link" href="${escapeHtml(source.source_url)}" target="_blank" rel="noopener">Official reference</a>` : ""}
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
  message.querySelector(".bubble-body").innerHTML =
    '<div class="typing"><span></span><span></span><span></span></div>';
  return message;
}

async function sendQuery(query) {
  createMessage("user", query);
  sendButton.disabled = true;
  const loadingNode = createTypingMessage();

  try {
    const response = await fetchWithRetry("/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query,
        mask_sensitive: maskToggle.checked,
        branch: branchFilter.value,
      }),
    }, 5, 120000);
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
    const hint =
      error.name === "AbortError"
        ? "Request timed out — the server may still be loading models. Wait for Status: Online, then try again."
        : "Connection failed — stop any old server (Ctrl+C), then run: bash scripts/run_server.sh";
    createMessage("bot", hint);
  } finally {
    sendButton.disabled = false;
    queryInput.focus();
  }
}

function renderFileList(files) {
  fileList.innerHTML = "";
  if (!files || files.length === 0) {
    fileList.innerHTML = "<li>No files uploaded yet</li>";
    return;
  }
  files.forEach((name) => {
    const item = document.createElement("li");
    item.textContent = name;
    fileList.appendChild(item);
  });
}

async function uploadFiles(fileListInput) {
  if (!fileListInput || fileListInput.length === 0) return;

  const formData = new FormData();
  Array.from(fileListInput).forEach((file) => formData.append("files", file));

  uploadStatus.classList.remove("error");
  uploadStatus.textContent = "Uploading and indexing...";

  try {
    const response = await fetchWithRetry("/upload", { method: "POST", body: formData });
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Upload failed");
    }

    uploadStatus.textContent = data.message || "Upload complete.";
    renderFileList(data.files);
    await refreshHealth();
    createMessage(
      "bot",
      `Upload complete — ${data.indexed_chunks} military document passages are now indexed. Ask about doctrine, standards, or chain of command.`
    );
  } catch (error) {
    uploadStatus.classList.add("error");
    uploadStatus.textContent = error.message;
  } finally {
    fileInput.value = "";
  }
}

function setBackendStatus(state, data = {}) {
  if (state === "online") {
    statusLabel.textContent = "Online";
    chunkCount.textContent = `${data.indexed_chunks} chunks`;
    statusPill.classList.add("online");
    statusPill.textContent = "Backend connected · Local RAG active";
    renderFileList(data.files);
    return;
  }

  if (state === "starting") {
    statusLabel.textContent = "Starting";
    chunkCount.textContent = "—";
    statusPill.classList.remove("online");
    statusPill.textContent = "Loading models — first start can take 1–2 min";
    return;
  }

  statusLabel.textContent = "Offline";
  chunkCount.textContent = "—";
  statusPill.classList.remove("online");
  statusPill.textContent = "Run: bash scripts/run_server.sh (not run_dev.sh)";
}

async function refreshHealth() {
  try {
    const response = await fetchWithRetry("/health", {}, 3, 15000);
    const data = await response.json();

    if (data.ready) {
      setBackendStatus("online", data);
      return true;
    }

    setBackendStatus("starting");
    return false;
  } catch (_error) {
    setBackendStatus("offline");
    return false;
  }
}

async function waitForBackend(maxAttempts = 40) {
  for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
    const ready = await refreshHealth();
    if (ready) return;
    await new Promise((resolve) => setTimeout(resolve, 3000));
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
  queryInput.value = card.dataset.query || card.textContent.trim();
  autoResize(queryInput);
  chatForm.requestSubmit();
});

clearChatButton.addEventListener("click", () => {
  messagesEl.innerHTML = "";
  createMessage(
    "bot",
    "Fresh start. Ask about joining, MEPS, ASVAB, benefits, ranks, or pick a branch filter and quick prompt."
  );
});

fileInput.addEventListener("change", (event) => {
  uploadFiles(event.target.files);
});

uploadZone.addEventListener("dragover", (event) => {
  event.preventDefault();
  uploadZone.classList.add("dragover");
});

uploadZone.addEventListener("dragleave", () => {
  uploadZone.classList.remove("dragover");
});

uploadZone.addEventListener("drop", (event) => {
  event.preventDefault();
  uploadZone.classList.remove("dragover");
  uploadFiles(event.dataTransfer.files);
});

queryInput.addEventListener("input", () => autoResize(queryInput));

queryInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    chatForm.requestSubmit();
  }
});

waitForBackend();
