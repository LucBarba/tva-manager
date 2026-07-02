/* DomoPi – page configuration : appairages, utilisateurs, systeme. */
"use strict";

/** Recharge utilisateurs et informations systeme. */
async function refresh() {
  try {
    const users = await api("/api/users");
    document.getElementById("user-rows").innerHTML = users
      .map(
        (user) =>
          "<tr><td>" + esc(user.username) + "</td>" +
          '<td><span class="badge text-bg-' + (user.role === "admin" ? "danger" : "secondary") + '">' +
          esc(user.role) + "</span></td>" +
          '<td class="text-end"><button class="btn btn-outline-danger btn-sm user-delete" data-id="' +
          user.id + '"><i class="bi bi-trash"></i></button></td></tr>'
      )
      .join("");
  } catch (_error) {
    document.getElementById("user-rows").innerHTML =
      '<tr><td class="text-body-secondary">Réservé aux administrateurs.</td></tr>';
  }
  const info = await api("/api/system/info");
  document.getElementById("system-info").innerHTML =
    "<dt class=\"col-5\">Version</dt><dd class=\"col-7\">" + esc(info.version) + "</dd>" +
    "<dt class=\"col-5\">Python</dt><dd class=\"col-7\">" + esc(info.python) + "</dd>" +
    "<dt class=\"col-5\">Environnement</dt><dd class=\"col-7\">" + esc(info.environment) + "</dd>" +
    "<dt class=\"col-5\">Périphériques</dt><dd class=\"col-7\">" + esc(info.device_count) + "</dd>" +
    "<dt class=\"col-5\">Pilote RF</dt><dd class=\"col-7\">" + esc(info.integrations.rf_driver) + "</dd>";
}

document.getElementById("hue-pair").addEventListener("click", async () => {
  try {
    await api("/api/hue/pair", { method: "POST" });
    toast("Pont Hue appairé");
  } catch (error) {
    toast(error.message, "danger");
  }
});

document.getElementById("matter-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const result = await api("/api/matter/commission", {
      method: "POST",
      body: JSON.stringify({ pairing_code: document.getElementById("pairing-code").value }),
    });
    toast(result.message);
    event.target.reset();
  } catch (error) {
    toast(error.message, "danger");
  }
});

document.getElementById("user-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.target);
  try {
    await api("/api/users", {
      method: "POST",
      body: JSON.stringify({
        username: form.get("username"),
        password: form.get("password"),
        role: form.get("role"),
      }),
    });
    toast("Utilisateur créé");
    event.target.reset();
    refresh();
  } catch (error) {
    toast(error.message, "danger");
  }
});

document.addEventListener("click", async (event) => {
  const deleteBtn = event.target.closest(".user-delete");
  if (deleteBtn && window.confirm("Supprimer cet utilisateur ?")) {
    try {
      await api("/api/users/" + deleteBtn.dataset.id, { method: "DELETE" });
      refresh();
    } catch (error) {
      toast(error.message, "danger");
    }
  }
});

refresh().catch((error) => toast(error.message, "danger"));
