#!/usr/bin/env python3
"""Personal job alerts: each subscriber gets only the new jobs matching the filters they saved.

On the website, a visitor sets filters (seniority, field, state, search words, company size...) and
clicks "Email me these jobs". The filters are saved on their Brevo contact as the same text the site
keeps after the # in its address (for example  level=senior&field=0&state=CA&q=python ), together
with how often they want emails. Every run, this script reads the alert list from Brevo, finds the
new jobs that match each person's filters, and sends each person one email (skipped when nothing
matches). The matching rules are the same as the website's filters.

Settings (GitHub variables / secrets):
  BREVO_API_KEY, BREVO_SENDER_EMAIL, BREVO_SENDER_NAME   as for the digests
  BREVO_ALERT_LIST     Brevo list that alert sign-ups go into
  ALERT_ATTR           contact attribute holding the filters (default BIO_ALERT); the frequency is
                       in <ALERT_ATTR>_FREQ (daily | weekly | monthly)
  BREVO_SEND=1         actually send (otherwise it only reports what it would send)
  ALERT_MAX            most alert emails per run (default 200; Brevo's free plan sends 300 a day)
"""
import html
import json
import os
import re
import urllib.parse
import urllib.request

SN = {"AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland", "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi", "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York", "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina", "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming", "DC": "District of Columbia", "PR": "Puerto Rico"}
CITY = {"boston": "MA", "cambridge": "MA", "waltham": "MA", "lexington": "MA", "watertown": "MA", "woburn": "MA", "bedford": "MA", "andover": "MA", "framingham": "MA", "marlborough": "MA", "somerville": "MA", "san diego": "CA", "san francisco": "CA", "south san francisco": "CA", "redwood city": "CA", "menlo park": "CA", "palo alto": "CA", "foster city": "CA", "hayward": "CA", "emeryville": "CA", "carlsbad": "CA", "irvine": "CA", "los angeles": "CA", "thousand oaks": "CA", "fremont": "CA", "pleasanton": "CA", "san carlos": "CA", "brisbane": "CA", "alameda": "CA", "seattle": "WA", "bothell": "WA", "new york": "NY", "tarrytown": "NY", "sleepy hollow": "NY", "rensselaer": "NY", "renss": "NY", "rochester": "NY", "princeton": "NJ", "rahway": "NJ", "raritan": "NJ", "east hanover": "NJ", "summit": "NJ", "titusville": "NJ", "bridgewater": "NJ", "hopewell": "NJ", "lawrenceville": "NJ", "new brunswick": "NJ", "basking ridge": "NJ", "plainsboro": "NJ", "philadelphia": "PA", "pittsburgh": "PA", "collegeville": "PA", "malvern": "PA", "spring house": "PA", "west point": "PA", "upper gwynedd": "PA", "horsham": "PA", "chicago": "IL", "lake county": "IL", "durham": "NC", "raleigh": "NC", "research triangle park": "NC", "rtp": "NC", "morrisville": "NC", "burlington": "NC", "greenville": "NC", "sanford": "NC", "holly springs": "NC", "houston": "TX", "dallas": "TX", "austin": "TX", "baltimore": "MD", "bethesda": "MD", "gaithersburg": "MD", "rockville": "MD", "frederick": "MD", "salt lake city": "UT", "denver": "CO", "boulder": "CO", "madison": "WI", "indianapolis": "IN", "atlanta": "GA", "nashville": "TN", "minneapolis": "MN", "st. louis": "MO", "saint louis": "MO", "phoenix": "AZ", "tempe": "AZ", "miami": "FL", "tampa": "FL", "orlando": "FL", "portland": "OR", "new haven": "CT", "groton": "CT", "branford": "CT", "wilmington": "DE", "kalamazoo": "MI", "ann arbor": "MI", "juncos": "PR", "richmond": "VA", "charlotte": "NC"}
FIELDS = [(n, re.compile(r, re.I | re.A)) for n, r in [["Bioinformatics & data", "bioinformatic|computational|data scien|machine learning|\\bml\\b|software|engineer.*data|statistic|biostat|\\bai\\b"], ["Research & development", "scientist|research|r&d|discovery|assay develop|biolog|chemist"], ["Clinical lab", "clinical lab|laboratory|\\bclia\\b|molecular pathology|technologist|cytogenet|histotech|phlebotom"], ["Clinical development", "clinical (trial|research|operations|development)|\\bcra\\b|clinical study|medical monitor|pharmacovigil"], ["Genetic counseling", "genetic counsel"], ["Manufacturing & quality", "manufactur|quality|\\bqc\\b|\\bqa\\b|process develop|validation|\\bcmc\\b|bioprocess"], ["Regulatory & medical", "regulatory|medical affairs|medical science liaison|\\bmsl\\b"], ["Sales & field", "sales|account (executive|manager)|field application|commercial|market access|reimbursement"]]]
LEVEL_NAMES = {"intern": "Intern / student", "postdoc": "Postdoc / fellow", "exec": "Director & up",
               "lead": "Principal / manager", "senior": "Senior", "entry": "Entry level", "mid": "Mid-level"}

