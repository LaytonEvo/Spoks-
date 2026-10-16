"use strict";
// Journey simulator: "Test a journey" tab on each Evoflows flow.
// Runs a pretend customer through the flow's definition (what's on Evoflows, else the approved build), using the
// engine's rules from the contract: conditions are checked when each step is due, waits run from the previous step,
// "then send at" lands on that calendar day, quiet hours 21:00–08:00, the 16-hour gap delays (never skips), a
// flow's exit condition is checked before every step, checkout flows end on purchase and unsubscribing ends any run.
// It shows what should happen; Luke's staff tests are the proof that the engine does it.

const SIM = { byFlow: {}, pinned: {} };
const DAY = 864e5;
const EVENT_TYPES = {
  order: "Places an order", join_free: "Joins Free membership", join_annual: "Joins annual membership",
  cancel: "Cancels membership", unsubscribe: "Unsubscribes", checkout: "Starts a checkout",
};

function simFields(def) {
  const out = new Set();
  const walkC = (c) => {
    if (!c) return;
    if (c.field) out.add(c.field);
    (c.all || []).forEach(walkC); (c.any || []).forEach(walkC); if (c.not) walkC(c.not);
  };
  const walkS = (steps) => (steps || []).forEach((s) => { walkC(s.when); (s.branches || []).forEach((b) => { walkC(b.when); walkS(b.steps); }); });
  walkC((def.trigger || {}).when); walkC((def.exit || {}).when); walkS(def.steps);
  return out;
}

function simDefaults(f) {
  const d = new Date(); d.setDate(d.getDate() + ((2 - d.getDay() + 7) % 7 || 7)); d.setHours(18, 40, 0, 0);  // next Tuesday 18:40
  const custom = (f.definition.trigger || {}).type === "custom";
  return { start: d.toISOString().slice(0, 16), tier: custom && /annual/.test(f.id) ? "annual" : custom ? "free" : "none",
    basket: 129, items: { trolley: false, moto: false, clubs: false, used: false, shoes: false }, order_age: 1, till: false,
    ordered_before: false, first_name: true, opted_in: true, events: [] };
}

function toLocal(iso) { return new Date(iso); }  // the browser's clock (London for the team)

function stateAt(f, sc, t) {
  let tier = sc.tier, orders = sc.ordered_before ? 1 : 0, unsub = false;
  for (const e of sc.events) {
    if (e.at > t) continue;
    if (e.type === "join_free") tier = "free";
    if (e.type === "join_annual") tier = "annual";
    if (e.type === "cancel") tier = "none";
    if (e.type === "order") orders += 1;
    if (e.type === "unsubscribe") unsub = true;
  }
  const it = sc.items, trolley = it.trolley || it.moto;
  return {
    "flags.is_annual": tier === "annual", "flags.is_free_member": tier === "free", "flags.is_member": tier !== "none",
    "customer.member": tier !== "none", "customer.member_tier": tier === "annual" ? "annual_pro" : tier === "free" ? "free" : null,
    "flags.has_trolley": trolley, "flags.has_motocaddy_trolley": it.moto, "flags.has_clubs": it.clubs, "flags.has_used_clubs": it.used,
    "flags.has_shoes": it.shoes, "flags.has_hardware": trolley || it.clubs || it.used,
    "checkout.total": +sc.basket, "order.total": +sc.basket, "order.age_days": +sc.order_age + Math.floor((t - sc.t0) / DAY),
    "order.source": sc.till ? "pos" : "web", "customer.orders_count": orders,
    "event.data.tier": sc.tier === "annual" ? "annual_pro" : sc.tier, "contact.consent": unsub ? "blocklisted" : "ok",
    "contact.uuid": sc.group === "b" ? "f0000000" : "00000000",  // A/B tests split on the contact's random ID
  };
}

function evalC(c, st) {
  if (!c) return true;
  if (c.all) return c.all.every((x) => evalC(x, st));
  if (c.any) return c.any.some((x) => evalC(x, st));
  if (c.not) return !evalC(c.not, st);
  const v = st[c.field];
  if ("exists" in c) return (v != null && v !== "") === !!c.exists;
  if (v == null) return false;  // missing field = false (engine rule)
  if ("eq" in c) return v === c.eq;
  if ("ne" in c) return v !== c.ne;
  if ("gt" in c) return v > c.gt;
  if ("gte" in c) return v >= c.gte;
  if ("lt" in c) return v < c.lt;
  if ("lte" in c) return v <= c.lte;
  if ("in" in c) return c.in.includes(v);
  if ("nin" in c) return !c.nin.includes(v);
  if ("contains" in c) return Array.isArray(v) && v.includes(c.contains);
  if ("not_contains" in c) return Array.isArray(v) && !v.includes(c.not_contains);
  return false;
}

