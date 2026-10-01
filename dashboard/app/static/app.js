"use strict";
const $ = (sel, el = document) => el.querySelector(sel);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const n = (v) => (v == null ? "–" : Math.round(v).toLocaleString("en-GB"));
const pct = (v) => (v == null ? "–" : (v * 100).toFixed(1) + "%");
const gbp = (v, dp = 0) => (v == null ? "–" : "£" + v.toLocaleString("en-GB", { minimumFractionDigits: dp, maximumFractionDigits: dp }));
const TF_LABEL = { last_30_days: "last 30 days", last_90_days: "last 90 days", last_365_days: "last 12 months" };

const state = { snap: null, status: null, tf: "last_90_days", flowId: null, draftId: null, tab: "journey", search: "", pvId: null, pvWidth: "600", sort: null, show: "all", page: null, cmp: null };
const PAGES = { drafts: "New flows to approve", fixes: "Fixes to approve", programme: "Programme", compare: "Compare", tests: "A/B tests", summary: "Monday summary" };
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
  let html = `<button type="button" class="flow-link" data-id="" ${!state.flowId && !state.page ? 'aria-current="true"' : ""}><span class="fname">All flows overview</span></button>`;
  for (const [k, l] of Object.entries(PAGES)) html += `<a class="flow-link page-link" href="#${k}" ${state.page === k ? 'aria-current="true"' : ""}><span class="fname">${l}</span></a>`;
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

// ---------- judging performance against the account's own flows ----------
const MIN_SENDS = 50;
const COLS = [
  { key: "name", label: "Flow", val: (f) => f.name.toLowerCase() },
  { key: "verdict", label: "Verdict", val: (f, r) => r.get(f.id).verdict.rank },
  { key: "recipients", label: "Sends", val: (f) => totals(f).recipients ?? 0 },
  { key: "open_rate", label: "Open rate", val: (f) => totals(f).open_rate },
  { key: "click_rate", label: "Click rate", val: (f) => totals(f).click_rate },
  { key: "conversions", label: "Orders", val: (f) => totals(f).conversions },
  { key: "revenue", label: "Revenue", val: (f) => totals(f).revenue },
  { key: "rps", label: "Per send", val: (f) => (totals(f).recipients ? totals(f).revenue_per_recipient : null) },
  { key: "trend", label: "Revenue trend", val: (f) => { const t = trendFor(flowWeekly(f), "conversion_value"); return t && t.pct != null ? t.pct : null; } },
  { key: "unsubscribe_rate", label: "Unsub rate", val: (f) => totals(f).unsubscribe_rate },
];
const isPostPurchase = (f) => /placed order|fulfilled|delivered|shipment/i.test(f.trigger || "");
function median(xs) {
  const v = xs.filter((x) => x != null).sort((a, b) => a - b);
  if (!v.length) return null;
  const m = Math.floor(v.length / 2);
  return v.length % 2 ? v[m] : (v[m - 1] + v[m]) / 2;
}
function rateFlows(flows) {
  const eligible = flows.filter((f) => (totals(f).recipients || 0) >= MIN_SENDS);
  const med = {
    open_rate: median(eligible.map((f) => totals(f).open_rate)),
    click_rate: median(eligible.map((f) => totals(f).click_rate)),
    rps: median(eligible.filter((f) => !isPostPurchase(f)).map((f) => totals(f).revenue_per_recipient)),
  };
  const rel = (v, m) => (v == null || !m ? null : v / m);
  const out = new Map();
  for (const f of flows) {
    const t = totals(f), sends = t.recipients || 0, low = sends > 0 && sends < MIN_SENDS;
    const tone = {};
    if (!low && sends) {
      for (const k of ["open_rate", "click_rate"]) {
        const r = rel(t[k], med[k]);
        if (r != null) tone[k] = r >= 1.25 ? "good" : r <= 0.75 ? "poor" : "";
      }
      if (!isPostPurchase(f)) {
        const r = rel(t.revenue_per_recipient, med.rps);
        if (r != null) tone.rps = r >= 1.25 ? "good" : r <= 0.75 ? "poor" : "";
      }
    }
    if (sends && (t.unsubscribe_rate || 0) > 0.01) tone.unsubscribe_rate = "poor";
    else if (sends && (t.unsubscribe_rate || 0) > 0.005) tone.unsubscribe_rate = "warn";
    const c = counts(f);
    let verdict;
    if (f.status !== "live" && !sends) verdict = { label: f.status === "draft" ? "Draft" : "Not live", tone: "off", rank: 6, why: "Not sending to anyone." };
    else if (!sends) verdict = { label: "Not sending", tone: "poor", rank: 0, why: "Live but nobody received a message in this period. Check the trigger and filters." };
    else if (low) verdict = { label: "Too few sends", tone: "off", rank: 5, why: `Under ${MIN_SENDS} sends, so the rates swing too much to judge.` };
    else if ((t.unsubscribe_rate || 0) > 0.01) verdict = { label: "Losing subscribers", tone: "poor", rank: 1, why: "More than 1% of recipients unsubscribed." };
    else {
      const key = isPostPurchase(f) ? "click_rate" : "rps";
      const r = rel(key === "rps" ? t.revenue_per_recipient : t.click_rate, med[key]);
      const what = key === "rps" ? "revenue per send" : "click rate (post-purchase flow)";
      if (r == null) verdict = { label: "No benchmark", tone: "off", rank: 5, why: "Not enough comparable flows." };
      else if (r >= 1.25) verdict = { label: "Strong", tone: "good", rank: 4, why: `${what} is ${r.toFixed(1)}× your typical flow.` };
      else if (r <= 0.75) verdict = { label: "Underperforming", tone: "warn", rank: 2, why: `${what} is ${r.toFixed(2)}× your typical flow.` };
      else verdict = { label: "On par", tone: "", rank: 3, why: `${what} is close to your typical flow.` };
    }
    out.set(f.id, { tone, low, verdict, attention: verdict.rank <= 2 || c.high > 0 });
  }
  return out;
}

