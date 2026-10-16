"use strict";
// "Live" view of a simulated journey: the flow drawn as a diagram, the customer as a glowing dot moving along their
// route in order, lines on the route flowing as it passes, emails lighting up as they're sent, a clock showing the
// customer's date and time, and the exit marked. Paths not taken stay greyed (collapsed unless "Show every path").

const VIZ = { showAll: false, speed: 1, playing: false, raf: null, key: null };
const CW = 214, GAP = 26;
const NODE = { enter: [196, 40], wait: [168, 26], email: [190, 52], split: [26, 26], stub: [150, 34], end: [150, 40], exit: [176, 40], set: [168, 26] };

function vizShort(name) {
  const n = (name || "").replace(/^F\d+\s+/, "");
  const [a, b] = n.split(" · ");
  return [a, b || ""];
}
function vizWaitText(s) {
  const f = s.for || {};
  const parts = [["days", "day"], ["hours", "hour"], ["minutes", "min"]].filter(([k]) => f[k]).map(([k, l]) => `${f[k]} ${l}${f[k] === 1 || l === "min" ? "" : "s"}`);
  return `⏱ ${parts.join(" ") || "0 min"}${s.until_time ? ` · ${s.until_time}` : ""}`;
}
function vizCountEmails(steps) {
  let n = 0;
  for (const s of steps || []) { if (s.type === "email") n += 1; for (const b of s.branches || []) n += vizCountEmails(b.steps); }
  return n;
}

function vizLayout(f, res) {
  const nodes = {}, edges = [], visited = res.visited, msgs = Object.fromEntries([...messages(f.steps)].map((m) => [m.message_id, m]));
  const expanded = (s, b) => VIZ.showAll || visited.has(`${s.id}:${b.id}`);
  const units = (steps) => Math.max(1, ...(steps || []).map((s) => s.type === "split" ? s.branches.reduce((a, b) => a + (expanded(s, b) ? units(b.steps) : 1), 0) : 1));
  const add = (id, type, cx, y, extra) => { const [w, h] = NODE[type]; nodes[id] = { id, type, x: cx - w / 2, y, w, h, cx, ...extra }; return nodes[id]; };
  const edge = (from, to, label, branchOf) => edges.push({ from, to, label, branchOf });
  const place = (steps, disp, left, width, y, prev) => {
    (steps || []).forEach((s, i) => {
      const d = (disp || [])[i] || {}, cx = left + width / 2;
      if (s.type === "split") {
        add(s.id, "split", cx, y, { label: "" });
        prev.forEach((p) => edge(p, s.id));
        y += NODE.split[1] + GAP + 30;
        const total = s.branches.reduce((a, b) => a + (expanded(s, b) ? units(b.steps) : 1), 0) * CW;
        let bx = left + (width - total) / 2;
        const lasts = [], bottoms = [];
        s.branches.forEach((b, j) => {
          const db = (d.branches || [])[j] || {}, bw = (expanded(s, b) ? units(b.steps) : 1) * CW;
          const label = db.label || b.id, cond = db.condition || "";
          if (expanded(s, b) && (b.steps || []).length) {
            const startCount = edges.length;
            const r = place(b.steps, db.steps, bx, bw, y, [s.id]);
            const first = edges[startCount];
            if (first) { first.label = label; first.cond = cond; first.branchOf = `${s.id}:${b.id}`; }
            lasts.push(...r.prev); bottoms.push(r.y);
          } else {
            const id = `${s.id}:${b.id}:stub`, n = vizCountEmails(b.steps);
            add(id, "stub", bx + bw / 2, y, { label, sub: n ? `${n} email${n === 1 ? "" : "s"} · not taken` : "nothing sent", cond });
            edge(s.id, id, null, `${s.id}:${b.id}`);
            lasts.push(id); bottoms.push(y + NODE.stub[1] + GAP);
          }
          bx += bw;
        });
        prev = lasts; y = Math.max(...bottoms);
        return;
      }
      let n;
      if (s.type === "wait") n = add(s.id, "wait", cx, y, { label: vizWaitText(s) });
      else if (s.type === "email") { const [a, b] = vizShort((msgs[s.template] || {}).name || s.template); n = add(s.id, "email", cx, y, { label: a, sub: b, onlyIf: (msgs[s.template] || {}).only_if }); }
      else n = add(s.id, "set", cx, y, { label: s.type === "exit" ? "Leaves the flow" : `${s.attribute || s.type}` });
      prev.forEach((p) => edge(p, s.id));
      prev = [s.id]; y += n.h + GAP;
    });
    return { prev, y };
  };
  const width = units(f.definition.steps) * CW;
  add("__enter", "enter", width / 2, 12, { label: (f.definition.trigger || {}).type === "custom" ? "Event arrives" : "Enters the flow", sub: "" });
  const r = place(f.definition.steps, f.steps, 0, width, 12 + NODE.enter[1] + GAP, ["__enter"]);
  // the way out sits beside (left early) or below (finished) the last step they reached
  const tr = res.trail || [], lastReal = [...tr].reverse().find((x) => !x[0].startsWith("__") || x[0] === "__enter");
  const endT = tr[tr.length - 1];
  let height = r.y + 20;
  if (endT && lastReal && nodes[lastReal[0]]) {
    const a = nodes[lastReal[0]], isExit = endT[0] === "__exit";
    const x = isExit ? a.x + a.w + 40 + NODE.exit[0] / 2 : a.cx, y = isExit ? a.y + a.h / 2 - NODE.exit[1] / 2 : a.y + a.h + GAP;
    add(endT[0], isExit ? "exit" : "end", x, y, { label: isExit ? "Leaves the flow" : "Finished", sub: isExit ? (endT[2] === "notenter" ? "Doesn't meet the entry rule" : (endT[3] || "").split(":")[0].replace(/^Leaves$/, (endT[3] || "").split(": ")[1] || "")).slice(0, 34) : `${res.sends} email${res.sends === 1 ? "" : "s"}` });
    edge(lastReal[0], endT[0], null, null, true);
    height = Math.max(height, y + NODE.end[1] + 30);
  }
  const maxX = Math.max(width, ...Object.values(nodes).map((n) => n.x + n.w + 10));
  // edge geometry and whether the customer travelled it
  const onTrail = new Set(tr.map((x) => x[0]));
  for (const e of edges) {
    const a = nodes[e.from], b = nodes[e.to];
    if (!a || !b) continue;
    let d;
    if (b.type === "exit") { const y = a.y + a.h / 2; d = `M${a.x + a.w},${y} H${b.x}`; }  // beside the step where they left
    else {
      // from a split, turn just below the diamond, so branch labels sit clear above each branch
      const x1 = a.cx, y1 = a.y + a.h, x2 = b.cx, y2 = b.y, mid = a.type === "split" ? y1 + 16 : y2 - 16;
      d = Math.abs(x1 - x2) < 1 ? `M${x1},${y1} V${y2}` : `M${x1},${y1} V${mid - 8} Q${x1},${mid} ${x1 + Math.sign(x2 - x1) * 8},${mid} H${x2 - Math.sign(x2 - x1) * 8} Q${x2},${mid} ${x2},${mid + 8} V${y2}`;
    }
    e.d = d;
    e.route = onTrail.has(e.from) && onTrail.has(e.to) && (!e.branchOf || visited.has(e.branchOf));
  }
  return { nodes, edges, width: maxX, height };
}

