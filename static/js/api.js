// Network layer: the only file that talks to the Flask backend.
export async function sendChat(message, showTranslation, verify) {
  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, show_translation: showTranslation, verify }),
  });
  let data = {};
  try { data = await res.json(); } catch (e) { /* non-JSON error page */ }
  if (!res.ok) throw new Error(data.error || "Something went wrong (status " + res.status + ").");
  return data;
}

export async function clearChat() {
  await fetch("/api/clear", { method: "POST" });
}
