"use strict";
// Email builder: edit an Evoflows email's words in place, move/remove/duplicate its blocks, add brand blocks from the
// library, preview it as different customers, then save a draft -> approve -> publish. Layout and personalisation are
// locked (the server refuses a block whose tags or {{ }} tokens changed).

const B = { key: null, doc: null, blocks: [], subject: "", preview: "", from: "", mode: "edit", previewN: null, audience: "non", width: "600", sel: null, dirty: false, subjMap: [], overrides: {}, theme: null, vals: {}, hist: [], fut: [], typing: null, comments: [], showResolved: false, drag: null };

const unesc = (s) => { const t = document.createElement("textarea"); t.innerHTML = s; return t.value; };
const escText = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
const PH_IMG = "data:image/svg+xml;utf8," + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="120" height="120"><rect width="100%" height="100%" fill="#EEF0EE"/><text x="50%" y="54%" font-family="Arial" font-size="12" fill="#7A807A" text-anchor="middle">product photo</text></svg>');

function bTokLabel(t) {
  const inner = t.replace(/^\{\{-?\s*|\s*-?\}\}$/g, "");
  const map = { ".Tx.Data.first_name": "first name", ".title": "product name", ".qty": "qty", ".line_total": "line price", ".price": "price",
    ".Tx.Data.total": "basket total", ".Tx.Data.order.first_item.title": "product name", ".Tx.Data.recovery_url": "basket link" };
  if (inner.includes("(index .Tx.Data.items 0).title")) return "product name";
  return map[inner] || inner.replace(".Tx.Data.", "").replace(/_/g, " ");
}
function subjToText(s) {
  B.subjMap = [];
  return s.replace(/\{\{ if \.Tx\.Data\.first_name \}\}, \{\{ \.Tx\.Data\.first_name \}\}\{\{ end \}\}|\{\{.*?\}\}/g, (m) => {
    const label = m.includes("first_name") && m.includes("if") ? "[, first name]" : `[${bTokLabel(m)}]`;
    B.subjMap.push([label, m]); return label;
  });
}
function textToSubj(t) { let s = t; for (const [label, tok] of B.subjMap) s = s.replace(label, tok); return s; }

function blockHtml(b) { return b.segs.map((x) => x[1]).join(""); }
function displayHtml(b, bi) {
  return b.segs.map(([k, v], si) => {
    if (k === "tag") {
      let out = dsFill(v, B.vals).replace(/src="\{\{[^"]*\}\}"/g, `src="${PH_IMG}"`).replace(/href="[^"]*"/g, 'href="#"');
      if (/^<img\b/i.test(v) && /src="https?:/.test(v) && !/eg-email-logo/.test(v)) out = out.replace(/^<img/i, `<img data-img="${bi}:${si}" title="Click to swap this image"`);
      return out;
    }
    if (k === "ctl") return "";
    if (k === "tok") return `<span class="tokchip" contenteditable="false" title="Filled in for each customer">${esc(bTokLabel(v))}</span>`;
    return `<span class="edt" contenteditable="true" spellcheck="true" data-b="${bi}" data-s="${si}">${esc(unesc(v))}</span>`;
  }).join("");
}

