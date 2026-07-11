const conversationId = crypto.randomUUID();

const historyEl = document.getElementById("history");
const formEl = document.getElementById("chat-form");
const inputEl = document.getElementById("message-input");

function appendMessage(role, text) {
    const el = document.createElement("div");
    el.className = `message ${role}`;
    el.textContent = text;
    historyEl.appendChild(el);
    historyEl.scrollTop = historyEl.scrollHeight;
}

async function sendMessage(message) {
    const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, conversation_id: conversationId }),
    });

    if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`);
    }

    const data = await response.json();
    return data.reply;
}

formEl.addEventListener("submit", async (event) => {
    event.preventDefault();
    const message = inputEl.value.trim();
    if (!message) return;

    inputEl.value = "";
    appendMessage("user", message);

    try {
        const reply = await sendMessage(message);
        appendMessage("assistant", reply);
    } catch (err) {
        appendMessage("assistant", "Something went wrong. Please try again.");
        console.error(err);
    }
});
