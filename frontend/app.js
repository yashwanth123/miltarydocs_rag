const messagesEl = document.getElementById("messages");
const chatForm = document.getElementById("chatForm");
const queryInput = document.getElementById("queryInput");
const sendButton = document.getElementById("sendButton");
const maskToggle = document.getElementById("maskToggle");
const clearChatButton = document.getElementById("clearChat");
const statusCard = document.getElementById("statusCard");
const statusLabel = document.getElementById("statusLabel");
const statusDetail = document.getElementById("statusDetail");

function createMessage(role, text, sources = []) {
  const template = document.getElementById("messageTemplate");
  const node = template.content.firstElementChild.cloneNode(true);
  node.classList.add(role);

  const bubble = node.querySelector(".bubble");
  bubble.textContent = text;

  if (role === "assistant" && sources.length > 0) {
    const sourcesTemplate = document.getElementById("sourcesTemplate");
    const sourcesNode = sourcesTemplate.content.firstElementChild.cloneNode(true);
    const list = sourcesNode.querySelector("ul");

    sources.forEach((source) => {
      const item = document.createElement("li");
      const meta = document.createElement("span");
      meta.className = "source-meta";
      meta.textContent = `${source.source}${source.page ? ` · page ${source.page}` : ""}`;
      item.appendChild(meta);
      item.appendChild(document.createTextNode(source.content.slice(0, 220)));
      list.appendChild(item);
    });

    bubble.appendChild(sourcesNode);
  }

  messagesEl.appendChild(node);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return node;
}

async function refreshHealth() {
  try {
    const response = await fetch("/health");
    const data = await response.json();
    statusCard.classList.remove("offline");
    statusCard.classList.add("online");
    statusLabel.textContent = "Backend online";
    statusDetail.textContent = `${data.indexed_chunks} indexed chunks ready`;
  } catch (error) {
    statusCard.classList.remove("online");
    statusCard.classList.add("offline");
    statusLabel.textContent = "Backend offline";
    statusDetail.textContent = "Start the API with uvicorn backend.main:app --reload";
  }
}

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const query = queryInput.value.trim();
  if (!query) {
    return;
  }

  createMessage("user", query);
  queryInput.value = "";
  sendButton.disabled = true;

  const loadingNode = createMessage("assistant", "Searching documents...");
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
      createMessage("assistant", data.detail || "Request failed.");
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
});

clearChatButton.addEventListener("click", () => {
  messagesEl.innerHTML = "";
  createMessage(
    "assistant",
    "Conversation cleared. Ask a new question whenever you are ready."
  );
});

queryInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    chatForm.requestSubmit();
  }
});

refreshHealth();
