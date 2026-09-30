"""Read-only access to Klaviyo: a live API source and a fixture source with the same interface.

Nothing in this module writes to Klaviyo. The only POST calls are the reporting and
template-render endpoints, which read data and change nothing.
"""
import datetime as dt
import json
import time

import httpx

from . import config

API = "https://a.klaviyo.com/api"

# Names for metrics we already know, so fixture mode (and offline labels) read well.
KNOWN_METRICS = {
    "T9sNn9": "Placed Order", "SwrKKw": "Checkout Started", "UiZD2S": "Added to Cart",
    "WDFj3H": "Viewed Product", "Y2WUPe": "Bounced Email", "R2UK7e": "Delivered Shipment",
    "WJizp7": "Fulfilled Order", "UiRDfZ": "Subscribed to Back in Stock", "Wz44Gj": "Received Email",
    "ULCbbQ": "Opened Email", "URfrxe": "Clicked Email", "SWbhwQ": "Consented to Receive SMS",
}


# Counts (not rates) so weeks and messages can be added together.
SERIES_STATS = ("recipients", "delivered", "opens_unique", "clicks_unique", "conversions",
                "conversion_value", "unsubscribe_uniques")


class KlaviyoError(RuntimeError):
    pass


class LiveSource:
    """Calls the Klaviyo REST API with a private key. Read-only endpoints only."""

    def __init__(self):
        self.client = httpx.Client(
            timeout=60,
            headers={
                "Authorization": f"Klaviyo-API-Key {config.KLAVIYO_API_KEY}",
                "revision": config.KLAVIYO_REVISION,
                "accept": "application/vnd.api+json",
                "content-type": "application/vnd.api+json",
            },
        )
        self._last = 0.0

    def _request(self, method, url, **kw):
        for attempt in range(6):
            wait = 0.4 - (time.monotonic() - self._last)
            if wait > 0:
                time.sleep(wait)
            self._last = time.monotonic()
            r = self.client.request(method, url if url.startswith("http") else API + url, **kw)
            if r.status_code == 429:
                time.sleep(float(r.headers.get("Retry-After", 30)) + 1)
                continue
            if r.status_code >= 400:
                raise KlaviyoError(f"Klaviyo {r.status_code} on {url.split('?')[0]}: {r.text[:500]}")
            return r.json()
        raise KlaviyoError(f"Klaviyo kept rate-limiting {url.split('?')[0]}; try again later.")

    def _paged(self, url, params=None):
        out, nxt = [], url
        while nxt:
            d = self._request("GET", nxt, params=params if nxt == url else None)
            out += d.get("data", [])
            nxt = (d.get("links") or {}).get("next")
        return out

    def flows(self):
        return self._paged("/flows", {"filter": "equals(archived,false)", "page[size]": 50,
                                      "fields[flow]": "name,status,trigger_type,updated,created"})

    def flow(self, flow_id):
        return self._request("GET", f"/flows/{flow_id}", params={"additional-fields[flow]": "definition"})["data"]

    def metrics(self):
        return {m["id"]: m["attributes"]["name"] for m in self._paged("/metrics", {"fields[metric]": "name"})}

    def audience_name(self, kind, audience_id):
        path = "lists" if kind == "list" else "segments"
        try:
            d = self._request("GET", f"/{path}/{audience_id}", params={f"fields[{path[:-1]}]": "name"})
            return d["data"]["attributes"]["name"]
        except KlaviyoError:
            return None

    def flow_report(self, timeframe_key):
        body = {"data": {"type": "flow-values-report", "attributes": {
            "statistics": ["recipients", "delivered", "open_rate", "click_rate", "conversion_rate",
                           "conversions", "conversion_value", "revenue_per_recipient",
                           "unsubscribe_rate", "spam_complaint_rate", "bounce_rate"],
            "timeframe": {"key": timeframe_key},
            "conversion_metric_id": config.CONVERSION_METRIC_ID,
            "group_by": ["flow_id", "flow_message_id", "send_channel"],
        }}}
        d = self._request("POST", "/flow-values-reports", content=json.dumps(body))
        return d["data"]["attributes"]["results"]

    def flow_series(self, weeks=52, interval="weekly"):
        """Week-by-week counts per message over the last `weeks` weeks (Klaviyo's weekly limit is 52).
        Returns (date_times, results)."""
        end = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
        start = end - dt.timedelta(weeks=weeks) + dt.timedelta(hours=1)
        body = {"data": {"type": "flow-series-report", "attributes": {
            "statistics": list(SERIES_STATS),
            "timeframe": {"start": start.isoformat(), "end": end.isoformat()}, "interval": interval,
            "conversion_metric_id": config.CONVERSION_METRIC_ID,
            "group_by": ["flow_id", "flow_message_id", "send_channel"],
        }}}
        d = self._request("POST", "/flow-series-reports", content=json.dumps(body))
        at = d["data"]["attributes"]
        return at.get("date_times") or [], at.get("results") or []

    def render(self, template_id, context):
        body = {"data": {"type": "template", "id": template_id, "attributes": {"context": context}}}
        d = self._request("POST", "/template-render", content=json.dumps(body))
        return d["data"]["attributes"].get("html") or ""

    def template_html(self, template_id):
        d = self._request("GET", f"/templates/{template_id}", params={"fields[template]": "html"})
        return d["data"]["attributes"].get("html") or ""


class FixtureSource:
    """Serves saved Klaviyo responses from dashboard/fixtures (same shapes as the live API)."""

    def __init__(self):
        self.dir = config.FIXTURE_DIR

    def flows(self):
        return [json.loads(p.read_text())["data"] for p in sorted((self.dir / "flows").glob("*.json"))]

    def flow(self, flow_id):
        return json.loads((self.dir / "flows" / f"{flow_id}.json").read_text())["data"]

    def metrics(self):
        return dict(KNOWN_METRICS)

    def audience_name(self, kind, audience_id):
        return None

    def flow_report(self, timeframe_key):
        p = self.dir / f"flow_report_{timeframe_key}.json"
        if not p.exists():
            return None
        return json.loads(p.read_text())["data"]["attributes"]["results"]

    def render(self, template_id, context):
        p = self.dir / "renders" / f"{template_id}.html"
        return p.read_text() if p.exists() else ""

    def template_html(self, template_id):
        return self.render(template_id, None)

    def flow_series(self, weeks=52, interval="weekly"):
        p = self.dir / "flow_series_weekly.json"
        if not p.exists():
            return [], []
        at = json.loads(p.read_text())["data"]["attributes"]
        return at.get("date_times") or [], at.get("results") or []


def get_source():
    return FixtureSource() if config.USE_FIXTURES else LiveSource()
