// Enhance the existing HTML form; native submission still works without JavaScript.
let pending = false;

document.addEventListener("submit", async (event) => {
  const form = event.target;
  if (form.id !== "ask-form" || !window.fetch || !window.AbortController) return;
  event.preventDefault();
  if (pending) return;
  pending = true;
  const button = form.querySelector('button[type="submit"]');
  const progress = form.querySelector("#request-progress");
  const oldResult = form.parentElement.querySelector(".result");
  const originalLabel = button.textContent;
  const body = new URLSearchParams(new FormData(form));
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 130000);
  button.disabled = true;
  button.textContent = "Checking…";
  form.setAttribute("aria-busy", "true");
  progress.hidden = false;
  progress.textContent = "Checking your request. The local model may take a moment. Please wait.";
  if (oldResult) oldResult.hidden = true;
  try {
    const response = await fetch(form.action, {
      method: "POST", body, credentials: "same-origin", signal: controller.signal,
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
    const html = await response.text();
    const page = new DOMParser().parseFromString(html, "text/html");
    const main = page.querySelector("main");
    const result = main && main.querySelector(".result");
    if (!main || !result) throw new Error("Unexpected response page");
    document.querySelector("main").replaceWith(main);
    const header = page.querySelector("header");
    if (header) document.querySelector("header").replaceWith(header);
    result.setAttribute("tabindex", "-1");
    result.focus();
  } catch (error) {
    progress.textContent = error.name === "AbortError"
      ? "This is taking too long. Your request may still be processing. Wait before trying again."
      : "We couldn't load the response. Your question is preserved. Check the server and connection before trying again.";
    // Do not restore the old answer: it belongs to the previous question.
  } finally {
    clearTimeout(timeout);
    pending = false;
    button.disabled = false;
    button.textContent = originalLabel;
    form.removeAttribute("aria-busy");
  }
});
