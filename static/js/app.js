const csrf = document.querySelector("meta[name=csrf-token]").content;
const MASK = "••••••••••";

async function fetchValue(url) {
  const response = await fetch(url, { method: "POST", headers: { "X-CSRFToken": csrf } });
  if (!response.ok) throw new Error("Request failed");
  const data = await response.json();
  return data.value;
}

document.addEventListener("click", async (event) => {
  const button = event.target.closest("button[data-show], button[data-copy]");
  if (!button) return;

  try {
    if (button.hasAttribute("data-show")) {
      const output = document.getElementById(button.dataset.target);
      if (output.classList.contains("open")) {
        output.textContent = MASK;
        output.classList.remove("open");
        button.textContent = "Show";
      } else {
        output.textContent = await fetchValue(button.dataset.url);
        output.classList.add("open");
        button.textContent = "Hide";
      }
    } else {
      await navigator.clipboard.writeText(await fetchValue(button.dataset.url));
      const label = button.textContent;
      button.textContent = "Copied";
      setTimeout(() => (button.textContent = label), 1500);
    }
  } catch (error) {
    alert("Something went wrong. Please try again.");
  }
});

document.addEventListener("submit", (event) => {
  const message = event.target.dataset.confirm;
  if (message && !confirm(message)) event.preventDefault();
});

const generateButton = document.getElementById("generate");
if (generateButton) {
  generateButton.addEventListener("click", () => {
    const chars = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789!@#$%&*-_=+";
    const numbers = crypto.getRandomValues(new Uint32Array(20));
    document.getElementById("id_value").value = Array.from(numbers, (n) => chars[n % chars.length]).join("");
  });
}

const EYE = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>';
const EYE_OFF = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>';

document.querySelectorAll("input[type=password]").forEach((input) => {
  const wrapper = document.createElement("div");
  wrapper.className = "password-wrap";
  input.parentNode.insertBefore(wrapper, input);
  wrapper.appendChild(input);

  const toggle = document.createElement("button");
  toggle.type = "button";
  toggle.className = "eye";
  toggle.innerHTML = EYE;
  toggle.setAttribute("aria-label", "Show password");
  wrapper.appendChild(toggle);

  toggle.addEventListener("click", () => {
    const isHidden = input.type === "password";
    input.type = isHidden ? "text" : "password";
    toggle.innerHTML = isHidden ? EYE_OFF : EYE;
    toggle.setAttribute("aria-label", isHidden ? "Hide password" : "Show password");
  });
});