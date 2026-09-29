"""Written flow reviews from Claude, grounded in the snapshot's numbers and Evolution Golf's rules."""
import datetime as dt
import json
from typing import List, Literal

import anthropic
from pydantic import BaseModel

from . import config

REVIEWS = config.DATA_DIR / "reviews"

SYSTEM = """You review email and SMS automation flows for Evolution Golf, a UK golf retailer \
(trolleys, clubs, bags, shoes, clothing; single paid membership at £36 a year).

Write for the owner and his business partner: plain UK English, short sentences, no jargon.

Ground rules:
- Use only the numbers in the data you are given. Quote them. Never invent benchmarks, \
industry averages or figures that are not in the data.
- Say when a number rests on a small sample (fewer than 100 recipients) and treat it as a hint, not a finding.
- "Recipients" are sends, not unique people. Revenue is Klaviyo-attributed revenue from Placed Order.
- Judge the copy as well as the numbers: clarity, relevance to the trigger, tone, and whether the \
email gives a real reason to act.

The business's own rules (flag any breach as high priority):
- No public discount codes in flows, and never a discount on trolleys, clubs or used clubs.
- No false urgency or fake deadlines (UK DMCC Act 2024): a deadline must match a real expiry.
- Unsubscribe rate should stay at or below 0.5% per message.
- In abandonment flows, the second email should reach at least 80% of the first email's recipients.
- Sender "⛳ Evolution Golf" for brand emails; personal emails come from "Alex at Evolution Golf".
- SMS must carry opt-out wording and respect quiet hours.

Recommendations must be concrete and doable in Klaviyo (what to change, where). Prefer a few \
important points over a long list."""


class Issue(BaseModel):
    priority: Literal["high", "medium", "low"]
    where: str
    finding: str
    evidence: str
    recommendation: str


class Review(BaseModel):
    headline: str
    what_is_working: List[str]
    issues: List[Issue]
    next_test: str


def _compact(steps, tf):
    out = []
    for s in steps:
        if s["kind"] in ("email", "sms"):
            m = {k: s.get(k) for k in ("kind", "name", "status", "subject", "preview_text", "from_label", "body",
                                       "smart_sending", "utm", "opt_out")}
            m["metrics"] = (s.get("metrics") or {}).get(tf)
            m["checks"] = [f["text"] for f in (s.get("flags") or {}).get(tf, [])]
            if s.get("_text"):
                m["email_text"] = s["_text"][:2500]
            if s.get("ab_test"):
                m["ab_test"] = {"status": s["ab_test"]["status"], "started": s["ab_test"]["started"],
                                "variations": [{"subject": v.get("subject"), "share": v.get("share"),
                                                "metrics": (v.get("metrics") or {}).get(tf)} for v in s["ab_test"]["variations"]]}
            out.append({k: v for k, v in m.items() if v not in (None, [], "")})
        elif s["kind"] == "split":
            out.append({"split": s["label"], "branches": [{"path": b["label"], "steps": _compact(b["steps"], tf)} for b in s["branches"]]})
        else:
            out.append({s["kind"]: s["label"]})
    return out


def generate(flow, tf):
    if not config.ANTHROPIC_API_KEY:
        raise RuntimeError("Set ANTHROPIC_API_KEY to generate reviews.")
    payload = {
        "flow": flow["name"], "status": flow["status"], "trigger": flow["trigger"], "flow_filter": flow["flow_filter"],
        "re_entry": flow.get("reentry"), "period": tf.replace("_", " "), "totals": flow["totals"].get(tf),
        "flow_checks": [f["text"] for f in flow["flags"].get(tf, [])], "journey": _compact(flow["steps"], tf),
    }
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    response = client.beta.messages.parse(
        model=config.REVIEW_MODEL,
        max_tokens=16000,
        system=SYSTEM,
        output_config={"effort": "high"},
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        messages=[{"role": "user", "content": "Review this flow.\n\n" + json.dumps(payload, ensure_ascii=False)}],
        output_format=Review,
    )
    if response.stop_reason == "refusal":
        raise RuntimeError("Claude declined to review this flow. Try again or review it manually.")
    review = response.parsed_output
    record = {"flow_id": flow["id"], "timeframe": tf, "model": config.REVIEW_MODEL,
              "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
              "review": review.model_dump()}
    REVIEWS.mkdir(parents=True, exist_ok=True)
    (REVIEWS / f"{flow['id']}.json").write_text(json.dumps(record, ensure_ascii=False, indent=1))
    return record


def load(flow_id):
    p = REVIEWS / f"{flow_id}.json"
    return json.loads(p.read_text()) if p.exists() else None
