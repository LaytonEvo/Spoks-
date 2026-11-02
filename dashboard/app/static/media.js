"use strict";
// Brand & media library: brand rules, every image our emails use (and where), and checked uploads to Shopify Files.
const MEDIA = { data: null, src: null, tab: "unsplash", results: [], q: "", busy: false };

async function renderMedia() {
  $("#main").innerHTML = `<p class="muted">Loading…</p>`;
  [MEDIA.data, MEDIA.src] = await Promise.all([api("/api/media"), api("/api/media/sources").catch(() => null)]);
  const d = MEDIA.data, b = d.brand;
  const img = (x) => `<figure class="m-card"><div class="m-thumb"><img src="${esc(x.url)}" alt="${esc(x.alt)}" loading="lazy"></div>
    <figcaption><b>${esc(x.name)}</b><span class="muted small">${esc(x.alt || "no alt text")}</span>
    <span class="small">${x.used_in.length ? `In ${x.used_in.length} email${x.used_in.length === 1 ? "" : "s"}: ${x.used_in.slice(0, 4).map((k) => `<a href="#edit/${esc(k)}">${esc(k)}</a>`).join(", ")}${x.used_in.length > 4 ? "…" : ""}` : "Not used yet"}</span>
    ${x.uploaded ? `<span class="muted small">Added by ${esc(x.uploaded.by)} ${esc((x.uploaded.at || "").slice(0, 10))}</span>` : ""}
    ${x.uploaded && x.uploaded.ai ? `<span class="m-badge ai" title="${esc(x.uploaded.prompt || "")}">AI-generated</span>` : ""}
    ${x.uploaded && x.uploaded.licence && !x.uploaded.ai ? `<span class="small">${x.uploaded.licence_url ? `<a href="${esc(x.uploaded.licence_url)}" target="_blank" rel="noopener">${esc(x.uploaded.licence)}</a>` : esc(x.uploaded.licence)}${x.uploaded.credit ? ` · ${x.uploaded.credit_url ? `<a href="${esc(x.uploaded.credit_url)}" target="_blank" rel="noopener">${esc(x.uploaded.credit)}</a>` : esc(x.uploaded.credit)}` : ""}${x.uploaded.needs_credit ? ` <span class="m-badge warn">credit needed</span>` : ""}</span>` : ""}
    <button type="button" class="link-btn small" data-copy="${esc(x.url)}">Copy link</button></figcaption></figure>`;
  $("#main").innerHTML = `<p class="eyebrow">Brand & media</p><h1>The brand, and every image in the emails</h1>
    <div class="m-grid2">
      <div class="panel"><h3>Colours</h3><div class="m-swatches">${b.colours.map(([n, hex, use]) => `<div class="m-sw"><span style="background:${esc(hex)}"></span><b>${esc(n)}</b><code>${esc(hex)}</code><span class="muted small">${esc(use)}</span></div>`).join("")}</div>
        <h3>Fonts</h3><ul>${b.fonts.map(([f, fb, use]) => `<li><b>${esc(f)}</b> (falls back to ${esc(fb)}): ${esc(use)}</li>`).join("")}</ul></div>
      <div class="panel"><h3>Rules every email follows</h3><ul>${b.rules.map((r) => `<li>${esc(r)}</li>`).join("")}</ul>
        <p class="muted small">The email builder enforces these: you edit words and swap images, the design stays fixed.</p></div>
    </div>
    <div class="panel m-upload"><h3>Add an image</h3>
      <p class="muted small">Checked before it's uploaded: JPG or PNG, size, alt text, and white backgrounds for product shots and cut-outs (transparent ones are flattened onto white). Uploaded images go to Shopify Files and appear below, ready to swap into emails.</p>
      <div class="m-form"><input type="file" id="m-file" accept="image/jpeg,image/png">
        <label>What is it? <select id="m-kind"><option value="photo">Photo (lifestyle, full width)</option><option value="product">Product shot (white background)</option><option value="cutout">Cut-out (transparent or white)</option><option value="icon">Icon or logo</option></select></label>
        <label>Alt text <input id="m-alt" placeholder="e.g. A golfer pushing a Motocaddy trolley up the 18th" maxlength="250"></label>
        <button type="button" class="btn" id="m-go">Check and upload</button></div>
      <div id="m-out"></div>${d.can_upload ? "" : `<div class="m-addurl"><p class="muted small"><b>Uploading from here comes later</b> (an upload route on Evoflows, after F3 goes live). For now: upload the image in Shopify admin → Content → Files, copy its link, and paste it here. The same checks run before it joins the library. Choosing a file above still checks it without uploading.</p>
        <div class="m-form"><label>Shopify Files link <input id="m-url" placeholder="https://cdn.shopify.com/s/files/…/eg-email-….jpg" maxlength="500"></label>
        <button type="button" class="btn-line" id="m-addurl">Check and add</button></div></div>`}</div>
    <div id="m-find"></div>
    <h2>Images in use <span class="muted">(${d.images.length})</span></h2>
    <div class="m-images">${d.images.map(img).join("")}</div>`;
  drawFind();
}
document.addEventListener("click", async (e) => {
  const c = e.target.closest("[data-copy]");
  if (c) { try { await navigator.clipboard.writeText(c.dataset.copy); c.textContent = "Copied"; } catch (err) { c.textContent = c.dataset.copy; } return; }
  if (e.target.id === "m-addurl") {
    const out = $("#m-out"); e.target.disabled = true; out.innerHTML = `<p class="muted">Checking…</p>`;
    try {
      const r = await api("/api/media/add-url", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ url: $("#m-url").value, alt: $("#m-alt").value, kind: $("#m-kind").value }) });
      out.innerHTML = `${r.info && r.info.width ? `<p class="muted small">${r.info.format} · ${r.info.width} × ${r.info.height} px</p>` : ""}${r.errors.map((x) => `<div class="flag high">${esc(x)}</div>`).join("")}${r.warnings.map((x) => `<div class="flag medium">${esc(x)}</div>`).join("")}${r.uploaded ? `<div class="flag">Added ${esc(r.name)} to the library.</div>` : ""}`;
      if (r.uploaded) { MEDIA.data = null; setTimeout(renderMedia, 1200); }
    } catch (err) { out.innerHTML = `<p class="flag high">${esc(err.message)}</p>`; }
    e.target.disabled = false; return;
  }
  if (e.target.id !== "m-go") return;
  const f = $("#m-file").files[0], out = $("#m-out");
  if (!f) { out.innerHTML = `<p class="flag medium">Choose an image first.</p>`; return; }
  e.target.disabled = true; out.innerHTML = `<p class="muted">Checking…</p>`;
  const data = await new Promise((res) => { const r = new FileReader(); r.onload = () => res(r.result); r.readAsDataURL(f); });
  try {
    const r = await api("/api/media/upload", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ name: f.name, data, alt: $("#m-alt").value, kind: $("#m-kind").value }) });
    out.innerHTML = `${r.info && r.info.width ? `<p class="muted small">${r.info.format} · ${r.info.width} × ${r.info.height} px</p>` : ""}${r.errors.map((x) => `<div class="flag high">${esc(x)}</div>`).join("")}${r.warnings.map((x) => `<div class="flag medium">${esc(x)}</div>`).join("")}
      ${r.uploaded ? `<div class="flag">Uploaded as ${esc(r.name)}.</div>` : ""}`;
    if (r.uploaded) setTimeout(renderMedia, 1200);
  } catch (err) { out.innerHTML = `<p class="flag high">${esc(err.message)}</p>`; }
  e.target.disabled = false;
});

