"use strict";
// Brand & media library: brand rules, every image our emails use (and where), and checked uploads to Shopify Files.
const MEDIA = { data: null };

async function renderMedia() {
  $("#main").innerHTML = `<p class="muted">Loading…</p>`;
  MEDIA.data = await api("/api/media");
  const d = MEDIA.data, b = d.brand;
  const img = (x) => `<figure class="m-card"><div class="m-thumb"><img src="${esc(x.url)}" alt="${esc(x.alt)}" loading="lazy"></div>
    <figcaption><b>${esc(x.name)}</b><span class="muted small">${esc(x.alt || "no alt text")}</span>
    <span class="small">${x.used_in.length ? `In ${x.used_in.length} email${x.used_in.length === 1 ? "" : "s"}: ${x.used_in.slice(0, 4).map((k) => `<a href="#edit/${esc(k)}">${esc(k)}</a>`).join(", ")}${x.used_in.length > 4 ? "…" : ""}` : "Not used yet"}</span>
    ${x.uploaded ? `<span class="muted small">Uploaded by ${esc(x.uploaded.by)} ${esc((x.uploaded.at || "").slice(0, 10))}</span>` : ""}
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
      <div id="m-out"></div>${d.can_upload ? "" : `<p class="flag medium">Uploading needs a Shopify key in Railway (SHOPIFY_STORE and SHOPIFY_ADMIN_TOKEN with write_files). Until then the checks still run, so you can test images.</p>`}</div>
    <h2>Images in use <span class="muted">(${d.images.length})</span></h2>
    <div class="m-images">${d.images.map(img).join("")}</div>`;
}
document.addEventListener("click", async (e) => {
  const c = e.target.closest("[data-copy]");
  if (c) { try { await navigator.clipboard.writeText(c.dataset.copy); c.textContent = "Copied"; } catch (err) { c.textContent = c.dataset.copy; } return; }
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