function addWait(t, s, st) {
  const f = s.when && !evalC(s.when, st) && s.else_for ? s.else_for : s.for || {};
  const d = new Date(t + ((f.hours || 0) * 60 + (f.minutes || 0)) * 60000);
  if (f.days) d.setDate(d.getDate() + f.days);
  if (s.until_time) {
    const [h, m] = s.until_time.split(":").map(Number);
    const x = new Date(d); x.setHours(h, m, 0, 0);
    if (x < d && !f.days) x.setDate(x.getDate() + 1);  // "send at" on the day the wait lands (next day if already past)
    return x.getTime();
  }
  return d.getTime();
}

function quiet(t, def) {
  const q = ((def.send_window || {}).quiet_hours) || ["21:00", "08:00"];
  const [qs, qe] = q.map((x) => x.split(":").map(Number));
  const d = new Date(t), mins = d.getHours() * 60 + d.getMinutes(), start = qs[0] * 60 + qs[1], end = qe[0] * 60 + qe[1];
  if (mins >= start || mins < end) {
    const x = new Date(d); if (mins >= start) x.setDate(x.getDate() + 1); x.setHours(qe[0], qe[1], 0, 0); return x.getTime();
  }
  return t;
}

function simulate(f, raw) {
  const def = f.definition, msgs = Object.fromEntries([...messages(f.steps)].map((m) => [m.message_id, m]));
  const t0 = toLocal(raw.start).getTime();
  const sc = { ...raw, t0, events: raw.events.map((e) => ({ ...e, at: t0 + (+e.day) * DAY + (() => { const [h, m] = (e.time || "12:00").split(":").map(Number); const base = new Date(t0); base.setHours(0, 0, 0, 0); return base.getTime() + h * 36e5 + m * 6e4 - t0; })() })).sort((a, b) => a.at - b.at) };
  const items = [], visited = new Set();
  const trig = def.trigger || {};
  const st0 = stateAt(f, sc, t0);
  items.push({ t: t0, kind: "enter", text: f.trigger });
  if (trig.when && !evalC(trig.when, st0)) return { entered: false, items: [{ t: t0, kind: "notenter", text: `Doesn't enter: needs ${f.flow_filter}.` }], visited, sends: 0 };
  const capFlow = def.max_per_contact_hours ?? 16, newsletter = def.consent === "newsletter_only";
  const checkoutFlow = /checkout|cart/.test(trig.type || "");
  let t = t0, last = null, done = null, sends = 0;
  const exitBy = (until) => {
    for (const e of sc.events) {
      if (e.at <= t || e.at > until) continue;
      if (e.type === "unsubscribe") return { t: e.at, text: "Unsubscribed: Evoflows blocks all further email and ends the run." };
      if (e.type === "order" && checkoutFlow) return { t: e.at, text: "Placed an order: checkout flows end on purchase." };
      if (e.type === "checkout" && !checkoutFlow && trig.type === "subscribed") items.push({ t: e.at, kind: "note", text: "Started a checkout. F3 can start now too; Evoflows can't take them out of this flow yet (requirements item 12), so both may send this week." });
    }
    if (def.exit && def.exit.when && evalC(def.exit.when, stateAt(f, sc, until))) {
      const ord = sc.events.find((e) => e.type === "order" && e.at > t && e.at <= until);
      return { t: ord ? ord.at : until, text: `Leaves: ${f.exit}.` };
    }
    return null;
  };
  const run = (steps) => {
    for (const s of steps || []) {
      if (done) return;
      if (s.type === "wait") {
        const next = addWait(t, s, stateAt(f, sc, t));
        const ex = exitBy(next); if (ex) { done = ex; return; }
        visited.add(s.id); t = next; continue;
      }
      if (s.type === "email") {
        const st = stateAt(f, sc, t);
        visited.add(s.id);
        const m = msgs[s.template] || { name: s.template, subject: "" };
        if (s.when && !evalC(s.when, st)) { items.push({ t, kind: "skip", text: `Skips “${m.name}”: only sent if ${m.only_if || "its condition is met"}.` }); continue; }
        const cap = s.max_per_contact_hours ?? capFlow;
        let send = t;
        const why = [];
        if (last != null && cap > 0 && send < last + cap * 36e5) { send = last + cap * 36e5; why.push(`held by the ${cap}-hour gap after the last email`); }
        const q = quiet(send, def); if (q !== send) { send = q; why.push("moved out of quiet hours (21:00–08:00)"); }
        const ex = send > t ? exitBy(send) : null; if (ex) { done = ex; return; }
        t = send;
        if (newsletter && !sc.opted_in) { items.push({ t, kind: "skip", text: `“${m.name}” not sent: they haven't opted in to marketing, so Evoflows refuses it.` }); continue; }
        if (stateAt(f, sc, t)["contact.consent"] !== "ok") { done = { t, text: "Unsubscribed: nothing more is sent." }; return; }
        items.push({ t, kind: "email", key: s.template, name: m.name, from: m.from_label, preview: m.preview_text,
          subject: (m.subject || "").replace("[, first name]", sc.first_name ? ", Sam" : ""), why: why.join(" and ") });
        last = t; sends += 1; continue;
      }
      if (s.type === "split") {
        const st = stateAt(f, sc, t);
        const branch = s.branches.find((b) => !b.when || evalC(b.when, st));
        visited.add(s.id);
        if (!branch) continue;
        visited.add(`${s.id}:${branch.id}`);
        items.push({ t, kind: "split", text: `Goes down “${simBranchName(f, s, branch)}”`, because: branch.when ? simBranchCond(f, s, branch) : "nothing earlier matched" });
        run(branch.steps);
        continue;
      }
      if (s.type === "exit") { done = { t, text: `Leaves the flow (${s.reason || "exit step"}).` }; return; }
      if (s.type === "set") { items.push({ t, kind: "note", text: `Sets ${s.attribute} = ${s.value}` }); visited.add(s.id); }
    }
  };
  run(def.steps);
  items.push(done ? { t: done.t, kind: "exit", text: done.text } : { t, kind: "end", text: `Reaches the end of the flow after ${sends} email${sends === 1 ? "" : "s"}.` });
  return { entered: true, items, visited, sends };
}

