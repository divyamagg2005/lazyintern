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