function vizNode(n) {
  const cls = `vz-node vz-${n.type}`;
  if (n.type === "split") return `<g class="${cls}" data-vz="${esc(n.id)}"><rect x="${n.x}" y="${n.y}" width="${n.w}" height="${n.h}" rx="3" transform="rotate(45 ${n.cx} ${n.y + n.h / 2})"/></g>`;
  const text = (t, dy, c = "") => `<text x="${n.cx}" y="${n.y + dy}" text-anchor="middle" class="${c}">${esc(t)}</text>`;
  const clip = (t, max) => (t.length > max ? t.slice(0, max - 1) + "…" : t);
  let inner = "";
  if (n.type === "email") inner = `${text("✉  " + clip(n.label, 26), 21, "vz-t1")}${text(clip(n.sub, 30), 38, "vz-t2")}`;
  else if (n.type === "wait" || n.type === "set") inner = text(clip(n.label, 26), 17, "vz-t2");
  else if (n.type === "stub") inner = `${text(clip(n.label, 24), 15, "vz-t1")}${text(clip(n.sub, 26), 28, "vz-t2")}`;
  else inner = `${text(n.label, n.sub ? 17 : 25, "vz-t1")}${n.sub ? text(clip(n.sub, 30), 32, "vz-t2") : ""}`;
  return `<g class="${cls}" data-vz="${esc(n.id)}"><rect x="${n.x}" y="${n.y}" width="${n.w}" height="${n.h}" rx="${n.type === "wait" || n.type === "set" ? 13 : 7}"/>${inner}${n.onlyIf ? `<title>Only if ${esc(n.onlyIf)}</title>` : ""}</g>`;
}