// branch labels and conditions come from the display steps (same order as the definition)
function simDisplaySplit(f, splitId) {
  let found = null;
  const walk = (def, disp) => {
    let di = 0;
    for (const s of def || []) {
      const d = disp[di]; di += 1;
      if (!d) return;
      if (s.type === "split" && d.kind === "split") {
        if (s.id === splitId) { found = d; return; }
        s.branches.forEach((b, i) => d.branches[i] && walk(b.steps, d.branches[i].steps));
      }
    }
  };
  walk(f.definition.steps, f.steps);
  return found;
}
function simBranchName(f, s, b) { const d = simDisplaySplit(f, s.id); const i = s.branches.indexOf(b); return (d && d.branches[i] && d.branches[i].label) || b.id; }
function simBranchCond(f, s, b) { const d = simDisplaySplit(f, s.id); const i = s.branches.indexOf(b); return (d && d.branches[i] && d.branches[i].condition) || ""; }

function simWhen(t, t0) {
  const d = new Date(t), day = Math.floor((new Date(t).setHours(0, 0, 0, 0) - new Date(t0).setHours(0, 0, 0, 0)) / DAY);
  return `${d.toLocaleDateString("en-GB", { weekday: "short", day: "numeric", month: "short" })}, ${d.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" })} · day ${day}`;
}

function simTimeline(f, res, sc, title) {
  const t0 = toLocal(sc.start).getTime();
  const row = (x) => {
    const when = `<span class="sim-when">${esc(simWhen(x.t, t0))}</span>`;
    if (x.kind === "email") return `<li class="sim-item k-email">${when}<div class="sim-card"><div class="msg-top"><span class="chan email">EMAIL</span><span class="msg-name">${esc(x.name)}</span>${x.from ? `<span class="msg-from">from ${esc(x.from)}</span>` : ""}</div>
      <p class="msg-subject">${esc(x.subject || "(no subject)")}</p>${x.preview ? `<p class="msg-preview">${esc(x.preview)}</p>` : ""}
      ${x.why ? `<p class="msg-cond">Due earlier; ${esc(x.why)}.</p>` : ""}<button type="button" class="link-btn" data-preview="${esc(x.key)}">Preview email →</button></div></li>`;
    const icon = { enter: "→", split: "⑂", skip: "–", exit: "■", end: "✓", note: "ℹ", notenter: "✕" }[x.kind] || "·";
    return `<li class="sim-item k-${x.kind}">${when}<div><span class="sim-icon">${icon}</span> ${esc(x.text)}${x.because ? `<span class="muted"> because ${esc(x.because)}</span>` : ""}</div></li>`;
  };
  return `<div class="sim-col"><h3>${esc(title)}</h3><p class="muted">${res.entered ? `${res.sends} email${res.sends === 1 ? "" : "s"}` : "Doesn't enter"}</p><ol class="sim-timeline">${res.items.map(row).join("")}</ol></div>`;
}

