# RadioSheet AI — CLAUDE.md

## CRITICAL: Read this file in full before generating any code.
Do not deviate from the tech stack, conventions, or constraints listed here.
If a request conflicts with this file, follow this file and flag the conflict.
Start every new session by reading this file first.

---

## What this project is

AI-assisted decision support system for radio run-sheet planning.
Solo final year project at GIMPA, BSc Information Technology.

Three core functions:
1. Generate a structured radio run-sheet from user inputs
2. Detect scheduling conflicts (5 rules) and apply fixes live
3. Produce data-driven scheduling recommendations via weighted scoring

This is ASSISTIVE AI, not generative AI. Rule-based scheduling only.
No creative content generation. This distinction is the theoretical foundation.

---

## Tech stack — DO NOT DEVIATE

Frontend:
- React 18 (NOT 19)
- Vite 5
- TypeScript strict mode
- Tailwind CSS v3.4.x (NOT v4)
- Zustand for state (NOT Redux)
- dnd-kit for drag-and-drop
- Axios for HTTP
- React Router v6

Backend:
- Python 3.12
- FastAPI
- SQLAlchemy 2.x ORM
- Pydantic v2
- SQLite for dev, PostgreSQL for production
- uvicorn

AI layer (pure Python, no ML libraries for MVP):
- backend/app/ai/scheduling_engine.py
- backend/app/ai/conflict_detector.py
- backend/app/ai/scorer.py
- backend/app/ai/notes_generator.py

Out of scope — do not add:
- Authentication or login
- Audio streaming or file uploads
- Real PDF generation (use print CSS)
- Multi-user features
- WebSockets for MVP

---

## Environment

python3 --version  → 3.12.3
node --version     → 22.22.1
OS                 → Ubuntu (WSL or native)

---

## Project structure

radiosheet-ai/
├── CLAUDE.md
├── frontend/
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── index.css              ← Tailwind directives only
│       ├── api/
│       │   ├── client.ts          ← Axios instance
│       │   ├── runsheet.ts
│       │   └── conflicts.ts
│       ├── components/
│       │   ├── ui/
│       │   └── layout/
│       ├── features/
│       │   ├── input-form/
│       │   ├── timeline/
│       │   ├── recommendations/
│       │   ├── presenter-notes/
│       │   ├── history/
│       │   └── export/
│       ├── store/
│       │   ├── runsheetStore.ts
│       │   └── uiStore.ts
│       ├── types/
│       │   ├── runsheet.ts
│       │   └── api.ts
│       └── utils/
│           ├── timeFormat.ts
│           └── colours.ts
└── backend/
    ├── main.py
    ├── requirements.txt
    └── app/
        ├── config.py
        ├── dependencies.py
        ├── api/v1/
        │   ├── router.py
        │   ├── runsheet/
        │   ├── conflicts/
        │   └── export/
        ├── ai/                    ← ALL AI LOGIC HERE ONLY
        │   ├── scheduling_engine.py
        │   ├── conflict_detector.py
        │   ├── scorer.py
        │   └── notes_generator.py
        ├── core/
        │   └── exceptions.py
        └── db/
            └── session.py

---

## Critical conventions

1. ALL AI logic in backend/app/ai/ — never in route handlers
2. Routes are thin: validate input, call service, return response
3. All routes under /api/v1/
4. Zustand only for state — no Context API for global state
5. No business logic in React components
6. TypeScript strict mode — no 'any' types
7. All FastAPI functions must be async def
8. Never return SQLAlchemy ORM objects directly — convert to Pydantic first

---

## main.py (must match this exactly)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import router as v1_router
from app.db.session import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="RadioSheet AI",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"status": "ok", "service": "RadioSheet AI"}

---

## Database session (backend/app/db/session.py)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./radiosheet.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

## DB dependency (backend/app/dependencies.py)

from app.db.session import SessionLocal

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

---

## Tailwind setup (v3.4 — exact install command)

npm install -D tailwindcss@^3.4.0 postcss autoprefixer
npx tailwindcss init -p

tailwind.config.js content:
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"]