function vizRender(f, res, sc) {
  const L = vizLayout(f, res);
  VIZ.layout = L; VIZ.res = res; VIZ.t0 = toLocal(sc.start).getTime();
  const edgeSvg = L.edges.filter((e) => e.d).map((e, i) => `<path id="vze-${i}" class="vz-edge${e.route ? " vz-route" : ""}" d="${e.d}" data-from="${esc(e.from)}" data-to="${esc(e.to)}"/>`).join("");
  const labels = L.edges.filter((e) => e.d && e.label).map((e) => {
    const b = L.nodes[e.to], a = L.nodes[e.from];
    return `<text class="vz-blabel${e.route ? " on" : ""}" x="${b.cx}" y="${b.y - 22}" text-anchor="middle">${esc(e.label)}</text>${e.cond && e.cond !== "everyone not matched above" ? `<text class="vz-bcond" x="${b.cx}" y="${b.y - 9}" text-anchor="middle">${esc(e.cond.length > 34 ? e.cond.slice(0, 33) + "…" : e.cond)}</text>` : ""}`;
  }).join("");
  return `<div class="panel vz-panel">
    <div class="vz-head"><div><h3>Watch it live</h3><p class="muted small">The dot is this customer. Lines flow as they travel; emails light up when they're sent.</p></div>
      <div class="vz-ctl"><span class="vz-clock" id="vz-clock">–</span>
        <button type="button" class="btn" id="vz-play">▶ Play</button><button type="button" class="btn-line" id="vz-replay">↺ Replay</button>
        <div class="seg seg-light" id="vz-speed">${[1, 2, 4].map((x) => `<button type="button" data-vzs="${x}" aria-pressed="${VIZ.speed === x}">${x}×</button>`).join("")}</div>
        <label class="chk small"><input type="checkbox" id="vz-all" ${VIZ.showAll ? "checked" : ""}> Show every path</label></div></div>
    <div class="vz-ticker" id="vz-ticker" aria-live="polite">Press play to send this customer through the flow.</div>
    <div class="vz-scroll"><svg class="vz" viewBox="-10 0 ${L.width + 20} ${L.height}" width="${L.width + 20}" height="${L.height}" role="img" aria-label="${esc(f.name)} as a diagram with this customer's route">
      <defs><filter id="vz-glow" x="-200%" y="-200%" width="500%" height="500%"><feGaussianBlur stdDeviation="4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>
      <g class="vz-edges">${edgeSvg}</g>${labels}<g class="vz-nodes">${Object.values(L.nodes).map(vizNode).join("")}</g>
      <circle id="vz-dot" r="7" cx="-50" cy="-50" filter="url(#vz-glow)"/></svg></div></div>`;
}

