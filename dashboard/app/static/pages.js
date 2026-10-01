"use strict";
// Trends, comparisons, programme tracker, A/B tests and the Monday summary.
// Shares helpers and state with app.js (loaded first).

const SERIES = { now: "#128A5E", before: "#C08A2E" }; // validated pair (light surface); text never wears these
const TF_WEEKS = { last_30_days: 4, last_90_days: 13, last_365_days: 26 };
const WEEK_LABEL = { 4: "previous 4 weeks", 13: "previous 13 weeks", 26: "previous 26 weeks" };

// ---------- weekly data ----------
function lastWeekIdx() {
  const w = state.snap.weeks || [];
  const gen = new Date(state.snap.generated_at);
  for (let i = w.length - 1; i >= 0; i -= 1) if (new Date(w[i]).getTime() + 7 * 864e5 <= gen.getTime()) return i;
  return w.length ? w.length - 1 : null;
}
function sumWeekly(msgs, channel) {
  const out = {};
  for (const m of msgs) {
    if (channel && m.kind !== channel) continue;
    const w = m.weekly;
    if (!w) continue;
    for (const k of Object.keys(w)) out[k] = out[k] ? out[k].map((v, i) => v + (w[k][i] || 0)) : w[k].slice();
  }
  return Object.keys(out).length ? out : null;
}
const flowWeekly = (f, channel) => sumWeekly([...messages(f.steps)], channel);
const sumRange = (arr, a, b) => { let s = 0; for (let i = Math.max(a, 0); i <= b; i += 1) s += (arr && arr[i]) || 0; return s; };
function change(cur, prev) {
  if (!prev) return cur ? { pct: null, label: "new" } : { pct: null, label: "–" };
  const p = (cur - prev) / prev;
  return { pct: p, label: `${p >= 0 ? "▲" : "▼"} ${Math.abs(p * 100).toFixed(0)}%` };
}
function trendFor(w, key) {
  const i = lastWeekIdx(), N = TF_WEEKS[state.tf] || 13;
  if (!w || i == null || i < 2 * N - 1) return null;
  const val = (a, b) => key === "rps" ? (sumRange(w.recipients, a, b) ? sumRange(w.conversion_value, a, b) / sumRange(w.recipients, a, b) : null) : sumRange(w[key], a, b);
  const cur = val(i - N + 1, i), prev = val(i - 2 * N + 1, i - N);
  if (cur == null || prev == null) return null;
  return { cur, prev, ...change(cur, prev), weeks: N };
}
function chip(t, goodWhenUp = true, title = "") {
  if (!t) return `<span class="muted">–</span>`;
  const tone = t.pct == null ? "" : Math.abs(t.pct) < 0.1 ? "" : (t.pct > 0) === goodWhenUp ? "good" : "poor";
  return `<span class="chg ${tone}" title="${esc(title || `vs the ${WEEK_LABEL[t.weeks]}`)}">${esc(t.label)}</span>`;
}

// ---------- small charts ----------
function spark(values, { w = 96, h = 26, label = "" } = {}) {
  if (!values || !values.some((v) => v)) return `<span class="muted">–</span>`;
  const max = Math.max(...values) || 1, step = w / Math.max(values.length - 1, 1);
  const pts = values.map((v, i) => [i * step, h - 3 - (v / max) * (h - 6)]);
  const d = pts.map((p, i) => `${i ? "L" : "M"}${p[0].toFixed(1)},${p[1].toFixed(1)}`).join("");
  const [lx, ly] = pts[pts.length - 1];
  return `<svg class="spark" width="${w}" height="${h}" viewBox="-3 0 ${w + 6} ${h}" role="img" aria-label="${esc(label)}">
    <path d="${d}L${w},${h}L0,${h}Z" fill="${SERIES.now}" opacity=".1"/><path d="${d}" fill="none" stroke="${SERIES.now}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>
    <circle cx="${lx}" cy="${ly}" r="3" fill="${SERIES.now}" stroke="#fff" stroke-width="2"/></svg>`;
}
function weekLabel(iso) { return new Date(iso).toLocaleDateString("en-GB", { day: "numeric", month: "short" }); }

// Column chart, one series. Hover shows the week and value.
function columns(values, weeks, { fmt = (v) => n(v), title = "", partialLast = false } = {}) {
  const H = 120, max = Math.max(...values, 0) || 1, nice = niceMax(max);
  const bw = 100 / values.length;
  const bars = values.map((v, i) => {
    const hPct = (v / nice) * 100, part = partialLast && i === values.length - 1;
    return `<div class="col${part ? " part" : ""}" style="left:${i * bw}%;width:${bw}%" data-tip="${esc(`Week of ${weekLabel(weeks[i])}${part ? " (so far)" : ""}: ${fmt(v)}`)}">
      <span style="height:${hPct}%"></span></div>`;
  }).join("");
  return `<figure class="colchart"><figcaption>${esc(title)}</figcaption>
    <div class="plot" style="height:${H}px"><div class="gridline" style="bottom:100%"><span>${fmt(nice)}</span></div><div class="gridline" style="bottom:50%"><span>${fmt(nice / 2)}</span></div>
      <div class="gridline base" style="bottom:0"><span>0</span></div>${bars}</div>
    <div class="xaxis"><span>${weekLabel(weeks[0])}</span><span>${weekLabel(weeks[weeks.length - 1])}</span></div></figure>`;
}
function niceMax(v) {
  const p = Math.pow(10, Math.floor(Math.log10(v))), m = v / p;
  return (m <= 1 ? 1 : m <= 2 ? 2 : m <= 5 ? 5 : 10) * p;
}

