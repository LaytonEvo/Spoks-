"""Writes the draft packs the dashboard's Drafts page creates in Klaviyo after Layton approves them.

Each pack: dashboard/app/drafts/<id>.json plus its emails in dashboard/app/drafts/html/<id>/<key>.html.
Flows are written in Klaviyo's API format (actions with "data"), so they can carry what the Windsor tool couldn't:
preview text, message names, send times, UTM tracking and SMS settings.

Run: python3 klaviyo/build_packs.py   (after build_f1.py / build_f2.py have written the live emails)
A pack that has been created in Klaviyo is frozen: give changes a new pack id and flow name (v2, v3 …).
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "design"))
import build_f1 as f1  # noqa: E402
import build_f2 as f2  # noqa: E402
import build_f3 as f3  # noqa: E402

OUT = ROOT.parent / "dashboard" / "app" / "drafts"
FROM = "info@evolutiongolf.co.uk"
BRAND, ALEX = "⛳ Evolution Golf", "Alex at Evolution Golf"

# ---------------- conditions ----------------
FS, ALL = {"type": "date", "operator": "flow-start"}, {"type": "date", "operator": "alltime"}


def last(n, unit="day"):
    return {"type": "date", "operator": "in-the-last", "unit": unit, "quantity": n}


def metric(mid, op, val, tf, filters=None):
    return {"type": "profile-metric", "metric_id": mid, "measurement": "count",
            "measurement_filter": {"type": "numeric", "operator": op, "value": val}, "timeframe_filter": tf, "metric_filters": filters}


def tier(op, value):
    return {"type": "profile-property", "property": "properties['MemberTier']", "filter": {"type": "string", "operator": op, "value": value}}


def all_of(*conds):
    return {"condition_groups": [{"conditions": [c]} for c in conds]}


def any_of(*conds):
    return {"condition_groups": [{"conditions": list(conds)}]}


NO_BOUNCE = metric("Y2WUPe", "equals", 0, last(30))

# ---------------- steps (Klaviyo API format) ----------------
def email(tid, key, name, subject, preview, nxt, sender=BRAND, smart=True):
    return {"temporary_id": tid, "type": "send-email", "links": {"next": nxt}, "data": {"status": "draft", "message": {
        "from_email": FROM, "from_label": sender, "reply_to_email": FROM, "subject_line": subject, "preview_text": preview,
        "template_ref": key, "smart_sending_enabled": smart, "transactional": False, "add_tracking_params": True, "name": name}}}


def sms(tid, name, body, nxt):
    return {"temporary_id": tid, "type": "send-sms", "links": {"next": nxt}, "data": {"status": "draft", "message": {
        "body": body, "name": name, "smart_sending_enabled": True, "transactional": False, "shorten_links": True,
        "add_org_prefix": False, "add_info_link": False, "add_opt_out_language": True, "sms_quiet_hours_enabled": True,
        "add_tracking_params": True}}}


def wait(tid, value, unit, nxt, at=None):
    data = {"unit": unit, "value": value, "secondary_value": 0, "timezone": "profile"}
    if at:
        data["delay_until_time"] = at
    return {"temporary_id": tid, "type": "time-delay", "links": {"next": nxt}, "data": data}


def split(tid, profile_filter, yes, no):
    return {"temporary_id": tid, "type": "conditional-split", "data": {"profile_filter": profile_filter},
            "links": {"next_if_true": yes, "next_if_false": no}}


# ---------------- packs ----------------
def templates(pid, emails, prefix, html_dir):
    out = []
    for e in emails:
        src = html_dir / f"{e['key']}.html"
        dest = OUT / "html" / pid / f"{e['key']}.html"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(src.read_text())
        t = {"key": e["key"], "file": f"{pid}/{e['key']}.html", "template_name": f"{prefix} · {e['name']}",
             "name": e["name"], "subject": e["subject"], "preview": e["preview"], "when": e["timing"], "sender": e["sender"]}
        prev = html_dir / f"{e['key']}.preview.html"  # an example-basket version for the dashboard (never sent)
        if prev.exists():
            (OUT / "html" / pid / prev.name).write_text(prev.read_text())
            t["preview_file"] = f"{pid}/{prev.name}"
        out.append(t)
    return out


def add_photos(pack, emails, slots, rules):
    """Photo spots: a version of each email with the photo positions drawn in, plus the briefs for the dashboard."""
    hosted = json.loads(f1.HOSTED.read_text())
    live = {"logo": f1.b.LIVE["logo"], "roundel": f1.b.LIVE["roundel"], **f1.PHOTOS}
    by_key = {e["key"]: e for e in emails}
    used = []
    for t in pack["templates"]:
        e = by_key.get(t["key"], {})
        if not e.get("slots"):
            continue
        rel = f"{pack['id']}/{t['key']}.photos.html"
        (OUT / "html" / rel).write_text(e["fn"](f1.Ctx(live, "slots", True, hosted, live=True)))
        t["photos_file"], t["photos"] = rel, list(e["slots"])
        used += [k for k in e["slots"] if k not in used]
    pack["photo_briefs"] = [dict(key=k, **slots[k]) for k in used]
    pack["photo_rules"] = rules
    return pack


def meta(emails):
    return {e["key"]: e for e in emails}


def f1_pack():
    pid, m = "f1-welcome-v3", meta(f1.EMAILS)
    hw = any_of(*[metric("WDFj3H", "greater-than-or-equal", 1, last(7),
                         [{"property": "Categories", "filter": {"type": "string", "operator": "contains", "value": c}}])
                  for c in ["Electric Trolleys", "GPS Electric Trolleys", "Remote Electric Trolleys", "Motocaddy Electric Golf Trolleys",
                            "Push Golf Trolleys", "Push & Electric Golf Trolleys", "Golf Trolleys", "Golf Clubs", "Drivers", "Fairway Woods",
                            "Hybrids & Utility Irons", "Wedges", "Putters", "All Approved Used Golf Clubs", "Approved Used Golf Clubs"]])
    E = lambda tid, key, nxt, sender=BRAND: email(tid, key, f"F1 {m[key]['name']}", m[key]["subject"], m[key]["preview"], nxt, sender)
    actions = [split("member", any_of({"type": "profile-property", "property": "properties['MemberTier']",
                                       "filter": {"type": "existence", "operator": "is-set"}}), None, "e1"),
               E("e1", "e1", "w1h"), wait("w1h", 1, "hours", "sms1"),
               sms("sms1", "F1 SMS 1 · Welcome", f1.SMS1, "w1d"), wait("w1d", 1, "days", "hw", at="09:30"),
               split("hw", hw, "e2h", "e2e")]
    for g in ("h", "e"):
        actions += [E("e2" + g, "e2" + g, "w2" + g), wait("w2" + g, 2, "days", "e3" + g, at="09:30"),
                    E("e3" + g, "e3", "w3" + g, ALEX), wait("w3" + g, 3, "days", "m4" + g, at="17:30"),
                    # E4 sells membership: skip anyone who joined during the flow
                    split("m4" + g, any_of({"type": "profile-property", "property": "properties['MemberTier']",
                                            "filter": {"type": "existence", "operator": "is-set"}}), None, "e4" + g),
                    E("e4" + g, "e4", None)]
    return pid, {
        "id": pid, "title": "F1 Welcome (v3, new look)",
        "summary": "New subscribers who haven't bought. Same flow as v2, in the new look "
                   "(editorial design, 7 Oct): serif headlines, thin rules, benefits tables, one button per email.",
        "replaces": "Once this is created, delete the earlier drafts “EG · F1 Welcome” (TQe2j4) and “EG · F1 Welcome v2” (STnrqk).",
        "outline": ["Starts: someone joins “1.0 Main Mailing List”. Leaves if they buy or start a checkout.",
                    "Members are skipped (they get F2).", "Email 1 straight away · text 1 an hour later",
                    "Next day 09:30: E2 Hardware if they looked at trolleys or clubs, otherwise E2 Everything else",
                    "2 days later 09:30: E3 from Alex · 3 days later 17:30: E4 Two ways to pay less"],
        "after": ["Set up the button test on Email 1 (Klaviyo can't add tests through its API): open Email 1 in the flow, choose "
                  "“Create A/B test”, set the new variation's content to the saved template “EG · F1 v3 · E1 · Welcome · Test B (brighter button)”, "
                  "split 50/50, pick the winner by click rate, and let it run until Klaviyo marks a winner.",
                  "Check the used-clubs line in E2 Hardware (“every set is checked before it goes on sale”) and edit if needed.",
                  "Send yourself a test of each email from the Klaviyo editor.",
                  "When happy, switch it on in Klaviyo and switch off “1. SM: Welcome Sequence”."],
        "split_labels": {"member": {"label": "Already a member?", "yes": "Member: leaves (gets F2)", "no": "Not a member"},
                         "hw": {"label": "Looked at trolleys, clubs or used clubs in the last 7 days", "yes": "Hardware", "no": "Everything else"},
                         "m4h": {"label": "Joined membership during the flow?", "yes": "Member: skips E4", "no": "Not a member"},
                         "m4e": {"label": "Joined membership during the flow?", "yes": "Member: skips E4", "no": "Not a member"}},
        "templates": templates(pid, f1.EMAILS, "EG · F1 v3", ROOT / "design" / "f1") + templates(pid, [dict(
            key="e1b", name="E1 · Welcome · Test B (brighter button)", subject=f1.EMAILS[0]["subject"], preview=f1.EMAILS[0]["preview"],
            timing="A/B test version of E1: set up in the Klaviyo editor", sender=f1.EMAILS[0]["sender"])], "EG · F1 v3", ROOT / "design" / "f1"),
        "flow": {"name": "EG · F1 Welcome v3", "definition": {
            "triggers": [{"type": "list", "id": "Tzck9t"}],
            "profile_filter": all_of(metric("T9sNn9", "equals", 0, ALL), metric("T9sNn9", "equals", 0, FS), NO_BOUNCE,
                                     metric("SwrKKw", "equals", 0, FS)),
            "entry_action_id": "member", "actions": actions}},
    }


def f2_packs():
    m = meta(f2.EMAILS)
    E = lambda tid, key, nxt, smart=True: email(tid, key, f"F2 {m[key]['name']}", m[key]["subject"], m[key]["preview"], nxt, smart=smart)
    still_free = any_of(tier("contains", "Free"))
    free = {
        "id": "f2-free", "title": "F2 Membership · Free",
        "summary": "New Free members: what Free gives them, then two honest emails about the £36 plan. If they upgrade, "
                   "they leave this flow and the Annual one picks them up.",
        "replaces": "Replaces “FLOW: Welcome - Evolution Free”. Switch that off when you switch this on (same starting segment).",
        "outline": ["Starts: someone joins your “Free TIer Members” segment.", "Day 0: You're in",
                    "Day 4, 09:30: the honest maths on £36 (only if still on Free)", "Day 12, 09:30: the plan in use (only if still on Free)"],
        "after": ["Send yourself a test of each email.", "Switch on in Klaviyo, and switch off “FLOW: Welcome - Evolution Free”."],
        "split_labels": {k: {"label": "Still on Free?", "yes": "Still Free", "no": "Upgraded: leaves (Annual flow takes over)"} for k in ("free1", "free2")},
        "templates": templates("f2-free", [m["fe1"], m["fe2"], m["fe3"]], "EG · F2 Free", ROOT / "design" / "f2"),
        "flow": {"name": "EG · F2 Membership · Free", "definition": {
            "triggers": [{"type": "segment", "id": "W3N8WF"}], "profile_filter": all_of(NO_BOUNCE), "entry_action_id": "fe1",
            "actions": [E("fe1", "fe1", "w4"), wait("w4", 4, "days", "free1", at="09:30"), split("free1", still_free, "fe2", None),
                        E("fe2", "fe2", "w8"), wait("w8", 8, "days", "free2", at="09:30"), split("free2", still_free, "fe3", None),
                        E("fe3", "fe3", None)]}},
    }
    annual = {
        "id": "f2-annual", "title": "F2 Membership · Annual (£36)",
        "summary": "New £36 annual members (tagged AnnualMember): welcome, member deals, first month, two months in, "
                   "a short monthly reminder that their 10% is ready, and the renewal reminder we promise in the welcome emails.",
        "replaces": "Replaces the old Club Access, Pro and Annual welcomes for new joiners (those old tiers aren't sold any more).",
        "outline": ["Starts: someone is tagged MemberTier = AnnualMember (a new segment, “EG · Members · Annual”, is created for this).",
                    "Leaves if they stop being an annual member.", "Day 0: welcome (always sends)", "Day 3, 09:30: member deals",
                    "Day 30, 09:30: first month", "Day 60, 09:30: two months in (this month's 10%, prize draw, daily deals)",
                    "Days 90 to 300, every 30 days: \"your 10% for this month is ready\"", "Day 335, 09:30: renewal reminder"],
        "after": ["Send yourself a test of each email.", "Switch on in Klaviyo."],
        "segments": [{"key": "annual", "name": "EG · Members · Annual", "definition": any_of(tier("equals", "AnnualMember"))}],
        "templates": templates("f2-annual", [m[k] for k in ("pe1", "pe2", "pe3", "pe4", "pem", "pe5")], "EG · F2 Annual", ROOT / "design" / "f2"),
        "flow": {"name": "EG · F2 Membership · Annual", "definition": {
            "triggers": [{"type": "segment", "ref": "annual"}], "profile_filter": all_of(NO_BOUNCE, tier("equals", "AnnualMember")),
            "entry_action_id": "pe1",
            "actions": [E("pe1", "pe1", "w3", smart=False), wait("w3", 3, "days", "pe2", at="09:30"), E("pe2", "pe2", "w27"),
                        wait("w27", 27, "days", "pe3", at="09:30"), E("pe3", "pe3", "w30"), wait("w30", 30, "days", "pe4", at="09:30"),
                        E("pe4", "pe4", "wm1")]
            # Months 3 to 10: the monthly 10% reminder every 30 days (days 90 to 300), then the renewal reminder at day 335.
            + [x for i in range(1, 9) for x in (
                wait(f"wm{i}", 30, "days", f"pm{i}", at="09:30"),
                email(f"pm{i}", "pem", f"F2 Annual · Monthly 10% reminder · month {i + 2}", m["pem"]["subject"], m["pem"]["preview"],
                      f"wm{i + 1}" if i < 8 else "w35"))]
            + [wait("w35", 35, "days", "pe5", at="09:30"), E("pe5", "pe5", None)]}},
    }
    return [("f2-free", free), ("f2-annual", annual)]


def f3_pack():
    pid, m = "f3-checkout", meta(f3.EMAILS)
    E = lambda tid, key, nxt, sender=BRAND: email(tid, key, f"F3 {m[key]['name']}", m[key]["subject"], m[key]["preview"], nxt, sender)
    hw = any_of(*[metric("SwrKKw", "greater-than-or-equal", 1, last(1),
                         [{"property": "Collections", "filter": {"type": "string", "operator": "contains", "value": c}}]) for c in f3.HARDWARE])
    annual = all_of(tier("equals", "AnnualMember"))
    S = lambda tid, nxt: sms(tid, "F3 SMS 1 · Basket still saved", f3.SMS1, nxt)
    actions = [wait("w45", 45, "minutes", "hw"), split("hw", hw, "w15", "e1e"),
               # Hardware
               wait("w15", 15, "minutes", "e1h"), E("e1h", "e1h", "h1"), wait("h1", 1, "days", "mh", at="09:30"),
               split("mh", annual, "e2mh", "e2h"),
               E("e2mh", "e2m", "h2m"), wait("h2m", 1, "days", "smshm", at="18:00"), S("smshm", "h3m"),
               wait("h3m", 1, "days", "e3hm", at="09:30"), E("e3hm", "e3h", None, ALEX),
               E("e2h", "e2h", "h2"), wait("h2", 1, "days", "smsh", at="18:00"), S("smsh", "h3"),
               wait("h3", 1, "days", "e3h", at="09:30"), E("e3h", "e3h", None, ALEX),
               # Everything else
               E("e1e", "e1e", "x1"), wait("x1", 1, "days", "me", at="09:30"), split("me", annual, "e2me", "e2e"),
               E("e2me", "e2m", "x2m"), wait("x2m", 1, "days", "smsem", at="18:00"), S("smsem", None),
               E("e2e", "e2e", "x2"), wait("x2", 1, "days", "smse", at="18:00"), S("smse", "x3"),
               wait("x3", 1, "days", "e3e", at="17:30"), E("e3e", "e3e", None)]
    return pid, {
        "id": pid, "title": "F3 Checkout abandonment (two groups)",
        "summary": "Anyone who starts a checkout worth £30 or more and doesn't order. Hardware (trolleys, clubs, used clubs) and "
                   "Everything else get their own emails; annual members get a members' version of email 2. No discount codes.",
        "replaces": "Replaces the live checkout flow and the September test draft “EG · F3 Checkout abandonment · Trolleys” (UXsJ3d), "
                    "which you can delete once this is created.",
        "outline": ["Starts: Checkout Started worth £30 or more. Leaves the moment they order.",
                    "45 minutes later: Hardware if the checkout has a trolley, club or used club; otherwise Everything else",
                    "Hardware: E1 at 1 hour · next day 09:30 E2 (members: Your 10% can go on this) · day 2 18:00 text · day 3 09:30 E3 from Alex",
                    "Everything else: E1 at 45 minutes · next day 09:30 E2 (members: Your 10% can go on this) · day 2 18:00 text · "
                    "day 3 17:30 E3 last nudge (non-members only)"],
        "after": ["Set re-entry to 7 days in the flow settings (the API can't), so someone who abandons twice in a week isn't emailed twice.",
                  "Confirm the delivery time in E1 Hardware (marked CONFIRM: “usually 3 to 5 working days”) and edit it in the editor.",
                  "Send yourself a test of E2 Hardware with a trolley in the basket and one with clubs, to check the right blocks show.",
                  "When happy, switch it on and switch off the live checkout flow."],
        "split_labels": {"hw": {"label": "Checkout has a trolley, club or used club", "yes": "Hardware", "no": "Everything else"},
                         "mh": {"label": "Annual member?", "yes": "Member", "no": "Not a member"},
                         "me": {"label": "Annual member?", "yes": "Member", "no": "Not a member"}},
        "templates": templates(pid, f3.EMAILS, "EG · F3", ROOT / "design" / "f3"),
        "flow": {"name": "EG · F3 Checkout abandonment", "definition": {
            "triggers": [{"type": "metric", "id": "SwrKKw", "trigger_filter": {"condition_groups": [{"conditions": [
                {"type": "metric-property", "metric_id": "SwrKKw", "field": "$value",
                 "filter": {"type": "numeric", "operator": "greater-than-or-equal", "value": 30}}]}]}}],
            "profile_filter": all_of(metric("T9sNn9", "equals", 0, FS), NO_BOUNCE),
            "entry_action_id": "w45", "actions": actions}},
    }


def check(pk):
    acts = {a["temporary_id"]: a for a in pk["flow"]["definition"]["actions"]}
    keys = {t["key"] for t in pk["templates"]}
    assert pk["flow"]["name"].startswith("EG ·")
    assert pk["flow"]["definition"]["entry_action_id"] in acts
    for a in acts.values():
        for nxt in (a.get("links") or {}).values():
            assert nxt is None or nxt in acts, (pk["id"], nxt)
        ref = ((a.get("data") or {}).get("message") or {}).get("template_ref")
        assert ref is None or ref in keys, (pk["id"], ref)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    packs = [f1_pack(), *f2_packs(), f3_pack()]
    add_photos(packs[0][1], f1.EMAILS, f1.SLOTS, f1.PHOTO_RULES)
    for _, pk in packs[1:]:
        add_photos(pk, f2.EMAILS, f1.SLOTS, f1.PHOTO_RULES)
    for pid, pk in packs:
        check(pk)
        (OUT / f"{pid}.json").write_text(json.dumps(pk, indent=1, ensure_ascii=False))
        print(pid, len(pk["templates"]), "emails", len(pk["flow"]["definition"]["actions"]), "steps")
