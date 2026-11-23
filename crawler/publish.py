#!/usr/bin/env python3
"""Turn the latest crawl into a newsletter post and (optionally) publish it.

    python3 crawler/publish.py                 # daily digest every day, weekly on Mondays, monthly on the 1st
    python3 crawler/publish.py --only weekly   # build/send just one of daily | weekly | monthly
    python3 crawler/publish.py --since 7       # one digest of jobs first seen in the last 7 days

Sign-ups from the website are tagged "daily", "weekly" or "monthly" in Buttondown, and each
digest is sent only to subscribers with that tag. Files: data/digest-<frequency>.md/.html.

The digest lists new jobs grouped by company. With COVERAGE data present, jobs that were
NOT found on LinkedIn, Indeed or Glassdoor are listed first ("Only here").

Optional destinations (set the environment variables / GitHub secrets to switch one on):

  Buttondown   BUTTONDOWN_API_KEY          -> creates an email per frequency (draft unless BUTTONDOWN_SEND=1)
  WordPress    WP_URL, WP_USER, WP_APP_PASSWORD
                                           -> posts the weekly digest (draft unless WP_STATUS=publish)
  Any newsletter that does RSS-to-email can also send data/feed.xml.
"""
import base64
import datetime as dt
import html
import json
import os
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")


def collect(since_days=None):
    jobs = json.load(open(os.path.join(DATA, "jobs.json")))
    latest = jobs["generated"]
    first = min((j["first_seen"] for c in jobs["companies"].values() for j in c["jobs"]), default=latest)
    if since_days:
        cutoff = (dt.date.fromisoformat(latest) - dt.timedelta(days=since_days)).isoformat()
        keep = lambda j: j["first_seen"] > cutoff and j["first_seen"] != first
    else:
        keep = lambda j: j["first_seen"] == latest and latest != first
    out = {}
    for name, c in jobs["companies"].items():
        sel = [j for j in c["jobs"] if keep(j)]
        if sel:
            out[name] = sel
    return latest, out


def only_here(j):
    cov = j.get("coverage")
    return bool(cov) and not (cov.get("linkedin") or cov.get("indeed") or cov.get("glassdoor"))


PERIOD = {"daily": (1, "today"), "weekly": (7, "this week"), "monthly": (30, "this month")}


def render(latest, by_co, site_url="", period=""):
    n = sum(len(v) for v in by_co.values())
    exclusive = sum(1 for v in by_co.values() for j in v if only_here(j))
    when = PERIOD[period][1] if period in PERIOD else latest
    title = f"{n} new biotech & genomics jobs {when}" if period else f"{n} new biotech & genomics jobs — {latest}"
    md = [f"# {title}", ""]
    hl = [f"<h1>{html.escape(title)}</h1>"]
    if exclusive:
        md += [f"**{exclusive}** of these were not found on LinkedIn, Indeed or Glassdoor (marked ★).", ""]
        hl.append(f"<p><b>{exclusive}</b> of these were not found on LinkedIn, Indeed or Glassdoor (marked ★).</p>")
    for name in sorted(by_co, key=lambda k: (-sum(only_here(j) for j in by_co[k]), k.lower())):
        md.append(f"## {name}")
        hl.append(f"<h2>{html.escape(name)}</h2><ul>")
        for j in sorted(by_co[name], key=lambda j: (not only_here(j), j["title"].lower())):
            star = "★ " if only_here(j) else ""
            md.append(f"- {star}[{j['title']}]({j['url']}) — {j.get('location', '')}")
            hl.append(f"<li>{star}<a href=\"{html.escape(j['url'])}\">{html.escape(j['title'])}</a> — {html.escape(j.get('location', ''))}</li>")
        md.append("")
        hl.append("</ul>")
    if site_url:
        md.append(f"Search every open job: {site_url}")
        hl.append(f"<p>Search every open job: <a href=\"{html.escape(site_url)}\">{html.escape(site_url)}</a></p>")
    return title, "\n".join(md), "\n".join(hl), n


def post_json(url, payload, headers):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json", **headers})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read() or b"{}")


def send_buttondown(title, md, tag=None):
    status = "about_to_send" if os.environ.get("BUTTONDOWN_SEND") == "1" else "draft"
    payload = {"subject": title, "body": md, "status": status}
    if tag:
        payload["filters"] = {"predicate": "and", "groups": [],
                              "filters": [{"operator": "contains", "field": "subscriber.tags", "value": tag}]}
    r = post_json("https://api.buttondown.com/v1/emails", payload,
                  {"Authorization": f"Token {os.environ['BUTTONDOWN_API_KEY']}"})
    print(f"buttondown ({tag or 'all'}):", r.get("id", r))


def send_wordpress(title, body_html):
    tok = base64.b64encode(f"{os.environ['WP_USER']}:{os.environ['WP_APP_PASSWORD']}".encode()).decode()
    r = post_json(os.environ["WP_URL"].rstrip("/") + "/wp-json/wp/v2/posts",
                  {"title": title, "content": body_html, "status": os.environ.get("WP_STATUS", "draft")},
                  {"Authorization": f"Basic {tok}"})
    print("wordpress:", r.get("link", r))


def due_today(today):
    out = ["daily"]
    if today.weekday() == int(os.environ.get("WEEKLY_DAY", "0")):   # 0 = Monday
        out.append("weekly")
    if today.day == 1:
        out.append("monthly")
    return out


def main():
    site = os.environ.get("SITE_URL", "")
    if "--since" in sys.argv:                       # one-off digest, sent to everyone
        since = int(sys.argv[sys.argv.index("--since") + 1])
        latest, by_co = collect(since)
        title, md, body_html, n = render(latest, by_co, site)
        open(os.path.join(DATA, "digest.md"), "w").write(md)
        open(os.path.join(DATA, "digest.html"), "w").write(body_html)
        print(f"digest: {n} new jobs")
        if n and os.environ.get("BUTTONDOWN_API_KEY"):
            send_buttondown(title, md)
        return

    if "--only" in sys.argv:
        freqs = [sys.argv[sys.argv.index("--only") + 1]]
    else:
        freqs = due_today(dt.date.today())
    for f in freqs:
        latest, by_co = collect(PERIOD[f][0])
        title, md, body_html, n = render(latest, by_co, site, f)
        open(os.path.join(DATA, f"digest-{f}.md"), "w").write(md)
        open(os.path.join(DATA, f"digest-{f}.html"), "w").write(body_html)
        print(f"{f} digest: {n} new jobs -> data/digest-{f}.md")
        if not n:
            continue
        if os.environ.get("BUTTONDOWN_API_KEY"):
            send_buttondown(title, md, f)
        if f == "weekly" and os.environ.get("WP_URL") and os.environ.get("WP_APP_PASSWORD"):
            send_wordpress(title, body_html)


if __name__ == "__main__":
    main()