// Two-series line chart for comparisons (legend + end labels + hover).
function lines(a, b, labels, { fmt = gbp, title = "" } = {}) {
  const W = 640, H = 170, P = { l: 44, r: 90, t: 10, b: 22 };
  const len = Math.max(a.values.length, b.values.length);
  const max = niceMax(Math.max(...a.values, ...b.values, 1));
  const x = (i) => P.l + (len > 1 ? (i / (len - 1)) * (W - P.l - P.r) : 0), y = (v) => P.t + (1 - v / max) * (H - P.t - P.b);
  const path = (vals) => vals.map((v, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join("");
  const end = (s) => { const i = s.values.length - 1; return `<circle cx="${x(i)}" cy="${y(s.values[i])}" r="4" fill="${s.color}" stroke="#fff" stroke-width="2"/><text x="${x(i) + 8}" y="${y(s.values[i]) + 4}" class="endlab">${esc(s.name)} ${esc(fmt(s.values[i]))}</text>`; };
  const hits = [...Array(len).keys()].map((i) => `<rect x="${x(i) - (W - P.l - P.r) / len / 2}" y="${P.t}" width="${(W - P.l - P.r) / len}" height="${H - P.t - P.b}" fill="transparent"
    data-tip="${esc(`${labels[i]}: ${a.name} ${a.values[i] != null ? fmt(a.values[i]) : "–"} · ${b.name} ${b.values[i] != null ? fmt(b.values[i]) : "–"}`)}"/>`).join("");
  return `<figure class="linechart"><figcaption>${esc(title)}</figcaption>
    <div class="legend-row"><span><i style="background:${a.color}"></i>${esc(a.name)}</span><span><i style="background:${b.color}"></i>${esc(b.name)}</span></div>
    <svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(title)}">
      ${[0, 0.5, 1].map((f) => `<line x1="${P.l}" x2="${W - P.r}" y1="${y(max * f)}" y2="${y(max * f)}" class="grid"/><text x="${P.l - 6}" y="${y(max * f) + 4}" class="tick" text-anchor="end">${esc(fmt(max * f))}</text>`).join("")}
      <text x="${P.l}" y="${H - 4}" class="tick">${esc(labels[0] || "")}</text><text x="${W - P.r}" y="${H - 4}" class="tick" text-anchor="end">${esc(labels[len - 1] || "")}</text>
      <path d="${path(b.values)}" fill="none" stroke="${b.color}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>
      <path d="${path(a.values)}" fill="none" stroke="${a.color}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>
      ${end(b)}${end(a)}${hits}</svg></figure>`;
}

// Shared tooltip for [data-tip] marks.
const tip = document.createElement("div");
tip.className = "tip"; tip.hidden = true; document.body.appendChild(tip);
document.addEventListener("mousemove", (e) => {
  const t = e.target.closest && e.target.closest("[data-tip]");
  if (!t) { tip.hidden = true; return; }
  tip.textContent = t.dataset.tip; tip.hidden = false;
  const r = tip.getBoundingClientRect();
  tip.style.left = Math.min(e.clientX + 12, innerWidth - r.width - 8) + "px";
  tip.style.top = (e.clientY - r.height - 10) + "px";
});

// ---------- flow page trend panel ----------
function flowTrendPanel(f) {
  const w = flowWeekly(f), weeks = state.snap.weeks || [];
  if (!w || !weeks.length) return state.snap.source === "klaviyo" && !weeks.length
    ? `<p class="muted">Week-by-week figures appear after the next refresh from Klaviyo.</p>` : "";
  const N = TF_WEEKS[state.tf] || 13, last = weeks.length - 1, from = Math.max(0, weeks.length - 2 * N);
  const partial = lastWeekIdx() !== last;
  const sl = (k) => w[k].slice(from), wk = weeks.slice(from);
  const tr = (k, up = true) => chip(trendFor(w, k), up);
  return `<div class="panel trend-panel"><div class="trend-head"><h3>Week by week</h3>
      <p class="muted">Change compares the last ${N} full weeks with the ${N} before. ${partial ? "The lightest column is the current week so far." : ""}</p></div>
    <div class="trend-grid">
      <div><div class="trend-kpi">Sends ${tr("recipients")}</div>${columns(sl("recipients"), wk, { title: "Sends per week", partialLast: partial })}</div>
      <div><div class="trend-kpi">Revenue ${tr("conversion_value")}</div>${columns(sl("conversion_value"), wk, { fmt: (v) => gbp(v), title: "Revenue per week", partialLast: partial })}</div>
      <div><div class="trend-kpi">Revenue per send ${tr("rps")}</div>${columns(sl("recipients").map((s, i) => (s ? sl("conversion_value")[i] / s : 0)), wk, { fmt: (v) => gbp(v, 2), title: "Revenue per send, per week", partialLast: partial })}</div>
    </div></div>`;
}
function messageTrend(m) {
  if (!m.weekly) return "";
  const t = trendFor(m.weekly, "recipients"), N = TF_WEEKS[state.tf] || 13;
  const vals = m.weekly.recipients.slice(-2 * N);
  return `<div class="msg-trend">${spark(vals, { label: `Sends per week, last ${2 * N} weeks` })}<span class="muted">sends per week</span>${chip(t)}</div>`;
}

// ---------- flow paths (for comparisons) ----------
function topPaths(f) {
  const split = f.steps.find((s) => s.kind === "split");
  if (!split) return [];
  if (split.split_type === "trigger-split") return flattenChain(split);
  if (split.split_type === "multi-branch-split") return split.branches.map((b) => ({ name: b.label, steps: b.steps }));
  return [];
}
function compareOptions() {
  const out = [];
  for (const f of state.snap.flows) {
    out.push({ key: f.id, label: f.name, flow: f, steps: f.steps });
    for (const p of topPaths(f)) out.push({ key: `${f.id}:${p.name}`, label: `${f.name} › ${p.name}`, flow: f, steps: p.steps, path: p.name });
  }
  return out;
}
const norm = (s) => String(s || "").toLowerCase().replace(/[\s—–-]+/g, " ").trim();
function findOption(opts, spec) {
  return opts.find((o) => norm(o.flow.name) === norm(spec.flow) && (spec.path ? norm(o.path) === norm(spec.path) : !o.path));
}
function stats(msgs, a, b) {
  const all = sumWeekly(msgs), em = sumWeekly(msgs, "email");
  if (!all) return null;
  const S = (w, k) => sumRange(w && w[k], a, b);
  const sends = S(all, "recipients"), del = S(all, "delivered"), rev = S(all, "conversion_value");
  return {
    sends, orders: S(all, "conversions"), revenue: rev, rps: sends ? rev / sends : null,
    open_rate: S(em, "delivered") ? S(em, "opens_unique") / S(em, "delivered") : null,
    click_rate: del ? S(all, "clicks_unique") / del : null, unsub_rate: del ? S(all, "unsubscribe_uniques") / del : null,
  };
}

// ---------- pages ----------
async function renderCompare() {
  const prog = await getProgramme();
  const opts = compareOptions();
  const presets = [];
  for (const f of prog.flows) for (const c of f.compare || []) {
    const A = findOption(opts, c.new), B = findOption(opts, c.old);
    presets.push({ label: `${f.id} ${c.label}: new vs old`, a: A && A.key, b: B && B.key, missing: !A ? c.new.flow : !B ? `${c.old.flow} › ${c.old.path}` : null });
  }
  if (!state.cmp) { const p = presets.find((x) => x.a && x.b); state.cmp = p ? { a: p.a, b: p.b } : { a: opts[0] && opts[0].key, b: opts[1] && opts[1].key }; }
  const A = opts.find((o) => o.key === state.cmp.a), B = opts.find((o) => o.key === state.cmp.b);
  const sel = (id, cur) => `<select id="${id}">${opts.map((o) => `<option value="${esc(o.key)}" ${o.key === cur ? "selected" : ""}>${esc(o.label)}</option>`).join("")}</select>`;
  let body = "";
  const weeks = state.snap.weeks || [], last = lastWeekIdx();
  if (!weeks.length || last == null) body = `<p class="muted">Comparisons need week-by-week figures, which arrive with the next refresh from Klaviyo.</p>`;
  else if (A && B) {
    const aMsgs = [...messages(A.steps)], bMsgs = [...messages(B.steps)];
    const aw = sumWeekly(aMsgs), bw = sumWeekly(bMsgs);
    const first = aw ? aw.recipients.findIndex((v) => v > 0) : -1;
    const bBefore = bw && first > 0 ? sumRange(bw.recipients, 0, first - 1) : 0;
    let aRange, bRange, how;
    if (first > 0 && bBefore > 0 && first <= last) {
      const k = Math.min(last - first + 1, 26);
      aRange = [first, first + k - 1]; bRange = [first - k, first - 1];
      how = `<b>${esc(A.label)}</b> since its first send (${k} week${k === 1 ? "" : "s"} from ${weekLabel(weeks[first])}) against <b>${esc(B.label)}</b> in the ${k} week${k === 1 ? "" : "s"} before that.`;
    } else {
      const N = TF_WEEKS[state.tf] || 13;
      aRange = bRange = [last - N + 1, last];
      how = `Both over the same ${N} full weeks (${weekLabel(weeks[last - N + 1])} to ${weekLabel(weeks[last])}).${first < 0 ? ` <b>${esc(A.label)}</b> hasn't sent anything yet, so this shows the baseline it has to beat.` : ""}`;
    }
    const sa = stats(aMsgs, ...aRange), sb = stats(bMsgs, ...bRange);
    const row = (label, k, f, up = true) => {
      const va = sa && sa[k], vb = sb && sb[k];
      return `<tr><td>${label}</td><td>${va == null ? "–" : f(va)}</td><td>${vb == null ? "–" : f(vb)}</td><td>${va != null && vb != null ? chip({ ...change(va, vb), weeks: 13 }, up, "A compared with B") : "–"}</td></tr>`;
    };
    const small = (sa && sa.sends < 100) || (sb && sb.sends < 100);
    const len = aRange[1] - aRange[0] + 1;
    const pick = (w, r) => [...Array(len).keys()].map((i) => (w ? w.conversion_value[r[0] + i] || 0 : 0));
    const lab = [...Array(len).keys()].map((i) => aRange === bRange ? weekLabel(weeks[aRange[0] + i]) : `Week ${i + 1}`);
    body = `<p class="how">${how}</p>
      ${small ? `<div class="flag medium">Under 100 sends on one side: treat this as a hint, not a result.</div>` : ""}
      <div class="panel table-wrap"><table class="cmp"><thead><tr><th></th><th><i class="key" style="background:${SERIES.now}"></i>A · ${esc(A.label)}</th><th><i class="key" style="background:${SERIES.before}"></i>B · ${esc(B.label)}</th><th>A vs B</th></tr></thead><tbody>
        ${row("Sends", "sends", n)}${row("Open rate (email)", "open_rate", pct)}${row("Click rate", "click_rate", pct)}
        ${row("Orders", "orders", n)}${row("Revenue", "revenue", (v) => gbp(v))}${row("Revenue per send", "rps", (v) => gbp(v, 2))}${row("Unsubscribe rate", "unsub_rate", (v) => (v * 100).toFixed(2) + "%", false)}
      </tbody></table></div>
      <div class="panel" style="margin-top:14px">${lines({ name: "A", color: SERIES.now, values: pick(aw, aRange) }, { name: "B", color: SERIES.before, values: pick(bw, bRange) }, lab, { title: "Revenue per week" })}</div>`;
  }
  $("#main").innerHTML = `<p class="eyebrow">Compare</p><h1>Before and after</h1>
    <p class="muted" style="max-width:80ch">Pick a new flow or path (A) and the one it replaces (B). Once A has started sending, A's weeks since launch are set against the same number of weeks of B just before launch, so both cover similar conditions.</p>
    ${presets.length ? `<div class="presets">${presets.map((p) => p.a && p.b ? `<button type="button" class="btn-soft" data-preset="${esc(p.a)}|${esc(p.b)}">${esc(p.label)}</button>` : `<span class="muted">${esc(p.label)}: can't find “${esc(p.missing)}”</span>`).join("")}</div>` : ""}
    <div class="pickers"><label>A (new) ${sel("cmp-a", state.cmp.a)}</label><label>B (old / before) ${sel("cmp-b", state.cmp.b)}</label></div>${body}`;
}

let programmeCache = null;
async function getProgramme() { if (!programmeCache) programmeCache = await api("/api/programme"); return programmeCache; }

async function renderProgramme() {
  const prog = await getProgramme();
  const rated = rateFlows(state.snap.flows);
  const order = [...prog.build_order, ...prog.flows.map((f) => f.id).filter((id) => !prog.build_order.includes(id))];
  const byId = Object.fromEntries(prog.flows.map((f) => [f.id, f]));
  const counts = { live: 0, draft: 0, todo: 0, skip: 0 };
  const rows = order.map((id, idx) => {
    const p = byId[id];
    const built = state.snap.flows.filter((f) => f.name.startsWith(p.match));
    const st = built.some((f) => f.status === "live") ? ["live", "Live"] : built.length ? ["draft", "Draft in Klaviyo"] : p.not_building ? ["skip", "Not in this build"] : ["todo", "Not started"];
    counts[st[0]] += 1;
    const olds = (p.replaces || []).map((name) => {
      const f = state.snap.flows.find((x) => norm(x.name) === norm(name));
      if (!f) return `<li>${esc(name)} <span class="muted">(not found)</span></li>`;
      const t = totals(f);
      return `<li><a href="#flow/${esc(f.id)}">${esc(f.name)}</a> ${pill(f.status)} <span class="muted num">${n(t.recipients)} sends · ${gbp(t.revenue)}</span> <span class="verdict ${rated.get(f.id).verdict.tone}">${esc(rated.get(f.id).verdict.label)}</span></li>`;
    }).join("");
    const qs = prog.questions.filter((q) => !q.answered && q.affects.includes(id));
    const drafts = built.map((f) => `<li><a href="#flow/${esc(f.id)}">${esc(f.name)}</a> ${pill(f.status)}</li>`).join("");
    return `<details class="prog ${st[0]}"><summary>
        <span class="prog-n">${idx < prog.build_order.length ? idx + 1 : "–"}</span><span class="prog-id">${esc(id)}</span><span class="prog-name">${esc(p.name)}</span>
        <span class="muted">Week ${esc(p.week)}</span><span class="stat ${st[0]}">${esc(st[1])}</span>
        <span class="muted prog-meta">${p.todos ? `${p.todos.length} to-do${p.todos.length === 1 ? "" : "s"} · ` : ""}${qs.length} open question${qs.length === 1 ? "" : "s"}</span></summary>
      <div class="prog-body">
        ${p.not_building ? `<p>${esc(p.not_building)}</p>` : ""}${p.gate ? `<p><b>Gate:</b> ${esc(p.gate)}</p>` : ""}${p.note ? `<p class="muted">${esc(p.note)}</p>` : ""}
        ${p.paths ? `<p><b>Paths:</b> ${p.paths.map(esc).join(" · ")}</p>` : ""}
        ${drafts ? `<h4>In Klaviyo</h4><ul>${drafts}</ul>` : ""}
        ${olds ? `<h4>Replaces</h4><ul>${olds}</ul>` : ""}
        ${p.todos ? `<h4>To do in Klaviyo</h4><ul>${p.todos.map((t) => `<li>${esc(t)}</li>`).join("")}</ul>` : ""}
        ${qs.length ? `<h4>Waiting on</h4><ul>${qs.map((q) => `<li><b>${esc(q.id)}</b> ${esc(q.text)}${q.answer ? ` <span class="muted">(${esc(q.answer)})</span>` : ""}</li>`).join("")}</ul>` : ""}
      </div></details>`;
  }).join("");
  const gaps = state.snap.flows.filter((f) => rated.get(f.id).verdict.label === "Not sending");
  const open = prog.questions.filter((q) => !q.answered);
  $("#main").innerHTML = `<p class="eyebrow">Programme</p><h1>Build Pack progress</h1>
    <div class="kpis">
      <div class="kpi"><div class="label">Live</div><div class="value">${counts.live}</div></div>
      <div class="kpi"><div class="label">Draft in Klaviyo</div><div class="value">${counts.draft}</div></div>
      <div class="kpi"><div class="label">Not started</div><div class="value">${counts.todo}</div></div>
      <div class="kpi"><div class="label">Not in this build</div><div class="value">${counts.skip}</div></div>
      <div class="kpi"><div class="label">Open questions</div><div class="value">${open.length}</div></div>
    </div>
    ${gaps.length ? `<div class="panel" style="margin-bottom:16px"><h3>Gaps right now</h3>${gaps.map((f) => `<div class="flag high"><span><a href="#flow/${esc(f.id)}"><b>${esc(f.name)}</b></a> is live but sent nothing in the ${esc(TF_LABEL[state.tf])}.</span></div>`).join("")}</div>` : ""}
    <p class="muted">Numbered in the pack's build order. Status comes from Klaviyo: a flow counts as built when its name starts with “EG · F<i>n</i>”. Click a row for details.</p>
    <div class="prog-list">${rows}</div>
    <h2 style="margin-top:28px">Open questions</h2>
    <div class="panel table-wrap"><table class="qs"><thead><tr><th>#</th><th>Question</th><th>Affects</th><th>Status</th></tr></thead><tbody>
      ${prog.questions.map((q) => `<tr><td>${esc(q.id)}</td><td>${esc(q.text)}${q.answer ? `<div class="muted">${esc(q.answer)}</div>` : ""}</td><td>${q.affects.map(esc).join(", ")}</td><td>${q.answered ? `<span class="stat live">Answered</span>` : `<span class="stat todo">Open</span>`}</td></tr>`).join("")}
    </tbody></table></div>`;
}

function renderTests() {
  const rows = [];
  for (const f of state.snap.flows) for (const m of messages(f.steps)) if (m.ab_test) rows.push({ f, m, ab: m.ab_test });
  const now = Date.now();
  const body = rows.map(({ f, m, ab }) => {
    const days = ab.started ? Math.floor((now - new Date(ab.started).getTime()) / 864e5) : null;
    const long = ab.status === "live" && days > 45;
    const vs = ab.variations.map((v, i) => {
      const s = mstats(v);
      return `<tr><td>${String.fromCharCode(65 + i)}</td><td>${esc(v.subject || v.name)}</td><td>${v.share != null ? Math.round(v.share * 100) + "%" : "–"}</td>
        <td>${s ? n(s.recipients) : "–"}</td><td>${s ? pct(s.open_rate) : "–"}</td><td>${s ? pct(s.click_rate) : "–"}</td><td>${s ? gbp(s.revenue_per_recipient, 2) : "–"}</td></tr>`;
    }).join("");
    const anyStats = ab.variations.some((v) => mstats(v));
    return `<div class="panel test ${long ? "long" : ""}">
      <div class="test-head"><div><p class="eyebrow">${esc(f.name)}</p><h3>${esc(m.name)}</h3></div>
        <div class="test-meta">${pill(ab.status || "unknown")} ${days != null ? `<span class="${long ? "warn-text" : "muted"}">${days} days running</span>` : ""}
        ${ab.winner_metric ? `<span class="muted">winner by ${esc(ab.winner_metric.replace(/-/g, " "))}</span>` : ""}
        <a href="https://www.klaviyo.com/flow/${esc(f.id)}/edit" target="_blank" rel="noopener">Open in Klaviyo ↗</a></div></div>
      ${long ? `<div class="flag medium">Running for ${days} days. Pick a winner in Klaviyo and end the test, or give it a clear end date.</div>` : ""}
      <table class="ab-t"><thead><tr><th></th><th>Subject</th><th>Share</th><th>Sends</th><th>Open</th><th>Click</th><th>Per send</th></tr></thead><tbody>${vs}</tbody></table>
      ${anyStats ? "" : `<p class="muted">No per-variation numbers came back from Klaviyo's reporting for this test. Its results are in the test's own view in Klaviyo.</p>`}
    </div>`;
  }).join("");
  $("#main").innerHTML = `<p class="eyebrow">A/B tests</p><h1>Every test in the flows</h1>
    <p class="muted">${rows.length} test${rows.length === 1 ? "" : "s"} found. Tests running longer than 45 days are flagged.</p>${body || `<p>No A/B tests in the current flows.</p>`}`;
}

async function renderSummary() {
  $("#main").innerHTML = `<p class="muted">Loading…</p>`;
  const s = await api("/api/summary");
  if (!s.generated_at) { $("#main").innerHTML = `<p>No data yet.</p>`; return; }
  const t = s.totals;
  const link = (id, name) => `<a href="#flow/${esc(id)}">${esc(name)}</a>`;
  const vsAvg = (now, avg) => chip({ ...change(now, avg), weeks: 4 }, true, "vs the 4-week average");
  $("#main").innerHTML = `<p class="eyebrow">Monday summary${s.week_of ? ` · week of ${esc(weekLabel(s.week_of))}` : ""}</p><h1>Last week in the flows</h1>
    <div class="summary-actions">${s.slack_enabled
      ? `<button type="button" class="btn" id="send-summary">Post to Slack now</button><span class="muted">Posts automatically on Mondays from 08:00.${s.last_sent ? ` Last posted ${esc(s.last_sent.slice(0, 16).replace("T", " "))} UTC.` : ""}</span>`
      : `<span class="muted">Not posting anywhere. To get this in Slack every Monday at 08:00, add a Slack incoming-webhook address as <code>SLACK_WEBHOOK_URL</code> in Railway Variables.</span>`}</div>
    ${s.has_weeks ? `<div class="kpis">
      <div class="kpi"><div class="label">Revenue last week</div><div class="value">${gbp(t.revenue)}</div><div class="kpi-sub">${vsAvg(t.revenue, t.revenue_avg4)} vs ${gbp(t.revenue_avg4)} a week</div></div>
      <div class="kpi"><div class="label">Sends last week</div><div class="value">${n(t.sends)}</div><div class="kpi-sub">${vsAvg(t.sends, t.sends_avg4)} vs ${n(t.sends_avg4)} a week</div></div>
    </div>` : `<p class="muted">Week-by-week figures appear after the next refresh from Klaviyo.</p>`}
    <div class="summary-grid">
      <div class="panel"><h3>Top actions</h3>${s.actions.length ? `<ol>${s.actions.map((a) => `<li>${link(a.flow_id, a.flow)}${a.message ? ` · ${esc(a.message)}` : ""}: ${esc(a.text)}</li>`).join("")}</ol>` : `<p class="muted">Nothing urgent.</p>`}</div>
      <div class="panel"><h3>Biggest moves</h3>${s.has_weeks && s.flows.length ? `<table class="mini"><thead><tr><th>Flow</th><th>Last week</th><th>4-week avg</th><th></th></tr></thead><tbody>
        ${s.flows.slice(0, 8).map((x) => `<tr><td>${link(x.id, x.name)}</td><td>${gbp(x.revenue)}</td><td>${gbp(x.revenue_avg4)}</td><td>${vsAvg(x.revenue, x.revenue_avg4)}</td></tr>`).join("")}</tbody></table>` : `<p class="muted">–</p>`}</div>
      <div class="panel"><h3>Stopped sending</h3>${s.stopped.length ? `<ul>${s.stopped.map((x) => `<li>${link(x.id, x.name)}: averaged ${n(x.sends_avg4)} sends a week, none last week</li>`).join("")}</ul>` : `<p class="muted">No live flow stopped last week.</p>`}</div>
      <div class="panel"><h3>Newly flagged</h3>${s.first_run ? `<p class="muted">Tracked from the first summary posted, so everything counts as known until then.</p>` : s.new_flags.length ? `<ul>${s.new_flags.map((x) => `<li>${link(x.flow_id, x.flow)}${x.message ? ` · ${esc(x.message)}` : ""}: ${esc(x.text)}</li>`).join("")}</ul>` : `<p class="muted">Nothing new since the last summary.</p>`}</div>
    </div>`;
}

document.addEventListener("change", (e) => {
  if (e.target.id === "cmp-a" || e.target.id === "cmp-b") { state.cmp = { a: $("#cmp-a").value, b: $("#cmp-b").value }; renderCompare(); }
});
document.addEventListener("click", async (e) => {
  const p = e.target.closest("[data-preset]");
  if (p) { const [a, b] = p.dataset.preset.split("|"); state.cmp = { a, b }; renderCompare(); return; }
  if (e.target.id === "send-summary") {
    const btn = e.target; btn.disabled = true; btn.textContent = "Posting…";
    try { await api("/api/summary/send", { method: "POST" }); btn.textContent = "Posted"; }
    catch (err) { alertInline(btn, err.message); }
  }
});

// ---------- fixes: recommend → approve → apply ----------
let fixState = { data: null, open: {} };
async function renderFixes() {
  fixState.data = await api("/api/fixes");
  const d = fixState.data, all = d.fixes;
  const group = (st) => all.filter((f) => st.includes(f.status));
  const review = group(["proposed"]), todo = group(["manual"]), done = group(["verified", "done"]), closed = group(["dismissed"]);
  const scanning = d.scan.running;
  const kindLabel = { unsubscribe: "Compliance", deadline: "DMCC check", text: "DMCC check" };
  const card = (f) => {
    const items = f.items || [];
    const open = items.filter((i) => !i.fixed), fixed = items.filter((i) => i.fixed);
    const hist = (f.history || []).map((h) => `<li>${esc(h.at.slice(0, 16).replace("T", " "))} · ${esc(h.by)} · ${esc(h.action)}${h.detail ? ` – ${esc(h.detail)}` : ""}</li>`).join("");
    const row = (i) => `<li class="${i.fixed ? "fixed" : ""}"><span class="tick" aria-hidden="true">${i.fixed ? "✓" : "○"}</span>
      <span><b>${esc(i.message || "")}</b>${i.kind === "text" ? "" : ""}${f.kind === "unsubscribe" ? "" : `<br><span class="muted">${esc(i.detail)}</span>`}
      ${i.suggestion && !i.fixed ? `<br>→ <span class="sugg">${esc(i.suggestion)}</span>` : ""}${i.codes && i.codes.length && !i.fixed ? ` <span class="muted">(uses ${esc(i.codes.join(", "))})</span>` : ""}
      ${i.fixed ? `<span class="muted"> – fixed</span>` : ""}</span></li>`;
    const previews = f.before_preview ? `<details class="fix-prev" ${fixState.open[f.id] ? "open" : ""} data-fix-open="${esc(f.id)}"><summary>Show what the fix looks like (first email)</summary>
        <div class="fix-frames"><figure><figcaption>Now</figcaption><iframe sandbox="" loading="lazy" src="/fixes/${esc(f.id)}/preview?which=before"></iframe></figure>
        <figure><figcaption>After the fix</figcaption><iframe sandbox="" loading="lazy" src="/fixes/${esc(f.id)}/preview?which=after"></iframe></figure></div></details>` : "";
    let actions = "";
    if (f.status === "proposed") actions = `<div class="fix-actions"><button type="button" class="btn" data-fix="approve" data-id="${esc(f.id)}">Approve: add to the Klaviyo to-do list</button>
        <button type="button" class="btn-line" data-fix="dismiss" data-id="${esc(f.id)}">Dismiss</button></div>`;
    else if (f.status === "manual") actions = `<div class="fix-actions"><a class="btn" href="${esc(f.klaviyo_url)}" target="_blank" rel="noopener">Open the flow in Klaviyo ↗</a>
        <span class="muted">When the changes are saved, press “Scan emails” at the top: each item is checked and ticked off.</span></div>`;
    const badge = { proposed: ["skip", "Waiting for approval"], manual: ["draft", `To do · ${open.length} of ${items.length} left`], verified: ["live", "Verified fixed in Klaviyo"], done: ["live", "Done"], dismissed: ["skip", "Dismissed"] }[f.status] || ["skip", f.status];
    return `<article class="panel fix ${esc(f.status)}"><div class="fix-head"><span class="fix-kind ${esc(f.kind)}">${esc(kindLabel[f.kind] || f.kind)}</span>
        <h3>${esc(f.title)} · <a href="#flow/${esc(f.flow_id)}">${esc(f.flow)}</a></h3><span class="stat ${badge[0]}">${esc(badge[1])}</span></div>
      <p>${esc(f.why)}</p>
      <details class="fix-items" ${f.status === "manual" ? "open" : ""}><summary>${open.length} email${open.length === 1 ? "" : "s"} to fix${fixed.length ? `, ${fixed.length} fixed` : ""}</summary><ul class="fix-list">${open.map(row).join("")}${fixed.map(row).join("")}</ul></details>
      ${f.status !== "verified" && f.status !== "dismissed" ? `<details class="fix-steps"><summary>How to fix it in Klaviyo</summary><ol>${(f.steps || []).map((x) => `<li>${esc(x)}</li>`).join("")}</ol></details>` : ""}
      ${previews}${actions}${hist ? `<ul class="fix-hist">${hist}</ul>` : ""}</article>`;
  };
  const section = (title, list, empty) => `<h2 class="fix-h">${title} <span class="muted">(${list.length})</span></h2>${list.length ? list.map(card).join("") : `<p class="muted">${empty}</p>`}`;
  const openCount = [...review, ...todo].reduce((a, f) => a + (f.open || 0), 0);
  $("#main").innerHTML = `<p class="eyebrow">Fixes</p><h1>Recommend, approve, track</h1>
    <p class="muted" style="max-width:88ch">The app reads every email in your flows and groups what needs fixing by flow. Klaviyo doesn't let apps edit emails that are inside flows (only its own editor can), so approving a card puts it on the Klaviyo to-do list with exact steps. After the changes are made, <b>Scan emails</b> checks each one and ticks it off, so “done” means verified in Klaviyo, not just clicked.</p>
    <div class="fix-bar"><button type="button" class="btn" id="fix-scan" ${scanning ? "disabled" : ""}>${scanning ? `Scanning: ${esc(d.scan.step)}` : "Scan emails"}</button>
      ${d.scan.error ? `<span class="flag high">${esc(d.scan.error)}</span>` : d.scan.finished_at ? `<span class="muted">Last scan ${esc(d.scan.finished_at.slice(0, 16).replace("T", " "))} UTC · ${openCount} email${openCount === 1 ? "" : "s"} still to fix</span>` : ""}</div>
    ${section("Waiting for approval", review, all.length ? "Nothing waiting." : "Run a scan to get the first proposals.")}
    ${section("To do in the Klaviyo editor", todo, "Nothing on the to-do list.")}
    ${section("Verified fixed", done, "Nothing verified yet.")}
    ${closed.length ? `<details class="fix-closed"><summary>Dismissed (${closed.length})</summary>${closed.map(card).join("")}</details>` : ""}`;
  if (scanning) setTimeout(() => { if (state.page === "fixes") renderFixes(); }, 3000);
}
document.addEventListener("toggle", (e) => { const t = e.target.closest && e.target.closest("[data-fix-open]"); if (t) fixState.open[t.dataset.fixOpen] = t.open; }, true);
document.addEventListener("click", async (e) => {
  if (e.target.id === "fix-keys") { e.target.disabled = true; await api("/api/fixes/check-keys", { method: "POST" }); renderFixes(); return; }
  if (e.target.id === "fix-scan") { e.target.disabled = true; await api("/api/fixes/scan", { method: "POST" }); setTimeout(renderFixes, 800); return; }
  const b = e.target.closest("[data-fix]");
  if (!b) return;
  const id = b.dataset.id, action = b.dataset.fix, body = {};
  if (action === "approve") {
    const inp = document.querySelector(`[data-replace="${CSS.escape(id)}"]`);
    if (inp) body.replace = inp.value;
    const f = fixState.data.fixes.find((x) => x.id === id);
    if (f && !f.items && f.kind !== "manual" && !confirm(`Apply this change to the live email in Klaviyo?\n\n${f.flow} · ${f.message}\n${f.change}`)) return;
  }
  if (action === "undo" && !confirm("Put this email back exactly as it was before the fix?")) return;
  b.disabled = true; b.textContent = action === "approve" ? "Applying…" : "Working…";
  try { await api(`/api/fixes/${encodeURIComponent(id)}/${action}`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) }); }
  catch (err) { alertInline(b, err.message); return; }
  renderFixes();
});