// ---------- animation ----------
function vizStop() { VIZ.playing = false; if (VIZ.raf) cancelAnimationFrame(VIZ.raf); VIZ.raf = null; const b = $("#vz-play"); if (b) b.textContent = "▶ Play"; }
function vizReset() {
  vizStop();
  document.querySelectorAll(".vz-node").forEach((n) => n.classList.remove("lit", "now", "skipped"));
  document.querySelectorAll(".vz-edge").forEach((e) => e.classList.remove("done", "flow"));
  const dot = $("#vz-dot"); if (dot) { dot.setAttribute("cx", -50); dot.setAttribute("cy", -50); }
  VIZ.i = 0; VIZ.seg = null;
}
function vizWhen(t) { return simWhen(t, VIZ.t0); }
function vizNodeEl(id) { return document.querySelector(`.vz-node[data-vz="${CSS.escape(id)}"]`); }
function vizCentre(id) { const n = VIZ.layout.nodes[id]; return n ? [n.cx, n.y + n.h / 2] : null; }
function vizArrive(i) {
  const [id, t, kind, extra] = VIZ.res.trail[i];
  document.querySelectorAll(".vz-node.now").forEach((n) => n.classList.remove("now"));
  const el = vizNodeEl(id);
  if (el) el.classList.add("lit", "now", ...(kind === "skip" ? ["skipped"] : []));
  $("#vz-clock").textContent = vizWhen(t);
  const tk = $("#vz-ticker");
  const n = VIZ.layout.nodes[id] || {};
  tk.className = `vz-ticker k-${kind}`;
  tk.textContent = { enter: `${vizWhen(t)} · ${VIZ.res.items[0].text}`, wait: `${vizWhen(t)} · Waiting: ${n.label ? n.label.replace("⏱ ", "") : ""}`,
    split: `${vizWhen(t)} · Splits: goes down “${(VIZ.res.items.find((x) => x.kind === "split" && x.t === t) || {}).text?.replace(/^Goes down “|”$/g, "") || extra}”`,
    email: `${vizWhen(t)} · ✉ Sent: ${extra}`, skip: `${vizWhen(t)} · Skipped an email (its condition isn't met)`,
    exit: `${vizWhen(t)} · ${extra || "Leaves the flow"}`, end: `${vizWhen(t)} · Finished after ${VIZ.res.sends} email${VIZ.res.sends === 1 ? "" : "s"}`,
    notenter: `${vizWhen(t)} · Doesn't enter this flow` }[kind] || "";
}
function vizPathBetween(a, b) {
  const p = document.querySelector(`.vz-edge[data-from="${CSS.escape(a)}"][data-to="${CSS.escape(b)}"]`);
  return p;
}
function vizStep(now) {
  if (!VIZ.playing) return;
  if (!document.getElementById("vz-dot")) { vizStop(); return; }  // left the page
  const tr = VIZ.res.trail;
  if (!VIZ.seg) {
    if (VIZ.i >= tr.length - 1) { vizArrive(tr.length - 1); vizStop(); $("#vz-play").textContent = "▶ Play again"; document.querySelectorAll(".vz-edge.vz-route").forEach((e) => e.classList.add("flow")); return; }
    const a = tr[VIZ.i][0], b = tr[VIZ.i + 1][0], path = vizPathBetween(a, b);
    const dwell = { email: 1100, split: 700, wait: 450, enter: 500, skip: 600 }[tr[VIZ.i][2]] || 400;
    VIZ.seg = { path, a, b, start: now + dwell / VIZ.speed, dur: (path ? Math.max(500, path.getTotalLength() * 4) : 600) / VIZ.speed };
  }
  const s = VIZ.seg;
  const k = Math.min(1, Math.max(0, (now - s.start) / s.dur));
  const dot = $("#vz-dot");
  let pt;
  if (s.path) { const len = s.path.getTotalLength(); pt = s.path.getPointAtLength(len * (k < 0.5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2)); }
  else { const A = vizCentre(s.a), B = vizCentre(s.b); pt = A && B ? { x: A[0] + (B[0] - A[0]) * k, y: A[1] + (B[1] - A[1]) * k } : { x: -50, y: -50 }; }
  dot.setAttribute("cx", pt.x); dot.setAttribute("cy", pt.y);
  if (s.path && k > 0) s.path.classList.add("flow");
  if (k >= 1) {
    if (s.path) s.path.classList.add("done");
    VIZ.i += 1; VIZ.seg = null; vizArrive(VIZ.i);
    const sc = $(".vz-scroll"), n = VIZ.layout.nodes[tr[VIZ.i][0]];
    if (sc && n) { const box = sc.getBoundingClientRect(), x = (n.cx / (VIZ.layout.width + 20)) * sc.scrollWidth; if (x < sc.scrollLeft + 60 || x > sc.scrollLeft + box.width - 60) sc.scrollTo({ left: x - box.width / 2, behavior: "smooth" }); }
  }
  VIZ.raf = requestAnimationFrame(vizStep);
}
function vizPlay() {
  if (matchMedia("(prefers-reduced-motion: reduce)").matches) {  // no motion: show the whole route at once
    VIZ.res.trail.forEach((_, i) => vizArrive(i)); document.querySelectorAll(".vz-edge.vz-route").forEach((e) => e.classList.add("done")); return;
  }
  if (VIZ.playing) { vizStop(); return; }
  if (!VIZ.res.trail || VIZ.i >= VIZ.res.trail.length - 1) vizReset();
  if (VIZ.i === 0 && !VIZ.seg) { vizArrive(0); const c = vizCentre("__enter"); const d = $("#vz-dot"); d.setAttribute("cx", c[0]); d.setAttribute("cy", c[1]); }
  VIZ.playing = true; $("#vz-play").textContent = "❚❚ Pause";
  VIZ.raf = requestAnimationFrame(vizStep);
}
document.addEventListener("click", (e) => {
  if (e.target.id === "vz-play") { vizPlay(); return; }
  if (e.target.id === "vz-replay") { vizReset(); vizPlay(); return; }
  const sp = e.target.closest("[data-vzs]");
  if (sp) { VIZ.speed = +sp.dataset.vzs; document.querySelectorAll("[data-vzs]").forEach((b) => b.setAttribute("aria-pressed", String(b === sp))); return; }
});
document.addEventListener("change", (e) => { if (e.target.id === "vz-all") { VIZ.showAll = e.target.checked; VIZ.autoplay = true; simRerender(); } });