// ---------- image picker for the builder ----------
async function pickImage(current) {
  const d = MEDIA.data || (MEDIA.data = await api("/api/media"));
  return new Promise((resolve) => {
    const ov = document.createElement("div");
    ov.className = "modal"; ov.innerHTML = `<div class="modal-card m-picker" role="dialog" aria-modal="true"><div class="modal-head"><div><h2>Swap the image</h2><p class="muted">Pick one from the library. Add new ones on the Brand & media page.</p></div>
      <div class="modal-actions"><button type="button" class="btn-ghost" data-pk="cancel">Cancel</button></div></div>
      <label class="m-altrow">Alt text <input id="pk-alt" value="${esc(current.alt)}" maxlength="250"></label>
      <div class="m-images">${d.images.filter((x) => x.kind !== "logo").map((x) => `<button type="button" class="m-pick${x.url === current.src ? " on" : ""}" data-pk-url="${esc(x.url)}" data-pk-alt="${esc(x.alt)}"><img src="${esc(x.url)}" alt="" loading="lazy"><span class="small">${esc(x.name)}</span></button>`).join("")}</div></div>`;
    document.body.appendChild(ov);
    $("#pk-alt").addEventListener("input", (e) => { e.target.dataset.edited = "1"; });
    ov.addEventListener("click", (e) => {
      const p = e.target.closest("[data-pk-url]");
      // a different picture takes its own alt text, unless you typed your own
      if (p) { const typed = $("#pk-alt").dataset.edited === "1" && $("#pk-alt").value.trim(); const alt = typed || (p.dataset.pkUrl === current.src ? current.alt : p.dataset.pkAlt); ov.remove(); resolve({ src: p.dataset.pkUrl, alt }); return; }
      if (e.target.dataset.pk === "cancel" || e.target === ov) { ov.remove(); resolve(null); }
    });
  });
}

