#!/usr/bin/env python3
"""Find job boards for US biotech, genomics, life-science tools and diagnostics companies.

Three passes (all write data/companies.json, plus a report in data/discover-report.json):

1. Tracked companies without a readable job board (most of data/companies.json): try likely board
   names on Greenhouse, Lever, Ashby, SmartRecruiters, Workable, BambooHR, Recruitee and Breezy, and
   read the company's careers page / website for links to any of those or to Workday.
2. New companies listed in crawler/candidates.txt (same method).
3. With --index: list every public job board on those systems from Common Crawl's open web index,
   and add the ones that are clearly life-science employers (judged by their job titles) and hire
   in the US.

    python3 crawler/discover.py                 # passes 1 and 2
    python3 crawler/discover.py --index         # all three (takes an hour or more)
    python3 crawler/discover.py --dry-run       # report only

Runs from GitHub Actions ("Find more companies" workflow), which can reach the job boards.
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crawl  # noqa: E402
from usloc import is_us  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), "data")
crawl.TIMEOUT = 12   # seconds; there are thousands of boards and websites to check

# Job titles that mark a life-science employer.
BIO = re.compile(r"scientist|assay|bioinformat|computational biolog|genom|sequenc|biolog|biochem|chemist|molecular|"
                 r"\bcell\b|cell therap|gene therap|crispr|protein|antibod|immun|oncolog|pharmac|biostat|toxicolog|"
                 r"translational|clinical (research|operations|trial|scientist|development|affairs)|medical (affairs|science)|"
                 r"\bmsl\b|regulatory affairs|laborator|\blab\b|patholog|microbiolog|virolog|in vivo|in vitro|vivarium|"
                 r"formulation|\bgmp\b|biologics|bioprocess|\bcmc\b|downstream|upstream|diagnostic|\bivd\b|\bclia\b|"
                 r"genetic counsel|histolog|cytometr|mass spec|proteomic|drug (discovery|development)|preclinical|"
                 r"medicinal chem|bioassay|qc analyst|quality control analyst|validation (scientist|engineer)", re.I)
BIO_NAME = re.compile(r"bio|thera|pharm|genom|gene|diagnos|medic|lab|cell|immun|onco|life sci|molecul|protein|rx\b|cur(e|a)", re.I)


def norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def _json(url, body=None, headers=None):
    try:
        return crawl.http_json(url, body=body, headers=headers, tries=1)
    except Exception:
        return None


def _text(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": crawl.UA})
        with urllib.request.urlopen(req, timeout=crawl.TIMEOUT) as r:
            return r.read(600_000).decode("utf-8", "replace")
    except Exception:
        return None


def summary(jobs):
    """(US jobs, life-science jobs, total) for a list of crawler jobs."""
    us = sum(1 for j in jobs if is_us(j.get("location") or ""))
    bio = sum(1 for j in jobs if BIO.search((j.get("title") or "") + " " + (j.get("department") or "")))
    return us, bio, len(jobs)


def board(platform, **ats):
    """Read one board with the crawler's own adapter: (ats, us, bio, total) or None."""
    ats = dict(platform=platform, **ats)
    try:
        jobs = crawl.ADAPTERS[platform](ats)
    except Exception:
        return None
    return (ats,) + summary(jobs)


def try_smartrecruiters(slug):
    d = _json(f"https://api.smartrecruiters.com/v1/companies/{slug}/postings?country=us&limit=100")
    if not d or not d.get("totalFound"):
        return None
    titles = [p.get("name", "") for p in d.get("content", [])]
    bio = sum(1 for t in titles if BIO.search(t))
    return {"platform": "smartrecruiters", "slug": slug}, d["totalFound"], bio, d["totalFound"]


def try_workday(host, site):
    tenant = host.split(".")[0]
    d = _json(f"https://{host}/wday/cxs/{tenant}/{site}/jobs",
              body={"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": "scientist"})
    if d is None:
        return None
    total = d.get("total") or 0
    return {"platform": "workday", "host": host, "tenant": tenant, "site": site}, total, total, total


GUESSABLE = ["greenhouse", "lever", "ashby", "workable", "recruitee", "breezy", "bamboohr"]


