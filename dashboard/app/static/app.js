"use strict";
const $ = (sel, el = document) => el.querySelector(sel);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const n = (v) => (v == null ? "–" : Math.round(v).toLocaleString("en-GB"));
const pct = (v) => (v == null ? "–" : (v * 100).toFixed(1) + "%");
const gbp = (v, dp = 0) => (v == null ? "–" : "£" + v.toLocaleString("en-GB", { minimumFractionDigits: dp, maximumFractionDigits: dp }));
const TF_LABEL = { last_30_days: "last 30 days", last_90_days: "last 90 days", last_365_days: "last 12 months" };

const state = { snap: null, status: null, tf: "last_90_days", flowId: null, draftId: null, tab: "journey", search: "", pvId: null, pvWidth: "600", sort: null, show: "evo", page: null, cmp: null };
// Klaviyo-only pages (Fixes, A/B tests, Flow map) are retired from the menu; their code stays for reference.
const PAGES = { drafts: "New flows to approve", programme: "Programme", compare: "Compare", summary: "Monday summary", evoflows: "Engine & events" };
const isEvo = (f) => f && f.platform === "evoflows";
const STATUS_LABEL = { live: "live", off: "switched off", not_pushed: "not pushed", manual: "manual", draft: "draft" };
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
function pill(status) { return `<span class="pill ${esc(status)}">${esc(STATUS_LABEL[status] || status)}</span>`; }
function platformTag(f) { return isEvo(f) ? `<span class="plat evo">Evoflows</span>` : `<span class="plat kl">Klaviyo</span>`; }
function flagList(list, inline) {
  if (!list || !list.length) return "";
  const html = list.map((f) => `<div class="flag ${esc(f.level)}">${esc(f.text)}</div>`).join("");
  return inline ? `<div class="flags-inline">${html}</div>` : html;
}

