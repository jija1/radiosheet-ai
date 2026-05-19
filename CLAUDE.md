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

## Project status — post-submission phase

Documentation has been submitted to GIMPA. The app is partially built and working.
The remaining features are being built in sessions A–J. Each session has a defined
scope. Do not start the next session's work until the current session is complete
and tests pass.

---

## Tech stack — DO NOT DEVIATE

Frontend:
- React 18 (NOT 19)
- Vite 5
- TypeScript strict mode
- Tailwind CSS v3.4.x (NOT v4)
- Zustand for state (NOT Redux)
- dnd-kit for drag-and-drop (installed — wired in Session D)
- Axios for HTTP
- React Router v6

Backend:
- Python 3.12
- FastAPI
- SQLAlchemy 2.x ORM
- Pydantic v2
- python-jose + passlib + bcrypt for JWT auth
- SQLite for dev, PostgreSQL for production
- uvicorn

AI layer (pure Python, no ML libraries):
- backend/app/ai/scheduling_engine.py
- backend/app/ai/conflict_detector.py
- backend/app/ai/scorer.py
- backend/app/ai/notes_generator.py
- backend/app/ai/compliance_validator.py  ← added in Session E

Out of scope — do not add:
- Audio streaming or file uploads
- WebSockets
- Real-time collaboration
- ML or neural network models

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
│       ├── index.css
│       ├── api/
│       │   ├── client.ts
│       │   ├── runsheet.ts
│       │   ├── conflicts.ts
│       │   └── auth.ts                    ← added Session A
│       ├── components/
│       │   ├── ui/
│       │   └── layout/
│       ├── features/
│       │   ├── auth/                      ← added Session A (login + register pages)
│       │   ├── dashboard/                 ← added Session B
│       │   ├── input-form/
│       │   ├── timeline/
│       │   ├── recommendations/
│       │   ├── presenter-notes/
│       │   ├── history/
│       │   ├── validate/                  ← added Session F
│       │   ├── settings/                  ← added Session H
│       │   ├── profile/                   ← added Session I
│       │   └── export/
│       ├── store/
│       │   ├── runsheetStore.ts
│       │   ├── uiStore.ts
│       │   └── authStore.ts               ← added Session A
│       ├── types/
│       │   ├── runsheet.ts
│       │   ├── api.ts
│       │   └── auth.ts                    ← added Session A
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
        │   ├── auth/                      ← added Session A
        │   ├── runsheet/
        │   ├── conflicts/
        │   ├── validate/                  ← added Session F
        │   ├── user/                      ← added Session B
        │   └── export/
        ├── ai/
        │   ├── scheduling_engine.py
        │   ├── conflict_detector.py
        │   ├── scorer.py
        │   ├── notes_generator.py
        │   └── compliance_validator.py    ← added Session E
        ├── models/
        │   ├── user.py                    ← added Session A
        │   ├── runsheet.py
        │   └── audit_log.py              ← added Session H
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
9. JWT token stored in Zustand authStore only — never in localStorage
10. All runsheet routes protected with Depends(get_current_user) after Session A

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

---

## DB and auth dependencies (backend/app/dependencies.py)

from app.db.session import SessionLocal
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from app.models.user import User
import os

