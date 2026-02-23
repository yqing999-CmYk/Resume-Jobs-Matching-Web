# Resume & Job Matcher

A full-stack web application that compares PDF resumes against HTML job descriptions using **OpenAI embedding vectors** and **cosine similarity**. It returns the top 3 best-matching jobs for any uploaded resume and generates **AI-powered improvement tips** for each match.

---

## Table of Contents

1. [Introduction](#introduction)
2. [Tech Stack](#tech-stack)
3. [Project Structure](#project-structure)
4. [How It Works](#how-it-works)
5. [Environment Setup](#environment-setup)
6. [How to Run (Local)](#how-to-run-local)
7. [API Reference](#api-reference)
8. [Wrap for Production Deployment](#wrap-for-production-deployment)
9. [Docker](#docker)
10. [Deploy to Hostinger VPS](#deploy-to-hostinger-vps)

---

## Introduction

Recruiters and job seekers often struggle to find the best match between a candidate's profile and available positions. This tool automates the process:

- Drop **PDF resumes** in the `Resume/` folder (or upload via the web UI)
- Drop **HTML job descriptions** in the `Job/` folder
- The app **embeds both** into high-dimensional vectors using OpenAI's embedding model
- **Cosine similarity** ranks every job against the resume
- The **top 3 matches** are shown with similarity scores and specific, numbered tips on how to improve the resume for each role

All embedding vectors are **cached to disk** so re-running the server or re-uploading the same resume avoids redundant OpenAI API calls.

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Backend framework** | [FastAPI](https://fastapi.tiangolo.com/) | Async REST API + static file serving |
| **ASGI server** | [Uvicorn](https://www.uvicorn.org/) | Runs FastAPI in development and production |
| **PDF parsing** | [PyMuPDF](https://pymupdf.readthedocs.io/) (`fitz`) | Extract plain text from PDF resumes |
| **HTML parsing** | [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) + `lxml` | Strip HTML tags from job descriptions |
| **AI embeddings** | [OpenAI](https://platform.openai.com/) `text-embedding-3-small` | Convert text to 1536-dimensional vectors |
| **AI tips** | OpenAI `gpt-4o-mini` | Generate resume improvement advice |
| **Similarity math** | [NumPy](https://numpy.org/) | Cosine similarity calculation |
| **Config** | [python-dotenv](https://github.com/theskumar/python-dotenv) | Load `.env` variables |
| **Frontend** | Vanilla HTML/CSS/JavaScript | Zero-dependency UI, served by FastAPI |
| **Containerization** | Docker + Docker Compose | Portable deployment |

---

## Project Structure

```
Resume-Job-Matching/
├── Plan/
│   └── PROJECT_PLAN.md          ← Design decisions and architecture notes
│
├── Resume/                       ← Uploaded PDF resumes are saved here
│   └── (your_resume.pdf)
│
├── Job/                          ← HTML job descriptions — add yours here
│   └── (job_title.html)
│
├── backend/
│   ├── __init__.py
│   ├── main.py                   ← FastAPI app, lifespan, API routes
│   ├── parser.py                 ← PDF text (PyMuPDF) + HTML text (BeautifulSoup)
│   ├── embeddings.py             ← OpenAI embeddings with SHA-256 disk cache
│   ├── matcher.py                ← In-memory job store, cosine similarity ranking
│   ├── advisor.py                ← GPT-4o-mini resume improvement tips
│   ├── config.py                 ← Settings loaded from .env
│   └── cache/                    ← Auto-created; stores .npy embedding cache files
│
├── frontend/
│   ├── index.html                ← Single-page UI
│   ├── style.css                 ← Responsive styles
│   └── app.js                    ← Fetch API, drag-and-drop, results rendering
│
├── run.py                        ← Convenience startup script
├── Dockerfile                    ← Multi-stage Docker build
├── docker-compose.yml            ← Compose for local/VPS deployment
├── requirements.txt              ← Python dependencies (pinned versions)
├── .env.example                  ← Environment variable template
├── .gitignore
└── README.md
```

---

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│  1. PARSE                                                   │
│     PDF resume  ──► PyMuPDF       ──► plain text            │
│     HTML job    ──► BeautifulSoup ──► plain text            │
│                                                             │
│  2. EMBED                                                   │
│     text ──► OpenAI text-embedding-3-small ──► float[1536]  │
│     (cached to backend/cache/<sha256>.npy)                  │
│                                                             │
│  3. RANK                                                    │
│     resume_vec · job_vec                                    │
│     ─────────────────────── = cosine similarity             │
│     ‖resume_vec‖ · ‖job_vec‖                                │
│     → sort descending → top 3                               │
│                                                             │
│  4. ADVISE                                                  │
│     GPT-4o-mini(resume_text, job_text) → numbered tips      │
│                                                             │
│  5. DISPLAY                                                 │
│     Browser UI shows rank, % score bar, and tips per job    │
└─────────────────────────────────────────────────────────────┘
```

**Embedding cache:** Every piece of text is hashed with SHA-256. Before calling the OpenAI API, the app checks if `backend/cache/<hash>.npy` already exists. If yes, it loads from disk — no API call. This means:
- Job embeddings computed once, reused on every restart
- Re-uploading the same resume PDF is instant

---

## Environment Setup

### Prerequisites
- **Python 3.11+**
- **pip**
- An **OpenAI API key** — get one at [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- (For Docker) **Docker Desktop** or Docker Engine + Compose v2

### Steps

```bash
# 1. Enter the project directory
cd Resume-Job-Matching

# 2. Create and activate a virtual environment
python -m venv venv

# Windows (Git Bash / WSL)
source venv/Scripts/activate

# macOS / Linux
source venv/bin/activate

# 3. Install all Python dependencies
pip install -r requirements.txt

# 4. Create your .env file
cp .env.example .env
```

Edit `.env` and fill in your key:

```env
OPENAI_API_KEY=sk-...your-key-here...

# Optional overrides (defaults shown):
EMBEDDING_MODEL=text-embedding-3-small
TIPS_MODEL=gpt-4o-mini
TOP_N=3
```

---

## How to Run (Local)

### Option A — convenience script

```bash
python run.py
```

### Option B — uvicorn directly

```bash
uvicorn backend.main:app --reload --port 8000
```

> **Important:** Always run from the project root directory (`Resume-Job-Matching/`), not from inside `backend/`.

Open **http://localhost:8000** in your browser.

### Using the app

1. Add HTML job descriptions to the `Job/` folder before starting the server.
   (Or click **Reload Job Descriptions** in the UI after adding files.)
2. Click **Browse** or drag a PDF onto the upload area.
3. Click **Find Matching Jobs**.
4. Results appear below — each card shows the similarity score bar and numbered improvement tips.

---

## API Reference

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Serves the web UI |
| `GET` | `/api/jobs` | List all loaded job descriptions |
| `POST` | `/api/match` | Upload PDF → top-N matches + tips |
| `POST` | `/api/reload-jobs` | Re-scan `Job/` folder |

### POST /api/match

**Request** — `multipart/form-data`:

| Field | Type | Description |
|-------|------|-------------|
| `resume` | `file` | PDF resume file |

**Response** — `application/json`:

```json
{
  "resume_filename": "john_doe.pdf",
  "top_matches": [
    {
      "rank": 1,
      "job_file": "senior_engineer.html",
      "job_title": "Senior Software Engineer at Acme",
      "similarity": 0.9134,
      "tips": "1. Add keywords like 'system design' and 'distributed systems'...\n2. Quantify your impact..."
    }
  ]
}
```

Interactive API docs available at **http://localhost:8000/docs** (Swagger UI).

---
---
##LICENSE:
  MIT
--- 