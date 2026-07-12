---
name: deployment
description: Use when deploying or configuring the frontend (Vercel), backend (Render), or database (Supabase) for AI Venture Studio, or when debugging deployment/environment issues.
---

# Skill: Deployment

## Targets
- Frontend (React/Tailwind/shadcn) → Vercel, free Hobby tier
- Backend (FastAPI) → Render, free tier
- Database/Auth/Storage → Supabase, free tier

## Required environment variables
Backend (Render):
- `NVIDIA_NIM_API_KEY`
- `GEMINI_API_KEY`
- `TAVILY_API_KEY`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY` (server-side only, never expose to frontend)
- `CHROMA_DB_PATH` or connection string if not fully local

Frontend (Vercel):
- `NEXT_PUBLIC_SUPABASE_URL` / equivalent for the framework in use
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` (anon key only — never the service role key)
- `NEXT_PUBLIC_API_BASE_URL` (points to the Render backend)

Never commit any of the above to the repo. Use `.env` locally (gitignored) and each platform's environment variable dashboard in production.

## Free-tier caveats to design around
- **Supabase**: free project auto-pauses after 7 days of inactivity. Resume manually from the dashboard before any demo. Consider a scheduled keep-alive ping if the gap between work sessions could exceed a week.
- **Render**: free web services spin down after inactivity. First request after idle has a ~30-50 second cold start. Hit the health-check endpoint a few minutes before any live demo to warm it up.
- **NVIDIA NIM**: free tier ~40 requests/minute shared across the whole key. See `skills/agent-orchestration/SKILL.md` for the mandatory backoff/failover handling.
- **Tavily**: free tier 1000 credits/month, separate from NIM/Gemini. Basic search = 1 credit, Advanced = 2 credits. See `skills/web-research/SKILL.md` for quota-conservation tactics.

## Deployment checklist
- [ ] Backend deployed to Render, health-check endpoint responding
- [ ] Frontend deployed to Vercel, pointing at the correct `NEXT_PUBLIC_API_BASE_URL`
- [ ] Supabase schema migrated, RLS policies enabled on all user-facing tables
- [ ] All secrets set as environment variables on Render/Vercel, none in the repo (including `TAVILY_API_KEY`)
- [ ] CORS configured on FastAPI backend to allow the Vercel frontend origin
- [ ] Smoke test: full pipeline run (idea input → report export) against the deployed URLs, not just localhost — test both with an uploaded document AND with web-research-only (no upload) to confirm both paths work
