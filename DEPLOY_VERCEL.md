# Deploying to Vercel

```
npx vercel login          # opens the browser; sign in yourself
npx vercel                # first deploy (preview) - answer the prompts, accept defaults
npx vercel --prod         # production URL
```

Environment variables (Vercel dashboard > Project > Settings > Environment Variables):

| Name | Purpose |
|---|---|
| `GEMINI_API_KEY` | Gemini provider (optional on the hosted demo - ideas fall back to templates without it) |
| `GROK_API_KEY` | Grok provider (optional) |
| `GEMINI_MODEL` | `gemini-flash-latest` |
| `SECRET_KEY` | any random string |
| `DATABASE_URL` | optional but recommended: a free Postgres (e.g. Neon) so data survives restarts |

Notes
- Without `DATABASE_URL` the app uses SQLite in `/tmp`: the demo dataset is re-seeded on every cold start and
  anything you add is lost when the instance recycles.
- Live scraping needs Chrome, so it is disabled on Vercel (the API explains this). Run locally for the scraping demo.
- Analysis runs synchronously on Vercel (functions are frozen after responding).
