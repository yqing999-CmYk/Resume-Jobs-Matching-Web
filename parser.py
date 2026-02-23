"""
Text extraction from PDF (PyMuPDF) and HTML (BeautifulSoup).
"""
from pathlib import Path
import fitz  # PyMuPDF
from bs4 import BeautifulSoup


def extract_pdf_text(pdf_path: str | Path) -> str:
    """Extract all text from a PDF file, page by page."""
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    doc = fitz.open(str(pdf_path))
    pages: list[str] = []
    for page in doc:
        pages.append(page.get_text())
    doc.close()

    text = "\n".join(pages).strip()
    if not text:
        raise ValueError(f"No extractable text found in {pdf_path.name}. "
                         "The PDF may be image-based (scanned).")
    return text


def extract_html_text(html_path: str | Path) -> str:
    """Extract readable text from an HTML job description file."""
    html_path = Path(html_path)
    if not html_path.exists():
        raise FileNotFoundError(f"HTML file not found: {html_path}")

    raw = html_path.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(raw, "lxml")

    # Remove non-content tags
    for tag in soup(["script", "style", "noscript", "head", "meta", "link"]):
        tag.decompose()

    text = soup.get_text(separator="\n")
    # Collapse blank lines
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    return "\n".join(lines)


def get_job_title(html_path: str | Path) -> str:
    """Best-effort: extract a job title from <title> or first <h1>/<h2>."""
    html_path = Path(html_path)
    raw = html_path.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(raw, "lxml")

    if soup.title and soup.title.string:
        return soup.title.string.strip()
    for tag in ["h1", "h2", "h3"]:
        el = soup.find(tag)
        if el:
            return el.get_text(strip=True)
    return html_path.stem  # fallback: filename without extension
