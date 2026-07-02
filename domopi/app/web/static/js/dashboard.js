/* DomoPi – tableau de bord : cartes appareils et mises a jour temps reel. */
"use strict";

const state = { devices: [] };

/** Recharge tous les appareils puis redessine les cartes. */
async function loadDevices() {
  state.devices = await api("/api/devices");
  render();
}

/** Redessine les trois zones (capteurs, volets, lumieres). */
function render() {
  renderSensors(state.devices.filter((d) => d.type.includes("sensor")));
  renderShutters(state.devices.filter((d) => d.type === "shutter"));
  renderLights(state.devices.filter((d) => d.type === "light"));
}

function renderSensors(sensors) {
  const zone = document.getElementById("sensor-cards");
  zone.innerHTML = sensors
    .map((sensor) => {
      const a = sensor.attributes;
      return (
        '<div class="col-6 col-md-4 col-xl-3"><div class="card device-card h-100"><div class="card-body">' +
        '<div class="d-flex justify-content-between">' +
        '<div><div class="text-body-secondary small">' + esc(sensor.name) + "</div>" +
        '<div class="sensor-value">' + (a.temperature != null ? esc(a.temperature) + "°C" : "–") + "</div>" +
        '<div class="small text-body-secondary">' +
        (a.humidity != null ? '<i class="bi bi-droplet"></i> ' + esc(a.humidity) + "% " : "") +
        (a.battery != null ? '<i class="bi bi-battery-half"></i> ' + esc(a.battery) + "%" : "") +
        "</div></div>" +
        '<i class="bi bi-thermometer-half device-icon text-info"></i>' +
        "</div></div></div></div>"
      );
    })
    .join("");
}

function renderShutters(shutters) {
  const zone = document.getElementById("shutter-cards");
  zone.innerHTML = shutters
    .map((shutter) => {
      const position = shutter.attributes.position ?? 0;
      return (
        '<div class="col-6 col-md-4 col-xl-3"><div class="card device-card h-100" data-uid="' + esc(shutter.uid) + '">' +
        '<div class="card-body">' +
        '<div class="d-flex justify-content-between mb-2">' +
        '<div><div class="fw-semibold">' + esc(shutter.name) + "</div>" +
        '<div class="small text-body-secondary">' + esc(shutter.room || "") + "</div></div>" +
        '<i class="bi bi-window device-icon text-primary"></i></div>' +
        '<div class="progress position-bar mb-2"><div class="progress-bar" style="width:' + Number(position) + '%"></div></div>' +
        '<div class="btn-group w-100 btn-group-sm">' +
        '<button class="btn btn-outline-primary shutter-cmd" data-cmd="open"><i class="bi bi-chevron-up"></i></button>' +
        '<button class="btn btn-outline-primary shutter-cmd" data-cmd="stop"><i class="bi bi-square"></i></button>' +
        '<button class="btn btn-outline-primary shutter-cmd" data-cmd="favorite"><i class="bi bi-star"></i></button>' +
        '<button class="btn btn-outline-primary shutter-cmd" data-cmd="close"><i class="bi bi-chevron-down"></i></button>' +
        "</div></div></div></div>"
      );
    })
    .join("");
}

function renderLights(lights) {
  const zone = document.getElementById("light-cards");
  zone.innerHTML = lights
    .map((light) => {
      const on = Boolean(light.attributes.on);
      return (
        '<div class="col-6 col-md-4 col-xl-3"><div class="card device-card h-100 ' + (on ? "light-on" : "") +
        '" data-uid="' + esc(light.uid) + '"><div class="card-body d-flex justify-content-between align-items-center">' +
        "<div><div class=\"fw-semibold\">" + esc(light.name) + "</div>" +
        '<div class="small text-body-secondary">' + esc(light.room || "") + "</div></div>" +
        '<div class="form-check form-switch">' +
        '<input class="form-check-input light-toggle" type="checkbox" ' + (on ? "checked" : "") + "></div>" +
        "</div></div></div>"
      );
    })
    .join("");
}

/* Delegation d'evenements pour les commandes */
document.addEventListener("click", async (event) => {
  const command = event.target.closest(".shutter-cmd");
  if (command) {
    const uid = command.closest("[data-uid]").dataset.uid;
    const card = command.closest(".card");
    card.classList.add("shutter-moving");
    try {
      await api("/api/devices/" + encodeURIComponent(uid) + "/command", {
        method: "POST",
        body: JSON.stringify({ command: command.dataset.cmd, params: {} }),
      });
    } catch (error) {
      toast(error.message, "danger");
    } finally {
      setTimeout(() => card.classList.remove("shutter-moving"), 2000);
    }
  }
});

document.addEventListener("change", async (event) => {
  if (event.target.classList.contains("light-toggle")) {
    const uid = event.target.closest("[data-uid]").dataset.uid;
    try {
      await api("/api/devices/" + encodeURIComponent(uid) + "/command", {
        method: "POST",
        body: JSON.stringify({ command: event.target.checked ? "on" : "off", params: {} }),
      });
    } catch (error) {
      toast(error.message, "danger");
    }
  }
});

/* Mises a jour temps reel : patch de l'appareil concerne puis re-rendu */
connectWebSocket((event) => {
  if (event.type === "device_state_changed") {
    const device = state.devices.find((d) => d.uid === event.payload.uid);
    if (device && event.payload.attributes) {
      Object.assign(device.attributes, event.payload.attributes);
      render();
    }
  } else if (event.type === "device_added" || event.type === "device_removed") {
    loadDevices();
  }
});

loadDevices().catch((error) => toast(error.message, "danger"));