def careers_url(ats):
    p, s = ats["platform"], ats.get("slug", "")
    return {"greenhouse": f"https://job-boards.greenhouse.io/{s}", "lever": f"https://jobs.lever.co/{s}",
            "ashby": f"https://jobs.ashbyhq.com/{s}", "smartrecruiters": f"https://jobs.smartrecruiters.com/{s}",
            "workable": f"https://apply.workable.com/{s}/", "bamboohr": f"https://{s}.bamboohr.com/careers",
            "recruitee": f"https://{s}.recruitee.com/", "breezy": f"https://{s}.breezy.hr/",
            "workday": f"https://{ats.get('host')}/en-US/{ats.get('site')}"}[p]


# Links to readable job boards as they appear on companies' own careers pages.
LINKS = [
    (r"(?:job-boards|boards)\.greenhouse\.io/(?:embed/job_board\?for=)?([a-z0-9_-]+)", lambda m: board("greenhouse", slug=m[0].lower())),
    (r"greenhouse\.io/embed/job_board(?:/js)?\?for=([a-z0-9_-]+)", lambda m: board("greenhouse", slug=m[0].lower())),
    (r"jobs\.lever\.co/([a-z0-9_.-]+)", lambda m: board("lever", slug=m[0].lower())),
    (r"jobs\.ashbyhq\.com/([A-Za-z0-9_.%-]+)", lambda m: board("ashby", slug=m[0])),
    (r"(?:jobs|careers)\.smartrecruiters\.com/([A-Za-z0-9_-]+)", lambda m: try_smartrecruiters(m[0])),
    (r"apply\.workable\.com/([a-z0-9_-]+)", lambda m: board("workable", slug=m[0].lower())),
    (r"([a-z0-9-]+)\.bamboohr\.com", lambda m: board("bamboohr", slug=m[0].lower())),
    (r"([a-z0-9-]+)\.recruitee\.com", lambda m: board("recruitee", slug=m[0].lower())),
    (r"([a-z0-9-]+)\.breezy\.hr", lambda m: board("breezy", slug=m[0].lower())),
    (r"([a-z0-9-]+\.wd\d+\.myworkdayjobs\.com)/(?:[a-z]{2}-[A-Z]{2}/)?([A-Za-z0-9_-]+)", lambda m: try_workday(m[0], m[1])),
]
LINKS = [(re.compile(rx, re.I), fn) for rx, fn in LINKS]
SKIP_SLUGS = {"www", "api", "app", "careers", "jobs", "embed", "static", "assets", "cdn", "help", "support"}
PATHS = ["", "careers", "careers/", "jobs", "company/careers", "about/careers", "join-us", "join", "work-with-us", "open-positions"]


def scan_site(url):
    """Every readable job board linked from a company's careers page or website."""
    if not url:
        return []
    base = url if url.startswith("http") else "https://" + url
    path = urllib.parse.urlparse(base).path.strip("/")
    root = re.match(r"https?://[^/]+", base).group(0)
    pages = [base] + [root + "/" + p for p in PATHS]
    found, seen = [], set()
    for u in dict.fromkeys(pages):
        html = _text(u)
        if not html:
            continue
        for rx, fn in LINKS:
            for m in rx.finditer(html):
                key = m.group(0).lower()
                if key in seen or m.groups()[0].lower() in SKIP_SLUGS:
                    continue
                seen.add(key)
                r = fn(m.groups())
                if r:
                    found.append(r)
        if found:
            break
    return found


def slugs(name, website=""):
    base = re.sub(r"\s*\(.*?\)", "", name).lower()
    base = re.sub(r"\b(inc|llc|ltd|corp|corporation|co|company|the|plc|holdings|group)\b\.?", "", base)
    joined = re.sub(r"[^a-z0-9]", "", base)
    dashed = re.sub(r"[^a-z0-9]+", "-", base).strip("-")
    short = re.sub(r"\b(therapeutics|biosciences?|biotherapeutics|pharmaceuticals?|pharma|biotechnology|biotech|"
                   r"genomics|diagnostics|technologies|laboratories|labs|medicines|sciences|health)\b", "", base)
    out = [joined, dashed, re.sub(r"[^a-z0-9]", "", short), joined + "inc"]
    host = urllib.parse.urlparse(website if website.startswith("http") else "https://" + website).netloc if website else ""
    if host:
        out.append(re.sub(r"^www\.", "", host).split(".")[0])
    return [s for s in dict.fromkeys(out) if len(s) > 2]


