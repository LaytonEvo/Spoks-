"use strict";
// A/B tests on Evoflows emails: version B is edited in the builder; a test splits one email step by the contact's
// random ID; results come from Evoflows' per-step numbers; ending it keeps one version.
const AB = { data: null };
const abPct = (v) => (v == null ? "–" : (v * 100).toFixed(1) + "%");

async function renderAbtests() {
  $("#main").innerHTML = `<p class="muted">Loading…</p>`;
  AB.data = await api("/api/abtests");
  const d = AB.data;
  const flowName = (k) => (d.flows.find((f) => f.key === k) || {}).name || k;
  const step = (ok, label, action) => `<li class="${ok ? "done" : ""}"><span class="tick">${ok ? "✓" : "○"}</span> ${label}${action ? ` ${action}` : ""}</li>`;
  const card = (t) => {
    const r = t.results, bPub = t.status !== "draft" || t.b_published;
    const res = r ? `<table class="mini ab-res"><thead><tr><th></th><th>Sends</th><th>Orders after</th><th>Conversion</th><th>Revenue</th><th>Per send</th><th>Unsub rate</th></tr></thead><tbody>
        ${["a", "b"].map((k) => `<tr class="${r.leader === k ? "lead" : ""}"><td><b>${k.toUpperCase()}</b> ${k === "a" ? "current email" : "test version"}</td><td>${n(r[k].sends)}</td><td>${n(r[k].orders)}</td><td>${abPct(r[k].conv)}</td><td>${gbp(r[k].revenue)}</td><td>${r[k].rps == null ? "–" : gbp(r[k].rps, 2)}</td><td>${abPct(r[k].unsub)}</td></tr>`).join("")}
      </tbody></table><p class="${r.enough && r.confidence >= 0.95 ? "" : "muted"}">${esc(r.verdict)} <span class="muted small">(${esc(TF_LABEL[r.period] || r.period)}, running ${r.days} days. Judged on orders, because Evoflows doesn't track opens or clicks yet.)</span></p>` : "";
    return `<article class="panel fix"><div class="fix-head"><span class="fix-kind">${esc(flowName(t.flow))}</span><h3>${esc(t.name)}</h3>
        <span class="stat ${{ running: "live", ended: "skip", cancelled: "skip", approved: "draft", draft: "todo" }[t.status]}">${esc(t.status)}</span></div>
      <p>Version A: <a href="#edit/${esc(t.template_a)}">the current email</a> · Version B: <a href="#edit/${esc(t.template_b)}">the test version</a> · B gets ${esc(t.share_b)}% of people${t.winner ? ` · kept ${esc(t.winner.toUpperCase())}` : ""}</p>
      ${t.status === "draft" || t.status === "approved" ? `<ol class="ab-steps">
        ${step(true, "Test created.")}
        ${step(t.status !== "draft", `Edit version B in the builder, then save, approve and publish it (customers don't see it until the test starts).`, `<a class="btn-line" href="#edit/${esc(t.template_b)}">Edit version B</a>`)}
        ${step(t.status === "approved", "Approve the test.", t.status === "draft" ? `<button type="button" class="btn-line" data-ab="approve" data-id="${esc(t.id)}">Approve</button>` : "")}
        ${step(false, "Start it: the flow is updated on Evoflows to split this email between A and B.", t.status === "approved" ? `<button type="button" class="btn" data-ab="start" data-id="${esc(t.id)}">Start the test</button>` : "")}
      </ol><button type="button" class="link-btn" data-ab="cancel" data-id="${esc(t.id)}">Cancel this test</button>` : ""}
      ${res}
      ${t.status === "running" ? `<div class="fix-actions"><button type="button" class="btn-line" data-ab="end" data-win="a" data-id="${esc(t.id)}">End: keep A</button><button type="button" class="btn-line" data-ab="end" data-win="b" data-id="${esc(t.id)}">End: keep B</button>
        <span class="muted small">Keeping B publishes its content under the original email; the flow goes back to one email.</span></div>` : ""}
      ${(t.history || []).length ? `<ul class="fix-hist">${t.history.map((h) => `<li>${esc(h.at.slice(0, 16).replace("T", " "))} · ${esc(h.by)} · ${esc(h.action)}</li>`).join("")}</ul>` : ""}</article>`;
  };
  $("#main").innerHTML = `<p class="eyebrow">A/B tests</p><h1>Test one email against another</h1>
    <p class="muted" style="max-width:90ch">Pick an email in a flow and write a version B in the builder. While the test runs, each person entering the flow is put in group A or B by their random contact ID, so the same person always gets the same version. Results are orders and revenue after each version. Opens and clicks come once Evoflows tracks them.</p>
    <p class="flag medium">Before the first test goes live, Luke needs to confirm the split works on Evoflows (requirements item 18). Until then, set tests up here but don't start them.</p>
    <div class="panel"><h3>New test</h3><div class="m-form ab-form">
      <label>Flow <select id="ab-flow">${d.flows.map((f) => `<option value="${esc(f.key)}">${esc(f.name)}</option>`).join("")}</select></label>
      <label>Email <select id="ab-step"></select></label>
      <label>Version B gets <select id="ab-share">${d.splits.map((s) => `<option value="${s}">${s}% of people</option>`).join("")}</select></label>
      <label>Name <input id="ab-name" placeholder="e.g. F3 E1 subject line" maxlength="80"></label>
      <button type="button" class="btn" id="ab-create">Create the test</button></div><p id="ab-out" class="muted small"></p></div>
    <h2 class="fix-h">Tests <span class="muted">(${d.tests.length})</span></h2>${d.tests.length ? d.tests.map(card).join("") : `<p class="muted">No tests yet.</p>`}`;
  abFillSteps();
}
function abFillSteps() {
  const f = AB.data.flows.find((x) => x.key === $("#ab-flow").value);
  $("#ab-step").innerHTML = (f ? f.emails : []).map((e) => `<option value="${esc(e.step)}">${esc(e.template)}${e.path ? ` (${esc(e.path)})` : ""}</option>`).join("") || `<option value="">No emails free to test</option>`;
}
document.addEventListener("change", (e) => { if (e.target.id === "ab-flow") abFillSteps(); });
document.addEventListener("click", async (e) => {
  if (e.target.id === "ab-create") {
    const out = $("#ab-out"); e.target.disabled = true;
    try {
      await api("/api/abtests", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ flow: $("#ab-flow").value, step: $("#ab-step").value, share: $("#ab-share").value, name: $("#ab-name").value }) });
      renderAbtests();
    } catch (err) { out.textContent = err.message; e.target.disabled = false; }
    return;
  }
  const b = e.target.closest("[data-ab]");
  if (!b) return;
  const act = b.dataset.ab;
  const msg = { start: "Start this test?\n\nThe flow on Evoflows is updated to split this email between A and B. It doesn't switch the flow on.", end: `End the test and keep ${(b.dataset.win || "").toUpperCase()}?`, cancel: "Cancel this test?" }[act];
  if (msg && !confirm(msg)) return;
  b.disabled = true;
  try { await api(`/api/abtests/${encodeURIComponent(b.dataset.id)}/${act}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ winner: b.dataset.win }) }); renderAbtests(); }
  catch (err) { alertInline(b, err.message); }
});
