# RadioSheet AI — CLAUDE.md

## What this project is
AI-assisted decision support system for radio run-sheet planning.
React (Vite) + TypeScript frontend. FastAPI backend. SQLite (dev) / PostgreSQL (prod).

## Tech stack
- Frontend: React 18, Vite, TypeScript, Zustand, dnd-kit
- Backend: Python, FastAPI, SQLAlchemy, Pydantic, SQLite
- AI layer: scheduling_engine.py, conflict_detector.py, scorer.py, notes_generator.py

## Key conventions
- All AI logic lives in backend/app/ai/ — NEVER in route handlers
- Routes are thin: receive request, call service, return response
- API is versioned: all routes under /api/v1/
- State: Zustand only — no Redux
- Dark UI theme (dark grey + blue accent) — do not use default Bootstrap white

## How to run
- Backend: uvicorn main:app --reload  (port 8000)
- Frontend: npm run dev               (port 5173)

## MVP priority order
1. Apply Fix button (live timeline update) — Priority 1
2. AI run-sheet generation from inputs
3. Colour-coded timeline view
4. Conflict detection (3+ rule types)
5. AI recommendations panel (3+ per run-sheet)
6. Presenter notes (6 segment types)
7. PDF export
8. History tab
