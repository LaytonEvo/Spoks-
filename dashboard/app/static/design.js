"use strict";
// Design controls shared by the Brand theme page and the email editor's "Design" panel, plus the Brand theme page.
const DS = { doc: null, theme: null, key: null, audience: "non", width: "600", checkTimer: null };

function dsMerge(base, over) {
  const out = JSON.parse(JSON.stringify(base));
  for (const [k, v] of Object.entries(over || {})) {
    if (k === "colours") out.colours = { ...out.colours, ...v };
    else if (v != null) out[k] = v;
  }
  return out;
}
function dsDiff(theme, base) {
  const d = {};
  for (const k of ["font_head", "font_body", "h1", "radius"]) if (theme[k] && theme[k] !== base[k]) d[k] = theme[k];
  const c = {};
  for (const [k, v] of Object.entries(theme.colours || {})) if ((v || "").toUpperCase() !== (base.colours[k] || "").toUpperCase()) c[k] = v;
  if (Object.keys(c).length) d.colours = c;
  return d;
}
// token -> value, mirroring design.values() on the server (minus the @import, which the page loads separately)
function dsValues(theme, stacks) {
  const v = {};
  for (const [k, x] of Object.entries(theme.colours)) v[`c:${k}`] = x;
  for (const [k, x] of Object.entries(stacks.fixed || { white: "#FFFFFF", trust: "#00B67A" })) v[`c:${k}`] = x;
  const h1 = stacks.h1[theme.h1];
  Object.assign(v, { "f:head": stacks.head[theme.font_head], "f:body": stacks.body[theme.font_body], h1: h1[0], h1m: h1[1], h1ml: h1[2], radius: stacks.radius[theme.radius], import: "" });
  return v;
}
function dsFill(html, vals) { return html.replace(/\[\[([a-z_:0-9]+)\]\]/g, (m, k) => (vals[k] != null ? vals[k] : m)); }
function dsLoadFonts(theme, families) {
  const fams = [families[theme.font_head], families[theme.font_body]].filter(Boolean);
  const href = fams.length ? `https://fonts.googleapis.com/css2?${fams.map((f) => `family=${f}`).join("&")}&display=swap` : "";
  let l = document.getElementById("ds-fonts");
  if (!l) { l = document.createElement("link"); l.id = "ds-fonts"; l.rel = "stylesheet"; document.head.appendChild(l); }
  if (href && l.href !== href) l.href = href;
}
// controls: base = what "reset" goes back to (the brand theme for an email; the default for the brand)
function dsControls(theme, opts, base, prefix) {
  const sel = (k, list, label) => `<label>${label} <span class="ds-row"><select data-ds="${k}">${list.map((o) => `<option ${theme[k] === o ? "selected" : ""}>${esc(o)}</option>`).join("")}</select>
      ${base && theme[k] !== base[k] ? `<button type="button" class="link-btn small" data-ds-reset="${k}" title="Back to ${esc(base[k])}">reset</button>` : ""}</span></label>`;
  const col = (c) => `<label class="ds-col"><input type="color" data-ds-col="${c.key}" value="${esc(theme.colours[c.key])}"><span>${esc(c.label)}</span>
      ${base && theme.colours[c.key].toUpperCase() !== base.colours[c.key].toUpperCase() ? `<button type="button" class="link-btn small" data-ds-reset="c:${c.key}">reset</button>` : ""}</label>`;
  return `<div class="ds-controls" data-ds-scope="${prefix}">
    ${sel("font_head", opts.fonts_head, "Headline font")}${sel("font_body", opts.fonts_body, "Body font")}
    ${sel("h1", opts.h1, "Headline size")}${sel("radius", opts.radius, "Button corners")}
    <p class="ds-sub">Colours</p>${opts.colours.map(col).join("")}
    <p class="muted small">Gmail and Outlook don't load web fonts: they show the backup (Georgia for serif headlines, Arial or Helvetica for body text).</p></div>`;
}
function dsRead(scope, theme, base) {
  const t = JSON.parse(JSON.stringify(theme));
  scope.querySelectorAll("[data-ds]").forEach((s) => { t[s.dataset.ds] = s.value; });
  scope.querySelectorAll("[data-ds-col]").forEach((i) => { t.colours[i.dataset.dsCol] = i.value.toUpperCase(); });
  return t;
}
function dsReset(theme, base, what) {
  const t = JSON.parse(JSON.stringify(theme));
  if (what.startsWith("c:")) t.colours[what.slice(2)] = base.colours[what.slice(2)]; else t[what] = base[what];
  return t;
}

