"""
FastAPI application entry point.
Serves the frontend as static files and exposes the matching API.
"""
import shutil
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.advisor import get_tips
from backend.config import RESUME_DIR, TOP_N
from backend.matcher import list_jobs, load_jobs, rank_resume, reload_jobs
from backend.parser import extract_pdf_text

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

# ---------------------------------------------------------------------------
# App setup — use lifespan (replaces deprecated @app.on_event)
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    count = load_jobs()
    print(f"[startup] Loaded {count} job(s) from Job/ folder.")
    yield  # application runs here
    # (add cleanup logic here if needed)


app = FastAPI(title="Resume-Job Matcher", version="1.0.0", lifespan=lifespan)


# ---------------------------------------------------------------------------
# Static frontend
# ---------------------------------------------------------------------------
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/", include_in_schema=False)
async def serve_frontend():
    index = FRONTEND_DIR / "index.html"
    if not index.exists():
        raise HTTPException(status_code=404, detail="Frontend not found.")
    return FileResponse(str(index))


# ---------------------------------------------------------------------------
# API routes
# ---------------------------------------------------------------------------
@app.get("/api/jobs")
async def api_list_jobs():
    """Return a list of all loaded job descriptions."""
    jobs = list_jobs()
    return {"jobs": jobs, "total": len(jobs)}


@app.post("/api/reload-jobs")
async def api_reload_jobs():
    """Re-scan the Job/ folder and refresh all embeddings."""
    count = reload_jobs()
    return {"message": f"Reloaded {count} job(s)."}


@app.post("/api/match")
async def api_match(resume: UploadFile = File(...)):
    """
    Upload a PDF resume → returns top-N matching jobs with similarity scores
    and AI-generated improvement tips for each match.
    """
    # Validate file type
    if not resume.filename or not resume.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    # Save to Resume/ folder
    save_path = RESUME_DIR / resume.filename
    with open(save_path, "wb") as f:
        shutil.copyfileobj(resume.file, f)

    # Extract text
    try:
        resume_text = extract_pdf_text(save_path)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF parsing error: {e}")

    # Rank jobs
    try:
        matches = rank_resume(resume_text, top_n=TOP_N)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Matching error: {e}")

    # Build response with tips
    results = []
    for match in matches:
        try:
            tips = get_tips(resume_text, match.job_text, match.job_title)
        except Exception as e:
            tips = f"(Could not generate tips: {e})"

        results.append({
            "rank": match.rank,
            "job_file": match.job_filename,
            "job_title": match.job_title,
            "similarity": match.similarity,
            "tips": tips,
        })

    return JSONResponse({
        "resume_filename": resume.filename,
        "top_matches": results,
    })
