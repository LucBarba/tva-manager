/* DomoPi – page lumieres Hue : pieces, scenes, ampoules. */
"use strict";

/** Recharge pieces, scenes et ampoules puis redessine la page. */
async function refresh() {
  const lights = (await api("/api/devices?type=light")) || [];
  renderLights(lights);
  try {
    const [rooms, scenes] = await Promise.all([api("/api/hue/rooms"), api("/api/hue/scenes")]);
    renderRooms(rooms);
    renderScenes(scenes);
  } catch (error) {
    document.getElementById("room-cards").innerHTML =
      '<div class="col"><div class="alert alert-warning">' + esc(error.message) +
      ' — appairer le pont depuis la page Configuration.</div></div>';
  }
}

function renderRooms(rooms) {
  document.getElementById("room-cards").innerHTML = rooms
    .map(
      (room) =>
        '<div class="col-6 col-md-4 col-xl-3"><div class="card h-100"><div class="card-body">' +
        '<div class="fw-semibold mb-2"><i class="bi bi-door-open"></i> ' + esc(room.name) + "</div>" +
        (room.grouped_light_id
          ? '<div class="btn-group w-100 btn-group-sm">' +
            '<button class="btn btn-outline-warning room-cmd" data-gid="' + esc(room.grouped_light_id) + '" data-on="true"><i class="bi bi-lightbulb-fill"></i> On</button>' +
            '<button class="btn btn-outline-secondary room-cmd" data-gid="' + esc(room.grouped_light_id) + '" data-on="false"><i class="bi bi-lightbulb-off"></i> Off</button></div>'
          : "") +
        "</div></div></div>"
    )
    .join("");
}

function renderScenes(scenes) {
  document.getElementById("scene-buttons").innerHTML = scenes
    .map(
      (scene) =>
        '<button class="btn btn-outline-info btn-sm scene-btn" data-id="' + esc(scene.id) + '">' +
        '<i class="bi bi-stars"></i> ' + esc(scene.name) + "</button>"
    )
    .join("");
}

function renderLights(lights) {
  document.getElementById("light-list").innerHTML = lights
    .map((light) => {
      const attributes = light.attributes;
      const on = Boolean(attributes.on);
      const brightness = attributes.brightness ?? 100;
      const mirek = attributes.color_temp_mirek ?? 300;
      return (
        '<div class="col-12 col-md-6 col-xl-4"><div class="card h-100 ' + (on ? "light-on" : "") +
        '" data-uid="' + esc(light.uid) + '"><div class="card-body">' +
        '<div class="d-flex justify-content-between align-items-center mb-2">' +
        '<div><span class="fw-semibold">' + esc(light.name) + "</span>" +
        '<div class="small text-body-secondary">' + esc(light.room || "") + "</div></div>" +
        '<div class="d-flex align-items-center gap-2"><i class="bi bi-lightbulb device-icon"></i>' +
        '<div class="form-check form-switch m-0"><input class="form-check-input light-toggle" type="checkbox" ' +
        (on ? "checked" : "") + "></div></div></div>" +
        '<label class="form-label small mb-0"><i class="bi bi-brightness-high"></i> Luminosité</label>' +
        '<input type="range" class="form-range light-brightness" min="1" max="100" value="' + Number(brightness) + '">' +
        '<label class="form-label small mb-0"><i class="bi bi-thermometer-sun"></i> Blancs (chaud ↔ froid)</label>' +
        '<input type="range" class="form-range light-mirek" min="153" max="500" value="' + (653 - Number(mirek)) + '">' +
        "</div></div></div>"
      );
    })
    .join("");
}

/** Envoie une commande a une ampoule par son uid. */
async function commandLight(uid, command, params) {
  try {
    await api("/api/devices/" + encodeURIComponent(uid) + "/command", {
      method: "POST",
      body: JSON.stringify({ command, params: params || {} }),
    });
  } catch (error) {
    toast(error.message, "danger");
  }
}

document.addEventListener("change", (event) => {
  const card = event.target.closest("[data-uid]");
  if (!card) return;
  const uid = card.dataset.uid;
  if (event.target.classList.contains("light-toggle")) {
    commandLight(uid, event.target.checked ? "on" : "off");
    card.classList.toggle("light-on", event.target.checked);
  } else if (event.target.classList.contains("light-brightness")) {
    commandLight(uid, "set_brightness", { brightness: Number(event.target.value) });
  } else if (event.target.classList.contains("light-mirek")) {
    // Le curseur va du chaud au froid : inversion vers les mireds
    commandLight(uid, "set_color_temp", { mirek: 653 - Number(event.target.value) });
  }
});

document.addEventListener("click", async (event) => {
  const sceneBtn = event.target.closest(".scene-btn");
  if (sceneBtn) {
    try {
      await api("/api/hue/scenes/" + encodeURIComponent(sceneBtn.dataset.id) + "/activate", { method: "POST" });
      toast("Scène activée");
    } catch (error) {
      toast(error.message, "danger");
    }
    return;
  }
  const roomCmd = event.target.closest(".room-cmd");
  if (roomCmd) {
    try {
      await api("/api/hue/groups/" + encodeURIComponent(roomCmd.dataset.gid) + "/command", {
        method: "POST",
        body: JSON.stringify({ on: roomCmd.dataset.on === "true" }),
      });
      setTimeout(refresh, 500);
    } catch (error) {
      toast(error.message, "danger");
    }
  }
});

document.getElementById("hue-refresh").addEventListener("click", async () => {
  try {
    await api("/api/hue/refresh", { method: "POST" });
    toast("Resynchronisation effectuée");
    refresh();
  } catch (error) {
    toast(error.message, "danger");
  }
});

refresh().catch((error) => toast(error.message, "danger"));
