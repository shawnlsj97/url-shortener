const authForm = document.querySelector("#auth-form");
const authError = document.querySelector("#auth-error");

function csrfHeaders() {
  const token = document.cookie.split("; ").find((item) => item.startsWith("ogp_csrf="))?.split("=")[1];
  return token ? { "X-CSRF-Token": decodeURIComponent(token) } : {};
}

function errorMessageFor(body, fallback) {
  if (typeof body.detail === "string") return body.detail;
  if (Array.isArray(body.detail)) return body.detail.map((item) => item.msg).join(" ");
  return fallback;
}

authForm?.addEventListener("submit", async (event) => {
  event.preventDefault();
  authError.hidden = true;

  const submitButton = authForm.querySelector("button[type='submit']");
  submitButton.disabled = true;
  const mode = authForm.dataset.mode;

  try {
    const response = await fetch(`/api/auth/${mode}`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...csrfHeaders() },
      body: JSON.stringify({
        email: document.querySelector("#email").value,
        password: document.querySelector("#password").value,
      }),
    });
    const body = await response.json();
    if (!response.ok) throw new Error(errorMessageFor(body, "Unable to continue."));
    window.location.assign("/dashboard");
  } catch (error) {
    authError.textContent = error.message || "Unable to continue.";
    authError.hidden = false;
  } finally {
    submitButton.disabled = false;
  }
});
