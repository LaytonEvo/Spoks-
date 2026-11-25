"""Layton-approved design roll-outs to existing emails, as drafts (never published here).

A roll-out is a file in rollouts/: {email key: [[old block, new block], ...]}, cut from the approved builds before and after
the design change (tokenised). Each email gets a new draft built on its open draft (else what is live), so pending
fixes are kept: every old block must appear exactly once, else that email is skipped and reported. The drafts appear with the
agents' fixes, where Layton publishes them.
"""
import json
import pathlib
import re

from . import builder, design

DIR = pathlib.Path(__file__).resolve().parent / "rollouts"
ROLLOUTS = {"members_b": "Members section Option B (Layton, 23 Nov 2026): small card badge, button after the lede, benefits grid",
            "f3_electric": "Trolley checks: the battery 'Range' check only for electric trolleys; push trolleys see Boot and Hills as 1-2 (Layton, 23 Nov 2026)"}


def _start(key):
    """What the next draft builds on: the open (draft/approved) version if there is one, since it carries changes waiting to be
    published (a theme publish republishes the live version but leaves open drafts open), else what's live."""
    rec = builder._load(key)
    open_ = [v for v in rec["versions"] if v["status"] in ("draft", "approved")]
    if not open_:
        return builder.live(key)
    d = max(open_, key=lambda v: v["n"])
    # a real publish after the draft (not a theme republish, which copies the live version) makes the draft out of date
    later = [v for v in rec["versions"] if v["n"] > d["n"] and v.get("published_by") and not (v.get("note") or "").startswith("brand theme")]
    return builder.live(key) if later else d


SEG = re.compile(r"(<[^>]+>|\{\{.*?\}\})", re.S)


def _carry(ht, old, new):
    """The email's block that has old's exact layout (words may differ), and new with the same word edits applied.
    Returns (block now in the email, new block with edits, [(was, now)], [edits that couldn't be placed]) or None."""
    if ht.count(old) == 1:
        return old, new, [], []
    cands = [b for b in builder.split(ht)[1] if builder._tags(builder.unwrap(b)[0]) == builder._tags(old)
             and builder.tokens(builder.unwrap(b)[0]) == builder.tokens(old)]
    if len(cands) != 1:
        return None
    cur = builder.unwrap(cands[0])[0]
    a, b = SEG.split(old), SEG.split(cur)
    if len(a) != len(b):
        return None
    edits = [(x, y) for x, y in zip(a, b) if x != y]
    out, lost = new, []
    for was, now in edits:
        if out.count(was) == 1:
            out = out.replace(was, now, 1)
        else:
            lost.append((was, now))
    return cur, out, edits, lost


def plan(name):
    if name not in ROLLOUTS:
        raise KeyError(name)
    pairs = json.loads((DIR / f"{name}.json").read_text())
    out = []
    for key, ps in pairs.items():
        v = _start(key)
        ht = builder._ht(v)
        done = all(ht.count(new) == 1 for _, new in ps)
        res = [_carry(ht, old, new) for old, new in ps]
        ok = not done and all(r and not r[3] for r in res)
        out.append({"key": key, "based_on": v.get("n", 0), "based_status": v.get("status"), "already": done, "ok": ok,
                    "carried": [e for r in res if r for e in r[2]], "not_placed": [e for r in res if r for e in r[3]],
                    "unmatched": sum(1 for r in res if not r)})
    return out


def apply(name, who):
    from . import agents
    pairs = json.loads((DIR / f"{name}.json").read_text())
    res = []
    for row in plan(name):
        if not row["ok"]:
            res.append({**row, "result": "skipped: already done" if row["already"] else "skipped: couldn't place every edit, do it by hand"})
            continue
        key = row["key"]
        v = _start(key)
        ht = builder._ht(v)
        for old, new in pairs[key]:
            cur, new2, _, _ = _carry(ht, old, new)
            assert ht.count(cur) == 1
            ht = ht.replace(cur, new2, 1)
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


def correct(key, pairs, note, who):
    """The reviewer's word corrections to an email's open draft (e.g. undoing a fixer edit that broke a ruling), as a new
    draft for Layton to publish. Each 'now' text must appear exactly once; personalisation and layout can't change."""
    import html as htmllib
    from . import agents
    v = _start(key)
    ht = builder._ht(v)
    before_tokens = builder.tokens(ht)
    done = []
    for now, was in pairs:
        hits = [x for x in dict.fromkeys([now, htmllib.escape(now, quote=False)]) if ht.count(x) == 1]
        if not hits:
            raise ValueError(f"{key}: “{now[:60]}” isn't in the draft exactly once ({ht.count(now)} times).")
        ht = ht.replace(hits[0], htmllib.escape(was, quote=False) if hits[0] != now else was, 1)
        done.append({"before": now, "text": was})
    if builder.tokens(ht) != before_tokens or builder._tags(ht) != builder._tags(builder._ht(v)):
        raise ValueError(f"{key}: a correction touched layout or personalisation.")
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
                                "at": builder._now(), "note": f"Reviewer correction: {note}"[:300]})
        builder._save(key, rec)
    c = builder.checks(html, v["subject"])
    agents._record(key, [{"id": f"correction:{key}:{n}", "detail": f"Reviewer correction: {note}"}], "drafted", who,
                   (f"Draft v{n} saved, built on v{v.get('n', 0)}. " + " ".join(c["errors"] + c["warnings"]))[:500], n, done)
    return {"key": key, "n": n, "based_on": v.get("n", 0), "edits": done, "errors": c["errors"], "warnings": c["warnings"]}
