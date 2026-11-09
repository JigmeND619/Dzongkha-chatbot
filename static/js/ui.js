// DOM rendering. Text is always set with textContent (never innerHTML) to avoid XSS.
const chat = document.getElementById("chat");
const statusEl = document.getElementById("status");
const errorEl = document.getElementById("error");
const sendBtn = document.getElementById("send-btn");

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function append(box) {
  chat.appendChild(box);
  box.scrollIntoView({ behavior: "smooth", block: "end" });
}

export function addUserMessage(text) {
  append(el("div", "msg user", text));
}

export function addAssistantMessage(data, showEnglish) {
  const box = el("div", "msg assistant");
  box.appendChild(el("div", "label", "Dzongkha"));
  const dz = el("div", "dz", data.dzongkha);
  dz.lang = "dz";
  box.appendChild(dz);

  let copyText = data.dzongkha;
  if (showEnglish && data.english_translation) {
    box.appendChild(el("div", "label", "English translation"));
    box.appendChild(el("div", "en", data.english_translation));
    copyText += "\n\n" + data.english_translation;
  }
  if (data.uncertain) {
    const note = data.uncertainty_note || "The AI is not confident this Dzongkha is accurate.";
    box.appendChild(el("div", "warn", "Uncertain: " + note + " Please verify with a fluent Dzongkha speaker."));
  }

  const tools = el("div", "tools");
  const copy = el("button", "copy", "Copy response");
  copy.type = "button";
  copy.addEventListener("click", async () => {
    try { await navigator.clipboard.writeText(copyText); copy.textContent = "Copied"; }
    catch (e) { copy.textContent = "Copy failed"; }
    setTimeout(() => (copy.textContent = "Copy response"), 1500);
  });
  tools.appendChild(copy);
  if (data.verified_by_self_review) {
    tools.appendChild(el("span", "", "Self-reviewed by AI (not proof of accuracy)"));
  }
  box.appendChild(tools);
  append(box);
}

export function setBusy(busy) {
  sendBtn.disabled = busy;
  statusEl.hidden = !busy;
}

export function isBusy() {
  return sendBtn.disabled;
}

export function showError(msg) {
  errorEl.textContent = msg;
  errorEl.hidden = !msg;
}

export function clearMessages() {
  chat.querySelectorAll(".msg:not(.welcome)").forEach((n) => n.remove());
  showError("");
}
