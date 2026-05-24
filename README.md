# appli.

> Manage everything you need during your job search: professional profile, CVs, AI-generated cover letters, and application tracking — all in one place.

**Stack:** React 19 + FastAPI · SQLite · Multi-provider AI (Gemini, Groq, Anthropic, OpenAI)

---

## What is appli.?

**appli.** is a local web app that centralizes your entire job search process. Build a modular professional profile, generate tailored CVs and cover letters with AI, track companies you're interested in, and keep a full log of every application you send.

### Features

- **Professional profile** — Manage modular sections (experience, education, projects, skills…) with tags and date ranges.
- **AI-powered cover letters** — Generate personalized cover letters from your profile and a job description. Edit the result and export to PDF/DOCX.
- **CV management** — Upload your own PDFs or generate CVs tailored to a specific offer.
- **Company tracking** — Save logos, URLs and notes for companies you're targeting.
- **Application tracking** — Log every application with its status (Sent, Interview, Technical test, Finished…), dates and notes.
- **Job offer scraper** — Extract offers from any job board URL using AI parsing or local heuristics.

---

## Project structure

```
appli/
├── api.py                  ← REST backend (FastAPI)
├── start.py                ← Dev startup script
├── config.py               ← Global config (reads .env)
├── requirements.txt        ← Python dependencies
├── .env.example            ← Environment variables template
│
├── backend/
│   ├── base.py             ← Data models + abstract BaseBackend interface
│   └── ai_backend.py       ← AI implementation (Claude, GPT, Gemini, Groq)
│
├── core/
│   ├── data_manager.py     ← Persistence layer (SQLite + SQLAlchemy)
│   ├── cv_builder.py       ← CV/Cover Letter export to PDF/DOCX
│   └── doc_editor.py       ← DOCX document generation utilities
│
└── frontend/               ← React app (Vite)
    ├── index.html
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── App.jsx                     ← Main router + app shell
        └── components/
            ├── Sidebar.jsx             ← Side navigation
            └── views/
                ├── Inicio.jsx          ← Home dashboard
                ├── Perfil.jsx          ← Professional profile
                ├── CVs.jsx             ← CV repository
                ├── Covers.jsx          ← Cover letters
                ├── Empresas.jsx        ← Company tracking
                ├── Aplicaciones.jsx    ← Application tracker
                └── Configuracion.jsx   ← Settings
```

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│               Frontend (React + Vite)            │
│  Home · Profile · CVs · Covers · Companies ·    │
│  Applications · Settings                        │
└──────────────────────┬──────────────────────────┘
                       │ HTTP REST  /api/*
┌──────────────────────▼──────────────────────────┐
│              Backend (FastAPI)  api.py           │
└────────┬───────────────────────┬────────────────┘
         │                       │
┌────────▼────────┐   ┌──────────▼──────────────┐
│  DataManager    │   │       AIBackend          │
│  SQLite +       │   │  Gemini · Groq ·         │
│  SQLAlchemy     │   │  Claude · OpenAI         │
└─────────────────┘   └─────────────────────────-┘
```

### Data models

| Model | Description |
|---|---|
| `ProfileSection` | Profile entry (category, title, content, company, date range, tags) |
| `CVDocument` | CV document — editable Markdown or uploaded PDF |
| `CoverLetter` | Cover letter with paths to generated DOCX and PDF |
| `JobOffer` | Scraped or manual job offer with match score |
| `JobApplication` | Application with status, company, position and dates |

---

## Setup

### Requirements

- Python 3.10+
- Node.js 18+

### 1. Clone and install Python dependencies

```bash
git clone https://github.com/your-username/appli.git
cd appli

python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and add your preferred AI provider key:

```env
AI_PROVIDER=gemini
AI_MODEL=gemini-2.0-flash

GEMINI_API_KEY=your_key_here
GROQ_API_KEY=
ANTHROPIC_API_KEY=
OPENAI_API_KEY=

DB_PATH=data/jobsearch.db
```

> The API key and provider can also be changed at any time from the **Settings** view in the UI — no need to touch files.

### 3. Run in development mode

```bash
python start.py
```

This starts both processes automatically:

- **Backend** → `http://localhost:8000` (FastAPI with hot-reload)
- **Frontend** → `http://localhost:3000` (Vite HMR)

Press `Ctrl+C` to stop everything.

---

## Tech stack

**Backend**
- [FastAPI](https://fastapi.tiangolo.com/) — Modern async REST framework
- [SQLAlchemy](https://www.sqlalchemy.org/) — ORM for SQLite
- [python-docx](https://python-docx.readthedocs.io/) — Word document generation
- [ReportLab](https://www.reportlab.com/) — PDF export
- [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) — Job offer scraping
- [Uvicorn](https://www.uvicorn.org/) — ASGI server

**Frontend**
- [React 19](https://react.dev/) — UI
- [Vite 8](https://vitejs.dev/) — Bundler and dev server

---

## License

MIT — see [LICENSE](./LICENSE) for details.