def probe(c):
    """Best US board for a company: (ats, us, bio, total) or None, and everything seen."""
    found = scan_site(c.get("careers") or c.get("website") or "")
    trusted = len(found)
    if not found:
        for s in slugs(c["name"], c.get("website") or ""):
            for p in GUESSABLE:
                r = board(p, slug=s)
                if r and r[3]:
                    found.append(r)
            r = try_smartrecruiters(s)
            if r:
                found.append(r)
    best = None
    for i, r in enumerate(found):
        ats, us, bio, total = r
        guessed = i >= trusted
        # A guessed board name may belong to an unrelated company with the same name, so it must
        # also look like a life-science employer.
        if us and (not guessed or bio >= 1) and (not best or us > best[1]):
            best = r
    return best, [{"board": r[0], "us_jobs": r[1], "bio_jobs": r[2]} for r in found]


# ---------- pass 3: every board in Common Crawl's index ----------

INDEX_PATTERNS = [
    ("greenhouse", "job-boards.greenhouse.io/*", r"greenhouse\.io/([a-z0-9_-]+)"),
    ("greenhouse", "boards.greenhouse.io/*", r"greenhouse\.io/([a-z0-9_-]+)"),
    ("lever", "jobs.lever.co/*", r"lever\.co/([a-z0-9_.-]+)"),
    ("ashby", "jobs.ashbyhq.com/*", r"ashbyhq\.com/([A-Za-z0-9_.%-]+)"),
    ("workable", "apply.workable.com/*", r"workable\.com/([a-z0-9_-]+)"),
    ("bamboohr", "*.bamboohr.com", r"//([a-z0-9-]+)\.bamboohr\.com"),
    ("recruitee", "*.recruitee.com", r"//([a-z0-9-]+)\.recruitee\.com"),
    ("breezy", "*.breezy.hr", r"//([a-z0-9-]+)\.breezy\.hr"),
]


def index_boards(max_pages):
    """{(platform, slug)} for every board seen in the latest Common Crawl index."""
    coll = _json("https://index.commoncrawl.org/collinfo.json")
    if not coll:
        print("Common Crawl index not reachable; skipping")
        return set()
    api = coll[0]["cdx-api"]
    out = set()
    for platform, pattern, rx in INDEX_PATTERNS:
        rx = re.compile(rx, re.I)
        q = urllib.parse.urlencode({"url": pattern, "output": "json", "fl": "url"})
        meta = _json(f"{api}?{q}&showNumPages=true") or {}
        pages = min(int(meta.get("pages", 1) or 1), max_pages)
        before = len(out)
        for page in range(pages):
            text = None
            for attempt in range(4):
                text = _text(f"{api}?{q}&page={page}")
                if text is not None:
                    break
                time.sleep(5 * (attempt + 1))   # the index asks clients to slow down when busy
            for line in (text or "").splitlines():
                m = rx.search(line)
                if m and m.group(1).lower() not in SKIP_SLUGS:
                    out.add((platform, m.group(1).lower() if platform != "ashby" else urllib.parse.unquote(m.group(1))))
        print(f"  {pattern}: {len(out) - before} boards ({pages} index pages)")
    return out


def board_name(ats, fallback):
    if ats["platform"] == "greenhouse":
        d = _json(f"https://boards-api.greenhouse.io/v1/boards/{ats['slug']}")
        if d and d.get("name"):
            return d["name"]
    if ats["platform"] == "workable":
        d = _json(f"https://apply.workable.com/api/v1/widget/accounts/{ats['slug']}")
        if d and d.get("name"):
            return d["name"]
    return fallback.replace("-", " ").replace("_", " ").title()


def board_key(ats):
    return json.dumps({k: (str(v).lower() if k in ("slug", "host", "tenant", "site") else v)
                       for k, v in (ats or {}).items()}, sort_keys=True)


