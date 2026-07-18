# ResumeCheck

A free ATS (Applicant Tracking System) resume checker. Upload a resume (PDF/DOCX), optionally
paste a job description, and get a transparent 0-100 score with a category breakdown and specific,
actionable fixes.

**Phase 1 (this build):** free checker only. No templates, no payments, no resume builder — the
data model leaves room for those in Phase 2 without a rewrite (see below).

## Architecture

```
frontend/   Next.js 16 (App Router) + TypeScript + Tailwind CSS  — UI only, calls the API
backend/    FastAPI (Python)  — parsing, ATS checks, scoring, Supabase persistence, email
sample_resumes/   Test fixtures (clean / multi-column / table-heavy / header-contact / scanned-image)
```

The frontend never talks to Supabase directly — it only calls the FastAPI backend
(`NEXT_PUBLIC_API_URL`), which owns all parsing, scoring, and persistence logic. This keeps the
door open for a future paid templates section / auth without touching the checker's internals.

## Local development

### Backend (FastAPI)

Requires Python 3.11+ (3.14 currently lacks prebuilt wheels for some dependencies — 3.11/3.12/3.13
are the safe choice).

```bash
cd backend
python -m venv .venv
./.venv/Scripts/activate        # Windows; use `source .venv/bin/activate` on macOS/Linux
pip install -r requirements.txt
cp .env.example .env            # fill in SUPABASE_URL / SUPABASE_ANON_KEY if you have your own project
uvicorn app.main:app --reload --port 8000
```

Run tests: `pytest` (from `backend/`). Regenerate `sample_resumes/` fixtures with
`python tests/generate_fixtures.py` (requires `pip install -r requirements-dev.txt`).

### Frontend (Next.js)

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:3000`. It expects the API at `NEXT_PUBLIC_API_URL` (see `.env.local`,
defaults to `http://localhost:8000`).

## Scoring rubric

The rubric is defined once, in `backend/app/scoring/rubric.py`, and echoed back to the frontend in
every API response (`rubric` field) so the "How is this score calculated?" panel in the UI is never
out of sync with the actual math:

- **With a job description pasted:** 4 categories, each weighted 25% — Parseability & Format,
  Layout & Structure, Content Completeness, Keyword Match.
- **Without a job description:** the same 3 non-keyword categories, rescaled to ~33% each.

Each category is a weighted sum of individual sub-checks (see `SUB_WEIGHTS` in `rubric.py`).

## Environment variables

| File | Variable | Purpose |
|---|---|---|
| `backend/.env` | `SUPABASE_URL`, `SUPABASE_ANON_KEY` | Report persistence + shareable report links. App runs fine without these — persistence is skipped, `/api/report/*` returns 503. |
| `backend/.env` | `RESEND_API_KEY`, `RESEND_FROM_EMAIL` | "Email me this report" delivery via [Resend](https://resend.com). Without a key, the email is still saved but delivery is skipped. |
| `backend/.env` | `ALLOWED_ORIGINS` | CORS allow-list for the frontend origin(s). |
| `frontend/.env.local` | `NEXT_PUBLIC_API_URL` | Where the frontend sends API requests. |

## Deployment

- **Frontend → Vercel**: import the repo, set the root directory to `frontend/`, add
  `NEXT_PUBLIC_API_URL` pointing at your deployed backend. `vercel.json` is already present.
- **Backend → Render**: `backend/render.yaml` defines a Python web service
  (`uvicorn app.main:app`). Create a new Render Web Service from this repo with root directory
  `backend/`, and set `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `RESEND_API_KEY`, `RESEND_FROM_EMAIL`,
  and `ALLOWED_ORIGINS` (your Vercel domain) in the Render dashboard — they're marked `sync: false`
  in `render.yaml` so they must be set manually rather than committed.
- The Supabase project (`reports` / `email_subscribers` tables) is already provisioned; reuse the
  same `SUPABASE_URL` / anon key in both local `.env` and the Render dashboard.

## Phase 2 (not built — see brief)

Paid ATS-friendly resume templates + checkout + resume builder. The `reports` table already has a
nullable `user_id` column as the only forward-looking hook; no `templates`/`purchases` tables exist
yet by design. The `/templates` route in the frontend is a static "coming soon" stub with no logic
behind it.