function simTree(f, visited) {
  const msgs = Object.fromEntries([...messages(f.steps)].map((m) => [m.message_id, m]));
  const walk = (steps, disp) => `<ul>${(steps || []).map((s, i) => {
    const on = visited.has(s.id) ? " on" : "";
    if (s.type === "wait") return `<li class="t-wait${on}">${esc((disp[i] || {}).label || "Wait")}</li>`;
    if (s.type === "email") return `<li class="t-email${on}">✉ ${esc((msgs[s.template] || {}).name || s.template)}</li>`;
    if (s.type === "split") return `<li class="t-split${on}">Split${(s.branches || []).map((b, j) => {
      const d = (disp[i] && disp[i].branches && disp[i].branches[j]) || {};
      const bo = visited.has(`${s.id}:${b.id}`) ? " on" : "";
      return `<div class="t-branch${bo}"><span class="t-bname">${esc(d.label || b.id)}</span> <span class="muted">${esc(d.condition || "")}</span>${walk(b.steps, d.steps || [])}</div>`;
    }).join("")}</li>`;
    return `<li class="${on}">${esc(s.type)}</li>`;
  }).join("")}</ul>`;
  return `<div class="panel sim-tree"><h3>The whole flow</h3><p class="muted">Highlighted: this customer's route. Greyed: paths they didn't take.</p>${walk(f.definition.steps, f.steps)}</div>`;
}

function simControls(f, sc) {
  const fields = simFields(f.definition), custom = (f.definition.trigger || {}).type === "custom";
  const has = (re) => [...fields].some((x) => re.test(x));
  const ctl = [];
  ctl.push(`<label>${esc(custom ? "Event arrives" : "Enters the flow")} <input type="datetime-local" data-sim="start" value="${esc(sc.start)}"></label>`);
  if (has(/^flags\.is_|^customer\.member|^event\.data\.tier/)) ctl.push(`<label>${custom ? "Joins as" : "Membership at the start"} <select data-sim="tier">
      ${(custom ? [["free", "Free"], ["annual", "Annual (£36)"]] : [["none", "Not a member"], ["free", "Free member"], ["annual", "Annual member"]]).map(([v, l]) => `<option value="${v}" ${sc.tier === v ? "selected" : ""}>${l}</option>`).join("")}</select></label>`);
  if (has(/^(checkout|order)\.total/)) ctl.push(`<label>${fields.has("checkout.total") ? "Basket value (£)" : "Order value (£)"} <input type="number" min="0" step="1" data-sim="basket" value="${esc(sc.basket)}"></label>`);
  if (has(/^flags\.has_/)) ctl.push(`<fieldset><legend>In the ${fields.has("checkout.total") ? "basket" : "order"}</legend>${[["trolley", "Trolley"], ["moto", "Motocaddy trolley"], ["clubs", "Clubs"], ["used", "Used clubs"], ["shoes", "Shoes"]].map(([k, l]) => `<label class="chk"><input type="checkbox" data-sim-item="${k}" ${sc.items[k] ? "checked" : ""}> ${l}</label>`).join("")}<span class="muted small">None ticked = accessories, balls, clothing</span></fieldset>`);
  if (fields.has("order.age_days")) ctl.push(`<label>Days from order to dispatch <input type="number" min="0" max="30" data-sim="order_age" value="${esc(sc.order_age)}"></label>`);
  if ((f.definition.trigger || {}).type && /^order_/.test(f.definition.trigger.type)) ctl.push(`<label class="chk"><input type="checkbox" data-sim="till" ${sc.till ? "checked" : ""}> Bought in the shop (till order)</label>`);
  if (fields.has("customer.orders_count")) ctl.push(`<label class="chk"><input type="checkbox" data-sim="ordered_before" ${sc.ordered_before ? "checked" : ""}> Has ordered before</label>`);
  if (f.definition.consent === "newsletter_only") ctl.push(`<label class="chk"><input type="checkbox" data-sim="opted_in" ${sc.opted_in ? "checked" : ""}> Opted in to marketing</label>`);
  if (fields.has("contact.uuid")) ctl.push(`<label>A/B test group <select data-sim="group"><option value="a" ${sc.group !== "b" ? "selected" : ""}>Group A (current email)</option><option value="b" ${sc.group === "b" ? "selected" : ""}>Group B (test version)</option></select></label>`);
  ctl.push(`<label class="chk"><input type="checkbox" data-sim="first_name" ${sc.first_name ? "checked" : ""}> We have their first name</label>`);
  const evs = sc.events.map((e, i) => `<div class="sim-ev"><select data-sim-ev="${i}" data-k="type">${Object.entries(EVENT_TYPES).map(([k, l]) => `<option value="${k}" ${e.type === k ? "selected" : ""}>${l}</option>`).join("")}</select>
      <label>day <input type="number" min="0" max="400" data-sim-ev="${i}" data-k="day" value="${esc(e.day)}"></label><input type="time" data-sim-ev="${i}" data-k="time" value="${esc(e.time)}">
      <button type="button" class="link-btn" data-sim-del="${i}" aria-label="Remove">✕</button></div>`).join("");
  return `<div class="panel sim-controls"><h3>The customer</h3>${ctl.join("")}
    <h3>What happens along the way</h3><p class="muted small">Day 0 is the day they enter.</p>${evs || `<p class="muted small">Nothing yet.</p>`}
    <button type="button" class="btn-line" id="sim-add">+ Add something that happens</button>
    <div class="sim-actions"><button type="button" class="btn-line" id="sim-pin">Pin this result to compare</button>${SIM.pinned[f.id] ? `<button type="button" class="link-btn" id="sim-unpin">Clear pinned</button>` : ""}
      <button type="button" class="link-btn" id="sim-reset">Start again</button></div></div>`;
}

