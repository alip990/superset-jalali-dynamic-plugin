const users = [
  { id: "sara", label: "سارا احمدی · شمال" },
  { id: "reza", label: "رضا کریمی · جنوب" },
  { id: "niloofar", label: "نیلوفر مرادی · شرق" },
  { id: "office", label: "دفتر مرکزی · همه مناطق" },
];

const userBox = document.getElementById("users");
const overlay = document.getElementById("overlay");
const errorBox = document.getElementById("error");
const who = document.getElementById("who");
const mountPoint = document.getElementById("dashboard");
let embedded = null;

function showError(message) {
  overlay.hidden = true;
  errorBox.hidden = false;
  errorBox.textContent = message;
}

function clearError() {
  errorBox.hidden = true;
  errorBox.textContent = "";
}

async function login(user) {
  const response = await fetch("/api/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user }),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || "ورود ناموفق بود");
  }
  return response.json();
}

function watchIframe() {
  const iframe = mountPoint.querySelector("iframe");
  if (!iframe) return;
  iframe.addEventListener("load", () => {
    overlay.hidden = true;
  });
  iframe.addEventListener("error", () => showError("داشبورد بارگذاری نشد"));
}

async function show(user) {
  clearError();
  overlay.hidden = false;
  document.querySelectorAll(".users button").forEach(button => {
    button.setAttribute("aria-pressed", String(button.dataset.user === user));
  });
  const session = await login(user);
  who.textContent = session.display_name;
  if (embedded) {
    embedded.unmount();
    embedded = null;
    mountPoint.replaceChildren();
  }
  const config = await fetch("/api/embed-config").then(response => {
    if (!response.ok) throw new Error("پیکربندی داشبورد در دسترس نیست");
    return response.json();
  });
  const sdk = window.supersetEmbeddedSdk;
  if (!sdk?.embedDashboard) {
    throw new Error("کتابخانهٔ نمایش داشبورد بارگذاری نشد");
  }
  embedded = await sdk.embedDashboard({
    id: config.dashboardUuid,
    supersetDomain: config.supersetDomain,
    mountPoint,
    fetchGuestToken: async () => {
      const response = await fetch("/api/guest-token");
      if (!response.ok) throw new Error("توکن مهمان صادر نشد");
      const body = await response.json();
      return body.token;
    },
    dashboardUiConfig: {
      hideTitle: true,
      filters: { visible: true, expanded: true },
    },
  });
  watchIframe();
}

users.forEach(user => {
  const button = document.createElement("button");
  button.type = "button";
  button.dataset.user = user.id;
  button.textContent = user.label;
  button.addEventListener("click", () => {
    show(user.id).catch(error => showError(error.message || "خطای ناشناخته"));
  });
  userBox.appendChild(button);
});

fetch("/api/session")
  .then(response => response.json())
  .then(body => {
    if (body.user) show(body.user).catch(error => showError(error.message));
  })
  .catch(() => {});
