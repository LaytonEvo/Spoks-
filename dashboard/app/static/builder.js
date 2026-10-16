"use strict";
// Email builder: edit an Evoflows email's words in place, move/remove/duplicate its blocks, add brand blocks from the
// library, preview it as different customers, then save a draft -> approve -> publish. Layout and personalisation are
// locked (the server refuses a block whose tags or {{ }} tokens changed).

const B = { key: null, doc: null, blocks: [], subject: "", preview: "", from: "", mode: "edit", previewN: null, audience: "non", width: "600", sel: null, dirty: false, subjMap: [], overrides: {}, theme: null, vals: {} };

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
  Object.assign(B, { key, doc: d, blocks: d.editing.blocks.map((x) => ({ src: x.src, segs: x.segments, meta: x.meta })), subject: subjToText(d.editing.subject),
    preview: d.editing.preview_text, from: d.editing.from_name, dirty: false, sel: null, overrides: d.design.overrides || {} });
  bTheme();
}
function bTheme() {
  const ds = B.doc.design;
  B.theme = dsMerge(ds.brand, B.overrides);
  B.vals = dsValues(B.theme, ds.stacks);
  dsLoadFonts(B.theme, ds.stacks.families);
}
function flowOf(key) { return state.snap.flows.find((f) => isEvo(f) && [...messages(f.steps)].some((m) => m.message_id === key)); }
function quickChecks() {
  const html = B.blocks.map(blockHtml).join("");
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
    <p class="eyebrow">${f ? `<a href="#flow/${esc(f.id)}">← ${esc(f.name)}</a>` : `<a href="#">← Overview</a>`}</p>
    <div class="flow-head"><div><h1>${esc(d.name)} <span class="stat ${st[0]}">${esc(st[1])}${ed.n ? ` · v${ed.n}` : ""}</span></h1>
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
      <button type="button" class="btn" id="b-save" ${B.dirty ? "" : "disabled"}>Save draft</button>
      ${B.dirty ? `<span class="muted small">Unsaved changes</span>` : ""}
    </div>
    <div class="b-wrap">
      <div class="b-canvas" id="b-canvas" style="max-width:${B.width}px"></div>
      <aside class="b-side">
        ${checks.errors.length || checks.warnings.length || qc.length ? `<div class="panel"><h3>Checks</h3>${checks.errors.map((x) => `<div class="flag high">${esc(x)}</div>`).join("")}${[...new Set([...checks.warnings, ...qc])].map((x) => `<div class="flag medium">${esc(x)}</div>`).join("")}</div>` : ""}
        <details class="panel ds-panel" ${Object.keys(B.overrides).length ? "open" : ""}><summary><h3 style="display:inline">Design</h3> <span class="muted small">${Object.keys(B.overrides).length ? "this email has its own design" : "uses the brand theme"}</span></summary>
          <p class="muted small">Changes here apply to this email only and win over the <a href="#theme">brand theme</a>.</p>
          ${dsControls(B.theme, d.design.options, d.design.brand, "email")}
          ${Object.keys(B.overrides).length ? `<button type="button" class="btn-line" id="b-ds-brand">Use the brand theme again</button>` : ""}
          <div id="b-ds-checks"></div></details>
        <div class="panel"><h3>Add a block</h3><p class="muted small">Brand blocks cut from approved emails. Added ${B.sel != null ? "after the selected block" : "above the footer"}.</p>
          ${d.library.filter((l) => !l.context || (l.context === "checkout" && f && f.trigger_type === "checkout_abandoned")).map((l) => `<button type="button" class="lib-item" data-lib="${esc(l.id)}"><b>${esc(l.name)}</b><span class="muted small">${esc(l.meta.summary.slice(0, 60))}</span></button>`).join("")}</div>
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
    previewInto($("#b-frame"), B.previewN != null ? { n: B.previewN } : { html: B.blocks.map(blockHtml).join(""), overrides: B.overrides });
    return;
  }
  c.innerHTML = B.blocks.map((b, i) => {
    const fixed = b.meta.kind === "Footer" || b.meta.kind === "Header";
    return `<div class="bblock${B.sel === i ? " sel" : ""}" data-bi="${i}">
      <div class="bblock-bar"><span class="bk">${esc(b.meta.kind)}</span>${b.meta.only_if ? `<span class="bcond">Only if: ${esc(b.meta.only_if)}</span>` : ""}
        <span class="bctl"><button type="button" data-bop="up" data-bi="${i}" title="Move up" ${i === 0 ? "disabled" : ""}>↑</button><button type="button" data-bop="down" data-bi="${i}" title="Move down" ${i === B.blocks.length - 1 ? "disabled" : ""}>↓</button>
        ${fixed ? "" : `<button type="button" data-bop="dup" data-bi="${i}" title="Duplicate">⧉</button><button type="button" data-bop="del" data-bi="${i}" title="Remove">✕</button>`}</span></div>
      <table role="presentation" class="card" width="600" cellpadding="0" cellspacing="0" style="width:100%;background:#fff"><tbody>${displayHtml(b, i)}</tbody></table></div>`;
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
  B.overrides = dsDiff(t, B.doc.design.brand); bTheme(); B.dirty = true; drawBuilder();
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
    if (op.dataset.bop === "up" && i > 0) [bl[i - 1], bl[i]] = [bl[i], bl[i - 1]];
    if (op.dataset.bop === "down" && i < bl.length - 1) [bl[i + 1], bl[i]] = [bl[i], bl[i + 1]];
    if (op.dataset.bop === "dup") bl.splice(i + 1, 0, JSON.parse(JSON.stringify(bl[i])));
    if (op.dataset.bop === "del" && confirm(`Remove this ${bl[i].meta.kind.toLowerCase()} block?`)) bl.splice(i, 1);
    B.sel = null; B.dirty = true; drawBuilder(); return;
  }
  if (blk && !e.target.closest(".edt")) { B.sel = +blk.dataset.bi; document.querySelectorAll(".bblock").forEach((x) => x.classList.toggle("sel", x === blk)); return; }
  const lib = e.target.closest("[data-lib]");
  if (lib) {
    const l = B.doc.library.find((x) => x.id === lib.dataset.lib);
    const footer = B.blocks.findIndex((b) => b.meta.kind === "Footer");
    const at = B.sel != null ? B.sel + 1 : footer >= 0 ? footer : B.blocks.length;
    B.blocks.splice(at, 0, { src: l.id, segs: JSON.parse(JSON.stringify(l.segments)), meta: l.meta });
    B.sel = at; B.dirty = true; B.mode = "edit"; drawBuilder();
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
        body: JSON.stringify({ subject: textToSubj(B.subject), preview_text: B.preview, from_name: B.from, overrides: B.overrides, blocks: B.blocks.map((b) => ({ src: b.src, html: blockHtml(b) })) }) });
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
