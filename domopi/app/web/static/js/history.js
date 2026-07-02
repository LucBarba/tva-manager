/* DomoPi – page journal d'evenements. */
"use strict";

const TYPE_BADGES = {
  device_state_changed: "primary",
  device_added: "success",
  device_removed: "danger",
  schedule_triggered: "info",
  rf_code_learned: "warning",
  user_login: "secondary",
};

/** Recharge le journal selon le filtre de source. */
async function refresh() {
  const source = document.getElementById("filter-source").value;
  const query = source ? "&source=" + encodeURIComponent(source) : "";
  const events = await api("/api/history/events?limit=200" + query);
  document.getElementById("event-rows").innerHTML = events
    .map(
      (event) =>
        "<tr><td class=\"text-nowrap\">" + new Date(event.timestamp).toLocaleString("fr-FR") + "</td>" +
        "<td>" + esc(event.source) + "</td>" +
        '<td><span class="badge text-bg-' + (TYPE_BADGES[event.event_type] || "secondary") + '">' +
        esc(event.event_type) + "</span></td>" +
        "<td>" + esc(event.message) + "</td></tr>"
    )
    .join("");
}

document.getElementById("filter-source").addEventListener("change", refresh);
document.getElementById("history-refresh").addEventListener("click", refresh);

refresh().catch((error) => toast(error.message, "danger"));