_I = re.I | re.A   # ASCII word boundaries, like the website
def level(t):
    """Seniority from the job title (same rules as the website)."""
    t = t or ""
    if re.search(r"\b(intern(ship)?|co-?op|student|summer associate|trainee|apprentice)\b", t, _I): return "intern"
    if re.search(r"\b(post-?doc(toral)?|postdoctoral|fellowship)\b", t, _I): return "postdoc"
    if re.search(r"\b(director|head of|vice president|vp|svp|evp|chief|president|general manager)\b", t, _I): return "exec"
    t2 = re.sub(r"\b(account|territory|key account|regional account|area sales|district sales|sales) manager\b", "", t, flags=_I)
    if re.search(r"\b(principal|manager|team lead|group lead|lead|supervisor|staff scientist)\b", t2, _I): return "lead"
    if re.search(r"\b(senior|sr)\b|\bstaff\b", t, _I) or re.search(r"\b(III|IV|V)\b", t, re.A): return "senior"
    if re.search(r"\b(entry|junior|jr|associate|assistant|technician|new grad|graduate|level 1)\b", t, _I) or re.search(r"\bI\b", t, re.A): return "entry"
    return "mid"

_RX1 = re.compile(r"(?:,|\s|-)\s*(" + "|".join(SN) + r")(?:\b|$)", re.A)
_RX2 = re.compile(r"\b(" + "|".join(re.escape(v) for v in SN.values()) + r")\b", _I)
_NM2AB = {v.lower(): k for k, v in SN.items()}
def region(loc):
    """US states (and "remote") a location string mentions (same rules as the website)."""
    loc = loc or ""
    r = set()
    if re.search("remote", loc, _I): r.add("remote")
    r.update(_RX1.findall(loc))
    r.update(_NM2AB[m.lower()] for m in _RX2.findall(loc))
    if not r or r == {"remote"}:
        low = loc.lower()
        for city, st in CITY.items():
            if city in low:
                r.add(st); break
    return r


def parse(saved):
    p = urllib.parse.parse_qs((saved or "").lstrip("#"))
    g = lambda k: (p.get(k) or [""])[0]
    return {"q": g("q").lower().split(), "locs": {x for x in g("state").split(",") if x}, "near": g("near"), "within": float(g("within")) if g("within").replace(".", "", 1).isdigit() else 25, "remote": g("remote") == "1", "size": g("size"), "only": g("only") == "1",
            "levels": {x for x in g("level").split(",") if x in LEVEL_NAMES},
            "fields": {int(x) for x in g("field").split(",") if x.isdigit() and int(x) < len(FIELDS)}}


UNIT, PER_KM = "mi", 1.609344   # the site's distance unit


def _location_ok(f, j):
    """Same rule as the website: in any chosen state, or within the distance of the chosen place."""
    if not f["locs"] and not f["near"]:
        return True
    if f["locs"] and region(j.get("location") or "") & f["locs"]:
        return True
    if f["near"]:
        import geo
        pt = geo.anchor(f["near"])
        if pt:
            pts = j.get("geo") or geo.coords(j.get("location"), j.get("region"))
            if any(geo.distance(pt, q) / PER_KM <= f["within"] for q in pts):
                return True
        if f["remote"] and "remote" in region(j.get("location") or ""):
            return True
    return False


def matches(f, j, company, size):
    if f["size"] and size != f["size"]: return False
    if f["levels"] and level(j.get("title") or "") not in f["levels"]: return False
    if f["fields"]:
        text = (j.get("title") or "") + " " + (j.get("department") or "")
        if not any(FIELDS[i][1].search(text) for i in f["fields"]): return False
    if f["q"]:
        hay = " ".join([j.get("title") or "", company, j.get("location") or "", j.get("department") or ""]).lower()
        if not all(t in hay for t in f["q"]): return False
    if not _location_ok(f, j): return False
    if f["only"]:
        from publish import only_here
        if not only_here(j): return False
    return True