// ---------- sidebar ----------
function renderSidebar() {
  const nav = $("#flow-list");
  const q = state.search.toLowerCase();
  const grp = (f) => `${isEvo(f) ? "evo" : "klaviyo"}:${f.status}`;
  const emailCount = (f) => new Set([...messages(f.steps)].filter((m) => m.kind === "email").map((m) => m.message_id)).size;
  const link = (f) => {
    const t = totals(f);
    const meta = isEvo(f) && f.status !== "live"
      ? `${f.status === "off" ? "Switched off" : "Not pushed yet"} · ${emailCount(f)} emails`
      : `${n(t.recipients)} sends · ${gbp(t.revenue)}${f.replaced_by ? ` · → ${esc(f.replaced_by.name.split(" ")[0])}` : ""}`;
    return `<button type="button" class="flow-link" data-id="${esc(f.id)}" ${state.flowId === f.id ? 'aria-current="true"' : ""}>
      <span class="fname">${esc(f.name)}</span><span class="fmeta num">${meta}${dots(counts(f))}</span></button>`;
  };
  const section = (groups) => groups.map(([key, label]) => {
    const flows = state.snap.flows.filter((f) => grp(f) === key && f.name.toLowerCase().includes(q));
    return flows.length ? `<p class="group-label">${label} · ${flows.length}</p>${flows.map(link).join("")}` : "";
  }).join("");
  let html = `<button type="button" class="flow-link" data-id="" ${!state.flowId && !state.page ? 'aria-current="true"' : ""}><span class="fname">All flows overview</span></button>`;
  for (const [k, l] of Object.entries(PAGES)) html += `<a class="flow-link page-link" href="#${k}" ${state.page === k ? 'aria-current="true"' : ""}><span class="fname">${l}</span></a>`;
  html += section([["evo:live", "Evoflows · live"], ["evo:off", "Evoflows · built, switched off"], ["evo:not_pushed", "Evoflows · not pushed yet"]]);
  // Klaviyo flows: kept for reference until each is switched off, folded away by default.
  const kl = state.snap.flows.filter((f) => !isEvo(f) && f.name.toLowerCase().includes(q));
  if (kl.length) {
    const viewing = kl.some((f) => f.id === state.flowId);
    let open = viewing || !!q;
    try { open = open || localStorage.getItem("eg-kl-open") === "1"; } catch (e) { /* storage unavailable */ }
    html += `<details class="kl-group" id="kl-group" ${open ? "open" : ""}><summary class="group-label">Klaviyo (being replaced) · ${kl.length}</summary>
      ${section([["klaviyo:live", "Live"], ["klaviyo:manual", "Manual"]])}</details>`;
  }
  nav.innerHTML = html;
}
document.addEventListener("toggle", (e) => {
  if (e.target.id === "kl-group") { try { localStorage.setItem("eg-kl-open", e.target.open ? "1" : "0"); } catch (err) { /* ignore */ } }
}, true);

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
    if (f.status !== "live" && !sends) verdict = { label: { draft: "Draft", off: "Switched off", not_pushed: "Not pushed" }[f.status] || "Not live", tone: "off", rank: 6, why: isEvo(f) ? "Built and checked, waiting to be switched on." : "Not sending to anyone." };
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
  // Headline numbers and "needs attention" follow the platform filter (Evoflows by default).
  const scope = state.show === "evo" ? state.snap.flows.filter(isEvo) : state.show === "klaviyo" ? state.snap.flows.filter((f) => !isEvo(f)) : state.snap.flows;
  const live = scope.filter((f) => f.status === "live");
  const sum = (k) => live.reduce((a, f) => a + (totals(f)[k] || 0), 0);
  const sends = sum("recipients"), revenue = sum("revenue"), orders = sum("conversions");
  const highs = [];
  for (const f of live) {
    for (const x of (f.flags[state.tf] || [])) if (x.level === "high") highs.push({ f, text: x.text });
    for (const m of messages(f.steps)) for (const x of ((m.flags || {})[state.tf] || [])) if (x.level === "high") highs.push({ f, m, text: x.text });
  }
  const rated = rateFlows(state.snap.flows);
  let list = state.snap.flows.filter((f) => state.show === "all" || (state.show === "evo" ? isEvo(f) : state.show === "klaviyo" ? !isEvo(f) : rated.get(f.id).attention));
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
    const na = `<td class="muted" title="Evoflows doesn't track opens or clicks yet">n/a</td>`;
    return `<tr data-id="${esc(f.id)}"><td>${platformTag(f)} <span class="fname">${esc(f.name)}</span> ${pill(f.status)}${f.replaced_by ? `<div class="muted small">Being replaced by ${esc(f.replaced_by.name)}</div>` : ""}</td>
      <td class="verdict-cell"><span class="verdict ${r.verdict.tone}" title="${esc(r.verdict.why)}">${esc(r.verdict.label)}</span></td>
      ${cell("recipients", n(t.recipients))}${isEvo(f) ? na + na : cell("open_rate", pct(t.open_rate)) + cell("click_rate", pct(t.click_rate))}${cell("conversions", n(t.conversions))}
      ${cell("revenue", gbp(t.revenue))}${cell("rps", t.recipients ? gbp(t.revenue_per_recipient, 2) : "–")}${trendCell(f)}${cell("unsubscribe_rate", pct(t.unsubscribe_rate))}<td>${dots(counts(f))}</td></tr>`;
  }).join("");
  const head = COLS.map((c) => {
    const on = state.sort && state.sort.key === c.key;
    const aria = on ? (state.sort.dir === "asc" ? "ascending" : "descending") : "none";
    return `<th aria-sort="${aria}"><button type="button" class="sort-btn" data-sort="${c.key}">${c.label}<span class="arrow" aria-hidden="true">${on ? (state.sort.dir === "asc" ? "▲" : "▼") : "↕"}</span></button></th>`;
  }).join("");
  const nAttention = state.snap.flows.filter((f) => rated.get(f.id).attention).length;
  $("#main").innerHTML = `
    <p class="eyebrow">${{ evo: "Evoflows", klaviyo: "Klaviyo (being replaced)" }[state.show] || "All flows"} · ${esc(TF_LABEL[state.tf])}</p>
    <h1>How the flows are doing</h1>
    <div class="kpis">
      <div class="kpi"><div class="label">Live flows</div><div class="value">${live.length}</div><div class="kpi-sub">${state.show === "evo" ? `${scope.length - live.length} built, switched off` : `${live.filter(isEvo).length} on Evoflows · ${live.filter((f) => !isEvo(f)).length} on Klaviyo`}</div></div>
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
        ${[["all", "All flows"], ["evo", "Evoflows"], ["klaviyo", "Klaviyo (being replaced)"], ["attention", `Needs work (${nAttention})`]].map(([k, l]) => `<button type="button" data-show="${k}" aria-pressed="${state.show === k}">${l}</button>`).join("")}
      </div>
      <p class="legend"><span class="sw good"></span>well above your typical flow <span class="sw poor"></span>well below, or unsubscribes over the limit <span class="sw lowv"></span>under ${MIN_SENDS} sends, too few to judge</p>
    </div>
    <div class="panel table-wrap"><table class="flows">
      <thead><tr>${head}<th>Checks</th></tr></thead>
      <tbody>${rows || `<tr><td colspan="11" class="muted">No flows match.</td></tr>`}</tbody></table></div>
    <p class="muted" style="margin-top:10px">“Typical flow” is the median of your own flows with ${MIN_SENDS}+ sends in this period, not an industry figure. Well above means at least 1.25× the median; well below means 0.75× or less. Post-purchase flows (triggered by an order or delivery) are judged on clicks, not revenue. Revenue trend compares the last ${TF_WEEKS[state.tf] || 13} full weeks with the ${TF_WEEKS[state.tf] || 13} before. Sends count every email and SMS delivered, not unique people. Revenue: on Evoflows, orders placed after one of the flow's emails; on Klaviyo, what Klaviyo attributes from Placed Order. Evoflows doesn't track opens or clicks yet, so those show as n/a and Evoflows flows triggered by an order can't be benchmarked until it does.</p>`;
}

