"""Free alternative to the paid job-search APIs, using the open-source JobSpy library
(https://github.com/speedyapply/JobSpy, `pip install python-jobspy`).

JobSpy reads LinkedIn, Indeed, Glassdoor and Google Jobs listings directly. It needs no API key,
but those sites limit how much one computer can read: LinkedIn usually starts blocking after
roughly 10 pages from one IP address, so runs are kept small and slow, and you can add proxies.
Reading those sites this way may break their terms of use; using it is your decision.

Settings (environment variables):
  JOBSEARCH_PROVIDER = jobspy          turns this on (no JOBSEARCH_API_KEY needed)
  JOBSPY_SITES       = indeed,linkedin (default; glassdoor and google also work)
  JOBSPY_RESULTS     = 40              listings to read per company per site
  JOBSPY_DELAY       = 4               seconds to wait between companies
  JOBSPY_PROXIES     = user:pass@host:port,host2:port   optional, comma-separated
  JOBSPY_MAX_COMPANIES = 150           companies to look up per run (0 = no limit); the rest are
                                       picked up on later runs, which keeps LinkedIn from blocking
"""
import os
import time

COUNTRY = {"il": ("Israel", "israel"), "us": ("United States", "usa")}
_count = 0


def available():
    try:
        import jobspy  # noqa: F401
        return True
    except ImportError:
        return False


def listings(company, country="il"):
    """Return [{title, location, url, site, company}] for one company, or [] if blocked/limited."""
    global _count
    from jobspy import scrape_jobs
    cap = int(os.environ.get("JOBSPY_MAX_COMPANIES", "150") or 0)
    if cap and _count >= cap:
        return []
    if _count:
        time.sleep(float(os.environ.get("JOBSPY_DELAY", "4")))
    _count += 1
    where, indeed_country = COUNTRY.get(country, COUNTRY["us"])
    sites = [s.strip() for s in os.environ.get("JOBSPY_SITES", "indeed,linkedin").split(",") if s.strip()]
    proxies = [p.strip() for p in os.environ.get("JOBSPY_PROXIES", "").split(",") if p.strip()] or None
    kw = dict(site_name=sites, search_term=f'"{company}"', location=where, country_indeed=indeed_country,
              results_wanted=int(os.environ.get("JOBSPY_RESULTS", "40")), proxies=proxies, verbose=0)
    if "google" in sites:
        kw["google_search_term"] = f"{company} jobs in {where}"
    df = scrape_jobs(**kw)
    out = []
    for r in df.to_dict("records"):
        loc = r.get("location")
        if isinstance(loc, dict):
            loc = ", ".join(str(v) for v in (loc.get("city"), loc.get("state"), loc.get("country")) if v)
        out.append({"title": r.get("title") or "", "location": str(loc or ""), "company": r.get("company") or "",
                    "url": r.get("job_url_direct") or r.get("job_url") or "", "site": str(r.get("site") or "")})
    return out


def listings_for_job(company, title, country="us"):
    """Search for one job title at one company on Indeed, LinkedIn and Google Jobs."""
    from jobspy import scrape_jobs
    time.sleep(float(os.environ.get("JOBSPY_DELAY", "4")))
    where, indeed_country = COUNTRY.get(country, COUNTRY["us"])
    sites = [s.strip() for s in os.environ.get("JOBSPY_JOB_SITES", "indeed,linkedin,google").split(",") if s.strip()]
    proxies = [p.strip() for p in os.environ.get("JOBSPY_PROXIES", "").split(",") if p.strip()] or None
    kw = dict(site_name=sites, search_term=f'{title} "{company}"', location=where, country_indeed=indeed_country,
              results_wanted=10, proxies=proxies, verbose=0)
    if "google" in sites:
        kw["google_search_term"] = f"{title} {company} jobs in {where}"
    out = []
    for r in scrape_jobs(**kw).to_dict("records"):
        loc = r.get("location")
        if isinstance(loc, dict):
            loc = ", ".join(str(v) for v in (loc.get("city"), loc.get("state"), loc.get("country")) if v)
        out.append({"title": r.get("title") or "", "location": str(loc or ""), "company": r.get("company") or "",
                    "url": r.get("job_url_direct") or r.get("job_url") or "", "site": str(r.get("site") or "")})
    return out
