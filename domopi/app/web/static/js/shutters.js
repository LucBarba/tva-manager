/* DomoPi – page volets : CRUD, groupes, apprentissage RF433. */
"use strict";

let shutters = [];
let learnShutterId = null;

/** Recharge volets et groupes puis redessine la page. */
async function refresh() {
  const [shutterList, groups] = await Promise.all([
    api("/api/shutters"),
    api("/api/shutters/groups"),
  ]);
  shutters = shutterList;
  renderShutters();
  renderGroups(groups);
  renderGroupChecks();
}

function commandButtons(prefix, id) {
  return (
    '<div class="btn-group w-100 btn-group-sm mt-2">' +
    ["open|bi-chevron-up", "stop|bi-square", "favorite|bi-star", "close|bi-chevron-down"]
      .map((pair) => {
        const [action, icon] = pair.split("|");
        return (
          '<button class="btn btn-outline-primary cmd-btn" data-kind="' + prefix +
          '" data-id="' + id + '" data-action="' + action + '"><i class="bi ' + icon + '"></i></button>'
        );
      })
      .join("") +
    "</div>"
  );
}

function renderShutters() {
  document.getElementById("shutter-list").innerHTML = shutters
    .map(
      (shutter) =>
        '<div class="col-12 col-md-6 col-xl-4"><div class="card h-100"><div class="card-body">' +
        '<div class="d-flex justify-content-between">' +
        '<div><span class="fw-semibold">' + esc(shutter.name) + "</span>" +
        ' <span class="badge text-bg-secondary">' + esc(shutter.protocol) + "</span>" +
        '<div class="small text-body-secondary">' + esc(shutter.room || "") + "</div></div>" +
        '<div class="btn-group btn-group-sm">' +
        (shutter.protocol === "rf433"
          ? '<button class="btn btn-outline-secondary learn-btn" data-id="' + shutter.id + '" title="Apprentissage"><i class="bi bi-broadcast"></i></button>'
          : '<button class="btn btn-outline-secondary prog-btn" data-id="' + shutter.id + '" title="Appairage PROG"><i class="bi bi-link-45deg"></i></button>') +
        '<button class="btn btn-outline-danger delete-btn" data-id="' + shutter.id + '"><i class="bi bi-trash"></i></button>' +
        "</div></div>" +
        commandButtons("shutter", shutter.id) +
        "</div></div></div>"
    )
    .join("");
}

function renderGroups(groups) {
  document.getElementById("group-cards").innerHTML = groups.length
    ? groups
        .map(
          (group) =>
            '<div class="col-12 col-md-6 col-xl-4"><div class="card h-100"><div class="card-body">' +
            '<div class="d-flex justify-content-between">' +
            '<span class="fw-semibold"><i class="bi bi-collection"></i> ' + esc(group.name) + "</span>" +
            '<button class="btn btn-outline-danger btn-sm group-delete" data-id="' + group.id + '"><i class="bi bi-trash"></i></button></div>' +
            '<div class="small text-body-secondary">' + group.shutter_ids.length + " volet(s)</div>" +
            commandButtons("group", group.id) +
            "</div></div></div>"
        )
        .join("")
    : '<div class="col"><p class="text-body-secondary">Aucun groupe pour le moment.</p></div>';
}

function renderGroupChecks() {
  document.getElementById("group-shutter-checks").innerHTML = shutters
    .map(
      (shutter) =>
        '<div class="form-check"><input class="form-check-input group-member" type="checkbox" value="' +
        shutter.id + '" id="gs' + shutter.id + '"><label class="form-check-label" for="gs' + shutter.id + '">' +
        esc(shutter.name) + "</label></div>"
    )
    .join("");
}

/* Creation d'un volet */
document.getElementById("shutter-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.target);
  try {
    await api("/api/shutters", {
      method: "POST",
      body: JSON.stringify({
        name: form.get("name"),
        room: form.get("room"),
        protocol: form.get("protocol"),
        travel_time_s: Number(form.get("travel_time_s")),
        favorite_position: Number(form.get("favorite_position")),
      }),
    });
    bootstrap.Modal.getInstance(document.getElementById("shutter-modal")).hide();
    event.target.reset();
    toast("Volet créé");
    refresh();
  } catch (error) {
    toast(error.message, "danger");
  }
});

/* Creation d'un groupe */
document.getElementById("group-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const ids = [...document.querySelectorAll(".group-member:checked")].map((c) => Number(c.value));
  if (!ids.length) {
    toast("Sélectionner au moins un volet", "warning");
    return;
  }
  try {
    await api("/api/shutters/groups", {
      method: "POST",
      body: JSON.stringify({ name: new FormData(event.target).get("name"), shutter_ids: ids }),
    });
    bootstrap.Modal.getInstance(document.getElementById("group-modal")).hide();
    event.target.reset();
    toast("Groupe créé");
    refresh();
  } catch (error) {
    toast(error.message, "danger");
  }
});

/* Actions deleguees : commandes, suppression, apprentissage */
document.addEventListener("click", async (event) => {
  const command = event.target.closest(".cmd-btn");
  if (command) {
    const path =
      command.dataset.kind === "group"
        ? "/api/shutters/groups/" + command.dataset.id + "/" + command.dataset.action
        : "/api/shutters/" + command.dataset.id + "/" + command.dataset.action;
    try {
      await api(path, { method: "POST" });
    } catch (error) {
      toast(error.message, "danger");
    }
    return;
  }
  const deleteBtn = event.target.closest(".delete-btn");
  if (deleteBtn && window.confirm("Supprimer ce volet ?")) {
    try {
      await api("/api/shutters/" + deleteBtn.dataset.id, { method: "DELETE" });
      refresh();
    } catch (error) {
      toast(error.message, "danger");
    }
    return;
  }
  const groupDelete = event.target.closest(".group-delete");
  if (groupDelete && window.confirm("Supprimer ce groupe ?")) {
    try {
      await api("/api/shutters/groups/" + groupDelete.dataset.id, { method: "DELETE" });
      refresh();
    } catch (error) {
      toast(error.message, "danger");
    }
    return;
  }
  const progBtn = event.target.closest(".prog-btn");
  if (progBtn) {
    try {
      await api("/api/shutters/" + progBtn.dataset.id + "/prog", { method: "POST" });
      toast("Trame PROG émise : le volet doit confirmer par un va-et-vient");
    } catch (error) {
      toast(error.message, "danger");
    }
    return;
  }
  const learnBtn = event.target.closest(".learn-btn");
  if (learnBtn) {
    learnShutterId = learnBtn.dataset.id;
    new bootstrap.Modal(document.getElementById("learn-modal")).show();
  }
});

/* Apprentissage d'une action RF433 */
document.getElementById("learn-buttons").addEventListener("click", async (event) => {
  const button = event.target.closest("[data-action]");
  if (!button || learnShutterId === null) return;
  const status = document.getElementById("learn-status");
  status.className = "alert alert-info mt-3";
  status.textContent = "Écoute en cours… appuyer sur le bouton de la télécommande.";
  try {
    const result = await api("/api/shutters/" + learnShutterId + "/learn/code", {
      method: "POST",
      body: JSON.stringify({ action: button.dataset.action, timeout_s: 15 }),
    });
    status.className = "alert alert-success mt-3";
    status.textContent = result.message;
    refresh();
  } catch (error) {
    status.className = "alert alert-danger mt-3";
    status.textContent = error.message;
  }
});

refresh().catch((error) => toast(error.message, "danger"));
