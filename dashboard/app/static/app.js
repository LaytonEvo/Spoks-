"use strict";
const $ = (sel, el = document) => el.querySelector(sel);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const n = (v) => (v == null ? "–" : Math.round(v).toLocaleString("en-GB"));
const pct = (v) => (v == null ? "–" : (v * 100).toFixed(1) + "%");
const gbp = (v, dp = 0) => (v == null ? "–" : "£" + v.toLocaleString("en-GB", { minimumFractionDigits: dp, maximumFractionDigits: dp }));
const TF_LABEL = { last_30_days: "last 30 days", last_90_days: "last 90 days", last_365_days: "last 12 months" };

const state = { snap: null, status: null, tf: "last_90_days", flowId: null, tab: "journey", search: "", pvId: null, pvWidth: "600" };
const WIDE = window.matchMedia("(min-width: 1200px)");
try { state.tf = localStorage.getItem("eg-tf") || state.tf; } catch (e) { /* storage unavailable */ }

async function api(path, opts) {
  const r = await fetch(path, opts);
  if (!r.ok) {
    let msg = r.statusText;
    try { msg = (await r.json()).detail || msg; } catch (e) { /* not JSON */ }
    throw new Error(msg);
  }
  return r.json();
}

// ---------- helpers over the snapshot ----------
function* messages(steps) {
  for (const s of steps) {
    if (s.kind === "email" || s.kind === "sms") yield s;
    else if (s.kind === "split") for (const b of s.branches) yield* messages(b.steps);
  }
}
function counts(flow) {
  const c = { high: 0, medium: 0 };
  const add = (list) => (list || []).forEach((f) => { if (c[f.level] != null) c[f.level] += 1; });
  add((flow.flags || {})[state.tf]);
  for (const m of messages(flow.steps)) add((m.flags || {})[state.tf]);
  return c;
}
const totals = (flow) => (flow.totals || {})[state.tf] || {};
const mstats = (m) => (m.metrics || {})[state.tf];
function dots(c) {
  return `<span class="dots">${c.high ? `<span class="dot high" title="${c.high} high">${c.high}</span>` : ""}${c.medium ? `<span class="dot medium" title="${c.medium} to check">${c.medium}</span>` : ""}</span>`;
}
function pill(status) { return `<span class="pill ${esc(status)}">${esc(status)}</span>`; }
function flagList(list, inline) {
  if (!list || !list.length) return "";
  const html = list.map((f) => `<div class="flag ${esc(f.level)}">${esc(f.text)}</div>`).join("");
  return inline ? `<div class="flags-inline">${html}</div>` : html;
}

// ---------- sidebar ----------
function renderSidebar() {
  const nav = $("#flow-list");
  const q = state.search.toLowerCase();
  const groups = [["live", "Live"], ["manual", "Manual"], ["draft", "New drafts"]];
  let html = `<button type="button" class="flow-link" data-id="" ${!state.flowId ? 'aria-current="true"' : ""}><span class="fname">All flows overview</span></button>`;
  for (const [status, label] of groups) {
    const flows = state.snap.flows.filter((f) => f.status === status && f.name.toLowerCase().includes(q));
    if (!flows.length) continue;
    html += `<p class="group-label">${label} · ${flows.length}</p>`;
    for (const f of flows) {
      const t = totals(f);
      html += `<button type="button" class="flow-link" data-id="${esc(f.id)}" ${state.flowId === f.id ? 'aria-current="true"' : ""}>
        <span class="fname">${esc(f.name)}</span>
        <span class="fmeta num">${n(t.recipients)} sends · ${gbp(t.revenue)}${dots(counts(f))}</span></button>`;
    }
  }
  nav.innerHTML = html;
}

