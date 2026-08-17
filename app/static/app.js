const form = document.querySelector("#create-link-form");
const urlInput = document.querySelector("#original-url");
const customAliasInput = document.querySelector("#custom-alias");
const expiresAtInput = document.querySelector("#expires-at");
const errorMessage = document.querySelector("#form-error");
const result = document.querySelector("#result");
const shortUrl = document.querySelector("#short-url");
const copyButton = document.querySelector("#copy-button");
const copyStatus = document.querySelector("#copy-status");

function csrfHeaders() {
  const token = document.cookie.split("; ").find((item) => item.startsWith("ogp_csrf="))?.split("=")[1];
  return token ? { "X-CSRF-Token": decodeURIComponent(token) } : {};
}

form?.addEventListener("submit", async (event) => {
  event.preventDefault();
  errorMessage.hidden = true;
  result.hidden = true;

  const submitButton = form.querySelector("button[type='submit']");
  submitButton.disabled = true;
  submitButton.textContent = "Shortening…";

  try {
    const response = await fetch("/api/links", {
      method: "POST",
      headers: { "Content-Type": "application/json", ...csrfHeaders() },
      body: JSON.stringify({
        original_url: urlInput.value,
        custom_alias: customAliasInput.value || null,
        expires_at: expiresAtInput.value ? new Date(expiresAtInput.value).toISOString() : null,
      }),
    });
    const body = await response.json();

    if (!response.ok) {
      throw new Error(body.detail || "Please enter a valid URL.");
    }

    shortUrl.href = body.short_url;
    shortUrl.textContent = body.short_url;
    copyStatus.textContent = "";
    result.hidden = false;
  } catch (error) {
    errorMessage.textContent = error.message || "Unable to shorten this URL.";
    errorMessage.hidden = false;
  } finally {
    submitButton.disabled = false;
    submitButton.textContent = "Shorten URL";
  }
});

copyButton?.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(shortUrl.href);
    copyStatus.textContent = "Copied to clipboard.";
  } catch {
    copyStatus.textContent = "Copy failed. Select the link and copy it manually.";
  }
});