// ---------------- Brand theme page ----------------
async function renderTheme() {
  $("#main").innerHTML = `<p class="muted">Loading…</p>`;
  DS.doc = await api("/api/design");
  DS.theme = JSON.parse(JSON.stringify(DS.doc.editing.theme));
  DS.key = DS.key || (DS.doc.emails[0] || {}).key;
  drawTheme();
}
function drawTheme() {
  const d = DS.doc, ed = d.editing, def = { colours: Object.fromEntries(d.options.colours.map((c) => [c.key, c.default])), font_head: "Fraunces", font_body: "Inter", h1: "Large (38px)", radius: "Square (2px)" };
  const changed = Object.keys(dsDiff(DS.theme, d.published)).length > 0;
  const st = { published: ["live", "Published"], draft: ["todo", "Draft, waiting for approval"], approved: ["draft", "Approved, not published"] }[ed.status] || ["skip", ed.status];
  const own = d.emails.filter((e) => Object.keys(e.overrides || {}).length);
  const vrow = (v) => `<li><b>v${v.n}</b> <span class="stat ${{ draft: "todo", approved: "draft", published: "live" }[v.status] || "skip"}">${esc(v.status)}</span>
    <span class="muted small">by ${esc(v.by)} ${esc((v.at || "").slice(0, 16).replace("T", " "))}${v.approved_by ? ` · approved by ${esc(v.approved_by)}` : ""}${v.published_by ? ` · published by ${esc(v.published_by)}` : ""}${v.applied ? ` · applied to ${v.applied.ok} of ${v.applied.total} emails` : ""}</span>
    ${v.status === "draft" ? `<button type="button" class="link-btn" data-th-approve="${v.n}">Approve</button>` : ""}${v.status === "approved" ? `<button type="button" class="link-btn" data-th-publish="${v.n}">Publish to every email</button>` : ""}</li>`;
  $("#main").innerHTML = `<p class="eyebrow">Design</p><h1>Brand theme <span class="stat ${st[0]}">${esc(st[1])}${ed.n ? ` · v${ed.n}` : ""}</span></h1>
    <p class="muted" style="max-width:90ch">Fonts, colours, headline size and button corners for every email. Change them here and preview any email; publishing re-sends every email to Evoflows in the new look. An email can still have its own design (set in its editor), which wins over the theme.</p>
    <div class="ds-wrap">
      <aside class="panel">${dsControls(DS.theme, d.options, def, "brand")}
        <div class="ds-actions"><button type="button" class="btn" id="th-save" ${changed ? "" : "disabled"}>Save draft</button>
          <button type="button" class="btn-line" id="th-default">Back to the original brand</button></div>
        <div id="th-checks">${dsChecksHtml(d.checks)}</div>
        <h3>Versions</h3><ul class="b-versions">${d.versions.map(vrow).join("") || `<li class="muted">No changes yet: the original brand.</li>`}</ul>
        ${own.length ? `<h3>Emails with their own design</h3><ul class="small">${own.map((e) => `<li><a href="#edit/${esc(e.key)}">${esc(e.name)}</a>: ${esc(Object.keys(e.overrides).map((k) => k === "colours" ? Object.keys(e.overrides.colours).join(", ") : k.replace("_", " ")).join(", "))}</li>`).join("")}</ul>` : ""}</aside>
      <div><div class="b-bar"><label>Preview <select id="th-key">${d.emails.map((e) => `<option value="${esc(e.key)}" ${e.key === DS.key ? "selected" : ""}>${esc(e.name)}</option>`).join("")}</select></label>
        <div class="seg seg-light">${[["non", "Not a member"], ["free", "Free"], ["annual", "Annual"]].map(([k, l]) => `<button type="button" data-th-aud="${k}" aria-pressed="${DS.audience === k}">${l}</button>`).join("")}</div>
        <div class="seg seg-light">${[["600", "Desktop"], ["375", "Phone"]].map(([k, l]) => `<button type="button" data-th-w="${k}" aria-pressed="${DS.width === k}">${l}</button>`).join("")}</div></div>
        <div class="b-canvas"><iframe id="th-frame" title="Preview" sandbox="" style="width:${DS.width}px;max-width:100%;height:1500px;border:0;background:#fff;display:block;margin:0 auto"></iframe></div></div>
    </div>`;
  dsPreview();
}
function dsChecksHtml(c) {
  if (!c) return "";
  return `<h3>Readability</h3>${c.warnings.length ? c.warnings.map((w) => `<div class="flag medium">${esc(w)}</div>`).join("") : `<p class="muted small">All text colours pass contrast checks (4.5:1).</p>`}`;
}
async function dsPreview() {
  const f = $("#th-frame"); if (!f) return;
  const r = await fetch("/design/preview", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ key: DS.key, theme: DS.theme, audience: DS.audience }) });
  f.srcdoc = await r.text();
}
function dsThemeChanged() {
  drawTheme();
  clearTimeout(DS.checkTimer);
  DS.checkTimer = setTimeout(async () => { const c = await api("/api/design/check", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ theme: DS.theme }) }); const el = $("#th-checks"); if (el) el.innerHTML = dsChecksHtml(c); }, 300);
}
document.addEventListener("change", (e) => {
  if (state.page === "theme" && e.target.closest('[data-ds-scope="brand"]')) { DS.theme = dsRead(e.target.closest(".ds-controls"), DS.theme); dsThemeChanged(); return; }
  if (e.target.id === "th-key") { DS.key = e.target.value; dsPreview(); }
});
document.addEventListener("click", async (e) => {
  if (state.page !== "theme") return;
  const rs = e.target.closest("[data-ds-reset]");
  if (rs && rs.closest('[data-ds-scope="brand"]')) { const d = DS.doc; const def = { colours: Object.fromEntries(d.options.colours.map((c) => [c.key, c.default])), font_head: "Fraunces", font_body: "Inter", h1: "Large (38px)", radius: "Square (2px)" }; DS.theme = dsReset(DS.theme, def, rs.dataset.dsReset); dsThemeChanged(); return; }
  if (e.target.id === "th-default") { const d = DS.doc; DS.theme = { colours: Object.fromEntries(d.options.colours.map((c) => [c.key, c.default])), font_head: "Fraunces", font_body: "Inter", h1: "Large (38px)", radius: "Square (2px)" }; dsThemeChanged(); return; }
  const au = e.target.closest("[data-th-aud]"); if (au) { DS.audience = au.dataset.thAud; drawTheme(); return; }
  const w = e.target.closest("[data-th-w]"); if (w) { DS.width = w.dataset.thW; drawTheme(); return; }
  if (e.target.id === "th-save") {
    e.target.disabled = true;
    try { await api("/api/design/save", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ theme: DS.theme }) }); renderTheme(); }
    catch (err) { alertInline(e.target, err.message); }
    return;
  }
  const ap = e.target.closest("[data-th-approve]"), pu = e.target.closest("[data-th-publish]");
  if (ap || pu) {
    const n = +(ap || pu).dataset[ap ? "thApprove" : "thPublish"];
    if (pu && !confirm(`Publish brand theme v${n}?\n\nEvery email is re-published to Evoflows in the new look (emails with their own design keep their own settings). Live flows use it from their next send.`)) return;
    (ap || pu).disabled = true; (ap || pu).textContent = pu ? "Publishing to every email…" : "Approving…";
    try { const r = await api(`/api/design/${ap ? "approve" : "publish"}/${n}`, { method: "POST" });
      if (pu) { const bad = (r.results || []).filter((x) => !x.status || x.status >= 400); alert(bad.length ? `Published, but ${bad.length} email(s) failed: ${bad.map((x) => x.key).join(", ")}` : `Published to ${r.results.length} emails.`); }
      renderTheme(); }
    catch (err) { alertInline(ap || pu, err.message); }
  }
});