function renderSim(f, el) {
  if (!f.definition) { el.innerHTML = `<p class="muted">This flow's definition isn't loaded yet. Press Refresh.</p>`; return; }
  const sc = SIM.byFlow[f.id] || (SIM.byFlow[f.id] = simDefaults(f));
  const res = simulate(f, sc);
  const pin = SIM.pinned[f.id];
  el.innerHTML = `<p class="muted" style="max-width:90ch">Set up a pretend customer and what they do, and see which emails they'd get, when, and why. It follows this flow's rules as they are on Evoflows: send times, quiet hours (21:00–08:00), the 16-hour gap between emails, and the reasons someone leaves. It shows what should happen; Luke's staff tests confirm the engine does it.</p>
    <div class="sim-wrap">${simControls(f, sc)}
      <div class="sim-results">${pin ? `<div class="sim-compare">${simTimeline(f, res, sc, "This customer")}${simTimeline(f, pin.res, pin.sc, "Pinned")}</div>` : simTimeline(f, res, sc, "This customer")}
        ${simTree(f, res.visited)}</div></div>`;
}

function simRerender() {
  const f = state.snap.flows.find((x) => x.id === state.flowId);
  const el = $("#tab-body");
  if (f && el && state.tab === "simulate") renderSim(f, el);
}
document.addEventListener("input", (e) => {
  const t = e.target, f = state.snap && state.snap.flows.find((x) => x.id === state.flowId);
  if (!f || !SIM.byFlow[f.id] || !t.closest(".sim-controls")) return;
  const sc = SIM.byFlow[f.id];
  if (t.dataset.sim) sc[t.dataset.sim] = t.type === "checkbox" ? t.checked : t.value;
  else if (t.dataset.simItem) sc.items[t.dataset.simItem] = t.checked;
  else if (t.dataset.simEv != null) sc.events[+t.dataset.simEv][t.dataset.k] = t.value;
  else return;
  if (t.type === "checkbox" || t.tagName === "SELECT") simRerender();
});
document.addEventListener("change", (e) => { if (e.target.closest && e.target.closest(".sim-controls") && e.target.type !== "checkbox" && e.target.tagName !== "SELECT") simRerender(); });
document.addEventListener("click", (e) => {
  const f = state.snap && state.snap.flows.find((x) => x.id === state.flowId);
  if (!f || state.tab !== "simulate") return;
  const sc = SIM.byFlow[f.id];
  if (e.target.id === "sim-add") { sc.events.push({ type: "order", day: 1, time: "12:00" }); simRerender(); }
  else if (e.target.dataset && e.target.dataset.simDel != null) { sc.events.splice(+e.target.dataset.simDel, 1); simRerender(); }
  else if (e.target.id === "sim-pin") { SIM.pinned[f.id] = { sc: JSON.parse(JSON.stringify(sc)), res: simulate(f, sc) }; simRerender(); }
  else if (e.target.id === "sim-unpin") { delete SIM.pinned[f.id]; simRerender(); }
  else if (e.target.id === "sim-reset") { SIM.byFlow[f.id] = simDefaults(f); simRerender(); }
});
