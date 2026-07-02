/* ==========================================================================
 * DomoPi – socle JavaScript commun a toutes les pages.
 * Fournit : appels API (avec jeton CSRF), notifications toast, bascule de
 * theme clair/sombre persistee, deconnexion et connexion WebSocket.
 * ========================================================================== */

"use strict";

/** Lit un cookie par son nom (utilise pour le jeton CSRF). */
function getCookie(name) {
  const match = document.cookie.match(new RegExp("(?:^|; )" + name + "=([^;]*)"));
  return match ? decodeURIComponent(match[1]) : "";
}

/**
 * Appelle l'API JSON avec gestion CSRF et erreurs.
 * Redirige vers /login si la session a expire.
 */
async function api(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  const method = (options.method || "GET").toUpperCase();
  if (method !== "GET") {
    headers["X-CSRF-Token"] = getCookie("csrf_token");
  }
  const response = await fetch(path, { ...options, headers });
  if (response.status === 401) {
    window.location.href = "/login";
    throw new Error("Session expirée");
  }
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || "Erreur " + response.status);
  }
  return response.status === 204 ? null : response.json();
}

/** Affiche une notification toast Bootstrap. */
function toast(message, variant = "success") {
  const container = document.getElementById("toast-container");
  if (!container) return;
  const el = document.createElement("div");
  el.className = "toast align-items-center text-bg-" + variant + " border-0";
  el.innerHTML =
    '<div class="d-flex"><div class="toast-body"></div>' +
    '<button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button></div>';
  el.querySelector(".toast-body").textContent = message;
  container.appendChild(el);
  const instance = new bootstrap.Toast(el, { delay: 3500 });
  instance.show();
  el.addEventListener("hidden.bs.toast", () => el.remove());
}

/** Echappe le HTML pour les rendus construits en JS (protection XSS). */
function esc(value) {
  const div = document.createElement("div");
  div.textContent = String(value ?? "");
  return div.innerHTML;
}

/* --- Theme clair/sombre ------------------------------------------------- */

function applyTheme(theme) {
  document.documentElement.setAttribute("data-bs-theme", theme);
  localStorage.setItem("domopi-theme", theme);
  const icon = document.querySelector("#theme-toggle i");
  if (icon) icon.className = theme === "dark" ? "bi bi-moon-stars" : "bi bi-sun";
}

applyTheme(localStorage.getItem("domopi-theme") || "dark");

document.addEventListener("DOMContentLoaded", () => {
  const themeToggle = document.getElementById("theme-toggle");
  if (themeToggle) {
    themeToggle.addEventListener("click", () => {
      const current = document.documentElement.getAttribute("data-bs-theme");
      applyTheme(current === "dark" ? "light" : "dark");
    });
  }
  const logoutBtn = document.getElementById("logout-btn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", async () => {
      await api("/api/auth/logout", { method: "POST" }).catch(() => {});
      window.location.href = "/login";
    });
  }
});

/* --- WebSocket temps reel ------------------------------------------------ */

/**
 * Ouvre le WebSocket d'etats et invoque `onEvent(event)` pour chaque
 * message. Reconnexion automatique avec repli progressif.
 */
function connectWebSocket(onEvent) {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  let retryDelay = 1000;

  function open() {
    const socket = new WebSocket(protocol + "//" + window.location.host + "/ws");
    socket.onopen = () => {
      retryDelay = 1000;
      const badge = document.getElementById("ws-status");
      if (badge) {
        badge.className = "badge text-bg-success";
        badge.innerHTML = '<i class="bi bi-wifi"></i> en direct';
      }
    };
    socket.onmessage = (message) => {
      try {
        onEvent(JSON.parse(message.data));
      } catch (_error) {
        /* message non JSON : ignore */
      }
    };
    socket.onclose = () => {
      const badge = document.getElementById("ws-status");
      if (badge) {
        badge.className = "badge text-bg-secondary";
        badge.innerHTML = '<i class="bi bi-wifi-off"></i> hors ligne';
      }
      setTimeout(open, retryDelay);
      retryDelay = Math.min(retryDelay * 2, 30000);
    };
  }
  open();
}
