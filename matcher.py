"""
Job store: loads all HTML jobs, embeds them (with cache), and ranks against a resume.
"""
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from backend.config import JOB_DIR, TOP_N
from backend.embeddings import get_embedding, cosine_similarity
from backend.parser import extract_html_text, get_job_title


@dataclass
class JobEntry:
    filename: str
    title: str
    text: str
    vector: np.ndarray = field(repr=False)


# In-memory store keyed by filename
_job_store: dict[str, JobEntry] = {}


def load_jobs(job_dir: Path = JOB_DIR) -> int:
    """
    Scan Job/ folder, embed any new HTML files, update the in-memory store.
    Returns the number of jobs loaded.
    """
    html_files = list(job_dir.glob("*.html")) + list(job_dir.glob("*.htm"))
    if not html_files:
        return 0

    for html_path in html_files:
        fname = html_path.name
        if fname in _job_store:
            continue  # already loaded

        text = extract_html_text(html_path)
        title = get_job_title(html_path)
        vector = get_embedding(text)
        _job_store[fname] = JobEntry(filename=fname, title=title, text=text, vector=vector)

    return len(_job_store)


def reload_jobs(job_dir: Path = JOB_DIR) -> int:
    """Force-reload all jobs (clears store first)."""
    _job_store.clear()
    return load_jobs(job_dir)


def list_jobs() -> list[dict]:
    return [{"filename": j.filename, "title": j.title} for j in _job_store.values()]


@dataclass
class MatchResult:
    rank: int
    job_filename: str
    job_title: str
    similarity: float
    job_text: str   # needed by advisor


def rank_resume(resume_text: str, top_n: int = TOP_N) -> list[MatchResult]:
    """
    Given resume text, return the top-N matching jobs sorted by cosine similarity.
    """
    if not _job_store:
        raise RuntimeError("No jobs loaded. Add HTML files to the Job/ folder.")

    resume_vec = get_embedding(resume_text)

    scores: list[tuple[float, JobEntry]] = []
    for job in _job_store.values():
        sim = cosine_similarity(resume_vec, job.vector)
        scores.append((sim, job))

    scores.sort(key=lambda x: x[0], reverse=True)
    top = scores[:top_n]

    return [
        MatchResult(
            rank=i + 1,
            job_filename=job.filename,
            job_title=job.title,
            similarity=round(sim, 4),
            job_text=job.text,
        )
        for i, (sim, job) in enumerate(top)
    ]
