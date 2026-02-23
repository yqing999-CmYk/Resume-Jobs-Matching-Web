/* ──────────────────────────────────────────────────────────
   Resume-Job Matcher — frontend logic
   ────────────────────────────────────────────────────────── */

const fileInput    = document.getElementById("file-input");
const dropZone     = document.getElementById("drop-zone");
const selectedFile = document.getElementById("selected-file");
const submitBtn    = document.getElementById("submit-btn");
const errorMsg     = document.getElementById("error-msg");
const spinner      = document.getElementById("spinner");
const resultsSection = document.getElementById("results-section");
const resultsContainer = document.getElementById("results-container");
const resumeName   = document.getElementById("resume-name");
const jobsCount    = document.getElementById("jobs-count");
const jobsList     = document.getElementById("jobs-list");
const reloadBtn    = document.getElementById("reload-btn");

let selectedPdf = null;

// ── File selection ────────────────────────────────────────

// Prevent the "browse" label click from bubbling to the dropZone listener,
// which would cause the file dialog to open twice (label + dropZone both
// trigger fileInput.click()).
const browseLabel = dropZone.querySelector("label");
if (browseLabel) {
  browseLabel.addEventListener("click", (e) => e.stopPropagation());
}

dropZone.addEventListener("click", () => fileInput.click());

fileInput.addEventListener("change", () => {
  if (fileInput.files.length > 0) setFile(fileInput.files[0]);
});

dropZone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropZone.classList.add("drag-over");
});
dropZone.addEventListener("dragleave", () => dropZone.classList.remove("drag-over"));
dropZone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropZone.classList.remove("drag-over");
  const file = e.dataTransfer.files[0];
  if (file) setFile(file);
});

function setFile(file) {
  if (!file.name.toLowerCase().endsWith(".pdf")) {
    showError("Please select a PDF file.");
    return;
  }
  selectedPdf = file;
  selectedFile.textContent = `Selected: ${file.name}`;
  submitBtn.disabled = false;
  hideError();
  resultsSection.hidden = true;
}

// ── Submit ────────────────────────────────────────────────

submitBtn.addEventListener("click", async () => {
  if (!selectedPdf) return;

  setLoading(true);
  hideError();
  resultsSection.hidden = true;

  const formData = new FormData();
  formData.append("resume", selectedPdf);

  try {
    const res = await fetch("/api/match", { method: "POST", body: formData });
    const data = await res.json();

    if (!res.ok) {
      showError(data.detail || `Server error (${res.status})`);
      return;
    }

    renderResults(data);
  } catch (err) {
    showError(`Network error: ${err.message}`);
  } finally {
    setLoading(false);
  }
});

// ── Reload jobs ───────────────────────────────────────────

reloadBtn.addEventListener("click", async () => {
  reloadBtn.disabled = true;
  reloadBtn.textContent = "Reloading…";
  try {
    const res = await fetch("/api/reload-jobs", { method: "POST" });
    const data = await res.json();
    reloadBtn.textContent = data.message || "Reloaded!";
    loadJobsList();
  } catch {
    reloadBtn.textContent = "Error — try again";
  } finally {
    setTimeout(() => {
      reloadBtn.textContent = "Reload Job Descriptions";
      reloadBtn.disabled = false;
    }, 2500);
  }
});

// ── Load jobs list on page load ───────────────────────────

async function loadJobsList() {
  try {
    const res = await fetch("/api/jobs");
    const data = await res.json();
    const jobs = data.jobs || [];

    jobsCount.textContent = jobs.length === 0
      ? "No job descriptions loaded. Add HTML files to the Job/ folder."
      : `${jobs.length} job description${jobs.length > 1 ? "s" : ""} loaded.`;

    jobsList.innerHTML = jobs
      .map(j => `<li>${escHtml(j.title)} <span class="tag">${escHtml(j.filename)}</span></li>`)
      .join("");
  } catch {
    jobsCount.textContent = "Could not load job list.";
  }
}

loadJobsList();

// ── Render results ────────────────────────────────────────

function renderResults(data) {
  resumeName.textContent = data.resume_filename;
  resultsContainer.innerHTML = "";

  const rankLabels = ["#1 Best Match", "#2 Strong Match", "#3 Good Match"];
  const rankClasses = ["rank-1", "rank-2", "rank-3"];

  (data.top_matches || []).forEach((match) => {
    const pct = Math.round(match.similarity * 100);
    const idx = match.rank - 1;

    const card = document.createElement("article");
    card.className = `result-card ${rankClasses[idx] || ""}`;
    card.innerHTML = `
      <div class="result-header">
        <span class="rank-badge">${rankLabels[idx] || `#${match.rank}`}</span>
        <span class="result-title">${escHtml(match.job_title)}</span>
        <span class="result-filename">${escHtml(match.job_file)}</span>
      </div>

      <div class="similarity-bar-wrap">
        <div class="similarity-label">
          <span>Similarity Score</span>
          <strong>${pct}%</strong>
        </div>
        <div class="similarity-bar">
          <div class="similarity-fill" style="width: 0%" data-target="${pct}"></div>
        </div>
      </div>

      <div class="tips-section">
        <h4>Resume Improvement Tips</h4>
        <div class="tips-content">${escHtml(match.tips)}</div>
      </div>
    `;

    resultsContainer.appendChild(card);

    // Animate bar after paint
    requestAnimationFrame(() => {
      const fill = card.querySelector(".similarity-fill");
      setTimeout(() => { fill.style.width = fill.dataset.target + "%"; }, 50);
    });
  });

  resultsSection.hidden = false;
  resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
}

// ── Helpers ───────────────────────────────────────────────

function setLoading(on) {
  spinner.hidden = !on;
  submitBtn.disabled = on;
}

function showError(msg) {
  errorMsg.textContent = msg;
  errorMsg.hidden = false;
}

function hideError() {
  errorMsg.hidden = true;
  errorMsg.textContent = "";
}

function escHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
