/* DomoPi – page programmations horaires. */
"use strict";

const DAY_NAMES = { 1: "Lu", 2: "Ma", 3: "Me", 4: "Je", 5: "Ve", 6: "Sa", 7: "Di" };
const SHUTTER_ACTIONS = ["open", "close", "stop", "favorite"];
const LIGHT_ACTIONS = ["on", "off"];

/** Recharge les programmations et les cibles disponibles. */
async function refresh() {
  const [schedules, shutters, groups, lights] = await Promise.all([
    api("/api/schedules"),
    api("/api/shutters"),
    api("/api/shutters/groups"),
    api("/api/devices?type=light"),
  ]);
  renderRows(schedules);
  renderTargets(shutters, groups, lights);
}

function renderRows(schedules) {
  document.getElementById("schedule-rows").innerHTML = schedules
    .map(
      (schedule) =>
        "<tr><td>" + esc(schedule.name) + "</td>" +
        "<td><code>" + esc(schedule.target_type) + ":" + esc(schedule.target_id) + "</code></td>" +
        "<td>" + esc(schedule.action) + "</td>" +
        "<td>" + esc(schedule.time) + "</td>" +
        "<td>" + schedule.days.map((day) => DAY_NAMES[day] || day).join(" ") + "</td>" +
        '<td><div class="form-check form-switch"><input class="form-check-input toggle-schedule" type="checkbox" data-id="' +
        schedule.id + '" ' + (schedule.enabled ? "checked" : "") + "></div></td>" +
        '<td class="text-end"><button class="btn btn-outline-danger btn-sm delete-schedule" data-id="' +
        schedule.id + '"><i class="bi bi-trash"></i></button></td></tr>'
    )
    .join("");
}

function renderTargets(shutters, groups, lights) {
  const select = document.getElementById("schedule-target");
  select.innerHTML =
    shutters.map((s) => '<option value="shutter|' + s.id + '">Volet – ' + esc(s.name) + "</option>").join("") +
    groups.map((g) => '<option value="shutter_group|' + g.id + '">Groupe – ' + esc(g.name) + "</option>").join("") +
    lights.map((l) => '<option value="light|' + esc(l.uid) + '">Lumière – ' + esc(l.name) + "</option>").join("");
  updateActions();
}

/** Adapte la liste des actions au type de cible choisi. */
function updateActions() {
  const value = document.getElementById("schedule-target").value || "shutter|";
  const isLight = value.startsWith("light|");
  document.getElementById("schedule-action").innerHTML = (isLight ? LIGHT_ACTIONS : SHUTTER_ACTIONS)
    .map((action) => '<option value="' + action + '">' + action + "</option>")
    .join("");
}

document.getElementById("schedule-target").addEventListener("change", updateActions);

document.getElementById("schedule-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.target);
  const [targetType, targetId] = String(form.get("target")).split("|");
  const days = [...document.querySelectorAll("#schedule-days input:checked")].map((c) => Number(c.value));
  if (!days.length) {
    toast("Sélectionner au moins un jour", "warning");
    return;
  }
  try {
    await api("/api/schedules", {
      method: "POST",
      body: JSON.stringify({
        name: form.get("name"),
        target_type: targetType,
        target_id: targetId,
        action: form.get("action"),
        time: form.get("time"),
        days,
        enabled: true,
      }),
    });
    bootstrap.Modal.getInstance(document.getElementById("schedule-modal")).hide();
    event.target.reset();
    toast("Programmation créée");
    refresh();
  } catch (error) {
    toast(error.message, "danger");
  }
});

document.addEventListener("click", async (event) => {
  const deleteBtn = event.target.closest(".delete-schedule");
  if (deleteBtn && window.confirm("Supprimer cette programmation ?")) {
    try {
      await api("/api/schedules/" + deleteBtn.dataset.id, { method: "DELETE" });
      refresh();
    } catch (error) {
      toast(error.message, "danger");
    }
  }
});

document.addEventListener("change", async (event) => {
  if (event.target.classList.contains("toggle-schedule")) {
    try {
      await api(
        "/api/schedules/" + event.target.dataset.id + "/enabled?enabled=" + event.target.checked,
        { method: "PATCH" }
      );
    } catch (error) {
      toast(error.message, "danger");
    }
  }
});

refresh().catch((error) => toast(error.message, "danger"));
