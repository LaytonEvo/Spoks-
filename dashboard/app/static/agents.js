"use strict";
// Agents: the manager's weekly brief (decide each recommendation), the QA & compliance report, approved actions,
// and the context the manager works from. Agents only report and draft; nothing here publishes or switches anything on.
const AG = { d: null, sev: "open", briefN: null, poll: null };
const SEV = { high: ["high", "High"], medium: ["medium", "Medium"], low: ["low", "Low"], info: ["skip", "Info"] };
const RATE = { good: ["live", "Good"], watch: ["todo", "Watch"], act: ["high", "Act"] };
const OWNER = { qa: "QA agent", email: "Email agent", product: "Product agent", design: "Design agent", data: "Data agent", layton: "Layton", luke: "Luke", dashboard: "Dashboard" };
const when = (s) => (s || "").slice(0, 16).replace("T", " ");

async function renderAgents() {
  $("#main").innerHTML = `<p class="muted">Loading…</p>`;
  AG.d = await api("/api/agents");
  if (AG.briefN && AG.d.brief && AG.d.brief.n !== AG.briefN) { try { AG.d.brief = await api(`/api/agents/brief/${AG.briefN}`); } catch (e) { AG.briefN = null; } }
  drawAgents();
  clearTimeout(AG.poll);
  if (AG.d.running.qa || AG.d.running.manager) AG.poll = setTimeout(() => { if (state.page === "agents") renderAgents(); }, 8000);
}
function drawAgents() {
  const d = AG.d;
  $("#main").innerHTML = `<p class="eyebrow">Agents</p><h1>Agents</h1>
    <p class="muted" style="max-width:90ch">A manager and its agents watch the emails and report to you. They check, analyse and draft; you decide. Nothing here publishes an email or switches a flow on.</p>
    ${agBrief(d)}${agQa(d)}${agActions(d)}${agTeam(d)}${agContext(d)}`;
}
function agBrief(d) {
  const r = d.brief;
  const head = `<div class="ag-head"><h2>Manager's brief</h2><span class="muted small">${d.schedule.manager} · ${esc(d.manager_model)}${d.slack ? " · also posted to Slack" : ""}</span>
    ${d.briefs.length > 1 ? `<select id="ag-briefs">${d.briefs.map((b) => `<option value="${b.n}" ${r && r.n === b.n ? "selected" : ""}>Brief ${b.n} · ${esc(when(b.at).slice(0, 10))}</option>`).join("")}</select>` : ""}
    <button type="button" class="btn-line" data-agrun="manager" ${d.running.manager || !d.ai ? "disabled" : ""}>${d.running.manager ? "Writing…" : "Write a brief now"}</button></div>`;
  if (!d.ai) return `<section class="panel">${head}<p class="flag medium">The manager needs ANTHROPIC_API_KEY in Railway.</p></section>`;
  if (!r) return `<section class="panel">${head}<p class="muted">No brief yet. The first is written on Monday at 07:00, or press “Write a brief now” (takes a minute or two).</p></section>`;
  const b = r.brief, dec = Object.fromEntries(d.decisions.map((x) => [x.rec, x]));
  const rec = (x, i) => {
    const dd = dec[x.id];
    return `<div class="ag-rec"><div class="ag-rec-h"><b>${i + 1}. ${esc(x.title)}</b> <span class="stat ${x.impact === "high" ? "high" : x.impact === "medium" ? "todo" : "skip"}">${esc(x.impact)} impact</span> <span class="muted small">${esc(x.effort)} effort · ${esc(OWNER[x.owner] || x.owner)}</span></div>
      <p>${esc(x.why)}</p><p class="small muted"><b>Evidence:</b> ${esc(x.evidence)}</p><p class="small"><b>Your decision:</b> ${esc(x.decision)}</p>
      ${dd ? `<p class="small"><span class="stat ${dd.decision === "approve" ? "live" : dd.decision === "reject" ? "high" : "todo"}">${{ approve: "Approved", reject: "Rejected", later: "Later" }[dd.decision]}</span> by ${esc(dd.by)} ${esc(when(dd.at))}${dd.note ? ` · “${esc(dd.note)}”` : ""} <button type="button" class="link-btn small" data-agchange="${esc(x.id)}">Change</button></p>`
      : `<div class="ag-dec" data-rec="${esc(x.id)}"><input placeholder="Note for the agents (optional)" maxlength="500"><button type="button" class="btn" data-agdec="approve">Approve</button><button type="button" class="btn-line" data-agdec="later">Later</button><button type="button" class="btn-line" data-agdec="reject">Reject</button></div>`}</div>`;
  };
  return `<section class="panel">${head}<p class="muted small">Written ${esc(when(r.at))} (${esc(r.reason)}) from the QA run of ${esc(when(r.qa_at))}.</p>
    <p class="ag-headline">${esc(b.headline)}</p>
    <div class="ag-status">${b.status.map((s) => `<div><span class="stat ${RATE[s.rating][0]}">${RATE[s.rating][1]}</span> <b>${esc(s.area)}</b><p class="small">${esc(s.summary)}</p></div>`).join("")}</div>
    ${b.recommendations.length ? `<h3>Recommendations</h3>${b.recommendations.map(rec).join("")}` : `<p class="muted">No recommendations this week.</p>`}
    ${b.questions.length ? `<h3>Questions for you</h3><ul>${b.questions.map((q) => `<li>${esc(q)}</li>`).join("")}</ul>` : ""}
    ${b.fyi.length ? `<h3>For your information</h3><ul class="small">${b.fyi.map((q) => `<li>${esc(q)}</li>`).join("")}</ul>` : ""}
    ${b.agent_feedback.length ? `<details><summary class="small">Feedback to the agents (${b.agent_feedback.length})</summary><ul class="small">${b.agent_feedback.map((q) => `<li>${esc(q)}</li>`).join("")}</ul></details>` : ""}</section>`;
}
function agQa(d) {
  const q = d.qa;
  const head = `<div class="ag-head"><h2>QA &amp; compliance</h2><span class="muted small">${d.schedule.qa}</span>
    <button type="button" class="btn-line" data-agrun="qa" ${d.running.qa ? "disabled" : ""}>${d.running.qa ? "Checking… (a few minutes)" : "Run checks now"}</button></div>`;
  if (!q) return `<section class="panel">${head}<p class="muted">No run yet. The first runs at 06:30, or press “Run checks now”.</p></section>`;
  const list = q.findings.filter((f) => AG.sev === "open" ? f.severity !== "info" : AG.sev === "new" ? f.status === "new" && f.severity !== "info" : f.severity === AG.sev);
  const trend = d.qa_history.slice(-14);
  const max = Math.max(1, ...trend.map((t) => t.counts.high + t.counts.medium + t.counts.low));
  return `<section class="panel">${head}
    <p class="muted small">Last run ${esc(when(q.at))} (${esc(q.reason)}): ${q.emails} emails, ${q.links_checked} links and images loaded${q.ai_checked ? `, ${q.ai_checked} changed email${q.ai_checked > 1 ? "s" : ""} read by Claude` : ""}, ${q.seconds}s.</p>
    <div class="ag-counts">${["high", "medium", "low", "info"].map((s) => `<button type="button" data-agsev="${s}" aria-pressed="${AG.sev === s}"><span class="stat ${SEV[s][0]}">${q.counts[s]}</span> ${SEV[s][1]}</button>`).join("")}
      <button type="button" data-agsev="open" aria-pressed="${AG.sev === "open"}">All open</button><button type="button" data-agsev="new" aria-pressed="${AG.sev === "new"}">New (${q.new})</button>
      <span class="muted small">${q.fixed ? `${q.fixed} fixed since the last run` : ""}</span>
      <span class="ag-spark" title="Open issues, last ${trend.length} runs">${trend.map((t) => `<i style="height:${Math.round(4 + 22 * (t.counts.high + t.counts.medium + t.counts.low) / max)}px" class="${t.counts.high ? "h" : ""}"></i>`).join("")}</span></div>
    ${list.length ? `<div class="table-wrap"><table class="ag-t"><thead><tr><th></th><th>Where</th><th>What</th><th>Fix</th><th>Since</th></tr></thead><tbody>
      ${list.map((f) => `<tr><td><span class="stat ${SEV[f.severity][0]}">${SEV[f.severity][1]}</span>${f.status === "new" && f.severity !== "info" ? ` <span class="m-badge">new</span>` : ""}</td>
        <td><a href="${esc(f.where)}">${esc(f.item)}</a><br><span class="muted small">${esc(f.area)}</span></td><td>${esc(f.detail)}</td><td class="small">${esc(f.fix || "")}</td><td class="small muted">${esc(f.since || "")}</td></tr>`).join("")}</tbody></table></div>`
      : `<p class="muted">Nothing here.</p>`}
    ${q.resolved && q.resolved.length ? `<details><summary class="small">Fixed since the last run (${q.resolved.length})</summary><ul class="small">${q.resolved.map((f) => `<li>${esc(f.item)}: ${esc(f.detail)}</li>`).join("")}</ul></details>` : ""}</section>`;
}
function agActions(d) {
  if (!d.actions.length) return "";
  const open = d.actions.filter((a) => !["done", "dropped"].includes(a.status)), closed = d.actions.filter((a) => ["done", "dropped"].includes(a.status));
  const row = (a) => `<tr><td><b>${esc(a.title)}</b>${a.note ? `<br><span class="small muted">“${esc(a.note)}”</span>` : ""}</td><td>${esc(OWNER[a.owner] || a.owner)}</td><td class="small muted">${esc(a.approved_by)} ${esc(when(a.approved_at).slice(0, 10))}</td>
    <td><select data-agact="${esc(a.rec)}">${["to do", "doing", "done", "dropped"].map((s) => `<option ${a.status === s ? "selected" : ""}>${s}</option>`).join("")}</select></td></tr>`;
  return `<section class="panel"><h2>Approved actions <span class="muted">(${open.length} open)</span></h2>
    <div class="table-wrap"><table class="ag-t"><thead><tr><th>Action</th><th>Owner</th><th>Approved</th><th>Status</th></tr></thead><tbody>${open.map(row).join("")}</tbody></table></div>
    ${closed.length ? `<details><summary class="small">Done or dropped (${closed.length})</summary><table class="ag-t"><tbody>${closed.map(row).join("")}</tbody></table></details>` : ""}</section>`;
}
function agTeam(d) {
  const rows = [["Manager", "live", "Weekly brief, your decisions, feedback to the agents", d.ai ? "" : "ANTHROPIC_API_KEY"],
    ["QA & compliance", "live", "Every email and flow, daily and after each change", ""],
    ["Email marketing", "planned", "Flow performance and copy, once F3 has 2–3 weeks of sends", "F3 live"],
    ["Product", "planned", "Shopify sales, abandoned products, stock, prices", "A read-only Shopify key (orders, products)"],
    ["Design", "planned", "Design changes tested through A/B tests", "Enough sends to test"],
    ["Data", "planned", "Tracking and data checks (part of QA until then)", "Opens and clicks on Evoflows"]];
  return `<section class="panel"><h2>The team</h2><div class="table-wrap"><table class="ag-t"><thead><tr><th>Agent</th><th>Status</th><th>Does</th><th>Waiting on</th></tr></thead><tbody>
    ${rows.map(([n, s, w, need]) => `<tr><td><b>${n}</b></td><td><span class="stat ${s === "live" ? "live" : "skip"}">${s}</span></td><td>${w}</td><td class="small muted">${esc(need)}</td></tr>`).join("")}</tbody></table></div></section>`;
}
function agContext(d) {
  return `<section class="panel"><details><summary><b>What the manager knows</b> <span class="muted small">standing context: keep it current so the brief is right</span></summary>
    <textarea id="ag-ctx" rows="10" maxlength="6000">${esc(d.context)}</textarea><button type="button" class="btn-line" id="ag-ctx-save">Save</button></details></section>`;
}
document.addEventListener("click", async (e) => {
  if (state.page !== "agents") return;
  const t = e.target;
  const run = t.closest("[data-agrun]");
  if (run) { run.disabled = true; try { await api(`/api/agents/run/${run.dataset.agrun}`, { method: "POST" }); setTimeout(renderAgents, 1500); } catch (err) { alertInline(run, err.message); run.disabled = false; } return; }
  const sv = t.closest("[data-agsev]"); if (sv) { AG.sev = sv.dataset.agsev; drawAgents(); return; }
  const dc = t.closest("[data-agdec]");
  if (dc) {
    const box = dc.closest(".ag-dec"); dc.disabled = true;
    try { await api("/api/agents/decide", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ brief: AG.d.brief.n, rec: box.dataset.rec, decision: dc.dataset.agdec, note: box.querySelector("input").value }) }); renderAgents(); }
    catch (err) { alertInline(dc, err.message); dc.disabled = false; }
    return;
  }
  const ch = t.closest("[data-agchange]"); if (ch) { AG.d.decisions = AG.d.decisions.filter((x) => x.rec !== ch.dataset.agchange); drawAgents(); return; }
  if (t.id === "ag-ctx-save") { t.disabled = true; try { await api("/api/agents/context", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text: $("#ag-ctx").value }) }); t.textContent = "Saved"; } catch (err) { alertInline(t, err.message); } t.disabled = false; }
});
document.addEventListener("change", async (e) => {
  if (state.page !== "agents") return;
  if (e.target.id === "ag-briefs") { AG.briefN = +e.target.value; AG.d.brief = await api(`/api/agents/brief/${AG.briefN}`); drawAgents(); return; }
  const a = e.target.dataset && e.target.dataset.agact;
  if (a) { try { AG.d.actions = (await api("/api/agents/action", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ rec: a, status: e.target.value }) })).actions; drawAgents(); } catch (err) { alertInline(e.target, err.message); } }
});
