from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

RESUME_DIR = BASE_DIR / "Resume"
JOB_DIR = BASE_DIR / "Job"
CACHE_DIR = BASE_DIR / "backend" / "cache"

RESUME_DIR.mkdir(exist_ok=True)
JOB_DIR.mkdir(exist_ok=True)
CACHE_DIR.mkdir(exist_ok=True)

OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
if not OPENAI_API_KEY:
    raise RuntimeError(
        "OPENAI_API_KEY is not set.\n"
        "Copy .env.example to .env and add your key:\n"
        "  OPENAI_API_KEY=sk-..."
    )
EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
TIPS_MODEL: str = os.getenv("TIPS_MODEL", "gpt-4o-mini")
TOP_N: int = int(os.getenv("TOP_N", "3"))