src/index.css must contain ONLY:
  @tailwind base;
  @tailwind components;
  @tailwind utilities;
  body { background-color: #0f1117; color: #e8eaf0; }

---

## Colour system

Background:      #0f1117
Card:            #13151f
Border:          #1e2133
Primary text:    #e8eaf0
Secondary text:  #8891a8
Accent:          #3b82f6
Heading blue:    #2E75B6

Segment colours:
  music:      #22c55e
  talk:       #3b82f6
  advert:     #f59e0b
  news:       #8b5cf6
  conflict:   #ef4444
  station_id: #06b6d4
  weather:    #10b981
  close:      #6b7280

---

## Pydantic v2 schemas

class ProgrammeType(str, Enum):
    MORNING_SHOW = "morning_show"
    DRIVE_TIME   = "drive_time"
    NEWS_HOUR    = "news_hour"
    MUSIC_ONLY   = "music_only"

class TalkMusicPreference(str, Enum):
    HEAVY_MUSIC = "heavy_music"
    BALANCED    = "balanced"
    TALK_HEAVY  = "talk_heavy"

class SegmentType(str, Enum):
    MUSIC = "music" | TALK = "talk" | ADVERT = "advert" | NEWS = "news"
    STATION_ID = "station_id" | WEATHER = "weather" | CLOSE = "close" | INTRO = "intro"

class ProgrammeInput(BaseModel):
    programme_type: ProgrammeType
    station_name: str = Field(max_length=100)
    broadcast_date: date
    start_time: str
    total_duration_minutes: int = Field(ge=15, le=240)
    presenter_name: str = Field(max_length=100)
    max_advert_blocks_per_hour: int = Field(ge=1, le=6, default=3)
    fixed_segments: list[FixedSegment] = []
    talk_music_preference: TalkMusicPreference = TalkMusicPreference.BALANCED

class Segment(BaseModel):
    id: str
    name: str
    type: SegmentType
    start_time: str
    end_time: str
    duration_minutes: int
    colour_hex: str
    presenter_notes: str = ""

class Conflict(BaseModel):
    rule_id: str
    severity: str
    message: str
    affected_segment_ids: list[str]
    suggested_fix: dict

class Recommendation(BaseModel):
    category: str
    message: str
    impact_score: float

class RunSheetResponse(BaseModel):
    runsheet_id: str
    programme_input: ProgrammeInput
    segments: list[Segment]
    conflicts: list[Conflict]
    recommendations: list[Recommendation]
    stats: RunSheetStats
    generated_at: str

---

## Conflict rules

C001 — Consecutive adverts:
  Trigger: 2+ Advert segments in a row, no non-Advert of ≥3 min between them
  Fix: insert 3-min Talk segment between them

C002 — Duration overrun:
  Trigger: total segment duration > total_duration_minutes + 60 seconds
  Fix: reduce longest non-mandatory segment by excess amount

C003 — Missing station ID:
  Trigger: no StationID in first 15 min OR no StationID in any 30-min window after
  Fix: insert 2-min StationID at minute 14 or midpoint of offending window

C004 — Excessive advert density:
  Trigger: total Advert duration > 20% of programme duration
  Fix: reduce longest advert block to bring density to 18%

C005 — Segment overlap:
  Trigger: any segment start_time < previous segment end_time
  Fix: shift segment to start at previous end_time, cascade forward

---

## Scoring model

4 dimensions, hand-coded weights:
  talk_music_balance:     0.30
  advert_distribution:    0.25
  engagement_placement:   0.25
  transition_quality:     0.20

Always return minimum 3 Recommendation objects.
If fewer than 3 dimensions trigger, include lowest-scoring as recommendations anyway.

---

## Presenter notes (6 types, 3 templates each by position)

Types: INTRO, MUSIC, NEWS, WEATHER, ADVERT, CLOSE
Positions: opening, middle, closing
Use f-strings with: segment.name, segment.duration_minutes,
                    programme.station_name, programme.presenter_name

---

## API endpoints

POST   /api/v1/runsheet/generate
GET    /api/v1/runsheet/history
GET    /api/v1/runsheet/{id}
POST   /api/v1/conflicts/detect
POST   /api/v1/conflicts/apply-fix
POST   /api/v1/export/preview

---

## MVP build order (follow exactly)

SESSION 1:  Backend structure — main.py, db/session.py, dependencies.py
SESSION 2:  scheduling_engine.py
SESSION 3:  conflict_detector.py (all 5 rules)
SESSION 4:  scorer.py (4 dimensions, min 3 recommendations)
SESSION 5:  notes_generator.py (6 types, 3 templates each)
SESSION 6:  API routes — runsheet/ conflicts/ export/
SESSION 7:  Frontend setup — Tailwind, Router, dark theme, App.tsx
SESSION 8:  Input form feature
SESSION 9:  Timeline view with colour-coded segments
SESSION 10: Conflict panel + Apply Fix live update
SESSION 11: Recommendations panel + presenter notes

Cut order if time runs short (cut from bottom):
  First cut:  PDF export
  Second cut: History tab
  Third cut:  Drag-and-drop
  Never cut:  Apply Fix, conflict detection, AI generation

---

## Apply Fix — how it must work

1. Conflict card appears in right panel with Apply Fix button
2. User clicks Apply Fix
3. POST to /api/v1/conflicts/apply-fix with {runsheet_id, conflict_id}
4. Backend applies suggested_fix from the Conflict object
5. Returns {updated_segments, remaining_conflicts}
6. Zustand store: set({ segments: response.updated_segments, conflicts: response.remaining_conflicts })
7. Timeline re-renders — conflict card disappears — stats bar updates

Common mistake: mutating state instead of replacing it
Wrong:  state.segments.push(...)
Right:  set({ segments: response.updated_segments })

---

## Known issues and fixes

CORS blocked:
  Fix: CORSMiddleware in main.py, restart uvicorn

Tailwind not applying:
  Fix: check content paths in tailwind.config.js
  Fix: check @tailwind directives in index.css
  Fix: restart npm run dev

SQLAlchemy DetachedInstanceError:
  Fix: use get_db Depends pattern, convert ORM to Pydantic before returning

Apply Fix not re-rendering:
  Fix: Zustand set() must replace arrays not mutate them

Pydantic v2 errors:
  Fix: use @field_validator not @validator
  Fix: use model_config = ConfigDict(...) not class Config

---

## How to run

Backend:
  cd backend
  source venv/bin/activate
  uvicorn main:app --reload
  → http://localhost:8000
  → http://localhost:8000/docs

Frontend:
  cd frontend
  npm run dev
  → http://localhost:5173

---

## Git workflow

Branches: main (protected) → dev → feat/[name] or fix/[name]
Remote: https://github.com/jija1/radiosheet-ai.git
Commit format: feat(scheduler): add five-stage pipeline

Always work on dev or a feature branch. Never push directly to main.

---

## Post-submission extensions (architecture supports all of these)

1. PostgreSQL: change DATABASE_URL in .env — zero code changes
2. Authentication: add JWT with python-jose, use get_current_user in dependencies.py
3. ML upgrade: replace hand-coded weights in scorer.py with trained values
4. Deployment: Railway/Render for backend, Vercel for frontend
5. Real PDF: add weasyprint to requirements.txt, update export/service.py
6. WebSockets: FastAPI native support, add /ws/runsheet/{id} endpoint
7. Mobile: React Native with same /api/v1/ backend unchanged