// ---------- overview ----------
function renderOverview() {
  const live = state.snap.flows.filter((f) => f.status === "live");
  const sum = (k) => live.reduce((a, f) => a + (totals(f)[k] || 0), 0);
  const sends = sum("recipients"), revenue = sum("revenue"), orders = sum("conversions");
  const highs = [];
  for (const f of live) {
    for (const x of (f.flags[state.tf] || [])) if (x.level === "high") highs.push({ f, text: x.text });
    for (const m of messages(f.steps)) for (const x of ((m.flags || {})[state.tf] || [])) if (x.level === "high") highs.push({ f, m, text: x.text });
  }
  const rows = state.snap.flows.map((f) => {
    const t = totals(f);
    return `<tr data-id="${esc(f.id)}"><td><span class="fname">${esc(f.name)}</span> ${pill(f.status)}</td>
      <td>${n(t.recipients)}</td><td>${pct(t.open_rate)}</td><td>${pct(t.click_rate)}</td><td>${n(t.conversions)}</td>
      <td>${gbp(t.revenue)}</td><td>${t.recipients ? gbp(t.revenue_per_recipient, 2) : "–"}</td><td>${pct(t.unsubscribe_rate)}</td><td>${dots(counts(f))}</td></tr>`;
  }).join("");
  $("#main").innerHTML = `
    <p class="eyebrow">All flows · ${esc(TF_LABEL[state.tf])}</p>
    <h1>How the flows are doing</h1>
    <div class="kpis">
      <div class="kpi"><div class="label">Live flows</div><div class="value">${live.length}</div></div>
      <div class="kpi"><div class="label">Sends</div><div class="value">${n(sends)}</div></div>
      <div class="kpi"><div class="label">Orders attributed</div><div class="value">${n(orders)}</div></div>
      <div class="kpi"><div class="label">Revenue attributed</div><div class="value">${gbp(revenue)}</div></div>
      <div class="kpi"><div class="label">Revenue per send</div><div class="value">${sends ? gbp(revenue / sends, 2) : "–"}</div></div>
    </div>
    ${highs.length ? `<div class="panel" style="margin-bottom:18px"><h2>Needs attention now</h2><p class="muted" style="margin:4px 0 8px">High-priority checks across live flows.</p>
      ${highs.slice(0, 12).map((h) => `<div class="flag high"><span><b>${esc(h.f.name)}</b>${h.m ? ` · ${esc(h.m.name)}` : ""}: ${esc(h.text)}</span></div>`).join("")}
      ${highs.length > 12 ? `<p class="muted">+ ${highs.length - 12} more in the individual flows.</p>` : ""}</div>` : ""}
    <div class="panel table-wrap"><table class="flows">
      <thead><tr><th>Flow</th><th>Sends</th><th>Open rate</th><th>Click rate</th><th>Orders</th><th>Revenue</th><th>Per send</th><th>Unsub rate</th><th>Checks</th></tr></thead>
      <tbody>${rows}</tbody></table></div>
    <p class="muted" style="margin-top:10px">Sends count every email and SMS delivered, not unique people. Revenue is what Klaviyo attributes to each message from Placed Order.</p>`;
}

