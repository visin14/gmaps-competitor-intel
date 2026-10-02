# Google Maps Competitor Update Intelligence Tool

Web tool that collects Google Maps **Updates/Posts** from manually chosen competitor profiles, stores them in a
repository (with duplicate detection), analyzes them with AI, calculates topic trends, and generates complete
draft Google Maps updates informed by that research.

- **Live demo:** https://gmaps-competitor-intel.vercel.app
- **Repository:** https://github.com/visin14/gmaps-competitor-intel
- **Demo video:** _<paste link>_

## Workflow
Project → add own profile → add competitors (manual) → add keywords → **scrape** → posts stored (text, images, date,
CTA, source URL, scrape time) → duplicates skipped → **AI analysis** (topic, sub-topic, keywords, content type, CTA,
offer pattern) → **trends** (e.g. "Hair Care Tips: 4 of 5 competitors, 80%") → **generate N ideas / complete updates**
→ history prevents repeats.

## Architecture
| Layer | Tech | Files |
|---|---|---|
| Web UI | Vanilla JS single-page app (responsive, dark theme) | `static/` |
| API | Flask + Flask-SQLAlchemy, blueprints per feature | `app.py`, `routes/` |
| Storage | SQLite locally; any SQLAlchemy URL (`DATABASE_URL`, e.g. Postgres) in production | `models.py`, `config.py` |
| Scraper | Python + Selenium; parsing isolated in a pure-HTML parser | `scraper/gmaps_scraper.py`, `scraper/parser.py` |
| AI | Shared client with retries + provider failover; Gemini and Grok adapters | `ai/` |
| Analytics | Topic trends, keyword counts, per-competitor publishing patterns | `utils/trends.py` |

### Duplicate detection
Each post gets a SHA-256 fingerprint: the post URL (scoped to the project) when available, otherwise
`competitor id + normalized text`. A unique index on the fingerprint makes re-scrapes skip stored posts; the scrape log
records "posts found / new / duplicates skipped". The same competitor in two projects never collides.

### CAPTCHA / verification handling
The scraper detects verification pages, sets the job to `awaiting_verification`, shows an alert with a **Resume**
button, and keeps polling so it also continues automatically once you solve it in the browser window. The log records
`captcha_encountered` and `manual_intervention`; an unsolved CAPTCHA times out and is logged as a failure instead of
failing silently. Missing Updates tabs / unrecognised pages are logged as `no_updates` with an HTML + screenshot
snapshot in `instance/scrape_debug/`.

### Generated-idea duplicate prevention
Every generated idea is stored per project. New requests send previous ideas to the model as an "avoid" list and
discard results whose title or wording is too similar to anything already generated (title similarity + word-overlap
score). The count requested (1–50) controls the number of ideas returned.

## AI providers
1. **Google Gemini** (`GEMINI_API_KEY`) - tested; automatic model discovery if a model is retired.
2. **xAI Grok** (`GROK_API_KEY`) - integrated with the same interface; needs its own key.

If one provider fails or runs out of quota the other is used; if none is available, analysis falls back to keyword
rules and ideas to templates (clearly labeled `fallback` in the UI and exports). Keys live only in `.env` / hosting
environment variables, never in source or the frontend.

## Bonus features implemented
- Automatic model discovery and failover across AI providers
- Per-competitor publishing patterns (volume, posts/week, top topics, CTAs, offer share)
- Top keywords and trend visualizations (donut + bar charts)
- Detailed scrape logs with manual-intervention tracking
- Persisted-Chrome-profile option to reduce CAPTCHA interruptions (`SCRAPER_PROFILE_DIR`)

Not implemented: keyword-based business discovery, scheduled scraping, third-party CAPTCHA solving.

## Run locally
```
pip install -r requirements.txt
copy .env.example .env      # add GEMINI_API_KEY / GROK_API_KEY
python app.py               # http://127.0.0.1:5000  (set PORT to change)
```
Optional one-time sign-in for the scraper's Chrome profile: `python sign_in_scraper_profile.py`.

## Demo dataset
The first start seeds the **"Luxe Salon & Spa"** project: 5 competitors, 55 demo posts (with generated illustrative
images), trends, scrape logs and sample ideas. **This is a seeded demo dataset, not data scraped live from Google
Maps**, so the platform stays fully usable if Google blocks scraping. The ideas labeled `demo` are hand-written samples.

## Deploying to Vercel
See [DEPLOY_VERCEL.md](DEPLOY_VERCEL.md). Live scraping needs Chrome, so it is disabled on the hosted app (the API
says so); run locally to demonstrate scraping.

## Submission exports
`python export_submission.py` writes CSV/JSON files to `submission/` (competitors, collected posts, AI analysis,
trends, keywords, publishing patterns, generated updates, scrape logs). Use `--generate N` to first create N new ideas
with the configured AI providers; every row keeps its provider so AI output is never mislabeled.

## Known limitations
- The Selenium extraction has been run against real Google Maps pages, but only profiles **without** an Updates tab have
  been seen so far, so post extraction on a live profile with Updates is verified only against sample HTML. Google
  changes its markup often; selectors live in `scraper/parser.py` (`CARD_SELECTORS`) and `UPDATES_TAB_XPATHS`.
- Gemini's free tier is small (about 20 requests/day per model), so AI analysis of large batches may fall back.
- Without `DATABASE_URL`, the Vercel deployment keeps data in temporary storage (demo data re-seeds on cold start).