async function renderBuilder() {
  const key = state.editKey;
  if (B.key !== key || !B.doc) {
    $("#main").innerHTML = `<p class="muted">Loading the email…</p>`;
    try { await loadBuilder(key); } catch (err) { $("#main").innerHTML = `<p class="flag high">${esc(err.message)}</p>`; return; }
  }
  drawBuilder();
}
async function loadBuilder(key) {
  const d = await api(`/api/builder/${encodeURIComponent(key)}`);
  Object.assign(B, { key, doc: d, blocks: d.editing.blocks.map((x) => ({ src: x.src, segs: x.segments, meta: x.meta, set: x.settings, cond: x.cond || "" })), subject: subjToText(d.editing.subject),
    preview: d.editing.preview_text, from: d.editing.from_name, dirty: false, sel: null, overrides: d.design.overrides || {}, hist: [], fut: [], typing: null });
  bTheme();
  try { B.comments = (await api(`/api/builder/${encodeURIComponent(key)}/comments`)).comments; } catch (err) { B.comments = []; }
}
// ---- settings wrapper (mirrors builder.wrap on the server, which rebuilds it on save) ----
const DEF_SET = { pt: 0, pb: 0, al: "l", bg: "w" };
function isDefSet(s) { return !s || (s.pt === 0 && s.pb === 0 && s.al === "l" && s.bg === "w"); }
function wrapHtml(b) {
  const inner = blockHtml(b), s = b.set || DEF_SET;
  if (isDefSet(s) && !b.cond) return inner;
  const row = `<tr class="egb pt${s.pt} pb${s.pb} al${s.al} bg${s.bg}"><td${s.bg === "s" ? ' bgcolor="[[c:stone]]"' : ""} style="padding:${s.pt}px 0 ${s.pb}px 0;${s.al === "c" ? "text-align:center;" : ""}"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">${inner}</table></td></tr>`;
  const c = (B.doc.conds_go || {})[b.cond];
  return b.cond && c ? `{{ if ${c} }}${row}{{ end }}` : row;
}
function blockLabel(b) { return `${b.meta.kind}: ${(b.meta.summary || "").slice(0, 50)}`; }
function condLabel(k) { const c = (B.doc.conds || []).find((x) => x.key === k); return c ? c.label : ""; }
// ---- undo / redo ----
function bSnap() { return JSON.stringify({ blocks: B.blocks, subject: B.subject, preview: B.preview, from: B.from, overrides: B.overrides }); }
function bPush() { B.hist.push(bSnap()); if (B.hist.length > 100) B.hist.shift(); B.fut = []; }
function bRestore(snap) { const o = JSON.parse(snap); Object.assign(B, { blocks: o.blocks, subject: o.subject, preview: o.preview, from: o.from, overrides: o.overrides }); bTheme(); B.dirty = true; B.typing = null; drawBuilder(); }
function bUndo() { if (!B.hist.length) return; B.fut.push(bSnap()); bRestore(B.hist.pop()); }
function bRedo() { if (!B.fut.length) return; B.hist.push(bSnap()); bRestore(B.fut.pop()); }
function bTheme() {
  const ds = B.doc.design;
  B.theme = dsMerge(ds.brand, B.overrides);
  B.vals = dsValues(B.theme, ds.stacks);
  dsLoadFonts(B.theme, ds.stacks.families);
}
function flowOf(key) { return state.snap.flows.find((f) => isEvo(f) && [...messages(f.steps)].some((m) => m.message_id === key)); }
function quickChecks() {
  const html = B.blocks.map(wrapHtml).join("");
  const n = (re) => (html.match(re) || []).length;
  const w = [];
  if (n(/display:inline-block;padding:15px 30px/g) > 1) w.push(`${n(/display:inline-block;padding:15px 30px/g)} buttons: the design allows one primary button.`);
  if (n(/bgcolor="\[\[c:stone\]\]"/g) > 1) w.push(`${n(/bgcolor="\[\[c:stone\]\]"/g)} stone panels: the design allows at most one.`);
  if (!B.subject.trim()) w.push("The subject line is empty.");
  return w;
}
function drawBuilder() {
  const d = B.doc, f = flowOf(B.key), ed = d.editing;
  const st = { "approved build": ["skip", B.key.endsWith("_b") ? "Test version B, not edited yet" : "Approved build"], draft: ["todo", "Draft, waiting for approval"], approved: ["draft", "Approved, not published"], published: ["live", "Published"] }[ed.status] || ["skip", ed.status];
  const vrow = (v) => `<li><b>v${v.n}</b> <span class="stat ${{ draft: "todo", approved: "draft", published: "live" }[v.status] || "skip"}">${esc(v.status)}</span>
      <span class="muted small">saved by ${esc(v.by)} ${esc((v.at || "").slice(0, 16).replace("T", " "))}${v.approved_by ? ` · approved by ${esc(v.approved_by)}` : ""}${v.published_by ? ` · published by ${esc(v.published_by)} ${esc((v.published_at || "").slice(0, 16).replace("T", " "))}` : ""}</span>
      <span class="bv-actions"><button type="button" class="link-btn" data-bv-preview="${v.n}">Preview</button>
      ${v.status === "draft" || v.status === "replaced" ? `<button type="button" class="link-btn" data-bv-approve="${v.n}">Approve</button>` : ""}
      ${v.status === "approved" || (v.status === "superseded" && v.approved_by) ? `<button type="button" class="link-btn" data-bv-publish="${v.n}">${v.status === "superseded" ? "Publish again" : "Publish"}</button>` : ""}</span></li>`;
  const qc = B.dirty ? quickChecks() : [], checks = B.dirty ? { errors: [], warnings: [] } : d.checks || { errors: [], warnings: [] };
  $("#main").innerHTML = `
    <p class="eyebrow">${f ? `<a href="#flow/${esc(f.id)}">← ${esc(f.name)}</a> · ` : ""}<a href="#emails">All emails</a></p>
    <div class="flow-head"><div><h1>${esc(d.name)} <span class="stat ${st[0]}">${esc(st[1])}${ed.n ? ` · v${ed.n}` : ""}</span></h1>
      ${d.custom ? `<p class="flag medium" style="max-width:90ch">A new email: not used by any flow yet. Once published, a flow can send it by its key <code>${esc(B.key)}</code>.</p>` : ""}
      <p class="meta">Edit the words in place, move or remove blocks, add brand blocks. Save makes a draft; it goes to customers only after it's approved and published.${d.published_n ? ` Customers currently get v${d.published_n}.` : " Customers currently get the approved build."}</p></div></div>
    <div class="b-fields panel">
      <label>Subject line <input id="b-subject" value="${esc(B.subject)}" maxlength="200"></label>
      <label>Preview text <input id="b-preview" value="${esc(B.preview)}" maxlength="250"></label>
      <label>From <select id="b-from">${d.senders.map((s) => `<option ${s === B.from ? "selected" : ""}>${esc(s)}</option>`).join("")}</select></label>
      <p class="muted small">Words in [brackets] are filled in for each customer and can't be edited.</p>
    </div>
    <div class="b-bar">
      <div class="seg seg-light" id="b-mode">${[["edit", "Edit"], ["non", "Preview: not a member"], ["free", "Free member"], ["annual", "Annual member"]].map(([k, l]) => `<button type="button" data-bmode="${k}" aria-pressed="${(B.mode === "edit" ? "edit" : B.audience) === k}">${l}</button>`).join("")}</div>
      <div class="seg seg-light" id="b-width"><button type="button" data-bw="600" aria-pressed="${B.width === "600"}">Desktop</button><button type="button" data-bw="375" aria-pressed="${B.width === "375"}">Phone</button></div>
      <span class="b-undo"><button type="button" class="btn-line" id="b-undo" title="Undo (Ctrl+Z)" ${B.hist.length ? "" : "disabled"}>↶ Undo</button><button type="button" class="btn-line" id="b-redo" title="Redo (Ctrl+Shift+Z)" ${B.fut.length ? "" : "disabled"}>↷ Redo</button></span>
      <button type="button" class="btn" id="b-save" ${B.dirty ? "" : "disabled"}>Save draft</button>
      ${B.dirty ? `<span class="muted small">Unsaved changes</span>` : ""}
    </div>
    <div class="b-wrap">
      <div class="b-canvas" id="b-canvas" style="max-width:${B.width}px"></div>
      <aside class="b-side">
        ${checks.errors.length || checks.warnings.length || qc.length ? `<div class="panel"><h3>Checks</h3>${checks.errors.map((x) => `<div class="flag high">${esc(x)}</div>`).join("")}${[...new Set([...checks.warnings, ...qc])].map((x) => `<div class="flag medium">${esc(x)}</div>`).join("")}</div>` : ""}
        <div id="b-setp">${bSettingsPanel()}</div>
        <div id="b-comp">${bCommentsPanel()}</div>
        <details class="panel ds-panel" ${Object.keys(B.overrides).length ? "open" : ""}><summary><h3 style="display:inline">Design</h3> <span class="muted small">${Object.keys(B.overrides).length ? "this email has its own design" : "uses the brand theme"}</span></summary>
          <p class="muted small">Changes here apply to this email only and win over the <a href="#theme">brand theme</a>.</p>
          ${dsControls(B.theme, d.design.options, d.design.brand, "email")}
          ${Object.keys(B.overrides).length ? `<button type="button" class="btn-line" id="b-ds-brand">Use the brand theme again</button>` : ""}
          <div id="b-ds-checks"></div></details>
        <div class="panel"><h3>Add a block</h3><p class="muted small">Brand blocks cut from approved emails. Drag one into the email, or click to add it ${B.sel != null ? "after the selected block" : "above the footer"}.</p>
          ${d.library.filter((l) => !l.context || (l.context === "checkout" && f && f.trigger_type === "checkout_abandoned")).map((l) => `<div role="button" tabindex="0" class="lib-item" draggable="true" data-lib="${esc(l.id)}"><b>${esc(l.name)}</b><span class="muted small">${esc(l.meta.summary.slice(0, 60))}</span></div>`).join("")}</div>
        <div class="panel"><h3>Send a test</h3><input id="b-test-to" type="email" placeholder="you@evolutiongolf.co.uk" style="width:100%">
          <p class="muted small">Sends the last saved version (save first). Staff addresses only.</p><button type="button" class="btn-line" id="b-test">Send test</button><p id="b-test-out" class="muted small"></p></div>
        <div class="panel"><h3>Versions</h3><ul class="b-versions">${d.versions.map(vrow).join("") || `<li class="muted">No edits yet.</li>`}
          <li><b>${B.key.endsWith("_b") ? "Starting copy" : "Approved build"}</b> <span class="muted small">${B.key.endsWith("_b") ? "a copy of the email customers get now" : "the version signed off in the copy docs"}</span> <span class="bv-actions"><button type="button" class="link-btn" data-bv-preview="0">Preview</button>${d.published_n ? `<button type="button" class="link-btn" id="b-restore">Go back to this</button>` : ""}</span></li></ul>
          <p class="muted small">Publishing replaces the email on Evoflows; live flows use it from their next send. Every version is kept.</p></div>
      </aside></div>`;
  drawCanvas();
}
function drawCanvas() {
  const c = $("#b-canvas");
  if (!c) return;
  c.style.maxWidth = B.width + "px";
  if (B.mode !== "edit") {
    c.innerHTML = `<iframe id="b-frame" title="Preview" sandbox="" style="width:${B.width}px;height:1400px;border:0;background:#fff"></iframe>`;
    previewInto($("#b-frame"), B.previewN != null ? { n: B.previewN } : { html: B.blocks.map(wrapHtml).join(""), overrides: B.overrides });
    return;
  }
  c.innerHTML = B.blocks.map((b, i) => {
    const fixed = b.meta.kind === "Footer" || b.meta.kind === "Header";
    const s = b.set || DEF_SET, nc = B.comments.filter((c) => !c.resolved && !c.reply_to && c.block === blockLabel(b)).length;
    const st = `padding:${s.pt}px 0 ${s.pb}px 0;${s.bg === "s" ? `background:${B.vals["c:stone"] || "#F1F3F1"};` : ""}${s.al === "c" ? "text-align:center;" : ""}`;
    return `<div class="bblock${B.sel === i ? " sel" : ""}" data-bi="${i}">
      <div class="bblock-bar"><span class="bdrag" draggable="true" data-drag="${i}" title="Drag to move">⠿</span><span class="bk">${esc(b.meta.kind)}</span>${b.meta.only_if ? `<span class="bcond">Only if: ${esc(b.meta.only_if)}</span>` : ""}${b.cond ? `<span class="bcond aud">Only: ${esc(condLabel(b.cond))}</span>` : ""}${nc ? `<span class="bcom" title="Open comments">💬 ${nc}</span>` : ""}
        <span class="bctl"><button type="button" data-bop="up" data-bi="${i}" title="Move up" ${i === 0 ? "disabled" : ""}>↑</button><button type="button" data-bop="down" data-bi="${i}" title="Move down" ${i === B.blocks.length - 1 ? "disabled" : ""}>↓</button>
        ${fixed ? "" : `<button type="button" data-bop="dup" data-bi="${i}" title="Duplicate">⧉</button><button type="button" data-bop="del" data-bi="${i}" title="Remove">✕</button>`}</span></div>
      <div style="${st}"><table role="presentation" class="card" width="600" cellpadding="0" cellspacing="0" style="width:100%;background:transparent"><tbody>${displayHtml(b, i)}</tbody></table></div></div>`;
  }).join("");
}
async function previewInto(frame, body) {
  try {
    const r = await fetch(`/builder/${encodeURIComponent(B.key)}/preview`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ...body, audience: B.audience }) });
    frame.srcdoc = await r.text();
  } catch (err) { frame.srcdoc = `<p>${esc(err.message)}</p>`; }
}
function markDirty() { if (!B.dirty) { B.dirty = true; const s = $("#b-save"); if (s) { s.disabled = false; s.insertAdjacentHTML("afterend", `<span class="muted small">Unsaved changes</span>`); } } }

