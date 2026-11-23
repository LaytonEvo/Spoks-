"""Layton-approved design roll-outs to existing emails, as drafts (never published here).

A roll-out is a file in rollouts/: {email key: [[old block, new block], ...]}, cut from the approved builds before and after
the design change (tokenised, personalisation identical). Each email gets a new draft built on its newest version, so pending
fixes are kept: every old block must appear exactly once, else that email is skipped and reported. The drafts appear with the
agents' fixes, where Layton publishes them.
"""
import json
import pathlib

from . import builder, design

DIR = pathlib.Path(__file__).resolve().parent / "rollouts"
ROLLOUTS = {"members_b": "Members section Option B (Layton, 23 Nov 2026): small card badge, button after the lede, benefits grid"}


def _start(key):
    """The newest version: an open draft/approved one if it's the latest, else what's live (published or the approved build)."""
    rec = builder._load(key)
    vs = [v for v in rec["versions"] if v["status"] in ("draft", "approved", "published")]
    v = max(vs, key=lambda v: v["n"]) if vs else None
    if v is None or v["status"] == "published":
        return builder.live(key)
    return v


def _card(b):
    return 'alt="The Evolution Golf annual member card"' in b


def plan(name):
    if name not in ROLLOUTS:
        raise KeyError(name)
    pairs = json.loads((DIR / f"{name}.json").read_text())
    out = []
    for key, ps in pairs.items():
        v = _start(key)
        ht = builder._ht(v)
        counts = [ht.count(old) for old, _ in ps]
        done = all(ht.count(new) == 1 for _, new in ps)
        row = {"key": key, "based_on": v.get("n", 0), "based_status": v.get("status"), "blocks": len(ps), "found": counts,
               "ok": all(c == 1 for c in counts), "already": done}
        if not row["ok"] and not done:  # show what's there now, so a hand-made pair can carry the edit over
            row["current"] = [b for b in builder.split(ht)[1] if any(_card(b) and _card(old) for old, _ in ps)
                              or any(old.split(">", 1)[0] in b and c == 0 for (old, _), c in zip(ps, counts))][:3]
        out.append(row)
    return out


def apply(name, who):
    from . import agents
    pairs = json.loads((DIR / f"{name}.json").read_text())
    res = []
    for row in plan(name):
        if not row["ok"]:
            res.append({**row, "result": "skipped: already done" if row["already"] else "skipped: the section was edited, do it by hand"})
            continue
        key = row["key"]
        v = _start(key)
        ht = builder._ht(v)
        for old, new in pairs[key]:
            ht = ht.replace(old, new, 1)
        overrides = v.get("overrides") or {}
        html = design.render(ht, design.merge(design.brand(), overrides))
        with builder._lock:
            rec = builder._load(key)
            n = max([x["n"] for x in rec["versions"]] + [0]) + 1
            for x in rec["versions"]:
                if x["status"] in ("draft", "approved"):
                    x["status"] = "replaced"
            rec["versions"].append({"n": n, "status": "draft", "subject": v["subject"], "preview_text": v["preview_text"],
                                    "from_name": v["from_name"], "html_t": ht, "overrides": overrides, "html": html, "by": who,
                                    "at": builder._now(), "note": ROLLOUTS[name][:300]})
            builder._save(key, rec)
        c = builder.checks(html, v["subject"])
        kept = f" Built on v{row['based_on']} ({row['based_status']}), so its changes are included." if row["based_on"] else ""
        agents._record(key, [{"id": f"rollout:{name}:{key}", "detail": ROLLOUTS[name]}], "drafted", who,
                       (f"Draft v{n} saved.{kept} " + " ".join(c["warnings"] + c["errors"]))[:500], n,
                       [{"before": "", "text": ROLLOUTS[name]}])
        res.append({**row, "result": f"drafted v{n}", "warnings": c["warnings"] + c["errors"]})
    agents.qa_soon(f"roll-out {name}")
    return res
