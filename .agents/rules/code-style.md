# Code Style Rules — AI Venture Studio

## Python (backend, agent pipeline)
- PEP 8
- Every function has a docstring
- No magic numbers — use named constants
- Type hints on all function signatures
- One responsibility per file — new features go in new files, not appended to `main.py`
- Pydantic models for all data schemas (agent state, report schemas, rules validation)

## React / Frontend
- Functional components with hooks only — no class components
- Tailwind utility classes for styling; use shadcn/ui components as the base before writing custom ones
- One component per file
- Co-locate a component's types with the component unless shared across multiple components

## API / integration
- Every external LLM call (NVIDIA NIM, Gemini) wraps in a retry-with-backoff helper — do not call the raw client directly from agent node code
- Every Supabase write from agent nodes includes `project_id` and `timestamp`
- No secrets in code — environment variables only

## General
- Modular file structure: one feature per file, not monolithic files
- Commit after every completed task
- Comment WHY, not WHAT, for anything non-obvious in the agent pipeline logic
