# LazyIntern Frontend (Dashboard Only)

This is the **frontend-only** dashboard for the LazyIntern pipeline. It is designed to sit on top of your backend (FastAPI/Supabase/etc.) and does **not** implement any scraping, scoring, or email sending logic.

All data comes from your backend via HTTP.

---

## Tech Stack

- Next.js (App Router, React 18)
- TypeScript
- Tailwind CSS

No API routes or server actions are used here — this app is purely a UI client.

---

## Getting Started

1. Install dependencies:

```bash
npm install
```

2. Point the frontend to your backend by setting:

```bash
export NEXT_PUBLIC_API_BASE_URL="https://your-backend-host"
```

The dashboard expects a **`GET /dashboard`** endpoint on that base URL.

3. Run the dev server:

```bash
npm run dev
```

Visit `http://localhost:3000` to see the dashboard.

---

## Expected `/dashboard` Response Shape

The UI is typed using `lib/types.ts`. Your backend should return JSON that conforms to the `DashboardData` interface:

- Discovery metrics (scraping tiers, Firecrawl limits, pre-score kills)
- Email metrics (regex vs Hunter, validation failures)
- Outreach metrics (Groq drafts, approvals, Gmail warmup, follow-ups)
- Performance metrics (funnel, reply rates, top company types)
- Retry metrics (active retries and max-retry failures)
- Scoring config (weights from the `scoring_config` table)

You can adjust `lib/types.ts` and your backend serializer together if you want to evolve the schema.

---

## Project Boundaries

- **This repo is frontend-only.** All pipeline phases (scraper, pre-scorer, Hunter, Groq, Twilio, Gmail, retry queue, etc.) live in your backend.
- The frontend never talks directly to Supabase or external APIs; it only calls your backend via `NEXT_PUBLIC_API_BASE_URL`.
- The **Scoring Weight Tuner** panel is currently **read-only** — you can later add secure backend endpoints & UI controls for editing weights if you want.

---

## Git Workflow Suggestion

Since your `main` branch is empty/locked:

- Create a feature branch for the frontend:

```bash
git checkout -b feat/frontend-dashboard
```

- Commit the frontend files from this folder.
- Your teammate can build the backend in a separate branch and later wire `/dashboard` to the real Supabase data.


# LazyIntern

Backend + dashboard for the internship discovery → outreach pipeline described in `logs/final_pipeline.md`.

## Backend setup (Windows)

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
scrapling install
copy .env.example .env
```

Fill in `.env` with your Supabase + API keys.

`scrapling install` downloads browsers for DynamicFetcher (Tier 2).

## Run API (Twilio webhooks)

```powershell
.\.venv\Scripts\activate
python -m uvicorn api.app:app --reload --port 8000
```

## Run one scheduler cycle (dev)

```powershell
.\.venv\Scripts\activate
python -m scheduler.cycle_manager --once
```

