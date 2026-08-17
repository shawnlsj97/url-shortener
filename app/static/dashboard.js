const dashboardForm = document.querySelector("#dashboard-create-form");
const dashboardError = document.querySelector("#dashboard-error");
const logoutButton = document.querySelector("#logout-button");

function csrfHeaders() {
  const token = document.cookie.split("; ").find((item) => item.startsWith("ogp_csrf="))?.split("=")[1];
  return token ? { "X-CSRF-Token": decodeURIComponent(token) } : {};
}

dashboardForm?.addEventListener("submit", async (event) => {
  event.preventDefault();
  dashboardError.hidden = true;
  const submitButton = dashboardForm.querySelector("button[type='submit']");
  submitButton.disabled = true;

  try {
    const expiresAt = document.querySelector("#dashboard-expires-at").value;
    const response = await fetch("/api/links", {
      method: "POST",
      headers: { "Content-Type": "application/json", ...csrfHeaders() },
      body: JSON.stringify({
        original_url: document.querySelector("#dashboard-original-url").value,
        custom_alias: document.querySelector("#dashboard-custom-alias").value || null,
        expires_at: expiresAt ? new Date(expiresAt).toISOString() : null,
      }),
    });
    const body = await response.json();
    if (!response.ok) throw new Error(body.detail || "Unable to create the link.");
    window.location.reload();
  } catch (error) {
    dashboardError.textContent = error.message || "Unable to create the link.";
    dashboardError.hidden = false;
  } finally {
    submitButton.disabled = false;
  }
});

document.querySelectorAll(".disable-button").forEach((button) => {
  button.addEventListener("click", async () => {
    const card = button.closest("[data-code]");
    if (!card || !window.confirm("Disable this link? It will stop redirecting.")) return;
    const response = await fetch(`/api/links/${card.dataset.code}`, {
      method: "DELETE",
      headers: csrfHeaders(),
    });
    if (response.ok) window.location.reload();
  });
});

logoutButton?.addEventListener("click", async () => {
  await fetch("/api/auth/logout", { method: "POST", headers: csrfHeaders() });
  window.location.assign("/");
});
