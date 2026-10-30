(() => {
  const launcher = document.getElementById("prismAiLauncher");
  const panel = document.getElementById("prismAiPanel");
  const closeBtn = document.getElementById("prismAiClose");
  const newChatBtn = document.getElementById("prismAiNewChat");
  const form = document.getElementById("prismAiForm");
  const input = document.getElementById("prismAiInput");
  const sendBtn = document.getElementById("prismAiSend");
  const messages = document.getElementById("prismAiMessages");
  const welcome = document.getElementById("prismAiWelcome");
  const errorBox = document.getElementById("prismAiError");
  if (!launcher || !panel || !form) return;

  let history = [];
  let busy = false;

  function openPanel() {
    panel.hidden = false;
    launcher.setAttribute("aria-expanded", "true");
    input.focus();
  }
  function closePanel() {
    panel.hidden = true;
    launcher.setAttribute("aria-expanded", "false");
  }
  function escapeText(text) { return String(text); }
  function addMessage(role, text) {
    welcome.hidden = true;
    const bubble = document.createElement("div");
    bubble.className = `prism-ai-message ${role}`;
    const label = document.createElement("span");
    label.className = "prism-ai-message-label";
    label.textContent = role === "user" ? "YOU" : "PRISM AI";
    const body = document.createElement("div");
    body.textContent = escapeText(text); // textContent prevents HTML injection
    bubble.append(label, body);
    messages.appendChild(bubble);
    messages.scrollTop = messages.scrollHeight;
    return bubble;
  }
  function showTyping() {
    const bubble = document.createElement("div");
    bubble.className = "prism-ai-message assistant";
    bubble.setAttribute("aria-label", "Prism AI is thinking");
    bubble.innerHTML = '<div class="prism-ai-typing"><span></span><span></span><span></span></div>';
    messages.appendChild(bubble);
    messages.scrollTop = messages.scrollHeight;
    return bubble;
  }
  function setBusy(value) {
    busy = value;
    sendBtn.disabled = value;
    input.disabled = value;
  }
  async function sendMessage(text) {
    const message = text.trim();
    if (!message || busy) return;
    errorBox.hidden = true;
    addMessage("user", message);
    input.value = "";
    input.style.height = "auto";
    const typing = showTyping();
    setBusy(true);
    try {
      const response = await fetch("/api/ai-chat", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({message, history})
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.error || "Sorry, the assistant could not respond. Please try again.");
      const reply = String(data.reply || "I couldn't create a response. Please try again.");
      typing.remove();
      addMessage("assistant", reply);
      history.push({role: "user", text: message}, {role: "model", text: reply});
      history = history.slice(-10);
    } catch (error) {
      typing.remove();
      errorBox.textContent = error.message || "Connection error. Please try again.";
      errorBox.hidden = false;
    } finally {
      setBusy(false);
      input.focus();
    }
  }

  launcher.addEventListener("click", () => panel.hidden ? openPanel() : closePanel());
  closeBtn.addEventListener("click", closePanel);
  newChatBtn.addEventListener("click", () => {
    history = [];
    messages.replaceChildren();
    welcome.hidden = false;
    errorBox.hidden = true;
    input.focus();
  });
  form.addEventListener("submit", event => {
    event.preventDefault();
    sendMessage(input.value);
  });
  input.addEventListener("input", () => {
    input.style.height = "auto";
    input.style.height = `${Math.min(input.scrollHeight, 100)}px`;
  });
  input.addEventListener("keydown", event => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      form.requestSubmit();
    }
  });
  document.querySelectorAll(".prism-ai-suggestions [data-prompt]").forEach(button => {
    button.addEventListener("click", () => sendMessage(button.dataset.prompt || ""));
  });
  document.addEventListener("keydown", event => {
    if (event.key === "Escape" && !panel.hidden) closePanel();
  });
})();
