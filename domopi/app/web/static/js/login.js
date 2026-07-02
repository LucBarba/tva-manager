/* DomoPi – page de connexion. */
"use strict";

document.getElementById("login-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const errorBox = document.getElementById("login-error");
  errorBox.classList.add("d-none");
  const body = {
    username: document.getElementById("username").value,
    password: document.getElementById("password").value,
  };
  const response = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (response.ok) {
    window.location.href = "/";
  } else {
    const payload = await response.json().catch(() => ({}));
    errorBox.textContent = payload.detail || "Identifiants invalides";
    errorBox.classList.remove("d-none");
  }
});