function trendCell(f) {
  const w = flowWeekly(f);
  if (!w || !w.conversion_value.some((v) => v)) return `<td class="trend-cell"><span class="muted">–</span></td>`;
  const N = TF_WEEKS[state.tf] || 13;
  return `<td class="trend-cell">${spark(w.conversion_value.slice(-2 * N), { label: `Revenue per week, last ${2 * N} weeks` })} ${chip(trendFor(w, "conversion_value"))}</td>`;
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
  const rated = rateFlows(state.snap.flows);
  let list = state.snap.flows.filter((f) => state.show === "all" || (state.show === "live" ? f.status === "live" : rated.get(f.id).attention));
  if (state.sort) {
    const col = COLS.find((c) => c.key === state.sort.key);
    const dir = state.sort.dir === "asc" ? 1 : -1;
    list = list.slice().sort((a, b) => {
      const va = col.val(a, rated), vb = col.val(b, rated);
      if (va == null && vb == null) return 0;
      if (va == null) return 1;
      if (vb == null) return -1;
      return (typeof va === "string" ? va.localeCompare(vb) : va - vb) * dir;
    });
  }
  const rows = list.map((f) => {
    const t = totals(f), r = rated.get(f.id);
    const cell = (k, v) => `<td class="${r.tone[k] || ""}${r.low ? " low" : ""}">${v}</td>`;
    return `<tr data-id="${esc(f.id)}"><td><span class="fname">${esc(f.name)}</span> ${pill(f.status)}</td>
      <td class="verdict-cell"><span class="verdict ${r.verdict.tone}" title="${esc(r.verdict.why)}">${esc(r.verdict.label)}</span></td>
      ${cell("recipients", n(t.recipients))}${cell("open_rate", pct(t.open_rate))}${cell("click_rate", pct(t.click_rate))}${cell("conversions", n(t.conversions))}
      ${cell("revenue", gbp(t.revenue))}${cell("rps", t.recipients ? gbp(t.revenue_per_recipient, 2) : "–")}${trendCell(f)}${cell("unsubscribe_rate", pct(t.unsubscribe_rate))}<td>${dots(counts(f))}</td></tr>`;
  }).join("");
  const head = COLS.map((c) => {
    const on = state.sort && state.sort.key === c.key;
    const aria = on ? (state.sort.dir === "asc" ? "ascending" : "descending") : "none";
    return `<th aria-sort="${aria}"><button type="button" class="sort-btn" data-sort="${c.key}">${c.label}<span class="arrow" aria-hidden="true">${on ? (state.sort.dir === "asc" ? "▲" : "▼") : "↕"}</span></button></th>`;
  }).join("");
  const nAttention = state.snap.flows.filter((f) => rated.get(f.id).attention).length;
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
    <div class="table-bar">
      <div class="seg seg-light" id="show" role="group" aria-label="Show">
        ${[["all", "All flows"], ["live", "Live"], ["attention", `Needs work (${nAttention})`]].map(([k, l]) => `<button type="button" data-show="${k}" aria-pressed="${state.show === k}">${l}</button>`).join("")}
      </div>
      <p class="legend"><span class="sw good"></span>well above your typical flow <span class="sw poor"></span>well below, or unsubscribes over the limit <span class="sw lowv"></span>under ${MIN_SENDS} sends, too few to judge</p>
    </div>
    <div class="panel table-wrap"><table class="flows">
      <thead><tr>${head}<th>Checks</th></tr></thead>
      <tbody>${rows || `<tr><td colspan="11" class="muted">No flows match.</td></tr>`}</tbody></table></div>
    <p class="muted" style="margin-top:10px">“Typical flow” is the median of your own flows with ${MIN_SENDS}+ sends in this period, not an industry figure. Well above means at least 1.25× the median; well below means 0.75× or less. Post-purchase flows (triggered by an order or delivery) are judged on clicks, not revenue. Revenue trend compares the last ${TF_WEEKS[state.tf] || 13} full weeks with the ${TF_WEEKS[state.tf] || 13} before. Sends count every email and SMS delivered, not unique people. Revenue is what Klaviyo attributes to each message from Placed Order.</p>`;
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
    ${body}${m.draft ? "" : metricRow(m) + messageTrend(m) + abTable(m)}${flagList(flags, true)}
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
  if (ms.some((m) => m.draft)) return `<span class="muted num">${ms.length} message${ms.length === 1 ? "" : "s"}</span>`;
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
    else if (s.split_type === "conditional-split") paths = [{ name: s.branches[0].label, cond: s.label, steps: s.branches[0].steps }, { name: s.branches[1].label, cond: "", steps: s.branches[1].steps }];
    else paths = s.branches.map((b) => ({ name: b.label, cond: b.condition || "", steps: b.steps }));
    const intro = s.split_type === "trigger-split" ? `Splits into ${paths.length} paths by what was in the basket or order`
      : s.split_type === "conditional-split" ? `Split: <b>${esc(s.label)}</b>` : `Split: <b>${esc(s.label)}</b>`;
    const openAt = Math.max(0, paths.findIndex((p) => [...messages(p.steps)].length));  // first path that sends something
    return `<div class="split"><p class="split-label">${intro}</p>${paths.map((p, i) => `
      <details class="path" ${i === openAt ? "open" : ""}><summary><span class="path-name">${esc(p.name)}</span>${pathSummary(p.steps)}
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
    ${flowTrendPanel(f)}
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
  if (state.draftId && draftState.current) {
    const d = draftState.current;
    return [{ name: d.flow_name }, [...messages(d.steps)].find((x) => x.message_id === messageId)];
  }
  const f = state.snap.flows.find((x) => x.id === state.flowId);
  return [f, f && [...messages(f.steps)].find((x) => x.message_id === messageId)];
}
function previewNote(m) {
  if (m.draft) return "How the email will look. Names show as “Sam”; in Klaviyo each person sees their own name, or none.";
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
  const src = m.preview_url || `/render/${encodeURIComponent(messageId)}`;
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
  $("#pv-frame").src = m.preview_url || `/render/${encodeURIComponent(messageId)}`;
  $("#preview").hidden = false;
  $("#pv-close").focus();
}
function closePreview() { $("#preview").hidden = true; $("#pv-frame").src = "about:blank"; }

// ---------- routing and events ----------
function render() {
  document.querySelectorAll("#period button").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.tf === state.tf)));
  document.querySelectorAll("#period button").forEach((b) => { b.disabled = !state.snap.timeframes.includes(b.dataset.tf); b.title = b.disabled ? "Not in this snapshot yet" : ""; });
  renderSidebar();
  if (state.page === "drafts") (state.draftId ? renderDraft() : renderDrafts());
  else if (state.page === "fixes") renderFixes();
  else if (state.page === "programme") renderProgramme();
  else if (state.page === "compare") renderCompare();
  else if (state.page === "tests") renderTests();
  else if (state.page === "summary") renderSummary();
  else if (state.flowId) renderFlow(); else renderOverview();
}
function route() {
  const pg = /^#(\w+)$/.exec(location.hash);
  state.page = pg && PAGES[pg[1]] ? pg[1] : null;
  const dm = /^#draft\/([a-z0-9-]+)/.exec(location.hash);
  state.draftId = dm ? dm[1] : null;
  if (state.draftId) state.page = "drafts";
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
  const link = e.target.closest(".flow-link:not(.page-link), table.flows tr[data-id]");
  if (link) { location.hash = link.dataset.id ? `#flow/${link.dataset.id}` : ""; if (!link.dataset.id) route(); return; }
  const tab = e.target.closest("[data-tab]");
  if (tab) { location.hash = `#flow/${state.flowId}/${tab.dataset.tab}`; return; }
  const pv = e.target.closest("[data-preview]");
  if (pv) { openPreview(pv.dataset.preview); return; }
  const pw = e.target.closest("#pane-width button");
  if (pw) { state.pvWidth = pw.dataset.w; showInPane(state.pvId); return; }
  const card = e.target.closest(".msg[data-pick]");
  if (card && WIDE.matches && !e.target.closest("a, button, summary")) { showInPane(card.dataset.pick); return; }
  const sb = e.target.closest("[data-sort]");
  if (sb) {
    const k = sb.dataset.sort, cur = state.sort;
    const firstDir = k === "name" || k === "verdict" ? "asc" : "desc";
    state.sort = !cur || cur.key !== k ? { key: k, dir: firstDir } : cur.dir === firstDir ? { key: k, dir: firstDir === "asc" ? "desc" : "asc" } : null;
    renderOverview(); $(`[data-sort="${k}"]`).focus(); return;
  }
  const sh = e.target.closest("[data-show]");
  if (sh) { state.show = sh.dataset.show; renderOverview(); return; }
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

WIDE.addEventListener("change", () => { if (state.snap && state.draftId) renderDraft(); else if (state.snap && state.flowId && state.tab === "journey") renderFlow(); });
