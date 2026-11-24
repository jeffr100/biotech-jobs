# US biotech & genomics jobs: website, crawler and newsletter

This folder is a searchable job board of **US-only** openings at about 1,440 genomics, diagnostics, life-science tools and biopharma companies. The jobs are read straight from each company's own career board, and the site can flag the ones that are **not** on LinkedIn, Indeed or Glassdoor.

| Path | What it is |
|---|---|
| `index.html` | The website. It has search, seniority, field, state, date, company-size and source filters, an email sign-up form and small text-ad spots. It reads `data/site.json`. |
| `site.config.js` | Settings for email sign-up (Brevo) and Google AdSense. |
| `data/companies.json` | Every company: its size, careers link or website, and job-board settings (`ats`). |
| `data/jobs.json` | Current US jobs, with the date each was first seen and, once checked, `coverage` (whether the job is on LinkedIn, Indeed or Glassdoor). |
| `data/feed.xml` | RSS feed of the jobs that are new in the latest run. |
| `data/digest-daily.md`, `-weekly`, `-monthly` | The newsletter emails for each frequency. |
| `crawler/crawl.py` | The crawler (Python 3, no packages to install). Set `US_ONLY=0` to keep every country. |
| `crawler/coverage_check.py` | Marks which jobs also appear on LinkedIn, Indeed or Glassdoor. |
| `crawler/publish.py` | Builds the daily, weekly and monthly digests and sends them through Brevo (or Buttondown) (and posts the weekly one to WordPress, if set up). |

## Running the site on your computer

The zip already includes the current job data, so the site works straight away:

- **Mac:** double-click `start_site.command`. If macOS says it can't be opened, right-click it and choose **Open**. Your browser opens http://localhost:8000.
- **Windows:** double-click `start_site.bat`. This needs Python from python.org.
- **Any system:** in this folder, run `python3 -m http.server 8000`, then open http://localhost:8000.

Opening `index.html` directly (as a `file://` address) won't load the jobs, because browsers block it from reading `data/site.json` that way. To refresh the data, run `python3 crawler/crawl.py`, then reload the page.

## Simplest setup: GitHub Pages + RSS-to-email (free to start)

1. Create a GitHub repository and upload this folder.
2. Go to **Settings → Pages** and set **Source: GitHub Actions**.
3. Go to **Actions → Job crawl → Run workflow**. The site appears at `https://<you>.github.io/<repo>/` and is updated every morning (the schedule is the cron line in `.github/workflows/weekly-crawl.yml`).
4. Set up email updates and ads as described below.

To re-publish the site without crawling again, for example after changing `index.html` or `site.config.js`, run `gh workflow run "Job crawl" -f crawl=false`. It takes about a minute. If only the "deploy" step of a run fails, open the run on GitHub and choose **Re-run failed jobs**: only the publishing step runs again.

## Email updates (daily, weekly or monthly) with Brevo