// ---------- flow view ----------
function metricRow(m) {
  const s = mstats(m);
  if (!s) return `<div class="metrics"><div class="metric"><div class="l">Performance</div><div class="v">No sends in this period</div></div></div>`;
  const cells = [["Sends", n(s.recipients)]];
  if (m.platform === "evoflows") cells.push(["Orders after", n(s.conversions)], ["Revenue", gbp(s.conversion_value)], ["Per send", gbp(s.revenue_per_recipient, 2)],
    ["Unsub rate", pct(s.unsubscribe_rate), (s.unsubscribe_rate || 0) > 0.005], ["Bounce rate", pct(s.bounce_rate), (s.bounce_rate || 0) > 0.02]);
  else {
    if (m.kind === "email") cells.push(["Open rate", pct(s.open_rate)]);
    cells.push(["Click rate", pct(s.click_rate)], ["Orders", n(s.conversions)], ["Revenue", gbp(s.conversion_value)],
      ["Per send", gbp(s.revenue_per_recipient, 2)], ["Unsub rate", pct(s.unsubscribe_rate), (s.unsubscribe_rate || 0) > 0.005]);
  }
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
      ${m.status && m.status !== "live" ? pill(m.status) : ""}${(m.photos || []).map((k) => `<span class="photo-chip">Photo ${esc(k)}</span>`).join("")}${m.from_label && m.kind === "email" ? `<span class="msg-from">from ${esc(m.from_label)}</span>` : ""}</div>
    ${body}${m.only_if ? `<p class="msg-cond">Only if: ${esc(m.only_if)}</p>` : ""}${m.cap_note ? `<p class="msg-cond">${esc(m.cap_note)}</p>` : ""}
    ${m.draft ? "" : metricRow(m) + messageTrend(m) + abTable(m)}${flagList(flags, true)}
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
  if (state.draftId && !ms.length) return `<span class="muted num">no emails</span>`;
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
    const intro = s.split_type === "evoflows" ? `Splits into ${paths.length} paths (the first one that matches)`
      : s.split_type === "trigger-split" ? `Splits into ${paths.length} paths by what was in the basket or order`
      : s.split_type === "conditional-split" ? `Split: <b>${esc(s.label)}</b>` : `Split: <b>${esc(s.label)}</b>`;
    const openAt = Math.max(0, paths.findIndex((p) => [...messages(p.steps)].length));  // first path that sends something
    return `<div class="split"><p class="split-label">${intro}</p>${paths.map((p, i) => `
      <details class="path" ${i === openAt ? "open" : ""}><summary><span class="path-name">${esc(p.name)}</span>${pathSummary(p.steps)}
        ${p.cond && (s.split_type === "trigger-split" || s.split_type === "evoflows") ? `<span class="path-cond">${esc(p.cond)}</span>` : ""}</summary>
        <div class="path-body">${renderSteps(p.steps)}</div></details>`).join("")}</div>`;
  }).join("");
}