document.addEventListener("input", (e) => {
  if (state.page !== "edit") return;
  const t = e.target;
  if (!((t.classList && t.classList.contains("edt")) || ["b-subject", "b-preview", "b-from"].includes(t.id))) return;
  if (B.typing !== t) { bPush(); B.typing = t; bUndoButtons(); }
  if (t.classList && t.classList.contains("edt")) { B.blocks[+t.dataset.b].segs[+t.dataset.s][1] = escText(t.textContent); markDirty(); return; }
  if (t.id === "b-subject") { B.subject = t.value; markDirty(); }
  if (t.id === "b-preview") { B.preview = t.value; markDirty(); }
  if (t.id === "b-from") { B.from = t.value; markDirty(); }
});
document.addEventListener("change", (e) => {
  if (state.page !== "edit" || !e.target.closest('[data-ds-scope="email"]')) return;
  bSetTheme(dsRead(e.target.closest(".ds-controls"), B.theme));
});
function bSetTheme(t) {
  bPush(); B.overrides = dsDiff(t, B.doc.design.brand); bTheme(); B.dirty = true; drawBuilder();
  api("/api/design/check", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ theme: B.theme }) })
    .then((c) => { const el = $("#b-ds-checks"); if (el) el.innerHTML = dsChecksHtml(c); }).catch(() => {});
}
document.addEventListener("keydown", (e) => { if (state.page === "edit" && e.target.classList && e.target.classList.contains("edt") && e.key === "Enter") e.preventDefault(); });
document.addEventListener("paste", (e) => {  // plain text only, so no markup sneaks in
  if (state.page !== "edit" || !(e.target.classList && e.target.classList.contains("edt"))) return;
  e.preventDefault(); document.execCommand("insertText", false, (e.clipboardData || window.clipboardData).getData("text/plain").replace(/\s+/g, " "));
});
document.addEventListener("click", async (e) => {
  if (state.page !== "edit") return;
  if (e.target.closest("#b-canvas a")) e.preventDefault();
  const im = e.target.closest("img[data-img]");
  if (im && B.mode === "edit") {
    const [bi, si] = im.dataset.img.split(":").map(Number), seg = B.blocks[bi].segs[si];
    const cur = { src: (seg[1].match(/src="([^"]*)"/) || [])[1], alt: (seg[1].match(/alt="([^"]*)"/) || [])[1] || "" };
    const pick = await pickImage(cur);
    if (pick) {
      bPush();
      const attr = (s) => s.replace(/&/g, "&amp;").replace(/"/g, "&quot;");
      seg[1] = seg[1].replace(/src="[^"]*"/, `src="${attr(pick.src)}"`).replace(/alt="[^"]*"/, `alt="${attr(pick.alt)}"`);
      B.dirty = true; drawBuilder();
    }
    return;
  }
  const rs = e.target.closest("[data-ds-reset]");
  if (rs && rs.closest('[data-ds-scope="email"]')) { bSetTheme(dsReset(B.theme, B.doc.design.brand, rs.dataset.dsReset)); return; }
  if (e.target.id === "b-ds-brand") { bSetTheme(JSON.parse(JSON.stringify(B.doc.design.brand))); return; }
  const blk = e.target.closest(".bblock");
  const op = e.target.closest("[data-bop]");
  if (op) {
    const i = +op.dataset.bi, bl = B.blocks;
    if (op.dataset.bop === "del" && !confirm(`Remove this ${bl[i].meta.kind.toLowerCase()} block?`)) return;
    bPush();
    if (op.dataset.bop === "up" && i > 0) [bl[i - 1], bl[i]] = [bl[i], bl[i - 1]];
    if (op.dataset.bop === "down" && i < bl.length - 1) [bl[i + 1], bl[i]] = [bl[i], bl[i + 1]];
    if (op.dataset.bop === "dup") bl.splice(i + 1, 0, JSON.parse(JSON.stringify(bl[i])));
    if (op.dataset.bop === "del") bl.splice(i, 1);
    B.sel = null; B.dirty = true; drawBuilder(); return;
  }
  if (blk && !e.target.closest("[data-drag]")) {
    const i = +blk.dataset.bi;
    if (B.sel !== i) { B.sel = i; document.querySelectorAll(".bblock").forEach((x) => x.classList.toggle("sel", x === blk)); bSide(); }
    if (!e.target.closest(".edt")) return;
  }
  const lib = e.target.closest("[data-lib]");
  if (lib) {
    const footer = B.blocks.findIndex((b) => b.meta.kind === "Footer");
    const at = bAddLib(lib.dataset.lib, B.sel != null ? B.sel + 1 : footer >= 0 ? footer : B.blocks.length);
    const el = document.querySelector(`.bblock[data-bi="${at}"]`); if (el) el.scrollIntoView({ block: "center" });
    return;
  }
  const m = e.target.closest("[data-bmode]");
  if (m) { if (m.dataset.bmode === "edit") B.mode = "edit"; else { B.mode = "preview"; B.audience = m.dataset.bmode; B.previewN = null; } drawBuilder(); return; }
  const w = e.target.closest("[data-bw]");
  if (w) { B.width = w.dataset.bw; drawBuilder(); return; }
  if (e.target.id === "b-save") {
    const btn = e.target; btn.disabled = true; btn.textContent = "Saving…";
    try {
      await api(`/api/builder/${encodeURIComponent(B.key)}/save`, { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ subject: textToSubj(B.subject), preview_text: B.preview, from_name: B.from, overrides: B.overrides, blocks: B.blocks.map((b) => ({ src: b.src, html: blockHtml(b), settings: b.set || DEF_SET, cond: b.cond || "" })) }) });
      await loadBuilder(B.key); drawBuilder();
    } catch (err) { alertInline(btn, err.message); btn.textContent = "Save draft"; }
    return;
  }
  const pv = e.target.closest("[data-bv-preview]");
  if (pv) { B.mode = "preview"; B.previewN = +pv.dataset.bvPreview; drawBuilder(); window.scrollTo({ top: $("#b-canvas").offsetTop - 80 }); return; }
  const ap = e.target.closest("[data-bv-approve]"), pu = e.target.closest("[data-bv-publish]");
  if (ap || pu) {
    const n = +(ap || pu).dataset[ap ? "bvApprove" : "bvPublish"];
    if (pu && !confirm(`Publish v${n} to Evoflows?\n\nIt replaces this email for customers from the next send of any live flow that uses it.`)) return;
    (ap || pu).disabled = true;
    try { await api(`/api/builder/${encodeURIComponent(B.key)}/${ap ? "approve" : "publish"}/${n}`, { method: "POST" }); await loadBuilder(B.key); drawBuilder(); }
    catch (err) { alertInline(ap || pu, err.message); }
    return;
  }
  if (e.target.id === "b-restore") {
    if (!confirm("Go back to the approved build? It's published to Evoflows straight away; your versions stay in the history.")) return;
    try { await api(`/api/builder/${encodeURIComponent(B.key)}/restore-build`, { method: "POST" }); await loadBuilder(B.key); drawBuilder(); }
    catch (err) { alertInline(e.target, err.message); }
    return;
  }
  if (e.target.id === "b-test") {
    const to = ($("#b-test-to").value || "").trim(), out = $("#b-test-out"), n = B.doc.versions.length ? B.doc.versions[0].n : 0;
    e.target.disabled = true; out.textContent = "Sending…";
    try { const r = await api(`/api/builder/${encodeURIComponent(B.key)}/test/${n}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ to }) });
      out.textContent = r.status < 400 ? `Sent v${n} to ${to}.` : `Failed (${r.status}).`; }
    catch (err) { out.textContent = err.message; }
    e.target.disabled = false;
  }
});
window.addEventListener("beforeunload", (e) => { if (state.page === "edit" && B.dirty) { e.preventDefault(); e.returnValue = ""; } });

// ---------------- full editor: block settings, drag and drop, undo/redo keys, comments ----------------
function bUndoButtons() { const u = $("#b-undo"), r = $("#b-redo"); if (u) u.disabled = !B.hist.length; if (r) r.disabled = !B.fut.length; }
function bAddLib(id, at) {
  const l = B.doc.library.find((x) => x.id === id);
  if (!l) return null;
  bPush();
  B.blocks.splice(at, 0, { src: l.id, segs: JSON.parse(JSON.stringify(l.segments)), meta: l.meta, set: { ...DEF_SET }, cond: "" });
  B.sel = at; B.dirty = true; B.mode = "edit"; drawBuilder();
  return at;
}
function bSettingsPanel() {
  if (B.sel == null || !B.blocks[B.sel]) return `<div class="panel"><h3>Block settings</h3><p class="muted small">Click a block to set who sees it, its spacing, alignment and background.</p></div>`;
  const b = B.blocks[B.sel], s = b.set || DEF_SET, foot = b.meta.kind === "Footer";
  const sp = (k, label) => `<label>${label} <select data-bset="${k}">${B.doc.spaces.map((v) => `<option value="${v}" ${s[k] === v ? "selected" : ""}>${v ? v + " px" : "None"}</option>`).join("")}</select></label>`;
  return `<div class="panel b-set"><h3>Block settings <span class="muted small">${esc(b.meta.kind)}</span></h3>
    <label>Show this block to <select data-bset="cond" ${foot ? "disabled" : ""}><option value="">Everyone who gets this email</option>${B.doc.conds.map((c) => `<option value="${esc(c.key)}" ${b.cond === c.key ? "selected" : ""}>${esc(c.label)}</option>`).join("")}</select></label>
    ${foot ? `<p class="muted small">The footer goes to everyone: it carries the unsubscribe link.</p>` : ""}
    ${b.meta.only_if ? `<p class="muted small">Already inside this block: only if ${esc(b.meta.only_if)} (fixed).</p>` : ""}
    <div class="b-set-row">${sp("pt", "Space above")}${sp("pb", "Space below")}</div>
    <div class="b-set-row"><label>Align <select data-bset="al"><option value="l" ${s.al === "l" ? "selected" : ""}>Left</option><option value="c" ${s.al === "c" ? "selected" : ""}>Centre</option></select></label>
      <label>Background <select data-bset="bg"><option value="w" ${s.bg === "w" ? "selected" : ""}>White</option><option value="s" ${s.bg === "s" ? "selected" : ""}>Stone panel (one per email)</option></select></label></div>
    <p class="muted small">Preview as a member or non-member to check who sees what.</p></div>`;
}
function bCommentsPanel() {
  const roots = B.comments.filter((c) => !c.reply_to && (B.showResolved || !c.resolved));
  const replies = (id) => B.comments.filter((c) => c.reply_to === id);
  const nres = B.comments.filter((c) => !c.reply_to && c.resolved).length;
  const one = (c) => `<div class="bc${c.resolved ? " res" : ""}" data-cid="${c.id}"><div class="bc-head"><b>${esc(c.by)}</b> <span class="muted small">${esc((c.at || "").slice(0, 16).replace("T", " "))}</span></div>
      ${c.block ? `<button type="button" class="link-btn small bc-block" data-cblock="${esc(c.block)}">${esc(c.block)}</button>` : ""}<p>${esc(c.text)}</p>
      ${replies(c.id).map((r) => `<div class="bc-reply"><b>${esc(r.by)}</b> <span class="muted small">${esc((r.at || "").slice(0, 16).replace("T", " "))}</span><p>${esc(r.text)}</p></div>`).join("")}
      <div class="bc-act"><button type="button" class="link-btn small" data-creply="${c.id}">Reply</button> <button type="button" class="link-btn small" data-cresolve="${c.id}" data-res="${c.resolved ? 0 : 1}">${c.resolved ? "Reopen" : "Resolve"}</button></div></div>`;
  const about = B.sel != null && B.blocks[B.sel] ? blockLabel(B.blocks[B.sel]) : "";
  return `<div class="panel b-comments"><h3>Comments <span class="muted small">${roots.filter((c) => !c.resolved).length} open</span></h3>
    ${roots.map(one).join("") || `<p class="muted small">No comments yet.</p>`}
    ${nres ? `<button type="button" class="link-btn small" id="bc-toggle">${B.showResolved ? "Hide" : "Show"} ${nres} resolved</button>` : ""}
    <textarea id="bc-text" rows="3" placeholder="Comment for whoever approves this email…" maxlength="2000"></textarea>
    <p class="muted small" id="bc-about" data-about="${esc(about)}">${about ? `About: ${esc(about)}` : "About the whole email (select a block to comment on it)"}</p>
    <button type="button" class="btn-line" id="bc-add">Add comment</button></div>`;
}
document.addEventListener("keydown", (e) => { if (state.page === "edit" && e.key === "Enter" && e.target.matches && e.target.matches(".lib-item")) { e.preventDefault(); e.target.click(); } });
document.addEventListener("focusout", (e) => { if (state.page === "edit" && B.typing === e.target) B.typing = null; });
document.addEventListener("change", (e) => {
  if (state.page !== "edit") return;
  const k = e.target.dataset && e.target.dataset.bset;
  if (!k || B.sel == null) return;
  bPush();
  const b = B.blocks[B.sel];
  if (k === "cond") b.cond = e.target.value;
  else b.set = { ...(b.set || DEF_SET), [k]: k === "pt" || k === "pb" ? +e.target.value : e.target.value };
  B.dirty = true; drawBuilder();
});
document.addEventListener("keydown", (e) => {
  if (state.page !== "edit" || !(e.ctrlKey || e.metaKey)) return;
  const k = e.key.toLowerCase();
  if (k === "z" || k === "y") {
    if (["bc-text", "b-test-to"].includes(e.target.id)) return;  // their own native undo
    e.preventDefault();
    if (k === "y" || e.shiftKey) bRedo(); else bUndo();
  }
  if (k === "s") { e.preventDefault(); const sv = $("#b-save"); if (sv && !sv.disabled) sv.click(); }
});
// drag and drop: the ⠿ handle moves a block; library items drop in
function bDropIndex(e) {
  const blk = e.target.closest && e.target.closest(".bblock");
  if (!blk) return null;
  const r = blk.getBoundingClientRect(), i = +blk.dataset.bi;
  return { el: blk, at: e.clientY < r.top + r.height / 2 ? i : i + 1, before: e.clientY < r.top + r.height / 2 };
}
function bClearDrop() { document.querySelectorAll(".bblock.drop-before,.bblock.drop-after").forEach((x) => x.classList.remove("drop-before", "drop-after")); }
document.addEventListener("dragstart", (e) => {
  if (state.page !== "edit") return;
  const h = e.target.closest && e.target.closest("[data-drag]"), l = e.target.closest && e.target.closest("[data-lib]");
  if (h) { B.drag = { from: +h.dataset.drag }; e.dataTransfer.effectAllowed = "move"; e.dataTransfer.setData("text/plain", "block"); const blk = h.closest(".bblock"); if (blk) e.dataTransfer.setDragImage(blk, 20, 20); }
  else if (l) { B.drag = { lib: l.dataset.lib }; e.dataTransfer.effectAllowed = "copy"; e.dataTransfer.setData("text/plain", "lib"); }
});
document.addEventListener("dragover", (e) => {
  if (state.page !== "edit" || !B.drag) return;
  const d = bDropIndex(e);
  if (!d) return;
  e.preventDefault();
  bClearDrop(); d.el.classList.add(d.before ? "drop-before" : "drop-after");
});
document.addEventListener("dragend", () => { bClearDrop(); B.drag = null; });
document.addEventListener("drop", (e) => {
  if (state.page !== "edit" || !B.drag) return;
  const d = bDropIndex(e), drag = B.drag;
  bClearDrop(); B.drag = null;
  if (!d) return;
  e.preventDefault();
  if (drag.lib) { bAddLib(drag.lib, d.at); return; }
  let to = d.at; const from = drag.from;
  if (to === from || to === from + 1) return;
  bPush();
  const [blk] = B.blocks.splice(from, 1);
  if (to > from) to -= 1;
  B.blocks.splice(to, 0, blk);
  B.sel = to; B.dirty = true; drawBuilder();
});
document.addEventListener("click", async (e) => {
  if (state.page !== "edit") return;
  if (e.target.id === "b-undo") { bUndo(); return; }
  if (e.target.id === "b-redo") { bRedo(); return; }
  if (e.target.closest(".bcom")) { const p = $(".b-comments"); if (p) p.scrollIntoView({ block: "center" }); return; }
  const cb = e.target.closest("[data-cblock]");
  if (cb) { const i = B.blocks.findIndex((b) => blockLabel(b) === cb.dataset.cblock); if (i >= 0) { B.sel = i; B.mode = "edit"; drawBuilder(); const el = document.querySelector(`.bblock[data-bi="${i}"]`); if (el) el.scrollIntoView({ block: "center" }); } else alertInline(cb, "That block has changed or moved out of the email."); return; }
  if (e.target.id === "bc-toggle") { B.showResolved = !B.showResolved; drawBuilder(); return; }
  const rp = e.target.closest("[data-creply]");
  if (rp) { const t = $("#bc-text"); t.dataset.reply = rp.dataset.creply; t.placeholder = "Reply…"; $("#bc-about").textContent = "Replying to a comment"; t.focus(); return; }
  const rs = e.target.closest("[data-cresolve]");
  if (rs) {
    try { B.comments = (await api(`/api/builder/${encodeURIComponent(B.key)}/comments/${rs.dataset.cresolve}/resolve`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ resolved: rs.dataset.res === "1" }) })).comments; drawBuilder(); }
    catch (err) { alertInline(rs, err.message); }
    return;
  }
  if (e.target.id === "bc-add") {
    const t = $("#bc-text"), text = t.value.trim();
    if (!text) return;
    e.target.disabled = true;
    try { B.comments = (await api(`/api/builder/${encodeURIComponent(B.key)}/comments`, { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, block: t.dataset.reply ? "" : $("#bc-about").dataset.about, reply_to: t.dataset.reply || null }) })).comments; drawBuilder(); }
    catch (err) { alertInline(e.target, err.message); e.target.disabled = false; }
  }
});
function bSide() { const a = $("#b-setp"), c = $("#b-comp"); if (a) a.innerHTML = bSettingsPanel(); if (c) { const t = $("#bc-text"), keep = t ? t.value : ""; c.innerHTML = bCommentsPanel(); if (keep) $("#bc-text").value = keep; } }

// ---------------- Emails page: every email the editor can open, and new emails from scratch ----------------
async function renderEmails() {
  $("#main").innerHTML = `<p class="muted">Loading…</p>`;
  const d = await api("/api/emails");
  const groups = {};
  for (const e of d.emails) { const g = e.custom ? "New emails" : d.flows[e.flow] || "Other"; (groups[g] = groups[g] || []).push(e); }
  const order = ["New emails", ...Object.values(d.flows), "Other"].filter((g) => groups[g]);
  const st = (e) => e.pending === "draft" ? `<span class="stat todo">Draft</span>` : e.pending === "approved" ? `<span class="stat draft">Approved</span>` : e.published_n ? `<span class="stat live">Published v${e.published_n}</span>` : `<span class="stat skip">${e.custom ? "Not published" : "Approved build"}</span>`;
  const row = (e) => `<tr data-edit="${esc(e.key)}"><td><a class="fname" href="#edit/${esc(e.key)}">${esc(e.name)}</a>${e.variant ? ` <span class="muted small">A/B version B</span>` : ""}</td>
    <td style="text-align:left">${esc((e.subject || "").replace(/\{\{.*?\}\}/g, "…").slice(0, 70))}</td><td style="text-align:left">${st(e)}</td>
    <td>${e.comments ? `💬 ${e.comments}` : ""}</td><td class="muted small">${esc((e.edited_at || "").slice(0, 10))}</td></tr>`;
  $("#main").innerHTML = `<p class="eyebrow">Email editor</p><h1>Emails</h1>
    <p class="muted" style="max-width:90ch">Every email on Evoflows, by flow, and emails composed from scratch. Open one to edit it; every change goes draft → approve → publish.</p>
    <div class="panel"><h3>New email</h3><div class="e-new">
      <label>Name <input id="e-name" maxlength="80" placeholder="e.g. Autumn trolley service reminder"></label>
      <label>Start from <select id="e-from"><option value="blank">A blank brand email (header, heading, paragraph, button, footer)</option>${d.emails.filter((e) => !e.variant).map((e) => `<option value="${esc(e.key)}">Copy of ${esc(e.name)}</option>`).join("")}</select></label>
      <button type="button" class="btn" id="e-create">Create</button></div>
      <p class="muted small">A new email isn't sent by any flow until a flow uses it. Built from brand blocks only, with the same checks as every email.</p></div>
    ${order.map((g) => `<h2>${esc(g)} <span class="muted">(${groups[g].length})</span></h2><div class="panel table-wrap"><table class="flows"><thead><tr><th>Email</th><th style="text-align:left">Subject</th><th style="text-align:left">Status</th><th>Comments</th><th>Last edit</th></tr></thead><tbody>${groups[g].map(row).join("")}</tbody></table></div>`).join("")}`;
}
document.addEventListener("click", async (e) => {
  if (state.page !== "emails") return;
  const tr = e.target.closest("tr[data-edit]");
  if (tr && !e.target.closest("a")) { location.hash = `#edit/${tr.dataset.edit}`; return; }
  if (e.target.id === "e-create") {
    e.target.disabled = true;
    try { const r = await api("/api/emails/new", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ name: $("#e-name").value, from: $("#e-from").value }) }); location.hash = `#edit/${r.key}`; }
    catch (err) { alertInline(e.target, err.message); e.target.disabled = false; }
  }
});
