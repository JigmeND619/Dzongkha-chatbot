// Entry point: connects user actions to the API and the UI.
import { sendChat, clearChat } from "./api.js";
import { addUserMessage, addAssistantMessage, setBusy, isBusy, showError, clearMessages } from "./ui.js";

const form = document.getElementById("composer");
const input = document.getElementById("input");
const translationToggle = document.getElementById("toggle-translation");
const verifyToggle = document.getElementById("toggle-verify");

async function handleSend(text) {
  showError("");
  const showEnglish = translationToggle.checked;
  addUserMessage(text);
  input.value = "";
  setBusy(true);
  try {
    addAssistantMessage(await sendChat(text, showEnglish, verifyToggle.checked), showEnglish);
  } catch (err) {
    showError(err.message || "Network error. Is the server running?");
  } finally {
    setBusy(false);
    input.focus();
  }
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  const text = input.value.trim();
  if (text && !isBusy()) handleSend(text);
});

// Enter sends; Shift+Enter inserts a new line (ignored while an input method is composing).
input.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey && !e.isComposing) {
    e.preventDefault();
    form.requestSubmit();
  }
});

document.querySelectorAll(".chip").forEach((chip) =>
  chip.addEventListener("click", () => !isBusy() && handleSend(chip.textContent)));

document.getElementById("clear-btn").addEventListener("click", async () => {
  if (!window.confirm("Clear this conversation? This cannot be undone.")) return;
  try { await clearChat(); } catch (e) { /* the screen is cleared either way */ }
  clearMessages();
});