SECRET_KEY = os.getenv("SECRET_KEY", "change-this-in-production")
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(token: str = Depends(oauth2_scheme), db = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    return user

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
  sig_tune:     #22c55e
  music:        #22c55e
  talk:         #3b82f6
  intro:        #3b82f6
  advert:       #f59e0b
  sponsor:      #f59e0b
  news:         #8b5cf6
  interview:    #8b5cf6
  conflict:     #ef4444
  station_id:   #06b6d4
  weather:      #10b981
  vox_pop:      #10b981
  drama:        #ec4899
  storytelling: #f97316
  close:        #6b7280

Compliance badge colours:
  compliant (90-100):    #22c55e  green
  moderate risk (70-89): #f59e0b  amber
  high risk (<70):       #ef4444  red

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
    SIG_TUNE = "sig_tune" | INTERVIEW = "interview" | VOX_POP = "vox_pop"
    PHONE_IN_SEGMENT = "phone_in_segment" | STORYTELLING = "storytelling"
    DRAMA = "drama" | SCRIPTED_REPORT = "scripted_report" | SPONSOR = "sponsor"

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

class ComplianceViolation(BaseModel):
    rule_id: str
    severity: str
    message: str
    penalty: int

class RunSheetResponse(BaseModel):
    runsheet_id: str
    programme_input: ProgrammeInput
    segments: list[Segment]
    conflicts: list[Conflict]
    recommendations: list[Recommendation]
    compliance_score: int
    compliance_risk: str
    compliance_violations: list[ComplianceViolation]
    stats: RunSheetStats
    generated_at: str

---

## Conflict rules (C001–C005 — already implemented)

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

## Ghana broadcasting compliance rules (G001–G005 — implemented in Session E)

SOURCE NOTE — important for viva defence:
The NCA Ghana FM Broadcasting Guidelines (2016) cover technical and operational
standards only (transmission power, equipment specs, studio setup). They contain
no scheduling-level content rules. Ghana does not currently publish specific
scheduling compliance metrics for community FM stations.

The G rules below are derived from general FM broadcasting best practice, informed
by the NCA licensing framework and NMC (National Media Commission) content
guidelines, and calibrated to thresholds commonly applied by international
regulators (Ofcom, EBU). They are a deliberate design decision, not citations
from a specific clause.

If asked in the viva: "The G rules encode best-practice scheduling discipline
derived from the broader Ghanaian regulatory environment and international FM
broadcasting standards. Ghana's NCA focuses on technical compliance; scheduling
content compliance is an area where community stations lack decision support tools,
which is precisely the gap this system addresses."

G001 — Opening Station ID:
  Trigger: no StationID segment within first 15 minutes
  Severity: moderate | Penalty: -10
  Basis: standard international practice for station identification

G002 — Periodic Station ID:
  Trigger: no StationID in any subsequent 30-minute window
  Severity: low | Penalty: -3
  Basis: standard international practice for station identification

G003 — Advert duration limit:
  Trigger: total advert segments > 20% of programme duration
  Severity: high | Penalty: -25
  Basis: Ofcom/EBU standard threshold; aligns with NMC ad conduct guidelines

G004 — Advert separation:
  Trigger: < 10 minutes between any two advert blocks
  Severity: moderate | Penalty: -10
  Basis: general listener experience best practice

G005 — Programme classification:
  Trigger: segment types inconsistent with declared programme type
  Severity: low | Penalty: -3
  Basis: FRI programme format methodology

Compliance score = 100 − Σ(penalties of triggered rules)
Risk levels: 90–100 = compliant (green), 70–89 = moderate (amber), below 70 = high (red)

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

## API endpoints (full reference)

POST   /api/v1/auth/register              ← Session A  (no auth required)
POST   /api/v1/auth/login                 ← Session A  (no auth required)
POST   /api/v1/runsheet/generate          ← protected after Session A
GET    /api/v1/runsheet/history           ← protected
GET    /api/v1/runsheet/{id}              ← protected
POST   /api/v1/runsheet/update-segments   ← Session C  (protected)
POST   /api/v1/conflicts/detect           ← protected
POST   /api/v1/conflicts/apply-fix        ← protected
POST   /api/v1/validate/runsheet          ← Session F  (protected)
POST   /api/v1/export/preview             ← Session G  (protected)
GET    /api/v1/user/dashboard             ← Session B  (protected)
GET    /api/v1/user/profile               ← Session I  (protected)
PATCH  /api/v1/user/profile               ← Session I  (protected)
GET    /api/v1/user/audit-log             ← Session H  (protected)

---

## Session backlog (A–J)

SESSION A:  JWT authentication — User model, register/login endpoints,
            get_current_user, protect all runsheet routes, auth frontend
            → Use Opus

SESSION B:  User dashboard — /dashboard page, stats, recent run-sheets,
            load past run-sheet into timeline
            → Use Sonnet

SESSION C:  Interactive segment editing — click to edit modal, add/delete
            segments, auto re-run conflict detection, update-segments endpoint
            → Use Sonnet

SESSION D:  Drag to reorder — wire dnd-kit to timeline, recalculate times,
            auto re-run conflict detection after reorder
            → Use Sonnet

SESSION E:  Ghana broadcasting compliance layer — compliance_validator.py (G001–G005),
            integrate into generation pipeline, compliance badge on frontend,
            'Broadcasting Compliance' section in conflict panel (NOT labelled
            'NCA rules' — label as 'Broadcasting Compliance'), 10 pytest unit tests
            → Use Opus

SESSION F:  Standalone validation mode — /validate page, file upload or paste,
            full conflict + compliance report
            → Use Sonnet

SESSION G:  PDF export — print-formatted view, FRI-style table, CSS @media print,
            no server-side PDF generation
            → Use Sonnet

SESSION H:  Audit logging + settings — AuditLog model, log all significant
            actions, /settings page, audit log viewer
            → Use Sonnet

SESSION I:  User profile — /profile page, display name edit, initials avatar,
            stats
            → Use Sonnet

SESSION J:  Polish and production readiness — loading states, error boundaries,
            toast notifications, rate limiting on auth, input sanitisation,
            responsive layout for tablet
            → Use Sonnet

---

## Claude Code model selection

Complex architectural work (Sessions A, E): claude-opus-4-7
All other sessions: claude-sonnet-4-6

To switch:
  claude config set model claude-opus-4-7
  claude config set model claude-sonnet-4-6

---

## Claude Code session preamble (use at the start of every session)

Read CLAUDE.md before doing anything else. Follow its conventions exactly.
Read the session task below carefully before writing any code.
Only change the files listed. Do not modify anything else.
After all changes, run the relevant tests and confirm they pass.
Stop when the task is complete. Do not start the next session's work.

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

JWT 401 errors:
  Fix: check SECRET_KEY env var matches between token generation and decode
  Fix: check Authorization header is Bearer <token> format
  Fix: check token expiry — default should be 24 hours for dev

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
Remote: git@github.com:jija1/radiosheet-ai.git
Commit format: feat(auth): implement JWT authentication — Session A

Always work on dev or a feature branch. Never push directly to main.
Commit after every session before starting the next:
  git add . && git commit -m 'feat(module): description' && git push origin dev

---

## Post-submission production notes

PostgreSQL: change DATABASE_URL in .env — zero code changes
Deployment: Railway/Render for backend, Vercel for frontend
Real PDF: add weasyprint to requirements.txt, update export/service.py
SSL: add reverse proxy (nginx or Caddy) in front of uvicorn for HTTPS