def read_candidates(path):
    out = []
    if not os.path.exists(path):
        return out
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if line and not line.startswith("#"):
            parts = [p.strip() for p in line.split("|")]
            out.append({"name": parts[0], "website": parts[1] if len(parts) > 1 else "",
                        "size": "large" if len(parts) > 2 and parts[2].lower() == "large" else "small"})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--index", action="store_true", help="also search Common Crawl's index for new boards")
    ap.add_argument("--index-pages", type=int, default=40, help="most index pages per board system")
    ap.add_argument("--workers", type=int, default=32)
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    path = os.path.join(DATA, "companies.json")
    companies = json.load(open(path))
    have_names = {norm(c["name"]) for c in companies}
    have_boards = {board_key(c["ats"]) for c in companies if c.get("ats")}
    report = {"boards_found": [], "added": [], "not_found": []}

    # passes 1 and 2
    missing = [c for c in companies if not c.get("ats") or c["ats"].get("platform") not in crawl.ADAPTERS]
    cands = read_candidates(os.path.join(HERE, "candidates.txt"))
    sites = {norm(c["name"]): c["website"] for c in cands if c["website"]}
    for c in missing:   # a tracked company with no website yet: use the one from the list
        if not (c.get("careers") or c.get("website")) and sites.get(norm(c["name"])):
            c["website"] = sites[norm(c["name"])]
    new = [dict(c, origin="finder") for c in cands if norm(c["name"]) not in have_names]
    todo = missing + new
    if a.limit:
        todo = todo[:a.limit]
    print(f"checking {len(missing)} tracked companies without a readable board and {len(new)} new names")
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        results = list(ex.map(probe, todo))
    added = []
    for c, (best, seen) in zip(todo, results):
        if not best:
            report["not_found"].append(c["name"])
            continue
        ats, us, bio, total = best
        if board_key(ats) in have_boards:
            continue
        have_boards.add(board_key(ats))
        if c in new:
            added.append({"name": c["name"], "careers": careers_url(ats), "ats": ats, "origin": "finder",
                          "website": c.get("website", ""), "size": c.get("size", "small")})
            report["added"].append({"name": c["name"], "board": ats, "us_jobs": us, "bio_jobs": bio})
        else:
            c["ats"], c["careers"] = ats, careers_url(ats)
            report["boards_found"].append({"name": c["name"], "board": ats, "us_jobs": us, "bio_jobs": bio})
        print(f"  + {c['name'][:40]:40s} {ats['platform']:15s} {us} US jobs ({bio} life-science)")

    # pass 3
    if a.index:
        print("listing job boards from Common Crawl's index ...")
        boards = [b for b in index_boards(a.index_pages) if board_key({"platform": b[0], "slug": b[1]}) not in have_boards]
        print(f"checking {len(boards)} boards not tracked yet")

        def check(b):
            r = board(b[0], slug=b[1])
            if not r:
                return None
            ats, us, bio, total = r
            # clearly a life-science employer hiring in the US
            if us >= 1 and bio >= 3 and bio >= 0.3 * total:
                return r
            return None
        with ThreadPoolExecutor(max_workers=a.workers) as ex:
            hits = [r for r in ex.map(check, boards) if r]
        for ats, us, bio, total in hits:
            name = board_name(ats, ats["slug"])
            if norm(name) in have_names:
                continue
            have_names.add(norm(name))
            added.append({"name": name, "careers": careers_url(ats), "ats": ats, "origin": "commoncrawl",
                          "size": "large" if total >= 100 else "small"})
            report["added"].append({"name": name, "board": ats, "us_jobs": us, "bio_jobs": bio, "from": "commoncrawl"})
            print(f"  + {name[:40]:40s} {ats['platform']:15s} {us} US jobs ({bio} life-science) [index]")

    print(f"boards found for {len(report['boards_found'])} tracked companies; {len(added)} companies added; "
          f"{len(report['not_found'])} still without a readable board")
    json.dump(report, open(os.path.join(DATA, "discover-report.json"), "w"), indent=1, ensure_ascii=False)
    if not a.dry_run:
        companies = sorted(companies + added, key=lambda c: c["name"].lower())
        json.dump(companies, open(path, "w"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
