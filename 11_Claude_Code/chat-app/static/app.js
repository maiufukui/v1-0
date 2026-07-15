const STORAGE_KEY = "chat-app-conversations";
const ACTIVE_KEY = "chat-app-active-conversation";

const historyEl = document.getElementById("history");
const formEl = document.getElementById("chat-form");
const inputEl = document.getElementById("message-input");
const conversationListEl = document.getElementById("conversation-list");
const newChatButton = document.getElementById("new-chat-button");

function loadConversations() {
    try {
        const raw = localStorage.getItem(STORAGE_KEY);
        return raw ? JSON.parse(raw) : [];
    } catch (err) {
        console.error("Failed to load conversations", err);
        return [];
    }
}

function createConversationObject() {
    return { id: crypto.randomUUID(), title: "New chat", messages: [] };
}

let conversations = loadConversations();
let activeId = localStorage.getItem(ACTIVE_KEY);

if (conversations.length === 0) {
    conversations = [createConversationObject()];
}
if (!activeId || !conversations.some((c) => c.id === activeId)) {
    activeId = conversations[0].id;
}

function saveConversations() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations));
    localStorage.setItem(ACTIVE_KEY, activeId);
}

function getActiveConversation() {
    return conversations.find((c) => c.id === activeId);
}

function appendMessage(role, text) {
    const el = document.createElement("div");
    el.className = `message ${role}`;
    el.textContent = text;
    historyEl.appendChild(el);
    historyEl.scrollTop = historyEl.scrollHeight;
}

function renderHistory() {
    historyEl.innerHTML = "";
    const conversation = getActiveConversation();
    if (!conversation) return;
    conversation.messages.forEach((m) => appendMessage(m.role, m.text));
}

function renderSidebar() {
    conversationListEl.innerHTML = "";
    conversations.forEach((conversation) => {
        const item = document.createElement("div");
        item.className =
            "conversation-item" + (conversation.id === activeId ? " active" : "");
        item.textContent = conversation.title;
        item.addEventListener("click", () => switchConversation(conversation.id));
        conversationListEl.appendChild(item);
    });
}

function switchConversation(id) {
    if (id === activeId) return;
    activeId = id;
    saveConversations();
    renderHistory();
    renderSidebar();
}

function startNewConversation() {
    const conversation = createConversationObject();
    conversations.unshift(conversation);
    activeId = conversation.id;
    saveConversations();
    renderHistory();
    renderSidebar();
    inputEl.focus();
}

function toolStatusLabel(event) {
    const input = event.input || {};
    switch (event.name) {
        case "Read":
            return `Reading ${input.file_path}...`;
        case "Glob":
            return `Searching for files matching "${input.pattern}"...`;
        case "Grep":
            return `Searching code for "${input.pattern}"...`;
        case "mcp__concierge__count_lines":
            return `Counting lines in ${input.file_path}...`;
        case "mcp__concierge__git_log":
            return "Checking recent commits...";
        default:
            return `Using ${event.name}...`;
    }
}

async function streamMessage(message, conversationId, onEvent) {
    const response = await fetch("/api/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, conversation_id: conversationId }),
    });

    if (!response.ok || !response.body) {
        throw new Error(`Request failed with status ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        let boundary;
        while ((boundary = buffer.indexOf("\n\n")) !== -1) {
            const rawEvent = buffer.slice(0, boundary);
            buffer = buffer.slice(boundary + 2);
            const line = rawEvent.split("\n").find((l) => l.startsWith("data: "));
            if (line) {
                onEvent(JSON.parse(line.slice(6)));
            }
        }
    }
}

formEl.addEventListener("submit", async (event) => {
    event.preventDefault();
    const message = inputEl.value.trim();
    if (!message) return;

    inputEl.value = "";
    const conversation = getActiveConversation();
    conversation.messages.push({ role: "user", text: message });
    if (conversation.title === "New chat") {
        conversation.title = message.length > 40 ? `${message.slice(0, 40)}…` : message;
    }
    appendMessage("user", message);
    saveConversations();
    renderSidebar();

    const statusEl = document.createElement("div");
    statusEl.className = "message assistant status";
    statusEl.textContent = "Thinking...";
    historyEl.appendChild(statusEl);
    historyEl.scrollTop = historyEl.scrollHeight;

    try {
        await streamMessage(message, conversation.id, (evt) => {
            if (evt.type === "tool") {
                statusEl.textContent = toolStatusLabel(evt);
                historyEl.scrollTop = historyEl.scrollHeight;
            } else if (evt.type === "result") {
                statusEl.remove();
                conversation.messages.push({ role: "assistant", text: evt.text });
                appendMessage("assistant", evt.text);
                saveConversations();
            }
        });
    } catch (err) {
        statusEl.remove();
        appendMessage("assistant", "Something went wrong. Please try again.");
        console.error(err);
    }
});

newChatButton.addEventListener("click", startNewConversation);

renderHistory();
renderSidebar();