// ---------- find or make an image: stock search, AI scenes, then crop, alt text and attach ----------
function drawFind() {
  const el = $("#m-find"), src = MEDIA.src;
  if (!el || !src) return;
  if (MEDIA.tab === "unsplash" && !src.unsplash) MEDIA.tab = "openverse";
  const tabs = [["unsplash", "Unsplash", src.unsplash], ["openverse", "Openverse (Creative Commons)", true], ["ai", "AI scene", src.ai]];
  const card = (r, i) => `<button type="button" class="m-pick m-res" data-res="${i}" title="${esc(r.alt)}"><img src="${esc(r.thumb)}" alt="" loading="lazy">
      <span class="small">${esc(r.credit).slice(0, 60)}</span><span class="muted small">${esc(r.licence)}${r.needs_credit ? " · credit needed" : ""}</span></button>`;
  const stagedCard = (m) => `<figure class="m-card"><div class="m-thumb"><img src="/media/staged/${esc(m.sid)}" alt="" loading="lazy"></div>
      <figcaption><b>${esc((m.title || "").slice(0, 50))}</b>${m.ai ? `<span class="m-badge ai">AI-generated</span>` : `<span class="muted small">${esc(m.licence || "")}</span>`}
      <span class="muted small">${m.width} × ${m.height}${m.ready ? " · email-ready" : ""}${(m.steps || []).length ? " · " + esc(m.steps[m.steps.length - 1]) : ""}</span>
      <span><button type="button" class="link-btn small" data-wb="${esc(m.sid)}">Open</button> · <button type="button" class="link-btn small" data-hide="${esc(m.sid)}">Remove</button></span></figcaption></figure>`;
  el.innerHTML = `<div class="panel m-findp"><h3>Find or make an image</h3>
    <div class="seg seg-light">${tabs.map(([k, l, on]) => `<button type="button" data-mtab="${k}" aria-pressed="${MEDIA.tab === k}" ${on ? "" : "disabled title='Add the key in Railway to switch this on'"}>${l}</button>`).join("")}</div>
    ${MEDIA.tab === "ai" ? `<div class="m-form"><label>Describe the scene <input id="m-q" value="${esc(MEDIA.q)}" maxlength="500" placeholder="e.g. a quiet fairway at sunrise, mist over the trees, autumn colours"></label>
        <label>Shape <select id="m-aspect"><option value="hero">Full-width photo</option><option value="banner">Wide banner</option><option value="square">Square</option></select></label>
        <button type="button" class="btn" id="m-gen">Generate</button></div>
        <p class="muted small">Scenes only: courses, weather, light, landscapes. No products we sell, no brands, no people recommending anything, no text. Use real photos for products. AI images are labelled in the library. Each one costs a few pence.</p>`
      : `<div class="m-form"><label>Search ${MEDIA.tab === "unsplash" ? "Unsplash" : "Openverse"} <input id="m-q" value="${esc(MEDIA.q)}" maxlength="100" placeholder="e.g. golf course autumn, fairway sunrise, links course"></label>
        <button type="button" class="btn" id="m-search">Search</button></div>
        <p class="muted small">${MEDIA.tab === "unsplash" ? "Unsplash photos are free for commercial use, no credit needed." : "Only images whose licence allows commercial use and edits. Some need a credit line in the email (marked)."}</p>`}
    <div id="m-res-out">${MEDIA.busy ? `<p class="muted">Working…</p>` : MEDIA.results.length ? `<div class="m-images">${MEDIA.results.map(card).join("")}</div>` : ""}</div></div>
    ${src.staged.length ? `<h2>Working on <span class="muted">(${src.staged.length})</span></h2><p class="muted small">Images brought in or made here, not in the library yet. Open one to crop it, write alt text and add it.</p><div class="m-images">${src.staged.map(stagedCard).join("")}</div>` : ""}`;
}
async function refreshSrc() { MEDIA.src = await api("/api/media/sources"); drawFind(); }
async function workbench(sid) {
  const src = MEDIA.src, m = src.staged.find((x) => x.sid === sid) || (await api("/api/media/sources")).staged.find((x) => x.sid === sid);
  if (!m) return;
  const ov = document.createElement("div");
  ov.className = "modal";
  const draw = (cur, msg) => {
    ov.innerHTML = `<div class="modal-card m-wb" role="dialog" aria-modal="true"><div class="modal-head"><div><h2>${esc((cur.title || "Image").slice(0, 70))}</h2>
        <p class="muted small">${cur.ai ? `<span class="m-badge ai">AI-generated</span> ${esc(cur.prompt || "")}` : `${cur.page ? `<a href="${esc(cur.page)}" target="_blank" rel="noopener">${esc(cur.credit || "")}</a>` : esc(cur.credit || "")} · ${cur.licence_url ? `<a href="${esc(cur.licence_url)}" target="_blank" rel="noopener">${esc(cur.licence)}</a>` : esc(cur.licence || "")}${cur.needs_credit ? ` <span class="m-badge warn">credit needed in the email</span>` : ""}`}</p></div>
        <div class="modal-actions"><button type="button" class="btn-ghost" data-wbx="close">Close</button></div></div>
      <div class="m-wb-body"><div class="m-wb-img"><img src="/media/staged/${esc(cur.sid)}" alt=""><p class="muted small">${cur.width} × ${cur.height} px${(cur.steps || []).length ? " · " + esc(cur.steps.join(" → ")) : ""}</p></div>
      <div class="m-wb-side">
        ${msg ? `<div class="flag ${msg.ok ? "" : "high"}">${esc(msg.text)}</div>` : ""}
        <h3>1. Tidy it</h3>
        <p>${src.ai ? `<button type="button" class="btn-line" data-wbop="remove_bg">Remove background (onto white)</button> <button type="button" class="btn-line" data-wbop="upscale">Upscale ×2</button>` : `<span class="muted small">Background removal and upscaling need FAL_KEY.</span>`}</p>
        <h3>2. Crop to an email size</h3>
        <label>Size <select id="wb-crop">${src.crops.map((c) => `<option value="${c.key}" ${cur.crop === c.key ? "selected" : ""}>${esc(c.label)}</option>`).join("")}</select></label>
        <label>Keep in view <select id="wb-focus">${src.focus.map((f) => `<option ${cur.focus === f ? "selected" : ""}>${f}</option>`).join("")}</select></label>
        <button type="button" class="btn-line" data-wbop="crop">Crop and make email-ready</button>
        <h3>3. Alt text</h3>
        <textarea id="wb-alt" rows="2" maxlength="250" placeholder="What the image shows, in one sentence">${esc(cur.alt || "")}</textarea>
        ${src.alt ? `<button type="button" class="link-btn small" data-wbop="alt">Suggest alt text (Claude)</button>` : ""}
        <h3>4. Add it to the library</h3>
        ${cur.ready ? `<p class="small">a) <a class="btn-line" href="/media/staged/${esc(cur.sid)}?download=1">Download the email-ready file</a></p>
          <p class="small">b) Upload it in Shopify admin → Content → Files, then copy its link.</p>
          <label>c) Shopify Files link <input id="wb-url" placeholder="https://cdn.shopify.com/s/files/…" maxlength="500"></label>
          <label>What is it? <select id="wb-kind"><option value="photo">Photo</option><option value="cutout">Cut-out on white</option><option value="product">Product shot</option></select></label>
          <button type="button" class="btn" data-wbop="attach">Add to the library</button>
          <p class="muted small">Evoflows will add an upload route after F3 goes live; then this becomes one button.</p>` : `<p class="muted small">Crop it first: that makes the email-ready file (JPG, 1200 px wide, light enough for email).</p>`}
      </div></div></div>`;
  };
  let cur = m;
  draw(cur);
  document.body.appendChild(ov);
  ov.addEventListener("click", async (e) => {
    if (e.target === ov || e.target.dataset.wbx === "close") { ov.remove(); refreshSrc(); return; }
    const b = e.target.closest("[data-wbop]");
    if (!b) return;
    const op = b.dataset.wbop, alt = $("#wb-alt") ? $("#wb-alt").value : "";
    b.disabled = true; const t = b.textContent; b.textContent = "Working…";
    try {
      if (op === "alt") { const r = await api(`/api/media/staged/${cur.sid}/alt`, { method: "POST" }); cur.alt = r.alt; draw(cur); return; }
      if (op === "attach") {
        const r = await api(`/api/media/staged/${cur.sid}/attach`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ url: $("#wb-url").value, alt, kind: $("#wb-kind").value }) });
        if (r.uploaded) { ov.remove(); MEDIA.data = null; renderMedia(); return; }
        cur.alt = alt; draw(cur, { ok: false, text: r.errors.join(" ") }); return;
      }
      const body = op === "crop" ? { op, crop: $("#wb-crop").value, focus: $("#wb-focus").value } : { op };
      const r = await api(`/api/media/staged/${cur.sid}/edit`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
      cur = { ...r, alt: alt || r.alt, focus: body.focus || cur.focus }; draw(cur, { ok: true, text: op === "crop" ? "Cropped. Download it below." : "Done: this is a new copy (the earlier one is kept under Working on)." });
    } catch (err) { b.disabled = false; b.textContent = t; draw({ ...cur, alt }, { ok: false, text: err.message }); }
  });
}
document.addEventListener("click", async (e) => {
  if (state.page !== "media") return;
  const tab = e.target.closest("[data-mtab]");
  if (tab) { MEDIA.tab = tab.dataset.mtab; MEDIA.results = []; drawFind(); return; }
  if (e.target.id === "m-search" || e.target.id === "m-gen") {
    MEDIA.q = $("#m-q").value; MEDIA.busy = true; const aspect = $("#m-aspect") ? $("#m-aspect").value : "hero"; drawFind();
    try {
      if (MEDIA.tab === "ai") {
        const m = await api("/api/media/generate", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ prompt: MEDIA.q, aspect }) });
        MEDIA.busy = false; await refreshSrc(); workbench(m.sid);
      } else { MEDIA.results = (await api(`/api/media/search?source=${MEDIA.tab}&q=${encodeURIComponent(MEDIA.q)}`)).results; MEDIA.busy = false; drawFind(); }
    } catch (err) { MEDIA.busy = false; drawFind(); $("#m-res-out").innerHTML = `<p class="flag high">${esc(err.message)}</p>`; }
    return;
  }
  const r = e.target.closest("[data-res]");
  if (r) {
    const it = MEDIA.results[+r.dataset.res];
    r.disabled = true; r.classList.add("busy");
    try { const m = await api("/api/media/stage", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ source: it.source, id: it.id }) }); await refreshSrc(); workbench(m.sid); }
    catch (err) { alertInline(r, err.message); r.disabled = false; r.classList.remove("busy"); }
    return;
  }
  const wb = e.target.closest("[data-wb]"); if (wb) { workbench(wb.dataset.wb); return; }
  const hd = e.target.closest("[data-hide]"); if (hd) { await api(`/api/media/staged/${hd.dataset.hide}/hide`, { method: "POST" }); refreshSrc(); }
});
document.addEventListener("keydown", (e) => { if (state.page === "media" && e.key === "Enter" && e.target.id === "m-q") { e.preventDefault(); const b = $("#m-search") || $("#m-gen"); if (b) b.click(); } });