function renderFlow() {
  const f = state.snap.flows.find((x) => x.id === state.flowId);
  if (!f) { state.flowId = null; return renderOverview(); }
  const t = totals(f), evo = isEvo(f);
  const re = evo ? `${f.reentry_text}.` : f.reentry ? `Re-entry: ${f.reentry.unit === "alltime" ? "once ever" : `after ${f.reentry.duration} ${f.reentry.unit}s`}.` : "";
  const ev = (state.status && state.status.evoflows) || {};
  const kpi = (l, v, sub = "") => `<div class="kpi"><div class="label">${l}</div><div class="value">${v}</div>${sub ? `<div class="kpi-sub">${sub}</div>` : ""}</div>`;
  const kpis = evo
    ? kpi("People entered", n(t.enrolled), t.active ? `${n(t.active)} in it now` : "") + kpi("Sends", n(t.recipients)) + kpi("Orders after an email", n(t.conversions))
      + kpi("Revenue", gbp(t.revenue)) + kpi("Revenue per send", t.recipients ? gbp(t.revenue_per_recipient, 2) : "–") + kpi("Unsubscribe rate", pct(t.unsubscribe_rate), t.recipients ? `bounces ${pct(t.bounce_rate)}` : "")
    : kpi("Sends", n(t.recipients)) + kpi("Open rate (email)", pct(t.open_rate)) + kpi("Click rate", pct(t.click_rate)) + kpi("Orders", n(t.conversions))
      + kpi("Revenue", gbp(t.revenue)) + kpi("Revenue per send", t.recipients ? gbp(t.revenue_per_recipient, 2) : "–");
  const banner = evo
    ? `${f.status !== "live" ? `<div class="panel note-panel"><p><b>${f.status === "off" ? "Built, checked and on Evoflows, switched off." : "Approved here, not on Evoflows yet."}</b> ${f.status === "off" ? "Luke switches it on after the staff test." : "Push it from New flows to approve."}${(f.replaces || []).length ? ` When it goes on, switch off in Klaviyo in the same hour: ${f.replaces.map(esc).join(", ")}.` : ""}</p></div>` : ""}
       ${(f.deviations || []).length ? `<details class="panel fix-steps"><summary>Differences from the approved Klaviyo version (${f.deviations.length})</summary><ul>${f.deviations.map((d) => `<li>${esc(d)}</li>`).join("")}</ul></details>` : ""}`
    : f.replaced_by ? `<div class="panel note-panel"><p>Being replaced by <a href="#flow/${esc(f.replaced_by.id)}"><b>${esc(f.replaced_by.name)}</b></a> on Evoflows (${esc(STATUS_LABEL[f.replaced_by.status] || f.replaced_by.status)}). Switch this off in Klaviyo in the same hour that one goes on.</p></div>` : "";
  $("#main").innerHTML = `
    <div class="flow-head"><div>
      <p class="eyebrow">${platformTag(f)} ${esc(TF_LABEL[state.tf])} · ${evo ? (f.version ? `version ${esc(f.version)} on Evoflows` : "not on Evoflows yet") : `updated in Klaviyo ${esc((f.updated || "").slice(0, 10))}`}</p>
      <h1>${esc(f.name)} ${pill(f.status)}</h1>
      <p class="meta">${esc(f.trigger)}.${f.flow_filter ? ` Only if: ${esc(f.flow_filter)}.` : ""}${evo && f.exit ? ` Leaves if: ${esc(f.exit)}.` : ""} ${esc(re)}${evo && f.consent ? ` Consent: ${f.consent === "newsletter_only" ? "opted in to marketing only" : "customers (soft opt-in) and subscribers"}.` : ""}</p></div>
      ${evo ? (ev.admin_url ? `<a href="${esc(ev.admin_url)}" target="_blank" rel="noopener">Open Evoflows admin ↗</a>` : "") : `<a href="https://www.klaviyo.com/flow/${esc(f.id)}/edit" target="_blank" rel="noopener">Open in Klaviyo ↗</a>`}</div>
    ${banner}
    <div class="kpis">${kpis}</div>
    ${flowTrendPanel(f)}
    ${(f.flags[state.tf] || []).length ? `<div class="panel"><h3>Flow checks</h3>${flagList(f.flags[state.tf])}</div>` : ""}
    <div class="tabs" role="tablist">
      ${[["journey", "Journey"], ...(evo ? [["people", "People in it"]] : []), ["review", "Review"], ["notes", "Notes"]].map(([k, l]) => `<button type="button" role="tab" data-tab="${k}" aria-selected="${state.tab === k}">${l}</button>`).join("")}
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
  if (state.tab === "people") {
    el.innerHTML = `<p class="muted">Loading…</p>`;
    let r;
    try { r = await api(`/api/evoflows/runs?flow=${encodeURIComponent(f.id)}`); }
    catch (err) { el.innerHTML = `<p class="flag high">${esc(err.message)}</p>`; return; }
    const list = (r && r.runs) || [];
    const mask = (e) => { const [u, d] = String(e || "").split("@"); return d ? `${u.slice(0, 2)}…@${d}` : ""; };
    const when = (x) => (x ? new Date(x).toLocaleString("en-GB", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" }) : "–");
    el.innerHTML = list.length ? `<p class="muted">The 100 most recent people to enter this flow. Email addresses are shortened.</p>
      <div class="panel table-wrap"><table class="mini"><thead><tr><th>Who</th><th>Entered</th><th>Status</th><th>Next email due</th><th>Basket / order</th><th>Left because</th></tr></thead><tbody>
      ${list.map((x) => `<tr><td>${esc(x.first_name || "")} <span class="muted">${esc(mask(x.email))}</span></td><td>${when(x.trigger_at)}</td><td>${esc(x.status)}</td><td>${when(x.next_due_at)}</td>
        <td>${x.basket ? `${gbp(x.basket.total, 2)} · ${n(x.basket.item_count)} item${x.basket.item_count === 1 ? "" : "s"}` : x.order ? esc(x.order.name || "") : "–"}</td><td>${esc(x.exit_reason || "")}</td></tr>`).join("")}</tbody></table></div>`
      : `<p class="muted">Nobody has entered this flow yet${f.status === "live" ? "" : ": it's switched off"}.</p>`;
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
  if (m.platform === "evoflows") return "The approved build, shown with an example basket and the name “Sam”. On Evoflows each person sees their own name and basket.";
  if (m.draft) return "How the email will look. Names show as “Sam”; in Klaviyo each person sees their own name, or none.";
  return m.render_mode === "unpersonalised"
    ? "Klaviyo won’t fill in this template without a real customer, so it shows the default text instead. Product details stay blank, and every version of any conditional section appears."
    : "Rendered with an example basket and the name “Sam”, not a real customer.";
}
function previewSrc(m, messageId) {
  if (!m.preview_url) return `/render/${encodeURIComponent(messageId)}`;
  return m.preview_url + (draftState.photos && (m.photos || []).length ? "?photos=1" : "");
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
  const src = previewSrc(m, messageId);
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
  $("#pv-frame").src = previewSrc(m, messageId);
  $("#preview").hidden = false;
  $("#pv-close").focus();
}
function closePreview() { $("#preview").hidden = true; $("#pv-frame").src = "about:blank"; }

// ---------- routing and events ----------
function render() {
  document.querySelectorAll("#period button").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.tf === state.tf)));
  document.querySelectorAll("#period button").forEach((b) => { b.disabled = !state.snap.timeframes.includes(b.dataset.tf); b.title = b.disabled ? "Not in this snapshot yet" : ""; });
  renderSidebar();
  if (state.page === "evoflows") renderEvoflows();
  else if (state.page === "flowmap") renderFlowMap();
  else if (state.page === "drafts") (state.draftId ? renderDraft() : renderDrafts());
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
  const dm = /^#draft\/([a-z0-9_-]+)/.exec(location.hash);
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
  const ev = s.evoflows || {};
  const t = (x) => (x ? new Date(x).toLocaleString("en-GB", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" }) : "never");
  const evoText = !ev.enabled ? "Evoflows not connected" : ev.running ? `Evoflows: ${ev.step}` : ev.error ? `Evoflows failed: ${ev.error}` : `Evoflows ${t(ev.generated_at)}`;
  $("#refreshed").textContent = !s.show_klaviyo ? evoText : `${evoText} · ${s.running ? `Klaviyo: ${s.step}` : s.error ? `Klaviyo failed: ${s.error}` : `Klaviyo ${s.source === "fixtures" ? "(saved test data)" : ""} ${when}`}`;
  $("#refresh").disabled = !!s.running || !!ev.running;
}
async function pollStatus() {
  state.status = await api("/api/status");
  setStatusText();
  const ev = state.status.evoflows || {};
  if (state.status.running || ev.running) setTimeout(pollStatus, 3000);
  else if (state.snap && (state.status.generated_at !== state.snap.klaviyo_generated_at || ev.generated_at !== state.snap.evoflows_generated_at)) { state.snap = await api("/api/snapshot"); render(); }
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