Visitors sign up on the site and choose daily, weekly or monthly emails. This uses [Brevo](https://www.brevo.com). Its free plan stores up to 100,000 contacts and sends up to 300 emails a day, with API access included.

**In Brevo** (one-time):
1. **Sender:** under **Senders, domains & dedicated IPs**, add and verify the address the emails come from.
2. **Lists:** under **Contacts → Lists**, create three lists: `Jobs daily`, `Jobs weekly`, `Jobs monthly`. Note each list's ID number.
3. **Forms:** under **Contacts → Forms**, create one subscription form per list. Double opt-in is recommended. Open each form's **Share → HTML code** and copy the form's `action` address (`https://….sibforms.com/serve/…`).
4. **API key:** under **SMTP & API → API keys**, create an API key.

**On your computer**, in this folder:
```bash
gh secret set BREVO_API_KEY                      # paste the key when asked (it's never shown or saved in the repo)
gh variable set BREVO_SENDER_EMAIL --body you@yourdomain.com
gh variable set BREVO_SENDER_NAME  --body "Biotech & Genomics Jobs"
gh variable set BREVO_LIST_DAILY   --body 3      # your list IDs
gh variable set BREVO_LIST_WEEKLY  --body 4
gh variable set BREVO_LIST_MONTHLY --body 5
gh variable set BREVO_SEND --body 1              # leave out at first to get drafts you can check in Brevo
```
Then put the three form addresses into `site.config.js` under `newsletter.brevoForms`, and commit and push.

Each morning the workflow runs `crawler/publish.py`:
- The **daily** email goes to the daily list every day.
- The **weekly** email goes to the weekly list on Mondays.
- The **monthly** email goes to the monthly list on the 1st.

Each email lists the jobs first seen in that period, with the jobs not found on LinkedIn or Indeed first, and has an unsubscribe link. Days with no new jobs send nothing.

**Free-plan limit:** 300 emails a day across all lists. A day's email goes to its whole list, so once a list passes about 300 people, Brevo holds back the rest until you resend or upgrade. The Starter plan, from about $9 a month, removes the daily cap.

Buttondown still works: set `newsletter.provider` to `"buttondown"` in `site.config.js` and add the `BUTTONDOWN_API_KEY` secret.

## Google ads (small text ads)

The site shows small Google text ads, each the size of one job row and labelled "Sponsored". There are three spots:
- the third item in the job list;
- one more every 25 jobs (`adsense.feedEvery`);
- under the sign-up box in the sidebar, on desktop only.

Until AdSense is set up they appear as dashed outlines. Set `adsense.showPlaceholders` to `false` to hide them.

Google no longer offers "text ads only" display units. Small text ads now come from **In-feed** (native) ad units styled with the "Text only" template.

1. Put the site where `ads.txt` can sit at the root of the address, such as your own domain (GitHub Pages supports custom domains) or a GitHub user site at `https://<you>.github.io/`. A project site at `https://<you>.github.io/<repo>/` can't serve `ads.txt` at the root, and AdSense never serves ads on localhost.
2. Apply at [Google AdSense](https://adsense.google.com) and wait for approval.
3. In AdSense, go to **Ads → By ad unit → In-feed ads**, choose the manual style and the **Text only** template, and match the fonts and colours to the site. Make one unit for each spot (top, feed, side).
4. Each unit's code shows a `data-ad-slot` and a `data-ad-layout-key`. Paste them into `site.config.js` under `adsense.slots`, and your publisher ID (`ca-pub-…`) into `adsense.client`.
5. Rename `ads.txt.example` to `ads.txt` and put your own publisher number in it.

Ads are switched off automatically when the site is served from a `github.io` address, because GitHub Pages doesn't allow sites run mainly for commercial purposes. Host on your own domain (for example with Cloudflare Pages or Netlify) to show them. To override this, set `adsense.disableOnGithubPages` to `false`.

## Seniority

The seniority filter and the coloured bar at the top of the page sort jobs into seven levels from the job title:
- Intern / student
- Entry level
- Mid-level
- Senior
- Principal / manager
- Director & up
- Postdoc / fellow

Titles without a clear signal count as mid-level. Sales titles such as "Account Manager" are not treated as manager-level. The rules are the `level()` function in `index.html`.

## Hosting on Netlify instead of GitHub Pages

GitHub Actions still runs the crawler every morning; Netlify only hosts the finished site. Netlify's free plan has 300 credits a month and each production deploy costs 15, so the workflow deploys once a week (Mondays) by default. Daily deploys (~450 credits/month) need the Personal plan or `NETLIFY_DEPLOY=daily` with enough credits.

1. Create a Netlify account and an empty site, and install the Netlify CLI: `brew install netlify-cli`, then `netlify login`.
2. In this folder run `netlify sites:create --name <pick-a-name>` and copy the **Site ID** it prints (also under Site configuration → General).
3. Create a personal access token in Netlify (User settings → Applications → Personal access tokens).
4. Tell GitHub to deploy to Netlify:
   ```bash
   gh variable set HOSTING --body netlify
   gh variable set SITE_URL --body https://<pick-a-name>.netlify.app/
   gh secret set NETLIFY_SITE_ID --body <site-id>
   gh secret set NETLIFY_AUTH_TOKEN          # paste the token when asked
   gh workflow run "Job crawl"
   ```
5. New Netlify projects may start private; publish the site in Netlify if it asks.

Don't also link the GitHub repository to Netlify for automatic builds: the daily data commit would trigger a paid deploy every day. To test by hand instead, run `netlify deploy --dir . --prod` from this folder, or drag the folder onto https://app.netlify.com/drop.

For Google ads, connect your own domain in Netlify (Domain management) so `ads.txt` sits at the root of that domain.

## WordPress

If you have a WordPress site, the workflow can post each digest:
1. In WordPress, go to **Users → Profile → Application Passwords** and create one.
2. Add these repository secrets: `WP_URL` (for example `https://example.com`), `WP_USER` and `WP_APP_PASSWORD`. Set `WP_STATUS=publish` to publish straight away; otherwise posts are saved as drafts.

Your WordPress subscribers (Jetpack or MailPoet) then get each post by email.

## Jobs on Indeed, LinkedIn and Google Jobs, and finding jobs that are missing there

Set these repository secrets:

| Secret | Value |
|---|---|
| `JOBSEARCH_PROVIDER` | `jsearch` (OpenWeb Ninja JSearch: Google for Jobs data, including LinkedIn, Indeed and Glassdoor) or `serpapi` (SerpApi Google Jobs) |
| `JOBSEARCH_API_KEY` | Your key from that provider |
| `JOBSEARCH_SCOPE` | `untracked` (default) or `all` |

With these set, each run does two things:
1. **Adds listings for companies whose own board isn't tracked.** They're labelled "via LinkedIn" and so on, and the site has a toggle for them.
2. **Checks coverage.** Each company's own-board jobs are compared with that company's listings on the job-search API, and every job is marked as found or not found on LinkedIn, Indeed and Glassdoor. The website's **Only jobs not on LinkedIn or Indeed** button then shows the ones you can't find elsewhere. The newsletter lists those first and marks them ★.

Only companies with new, unchecked jobs are queried, so after the first run the weekly cost is small. Run `python3 crawler/coverage_check.py --all` to re-check everything.

### Checking jobs one at a time

After the company-wide search, the crawler searches again for each job that wasn't found elsewhere. The query is the job title plus the company name ("Senior Scientist, Assay Development GRAIL"), run against Google Jobs, Indeed and LinkedIn. A company-wide search only returns a company's first few dozen listings, so jobs at large employers are often missed there. The individual search fills that gap.

- Each job gets `coverage.method` set to `company` or `job`, so you can see how it was checked. The site shows "also on LinkedIn, Indeed, Google Jobs" or "not on LinkedIn, Indeed or Google Jobs".
- `COVERAGE_PER_JOB_MAX` (default 200, or 100 with JobSpy) caps the individual searches per run. The newest jobs go first and the rest are picked up on later runs.
- `COVERAGE_PER_JOB=0` turns this pass off.
- Cost: one search per job. That is roughly $0.002–0.015 per job, depending on the plan, with JSearch or SerpApi, or free with JobSpy but slow, at about 4 seconds per job to avoid blocking.

### Free option: JobSpy (no API key)

Set the repository secret `JOBSEARCH_PROVIDER` to `jobspy` and leave out `JOBSEARCH_API_KEY`. The workflow installs the open-source [JobSpy](https://github.com/speedyapply/JobSpy) library, which reads LinkedIn and Indeed listings directly. It powers both features: the "not on LinkedIn or Indeed" check and the LinkedIn/Indeed job feed.

Limits to know:
- **Blocking.** LinkedIn starts blocking one computer after a few hundred requests. To avoid that, each run looks up only 75 companies per pass (`JOBSPY_MAX_COMPANIES`) and the rest are checked on later runs. GitHub's servers get blocked more often than a home connection; adding proxies (`JOBSPY_PROXIES`) helps.
- **Terms of use.** Reading LinkedIn and Indeed this way may break their terms of use. The paid APIs above avoid that.
- **Other optional settings.** `JOBSPY_SITES` defaults to `indeed,linkedin`; `glassdoor` and `google` also work.
- **Mac.** JobSpy needs Python 3.10 or newer. macOS's built-in Python is 3.9, so install a newer one (for example `brew install python`). `mac/run_weekly.sh` uses it automatically when `JOBSEARCH_PROVIDER=jobspy`.

## Company size

`size` is `large` (about 1,000+ employees) or `small`. It's set from three sources:
- a curated list of large companies;
- Wikidata employee counts;
- any company with 150 or more open US jobs, which is marked large.

Edit `companies.json` to correct it.

## Job boards

Supported boards are Greenhouse, Lever, Ashby, SmartRecruiters and Workday. To add or fix a company, edit its `ats` field:

```json
{"platform": "greenhouse", "slug": "natera"}
{"platform": "lever", "slug": "streck"}
{"platform": "ashby", "slug": "insitro"}
{"platform": "smartrecruiters", "slug": "abbvie"}
{"platform": "workday", "host": "illumina.wd1.myworkdayjobs.com", "tenant": "illumina", "site": "illumina-careers"}
```

## Data sources

- **Company list.** It combines four sources:
  - an initial list of companies;
  - the [LastRound AI ATS Company Directory](https://datahub.io/lastroundai-hiring-data/lastroundai-hiring-data/ats-directory) (CC BY 4.0);
  - Wikidata (CC0);
  - industry sponsors of trials on ClinicalTrials.gov.
- **Jobs.** Each company's public job board.

## Personal job alerts

Visitors can set filters and click **Email me these jobs**. Their filters (the text after `#` in the
page address) are saved on their Brevo contact, and each crawl emails them only the new jobs that
match, daily, weekly or monthly. Every alert email has a "Stop this alert" link.

Setup (once):
1. In Brevo, two text contact attributes: `BIO_ALERT` and `BIO_ALERT_FREQ`; a list for alert sign-ups.
2. A Brevo sign-up form that puts contacts in that list and has the email field plus the two attributes.
   Copy its address (Share > HTML) into `site.config.js` > `newsletter.alerts.form`.
3. Repository variable `BREVO_ALERT_LIST` = that list's ID (currently 12). `BREVO_SEND=1` sends for real.

Alert emails are sent one per person through Brevo's transactional email, which shares the free plan's
300-a-day limit with the digests; `ALERT_MAX` (default 200) caps alert emails per run.

## Checking LinkedIn reliably (paid proxy, a few dollars a month)

LinkedIn refuses searches from GitHub's servers, so without help jobs show "LinkedIn not checked".
Routing only the LinkedIn searches through a rotating residential proxy fixes this; Indeed and Google
are still searched directly, which keeps the proxy traffic small.

1. Buy a rotating residential proxy plan billed per GB (for example Webshare, about $3.50 for 1 GB).
2. Copy its connection string, `username:password@host:port`.
3. Repository secret `JOBSPY_PROXIES` = that string; variable `JOBSPY_SITES` = `indeed,linkedin`
   (and secret `JOBSEARCH_PROVIDER` = `jobspy` if it isn't set).

Optional: `JOBSPY_PROXY_SITES` lists the sites sent through the proxy (default `linkedin`).
