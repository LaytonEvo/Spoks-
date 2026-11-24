// ---------- Team: admins invite people and set their role (users.py on the server) ----------
const TEAM = { d: null, link: null };

async function renderTeam() {
  $("#main").innerHTML = `<p class="muted">Loading…</p>`;
  try { TEAM.d = await api("/api/team"); } catch (e) { $("#main").innerHTML = `<h1>Team</h1><p>${esc(e.message)}</p>`; return; }
  drawTeam();
}
function drawTeam() {
  const d = TEAM.d;
  const when = (x) => (x ? new Date(x).toLocaleString("en-GB", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" }) : "");
  const roleSel = (u) => `<select data-team-role="${esc(u.name)}" aria-label="Role for ${esc(u.label)}">${d.roles.map((r) => `<option value="${r.key}" ${u.role === r.key ? "selected" : ""}>${esc(r.label)}</option>`).join("")}</select>`;
  const label = (k) => (d.roles.find((r) => r.key === k) || {}).label || k;
  const stat = { active: ["live", "Active"], invited: ["todo", "Invited"], "invite expired": ["skip", "Invite expired"], disabled: ["skip", "Switched off"] };
  const row = (u) => {
    const [cls, txt] = stat[u.status] || ["skip", u.status];
    const mine = u.name === (state.status || {}).user;
    const acts = u.source === "railway" ? `<span class="small muted">Set in Railway</span>`
      : mine ? `<span class="small muted">You</span>`
      : `<button type="button" class="link-btn small" data-team-reinvite="${esc(u.name)}">New invite link</button>
         ${u.status === "disabled" ? `<button type="button" class="link-btn small" data-team-status="${esc(u.name)}" data-to="active">Switch back on</button>`
           : `<button type="button" class="link-btn small" data-team-status="${esc(u.name)}" data-to="disabled">Switch off</button>`}`;
    return `<tr><td><b>${esc(u.label)}</b><br><span class="small muted">${esc(u.name)}</span></td>
      <td>${u.source === "railway" || mine ? esc(label(u.role)) : roleSel(u)}</td>
      <td><span class="stat ${cls}">${txt}</span>${u.invite_expires ? `<br><span class="small muted">Link works until ${esc(when(u.invite_expires))}</span>` : ""}</td>
      <td class="small muted">${u.invited_by ? `Invited by ${esc(u.invited_by)} ${esc(when(u.invited_at))}` : ""}${u.last_sign_in ? `<br>Last signed in ${esc(when(u.last_sign_in))}` : ""}</td>
      <td>${acts}</td></tr>`;
  };
  $("#main").innerHTML = `<p class="eyebrow">Settings</p><h1>Team</h1>
    <p class="muted" style="max-width:88ch">Invite someone and the app gives you a one-time link to send them. They open it and choose their own password, and everything they approve or publish is recorded under their name. The app doesn't email the link: send it yourself, to them only. Links last 7 days and work once.</p>
    ${TEAM.link ? `<div class="panel" style="margin:16px 0"><p><b>Invite link for ${esc(TEAM.link.name)}</b> (works once, until ${esc(when(TEAM.link.expires))}):</p>
      <p style="display:flex;gap:8px;flex-wrap:wrap"><input id="team-link" readonly value="${esc(TEAM.link.url)}" style="flex:1 1 360px;min-width:0" aria-label="Invite link">
      <button type="button" class="btn" id="team-copy">Copy link</button></p>
      <p class="small muted">This is the only time the link is shown. Lost it? Use “New invite link” on their row.</p></div>` : ""}
    <div class="panel" style="margin:16px 0"><h3 style="margin-top:0">Invite someone</h3>
      <form id="team-form" style="display:flex;gap:12px;flex-wrap:wrap;align-items:flex-end">
        <label>Name <input id="team-label" required maxlength="60" placeholder="Luke Smith"></label>
        <label>Sign-in name <input id="team-name" required pattern="[a-z][a-z0-9._\\-]{1,31}" placeholder="luke" title="Lower case, starting with a letter"></label>
        <label>Role <select id="team-role">${d.roles.map((r) => `<option value="${r.key}" ${r.key === "editor" ? "selected" : ""}>${esc(r.label)}</option>`).join("")}</select></label>
        <button type="submit" class="btn">Create invite link</button></form>
      <ul class="small muted" style="margin:12px 0 0">${d.roles.map((r) => `<li><b>${esc(r.label)}:</b> ${esc(r.text)}</li>`).join("")}</ul></div>
    <table class="ag-t" style="width:100%"><thead><tr><th>Person</th><th>Role</th><th>Status</th><th>History</th><th></th></tr></thead>
      <tbody>${d.users.map(row).join("")}</tbody></table>`;
}
document.addEventListener("submit", async (e) => {
  if (e.target.id !== "team-form") return;
  e.preventDefault();
  try {
    const r = await api("/api/team/invite", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ label: $("#team-label").value, name: $("#team-name").value, role: $("#team-role").value }) });
    TEAM.d = r; TEAM.link = r.invite; drawTeam();
  } catch (err) { alert(err.message); }
});
document.addEventListener("click", async (e) => {
  const t = e.target;
  if (t.id === "team-copy") { try { await navigator.clipboard.writeText($("#team-link").value); t.textContent = "Copied"; } catch (err) { $("#team-link").select(); } return; }
  const ri = t.closest("[data-team-reinvite]");
  if (ri) {
    if (!confirm(`Make a new invite link for ${ri.dataset.teamReinvite}? Their current password stops working until they use it.`)) return;
    try { const r = await api(`/api/team/${encodeURIComponent(ri.dataset.teamReinvite)}/reinvite`, { method: "POST" }); TEAM.d = r; TEAM.link = r.invite; drawTeam(); } catch (err) { alert(err.message); }
    return;
  }
  const st = t.closest("[data-team-status]");
  if (st) {
    try { TEAM.d = await api(`/api/team/${encodeURIComponent(st.dataset.teamStatus)}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ status: st.dataset.to }) }); drawTeam(); } catch (err) { alert(err.message); }
  }
});
document.addEventListener("change", async (e) => {
  const s = e.target.closest("[data-team-role]");
  if (!s) return;
  try { TEAM.d = await api(`/api/team/${encodeURIComponent(s.dataset.teamRole)}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ role: s.value }) }); drawTeam(); } catch (err) { alert(err.message); }
});