def describe(f):
    parts = [LEVEL_NAMES[k] for k in sorted(f["levels"])] + [FIELDS[i][0] for i in sorted(f["fields"])]
    parts += ["Remote" if x == "remote" else SN.get(x, x) for x in sorted(f["locs"])]
    if f["near"]: parts.append(f"within {f['within']:g} {UNIT} of {f['near']}")
    if f["q"]: parts.append("\u201c" + " ".join(f["q"]) + "\u201d")
    if f["size"]: parts.append("large companies" if f["size"] == "large" else "startups and mid-size")
    if f["only"]: parts.append("not on LinkedIn or Indeed")
    return " \u00b7 ".join(parts) or "all jobs"


# ---------------------------------------------------------------- sending (shared with the Israel site)
def _brevo(method, path, payload=None):
    req = urllib.request.Request("https://api.brevo.com/v3" + path, method=method,
                                 data=json.dumps(payload).encode() if payload is not None else None,
                                 headers={"api-key": os.environ["BREVO_API_KEY"], "accept": "application/json",
                                          "content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read() or b"{}")


def alert_contacts(list_id):
    out, offset = [], 0
    while True:
        d = _brevo("GET", f"/contacts/lists/{list_id}/contacts?limit=500&offset={offset}")
        rows = d.get("contacts") or []
        out += rows
        if len(rows) < 500:
            return out
        offset += 500


def email_html(title, saved, by_co, site, email, freq, only_here, site_name):
    link = lambda frag: html.escape(site.rstrip("/") + "/#" + frag)
    rows = []
    for co in sorted(by_co, key=str.lower):
        rows.append(f"<h3 style=\"margin:18px 0 4px\">{html.escape(co)}</h3><ul style=\"margin:0;padding-left:18px\">")
        for j in sorted(by_co[co], key=lambda j: j["title"].lower()):
            star = "\u2605 " if only_here(j) else ""
            rows.append(f"<li>{star}<a href=\"{html.escape(j['url'])}\">{html.escape(j['title'])}</a>"
                        f" \u2014 {html.escape(j.get('location', ''))}</li>")
        rows.append("</ul>")
    stop = urllib.parse.urlencode({"stopalert": email})
    return (f"<html><body style=\"font-family:Arial,sans-serif;max-width:680px;margin:auto;color:#1d1630\">"
            f"<h2>{html.escape(title)}</h2>{''.join(rows)}"
            f"<p style=\"margin-top:22px\"><a href=\"{link(saved)}\">See every job matching this alert</a></p>"
            f"<hr><p style=\"font-size:12px;color:#666\">You get this {freq} because you set up a job alert on "
            f"{html.escape(site_name)}. To change it, open the link above, adjust the filters and save the alert again. "
            f"<a href=\"{link(stop)}\">Stop this alert</a></p></body></html>")


def send_alerts(due, collect, only_here, parse, matches, describe, meta, site, site_name, default_attr):
    list_id = (os.environ.get("BREVO_ALERT_LIST") or "").strip()
    sender = (os.environ.get("BREVO_SENDER_EMAIL") or "").strip()
    if not (os.environ.get("BREVO_API_KEY") and list_id and sender):
        print("alerts: skipped - set BREVO_API_KEY, BREVO_ALERT_LIST and BREVO_SENDER_EMAIL")
        return
    attr = (os.environ.get("ALERT_ATTR") or default_attr).upper()
    live = os.environ.get("BREVO_SEND") == "1"
    cap = int(os.environ.get("ALERT_MAX") or 200)
    new = {f: collect(days)[1] for f, days in due.items()}
    sent = skipped = 0
    for c in alert_contacts(list_id):
        a = c.get("attributes") or {}
        saved, freq = (a.get(attr) or "").strip(), (a.get(attr + "_FREQ") or "weekly").strip().lower()
        if c.get("emailBlacklisted") or not saved or saved == "stop" or freq not in new:
            continue
        f = parse(saved)
        by_co = {}
        for co, jobs in new[freq].items():
            size = (meta.get(co) or {}).get("size", "small")
            hit = [j for j in jobs if matches(f, j, co, size)]
            if hit:
                by_co[co] = hit
        n = sum(len(v) for v in by_co.values())
        if not n:
            skipped += 1
            continue
        if sent >= cap:
            print(f"alerts: reached ALERT_MAX={cap}; the rest wait for the next run")
            break
        title = f"{n} new job{'s' if n != 1 else ''} for your alert: {describe(f)}"
        if live:
            _brevo("POST", "/smtp/email", {
                "sender": {"name": os.environ.get("BREVO_SENDER_NAME") or site_name, "email": sender},
                "to": [{"email": c["email"]}], "subject": title, "tags": ["job-alert"],
                "htmlContent": email_html(title, saved, by_co, site, c["email"], freq, only_here, site_name)})
        sent += 1
    print(f"alerts: {'sent' if live else 'would send (set BREVO_SEND=1 to send)'} {sent} email(s); "
          f"{skipped} alert(s) had no new matching jobs")