// ---------- new flows to approve: the app creates them in Klaviyo as drafts ----------
let draftState = { data: null, current: null };
const DRAFT_BADGE = { ready: ["skip", "Waiting for approval"], creating: ["draft", "Creating in Klaviyo…"], created: ["live", "Created in Klaviyo (switched off)"], failed: ["flag high", "Stopped: see below"] };
const draftStatus = (p) => (p.running ? "creating" : p.status);
function draftActions(p, d) {
  const st = draftStatus(p);
  if (st === "ready" || st === "failed") return d.writes_enabled
    ? `<div class="fix-actions"><button type="button" class="btn" data-draft-approve="${esc(p.id)}">${st === "failed" ? "Try again" : "Approve: create in Klaviyo as a draft"}</button>
       <span class="muted">Creates ${p.emails.length} emails and the flow “${esc(p.flow_name)}”, switched off. Nothing sends.</span></div>`
    : `<p class="muted">The app has no Klaviyo write key, so it can't create drafts.</p>`;
  if (st === "creating") return `<p class="muted">Creating the emails and the flow. This takes a minute.</p>`;
  return `<div class="fix-actions"><a class="btn" href="${esc(p.klaviyo_url)}" target="_blank" rel="noopener">Open the draft in Klaviyo ↗</a>
      ${p.verify ? `<span class="${p.verify.ok ? "muted" : "flag high"}">Checked in Klaviyo: status ${esc(p.verify.status)}, ${esc(p.verify.steps)} of ${esc(p.verify.expected)} steps.</span>` : ""}</div>
      ${p.dropped && p.dropped.length ? `<p class="flag">Klaviyo didn't accept some settings, so set these in the editor: ${esc(p.dropped.join(", "))}.</p>` : ""}`;
}
const draftHist = (p) => (p.history || []).map((h) => `<li>${esc(h.at.slice(0, 16).replace("T", " "))} · ${esc(h.by)} · ${esc(h.action)}${h.detail ? ` – ${esc(h.detail)}` : ""}</li>`).join("");
async function renderDrafts() {
  draftState.data = await api("/api/drafts");
  const d = draftState.data;
  const card = (p) => {
    const [cls, label] = DRAFT_BADGE[draftStatus(p)] || ["skip", p.status];
    return `<article class="panel fix"><div class="fix-head"><span class="fix-kind">New flow</span><h3><a href="#draft/${esc(p.id)}">${esc(p.title)}</a></h3><span class="stat ${cls}">${esc(label)}</span></div>
      <p>${esc(p.summary)}</p>${p.replaces ? `<p class="muted">${esc(p.replaces)}</p>` : ""}
      <div class="fix-actions"><a class="btn${p.status === "created" ? "-line" : ""}" href="#draft/${esc(p.id)}">See the full flow and emails →</a>
      <span class="muted">${p.emails.length} emails · ${esc(p.trigger)}</span></div>
      ${p.error ? `<p class="flag high">${esc(p.error)}</p>` : ""}</article>`;
  };
  const waiting = d.packs.filter((p) => p.status !== "created"), made = d.packs.filter((p) => p.status === "created");
  $("#main").innerHTML = `<p class="eyebrow">New flows</p><h1>Approve, and the app builds them in Klaviyo</h1>
    <p class="muted" style="max-width:88ch">Open a flow to see every step and preview each email, laid out like your live flows. <b>Approve</b> creates the emails and the flow in Klaviyo as a draft, switched off. Nothing sends until you switch it on in Klaviyo yourself. The app can't switch flows on, change existing flows or delete anything.</p>
    <h2 class="fix-h">Waiting for approval <span class="muted">(${waiting.length})</span></h2>${waiting.length ? waiting.map(card).join("") : `<p class="muted">Nothing waiting.</p>`}
    <h2 class="fix-h">Created in Klaviyo <span class="muted">(${made.length})</span></h2>${made.length ? made.map(card).join("") : `<p class="muted">Nothing created yet.</p>`}`;
  if (d.packs.some((p) => p.running || p.status === "creating")) setTimeout(() => { if (state.page === "drafts" && !state.draftId) renderDrafts(); }, 3000);
}
async function renderDraft() {
  draftState.data = await api("/api/drafts");
  const d = draftState.data, p = d.packs.find((x) => x.id === state.draftId);
  if (!p) { location.hash = "#drafts"; return; }
  draftState.current = p;
  const [cls, label] = DRAFT_BADGE[draftStatus(p)] || ["skip", p.status];
  const emails = [...messages(p.steps)].filter((m) => m.kind === "email");
  if (!emails.some((m) => m.message_id === state.pvId)) state.pvId = emails[0] ? emails[0].message_id : null;
  const hist = draftHist(p);
  $("#main").innerHTML = `
    <p class="eyebrow"><a href="#drafts">← New flows to approve</a></p>
    <div class="flow-head"><div><h1>${esc(p.flow_name)} <span class="stat ${cls}">${esc(label)}</span></h1>
      <p class="meta">${esc(p.trigger)}.${p.flow_filter ? ` Only if: ${esc(p.flow_filter)}.` : ""}</p></div></div>
    <div class="panel draft-top"><p>${esc(p.summary)}</p>${p.replaces ? `<p class="muted">${esc(p.replaces)}</p>` : ""}
      ${p.error ? `<p class="flag high">${esc(p.error)}</p>` : ""}${draftActions(p, d)}
      ${p.status === "created" && (p.after || []).length ? `<details class="fix-steps"><summary>Before you switch it on</summary><ol>${p.after.map((x) => `<li>${esc(x)}</li>`).join("")}</ol></details>` : ""}
      ${hist ? `<details class="fix-steps"><summary>History</summary><ul class="fix-hist">${hist}</ul></details>` : ""}</div>
    <div class="journey-wrap"><div class="journey">${renderSteps(p.steps)}</div>
      <aside class="pane" aria-label="Email preview">${state.pvId ? `
        <div class="pane-head"><div><p class="eyebrow" id="pane-name"></p><h3 id="pane-subject"></h3></div>
          <div class="seg seg-light" id="pane-width"><button type="button" data-w="600">Desktop</button><button type="button" data-w="375">Phone</button></div></div>
        <p class="sample-note" id="pane-note"></p>
        <div class="frame-wrap"><iframe id="pane-frame" title="Email preview" sandbox=""></iframe></div>` : `<p class="muted" style="padding:16px">No emails in this flow.</p>`}
      </aside></div>`;
  if (state.pvId) showInPane(state.pvId);
  if (draftStatus(p) === "creating") setTimeout(() => { if (state.draftId === p.id) renderDraft(); }, 3000);
}
document.addEventListener("click", async (e) => {
  const b = e.target.closest("[data-draft-approve]");
  if (!b) return;
  const p = draftState.data.packs.find((x) => x.id === b.dataset.draftApprove);
  if (!confirm(`Create “${p.flow_name}” in Klaviyo?\n\n${p.emails.length} emails and the flow are created as a draft, switched off. Nothing sends.`)) return;
  b.disabled = true; b.textContent = "Starting…";
  try { await api(`/api/drafts/${encodeURIComponent(p.id)}/approve`, { method: "POST" }); }
  catch (err) { alertInline(b, err.message); return; }
  state.draftId ? renderDraft() : renderDrafts();
});