// ---------- flow view ----------
function metricRow(m) {
  const s = mstats(m);
  if (!s) return `<div class="metrics"><div class="metric"><div class="l">Performance</div><div class="v">No sends in this period</div></div></div>`;
  const cells = [["Sends", n(s.recipients)]];
  if (m.kind === "email") cells.push(["Open rate", pct(s.open_rate)]);
  cells.push(["Click rate", pct(s.click_rate)], ["Orders", n(s.conversions)], ["Revenue", gbp(s.conversion_value)],
    ["Per send", gbp(s.revenue_per_recipient, 2)], ["Unsub rate", pct(s.unsubscribe_rate), (s.unsubscribe_rate || 0) > 0.005]);
  return `<div class="metrics">${cells.map(([l, v, bad]) => `<div class="metric"><div class="l">${l}</div><div class="v ${bad ? "bad" : ""}">${v}</div></div>`).join("")}</div>`;
}
function abTable(m) {
  const ab = m.ab_test;
  if (!ab) return "";
  const rows = ab.variations.map((v, i) => {
    const s = mstats(v) || {};
    return `<tr><td>${String.fromCharCode(65 + i)}: ${esc(v.subject)}</td><td>${v.share != null ? Math.round(v.share * 100) + "%" : "–"}</td><td>${n(s.recipients)}</td><td>${pct(s.open_rate)}</td><td>${pct(s.click_rate)}</td><td>${gbp(s.conversion_value)}</td></tr>`;
  }).join("");
  return `<div class="ab"><p class="muted" style="margin:0 0 4px">A/B test (${esc(ab.status)}${ab.winner_metric ? `, winner by ${esc(ab.winner_metric.replace("-", " "))}` : ""})</p>
    <table><thead><tr><th>Variation</th><th>Share</th><th>Sends</th><th>Open</th><th>Click</th><th>Revenue</th></tr></thead><tbody>${rows}</tbody></table></div>`;
}
function msgCard(m) {
  const flags = (m.flags || {})[state.tf];
  const body = m.kind === "sms"
    ? `<div class="sms-body">${esc(m.body)}</div>`
    : `<p class="msg-subject">${esc(m.subject || "(no subject)")}</p>${m.preview_text ? `<p class="msg-preview">${esc(m.preview_text)}</p>` : ""}`;
  const pick = m.kind === "email" ? ` data-pick="${esc(m.message_id)}"` : "";
  return `<article class="msg${m.message_id === state.pvId && WIDE.matches ? " selected" : ""}"${pick}>
    <div class="msg-top"><span class="chan ${m.kind}">${m.kind.toUpperCase()}</span><span class="msg-name">${esc(m.name)}</span>
      ${m.status && m.status !== "live" ? pill(m.status) : ""}${m.from_label && m.kind === "email" ? `<span class="msg-from">from ${esc(m.from_label)}</span>` : ""}</div>
    ${body}${metricRow(m)}${abTable(m)}${flagList(flags, true)}
    ${m.kind === "email" ? `<div class="msg-actions"><button type="button" class="link-btn" data-preview="${esc(m.message_id)}">Preview email →</button></div>` : ""}
  </article>`;
}
function pathName(steps, fallback) {
  const first = [...messages(steps)][0];
  if (!first) return fallback;
  const m = /—\s*([A-Za-z &]+?)(\s*\(|$)/.exec(first.name || "");
  return m ? m[1].trim() : fallback;
}
function pathSummary(steps) {
  const ms = [...messages(steps)];
  const sends = ms.reduce((a, m) => a + ((mstats(m) || {}).recipients || 0), 0);
  const rev = ms.reduce((a, m) => a + ((mstats(m) || {}).conversion_value || 0), 0);
  return `<span class="muted num">${ms.length} message${ms.length === 1 ? "" : "s"} · ${n(sends)} sends · ${gbp(rev)}</span>`;
}
function flattenChain(split) {
  // A chain of yes/no splits of the same kind ("Trolleys? else Clubs? else Bags? ...") becomes named paths.
  const out = [];
  let cur = split, i = 1;
  while (cur) {
    const [yes, no] = cur.branches;
    out.push({ name: pathName(yes.steps, `Path ${i}`), cond: cur.label, steps: yes.steps });
    const next = no.steps.length === 1 && no.steps[0].kind === "split" && no.steps[0].split_type === split.split_type ? no.steps[0] : null;
    if (!next) { out.push({ name: "Everything else", cond: "Anyone not matched above", steps: no.steps }); break; }
    cur = next; i += 1;
  }
  return out;
}
function renderSteps(steps) {
  if (!steps.length) return `<div class="empty">Ends here.</div>`;
  return steps.map((s) => {
    if (s.kind === "email" || s.kind === "sms") return msgCard(s);
    if (s.kind === "delay") return `<div class="step-delay">⏱ ${esc(s.label)}</div>`;
    if (s.kind === "update") return `<div class="step-update">${esc(s.label)}</div>`;
    if (s.kind === "other") return `<div class="step-update">${esc(s.label)}</div>`;
    let paths;
    if (s.split_type === "trigger-split") paths = flattenChain(s);
    else if (s.split_type === "conditional-split") paths = [{ name: "Yes", cond: s.label, steps: s.branches[0].steps }, { name: "No", cond: "", steps: s.branches[1].steps }];
    else paths = s.branches.map((b) => ({ name: b.label, cond: b.condition || "", steps: b.steps }));
    const intro = s.split_type === "trigger-split" ? `Splits into ${paths.length} paths by what was in the basket or order`
      : s.split_type === "conditional-split" ? `Split: <b>${esc(s.label)}</b>` : `Split: <b>${esc(s.label)}</b>`;
    return `<div class="split"><p class="split-label">${intro}</p>${paths.map((p, i) => `
      <details class="path" ${i === 0 ? "open" : ""}><summary><span class="path-name">${esc(p.name)}</span>${pathSummary(p.steps)}
        ${p.cond && s.split_type === "trigger-split" ? `<span class="path-cond">${esc(p.cond)}</span>` : ""}</summary>
        <div class="path-body">${renderSteps(p.steps)}</div></details>`).join("")}</div>`;
  }).join("");
}

function renderFlow() {
  const f = state.snap.flows.find((x) => x.id === state.flowId);
  if (!f) { state.flowId = null; return renderOverview(); }
  const t = totals(f);
  const re = f.reentry ? `Re-entry: ${f.reentry.unit === "alltime" ? "once ever" : `after ${f.reentry.duration} ${f.reentry.unit}s`}.` : "";
  $("#main").innerHTML = `
    <div class="flow-head"><div>
      <p class="eyebrow">${esc(TF_LABEL[state.tf])} · updated in Klaviyo ${esc((f.updated || "").slice(0, 10))}</p>
      <h1>${esc(f.name)} ${pill(f.status)}</h1>
      <p class="meta">${esc(f.trigger)}.${f.flow_filter ? ` Only if: ${esc(f.flow_filter)}.` : ""} ${esc(re)}</p></div>
      <a href="https://www.klaviyo.com/flow/${esc(f.id)}/edit" target="_blank" rel="noopener">Open in Klaviyo ↗</a></div>
    <div class="kpis">
      <div class="kpi"><div class="label">Sends</div><div class="value">${n(t.recipients)}</div></div>
      <div class="kpi"><div class="label">Open rate (email)</div><div class="value">${pct(t.open_rate)}</div></div>
      <div class="kpi"><div class="label">Click rate</div><div class="value">${pct(t.click_rate)}</div></div>
      <div class="kpi"><div class="label">Orders</div><div class="value">${n(t.conversions)}</div></div>
      <div class="kpi"><div class="label">Revenue</div><div class="value">${gbp(t.revenue)}</div></div>
      <div class="kpi"><div class="label">Revenue per send</div><div class="value">${t.recipients ? gbp(t.revenue_per_recipient, 2) : "–"}</div></div>
    </div>
    ${(f.flags[state.tf] || []).length ? `<div class="panel"><h3>Flow checks</h3>${flagList(f.flags[state.tf])}</div>` : ""}
    <div class="tabs" role="tablist">
      ${[["journey", "Journey"], ["review", "Review"], ["notes", "Notes"]].map(([k, l]) => `<button type="button" role="tab" data-tab="${k}" aria-selected="${state.tab === k}">${l}</button>`).join("")}
    </div>
    <section id="tab-body"></section>`;
  renderTab(f);
}

async function renderTab(f) {
  const el = $("#tab-body");
  if (state.tab === "journey") {
    const emails = [...messages(f.steps)].filter((m) => m.kind === "email");
    if (!emails.some((m) => m.message_id === state.pvId)) state.pvId = emails[0] ? emails[0].message_id : null;
    el.innerHTML = `<div class="journey-wrap"><div class="journey">${renderSteps(f.steps)}</div>
      <aside class="pane" aria-label="Email preview">${state.pvId ? `
        <div class="pane-head"><div><p class="eyebrow" id="pane-name"></p><h3 id="pane-subject"></h3></div>
          <div class="seg seg-light" id="pane-width"><button type="button" data-w="600">Desktop</button><button type="button" data-w="375">Phone</button></div></div>
        <p class="sample-note" id="pane-note"></p>
        <div class="frame-wrap"><iframe id="pane-frame" title="Email preview" sandbox=""></iframe></div>` : `<p class="muted" style="padding:16px">No emails in this flow.</p>`}
      </aside></div>`;
    if (state.pvId) showInPane(state.pvId);
    return;
  }
  if (state.tab === "review") {
    el.innerHTML = `<p class="muted">Loading…</p>`;
    const rec = await api(`/api/reviews/${f.id}`).catch(() => ({}));
    const enabled = state.status && state.status.reviews_enabled;
    const btn = `<button type="button" class="btn" id="make-review" ${enabled ? "" : "disabled"}>${rec.review ? "Rewrite with the latest numbers" : "Write a review"}</button>
      ${enabled ? "" : `<p class="muted">Reviews need a Claude API key (ANTHROPIC_API_KEY) on the server.</p>`}`;
    if (!rec.review) { el.innerHTML = `<div class="review-grid"><p>Claude reads this flow's emails, timings and numbers for the ${esc(TF_LABEL[state.tf])}, checks them against your rules and suggests what to change.</p>${btn}</div>`; return; }
    const r = rec.review;
    el.innerHTML = `<div class="review-grid">
      <p class="eyebrow">Written ${esc(rec.generated_at.slice(0, 16).replace("T", " "))} · using the ${esc(TF_LABEL[rec.timeframe] || rec.timeframe)}</p>
      <h2>${esc(r.headline)}</h2>
      ${r.what_is_working.length ? `<div class="panel"><h3>What's working</h3><ul>${r.what_is_working.map((x) => `<li>${esc(x)}</li>`).join("")}</ul></div>` : ""}
      ${r.issues.map((i) => `<div class="issue ${esc(i.priority)}"><p class="where">${esc(i.priority.toUpperCase())} · ${esc(i.where)}</p>
        <p><b>${esc(i.finding)}</b></p><p class="muted">${esc(i.evidence)}</p><p>→ ${esc(i.recommendation)}</p></div>`).join("")}
      <div class="panel"><h3>Next test to run</h3><p>${esc(r.next_test)}</p></div>${btn}</div>`;
    return;
  }
  const notes = await api(`/api/notes/${f.id}`).catch(() => []);
  let name = "";
  try { name = localStorage.getItem("eg-name") || ""; } catch (e) { /* storage unavailable */ }
  el.innerHTML = `<div style="max-width:700px">${notes.length ? notes.slice().reverse().map((x) => `<div class="note"><div class="who">${esc(x.author)} · ${esc(x.at.slice(0, 16).replace("T", " "))}</div><div>${esc(x.text)}</div></div>`).join("") : `<p class="muted">No notes yet. Use this for decisions and things to try on this flow.</p>`}
    <form class="note-form" id="note-form"><label>Your name<input id="note-author" value="${esc(name)}" autocomplete="name"></label>
    <label>Note<textarea id="note-text" required></textarea></label><div><button class="btn" type="submit">Add note</button></div></form></div>`;
}

// ---------- preview ----------
function findMessage(messageId) {
  const f = state.snap.flows.find((x) => x.id === state.flowId);
  return [f, f && [...messages(f.steps)].find((x) => x.message_id === messageId)];
}
function previewNote(m) {
  return m.render_mode === "unpersonalised"
    ? "Klaviyo won’t fill in this template without a real customer, so it shows the default text instead. Product details stay blank, and every version of any conditional section appears."
    : "Rendered with an example basket and the name “Sam”, not a real customer.";
}
function showInPane(messageId) {
  const [, m] = findMessage(messageId);
  if (!m || !$("#pane-frame")) return;
  state.pvId = messageId;
  document.querySelectorAll(".msg[data-pick]").forEach((c) => c.classList.toggle("selected", c.dataset.pick === messageId));
  $("#pane-name").textContent = m.name;
  $("#pane-subject").textContent = m.subject || "(no subject)";
  $("#pane-note").textContent = previewNote(m);
  document.querySelectorAll("#pane-width button").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.w === state.pvWidth)));
  const fr = $("#pane-frame");
  fr.style.width = state.pvWidth + "px";
  const src = `/render/${encodeURIComponent(messageId)}`;
  if (fr.getAttribute("src") !== src) fr.src = src;
}
function openPreview(messageId) {
  if (WIDE.matches && $("#pane-frame")) { showInPane(messageId); return; }
  const [f, m] = findMessage(messageId);
  if (!m) return;
  $("#pv-eyebrow").textContent = f.name;
  $("#pv-title").textContent = m.subject || m.name;
  $("#pv-sub").textContent = [m.from_label && `From ${m.from_label}`, m.preview_text].filter(Boolean).join(" · ");
  $("#pv-note").textContent = previewNote(m);
  $("#pv-frame").src = `/render/${encodeURIComponent(messageId)}`;
  $("#preview").hidden = false;
  $("#pv-close").focus();
}
function closePreview() { $("#preview").hidden = true; $("#pv-frame").src = "about:blank"; }

// ---------- routing and events ----------
function render() {
  document.querySelectorAll("#period button").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.tf === state.tf)));
  document.querySelectorAll("#period button").forEach((b) => { b.disabled = !state.snap.timeframes.includes(b.dataset.tf); b.title = b.disabled ? "Not in this snapshot yet" : ""; });
  renderSidebar();
  if (state.flowId) renderFlow(); else renderOverview();
}
function route() {
  const m = /^#flow\/(\w+)(?:\/(\w+))?/.exec(location.hash);
  state.flowId = m ? m[1] : null;
  state.tab = (m && m[2]) || "journey";
  if (state.snap) { render(); $("#main").focus({ preventScroll: true }); }
}
function setStatusText() {
  const s = state.status || {};
  const when = s.generated_at ? new Date(s.generated_at).toLocaleString("en-GB", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" }) : "never";
  $("#refreshed").textContent = s.running ? `Refreshing: ${s.step}` : s.error ? `Refresh failed: ${s.error}` : `Data from ${s.source === "fixtures" ? "saved test data" : "Klaviyo"}, ${when}`;
  $("#refresh").disabled = !!s.running;
}
async function pollStatus() {
  state.status = await api("/api/status");
  setStatusText();
  if (state.status.running) setTimeout(pollStatus, 3000);
  else if (state.snap && state.status.generated_at !== state.snap.generated_at) { state.snap = await api("/api/snapshot"); render(); }
}

document.addEventListener("click", async (e) => {
  const link = e.target.closest(".flow-link, table.flows tr[data-id]");
  if (link) { location.hash = link.dataset.id ? `#flow/${link.dataset.id}` : ""; if (!link.dataset.id) route(); return; }
  const tab = e.target.closest("[data-tab]");
  if (tab) { location.hash = `#flow/${state.flowId}/${tab.dataset.tab}`; return; }
  const pv = e.target.closest("[data-preview]");
  if (pv) { openPreview(pv.dataset.preview); return; }
  const pw = e.target.closest("#pane-width button");
  if (pw) { state.pvWidth = pw.dataset.w; showInPane(state.pvId); return; }
  const card = e.target.closest(".msg[data-pick]");
  if (card && WIDE.matches && !e.target.closest("a, button, summary")) { showInPane(card.dataset.pick); return; }
  const tf = e.target.closest("#period button");
  if (tf && !tf.disabled) { state.tf = tf.dataset.tf; try { localStorage.setItem("eg-tf", state.tf); } catch (err) { /* ignore */ } render(); return; }
  const w = e.target.closest("#pv-width button");
  if (w) { document.querySelectorAll("#pv-width button").forEach((b) => b.setAttribute("aria-pressed", String(b === w))); $("#pv-frame").style.width = w.dataset.w + "px"; return; }
  if (e.target.id === "pv-close" || e.target.id === "preview") { closePreview(); return; }
  if (e.target.id === "home-link") { e.preventDefault(); location.hash = ""; route(); return; }
  if (e.target.id === "refresh") { await api("/api/refresh", { method: "POST" }); pollStatus(); return; }
  if (e.target.id === "make-review") {
    const btn = e.target; btn.disabled = true; btn.textContent = "Writing the review (up to a minute)…";
    try { await api(`/api/reviews/${state.flowId}?tf=${state.tf}`, { method: "POST" }); }
    catch (err) { alertInline(btn, err.message); return; }
    renderFlow();
  }
});
function alertInline(btn, msg) { btn.disabled = false; btn.textContent = "Try again"; btn.insertAdjacentHTML("afterend", `<p class="flag high">${esc(msg)}</p>`); }
document.addEventListener("submit", async (e) => {
  if (e.target.id !== "note-form") return;
  e.preventDefault();
  const author = $("#note-author").value, text = $("#note-text").value;
  try { localStorage.setItem("eg-name", author); } catch (err) { /* ignore */ }
  await api(`/api/notes/${state.flowId}`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ author, text }) });
  renderFlow();
});
document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !$("#preview").hidden) closePreview(); });
$("#search").addEventListener("input", (e) => { state.search = e.target.value; renderSidebar(); });
window.addEventListener("hashchange", route);

(async function start() {
  state.status = await api("/api/status");
  setStatusText();
  state.snap = await api("/api/snapshot");
  if (!state.snap.timeframes.includes(state.tf)) state.tf = state.snap.timeframes[0] || "last_90_days";
  route();
  if (!state.snap.flows.length || state.status.running) pollStatus();
})();

WIDE.addEventListener("change", () => { if (state.snap && state.flowId && state.tab === "journey") renderFlow(); });
