---
name: academic-paper-summarizer
description: Full pipeline for academic papers — download, summarize, and file. Accepts a single paper (PDF path, title, DOI, URL) or a batch list (.docx / .txt). Downloads missing papers automatically (tries open-access APIs then Sci-Hub; reports failures). Summarizes each paper into a structured PDF summary. Files the paper and its summary into the correct subfolder based on content. Trigger when the user says things like "summarize this paper", "הורד וסכם", "סכם את המאמר", "add these papers", or provides a list of papers/DOIs.
---

# Academic Paper Summarizer — Full Pipeline

Handles the complete lifecycle of an academic paper: download → summarize → file.

---

## Phase 0: Detect Input Type

Accept any of the following:

| Input | Action |
|---|---|
| PDF file path | Skip to Phase 2 |
| Title / DOI / URL (single) | Phase 1 → single paper |
| `.docx` or `.txt` list file | Phase 1 → batch mode |
| Pasted text / abstract | Skip to Phase 2, label as abstract-only |

Store all resolved PDF paths for use in later phases.

---

## Phase 1: Download (skip if PDF already provided)

Run the download script:

```bash
python -X utf8 scripts/download_papers.py --input "<path_or_title>" --output pdfs/
```

- For a single title/DOI/URL: pass it via `--titles "..."`.
- For a list file: pass via `--input "<path>"`.
- The script tries: Semantic Scholar → Unpaywall → OpenAlex → Google Scholar → Sci-Hub.
- After completion, read `pdfs/download_log.json` to get results.

After running:
- **Succeeded** → collect PDF paths, continue to Phase 2.
- **Failed** → report in chat as a clean list (title + reason), then continue with the papers that did succeed.

Example failure report:
```
לא הצלחתי להוריד:
• Wang 2024 (Wiley) — לא במאגר Sci-Hub, דורש VPN
• Khorshidi 2024 (Elsevier) — חדש מדי
```

---

## Phase 2a: Bibliometric Enrichment

For each paper (before writing the summary), fetch bibliometric data from Semantic Scholar.

**API call:**
```python
import httpx, time, math

SS_KEY = "<SEMANTIC_SCHOLAR_API_KEY>"  # optional — leave empty string if not available
CURRENT_YEAR = 2026

def fetch_biblio(title: str) -> dict:
    headers = {"x-api-key": SS_KEY} if SS_KEY else {}
    params = {
        "query": title,
        "limit": 1,
        "fields": "title,year,citationCount,influentialCitationCount,publicationVenue"
    }
    r = httpx.get("https://api.semanticscholar.org/graph/v1/paper/search",
                  params=params, headers=headers, timeout=10)
    time.sleep(1)  # rate limit — always, even with API key
    if r.status_code != 200 or not r.json().get("data"):
        return {}
    paper = r.json()["data"][0]
    year = paper.get("year") or 0
    total = paper.get("citationCount", 0)
    influential = paper.get("influentialCitationCount", 0)
    per_year = round(total / (CURRENT_YEAR - year), 1) if year and year < CURRENT_YEAR else "לא זמין"
    venue = (paper.get("publicationVenue") or {}).get("name", "")
    return {
        "total": total if total is not None else "לא זמין",
        "per_year": per_year,
        "influential": influential if influential is not None else "לא זמין",
        "venue": venue,
    }
```

For "פעיל לאחרונה": fetch the first page of citing papers and check for any with year ≥ 2023:
```python
def has_recent_citations(paper_id: str) -> str:
    headers = {"x-api-key": SS_KEY} if SS_KEY else {}
    r = httpx.get(f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}/citations",
                  params={"fields": "year", "limit": 100}, headers=headers, timeout=10)
    time.sleep(1)
    if r.status_code != 200:
        return "לא זמין"
    years = [c["citingPaper"].get("year") or 0 for c in r.json().get("data", [])]
    return "כן" if any(y >= 2023 for y in years) else "לא"
```

**If a metric is unavailable (API error, paper not found, field missing) → write `לא זמין`. Never fabricate values.**

**Journal metrics (H-index + Impact Factor) via OpenAlex** — free, no API key:
```python
def get_journal_metrics(venue_name: str) -> dict:
    if not venue_name or venue_name == "לא זמין":
        return {"h_index": "לא זמין", "impact_factor": "לא זמין"}
    r = httpx.get("https://api.openalex.org/sources",
                  params={"search": venue_name, "per-page": 1, "mailto": "<user_email>"},
                  timeout=15)
    time.sleep(1)
    if r.status_code != 200 or not r.json().get("results"):
        return {"h_index": "לא זמין", "impact_factor": "לא זמין"}
    stats = r.json()["results"][0].get("summary_stats", {})
    h = stats.get("h_index", "לא זמין")
    if2yr = stats.get("2yr_mean_citedness")
    impact = round(if2yr, 1) if if2yr is not None else "לא זמין"
    return {"h_index": h, "impact_factor": impact}
```
Note: `impact_factor` here is OpenAlex `2yr_mean_citedness` — a close open-access approximation of JCR Impact Factor, not the official Clarivate value. Quartile remains `לא זמין`.

Insert the following table **immediately after the `*[Journal Name, Year]*` line** in the summary:

```
| מדד | ערך |
|-----|-----|
| ציטוטים כולל | {total} |
| ציטוטים לשנה | {per_year} |
| ציטוטים משפיעים | {influential} |
| פעיל לאחרונה (2023–2025) | {recent} |
| H-index של כתב העת | {h_index} |
| אימפקט פקטור (2yr) | {impact_factor} |
| Quartile | {quartile} |
```

`{h_index}` and `{impact_factor}` — fetched from OpenAlex `summary_stats` (`h_index` and `2yr_mean_citedness`). Free, no API key required. `{quartile}` is not available via open APIs — default to `לא זמין`.

**API key note:** If the user has a Semantic Scholar API key, pass it via `SS_KEY`. Free key available at semanticscholar.org/product/api. Without a key, `sleep(1)` prevents most rate-limit errors for small batches.

---

## Phase 2: Summarize Each Paper

For each PDF, extract text:

```bash
python -c "from pypdf import PdfReader; r=PdfReader(r'<path>'); print('\n'.join(p.extract_text() or '' for p in r.pages))"
```

Then write the summary **in Hebrew (עברית)** in the following format (~300–500 words):

---

### [Title] — [Authors, Year]

*[Journal Name, Year]*

| מדד | ערך |
|-----|-----|
| ציטוטים כולל | — |
| ציטוטים לשנה | — |
| ציטוטים משפיעים | — |
| פעיל לאחרונה (2023–2025) | — |
| H-index של כתב העת | לא זמין |
| Quartile | לא זמין |

**שאלת המחקר**
משפט אחד המנסח את השאלה המרכזית או ההשערה.

**הקשר**
2–3 משפטים על הבעיה ומיקום המאמר בספרות.

**נתונים ומתודולוגיה**
- מקורות נתונים והיקף
- גישה אנליטית
- כלים או מסגרות מרכזיות

**ממצאים מרכזיים**
רשימה ממוספרת של התוצאות העיקריות. כלול נתונים סטטיסטיים כפי שמוצגים במאמר.

**תוצאות שליליות / ממצאי אפס**
ציין במפורש אם המאמר מצא תוצאות אפס. השמט אם אין.

**מגבלות**
רשימת נקודות כפי שמציינים המחברים. הוסף [משוער] לפערים ברורים.

**תרומות**
מה המאמר מוסיף — תיאורטית, אמפירית, או מתודולוגית.

---

### עקרונות מרכזיים

- חלץ רק את מה שנאמר במפורש. אל תסיק או תבדה.
- שמור על ניסוח המחברים.
- תוצאות שליליות חשובות כמו חיוביות.
- אין חיפושים חיצוניים — עבד רק מתוך תוכן המאמר.

---

## Phase 3: Save Summary as PDF

For each paper, save the summary as a PDF next to the source file:
- Input:  `pdfs/<paper_name>.pdf`
- Output: `pdfs/<paper_name>_summary.pdf`

Use the script below. Write it to `gen_summary.py`, run it, then delete it.

**CRITICAL — RTL rendering rules:**
- Do NOT use `multi_cell()` directly with bidi-processed text.
- Use `pdf.multi_cell(W, h, text, dry_run=True, output='LINES')` to get line splits, then apply `get_display()` to EACH line, then render with `cell()`.
- Use `align='R'` for Hebrew text. Title line uses `align='L'`.

```python
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from fpdf import FPDF
from bidi.algorithm import get_display

summary = """<SUMMARY TEXT HERE>"""
output_path = r"<OUTPUT PATH HERE>"

class PDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 10)
        self.set_text_color(120, 120, 120)
        self.cell(0, 8, "Academic Paper Summary", align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

pdf = PDF()
pdf.add_font("Arial", "", r"C:\Windows\Fonts\arial.ttf")
pdf.add_font("Arial", "B", r"C:\Windows\Fonts\arialbd.ttf")
pdf.add_font("Arial", "I", r"C:\Windows\Fonts\ariali.ttf")
pdf.add_page()
pdf.set_auto_page_break(auto=True, margin=20)
W = pdf.w - pdf.l_margin - pdf.r_margin

def render_rtl(text, style="", size=10, lh=6, color=(40, 40, 40)):
    pdf.set_font("Arial", style, size)
    pdf.set_text_color(*color)
    lines = pdf.multi_cell(W, lh, text, dry_run=True, output="LINES")
    for line in lines:
        pdf.cell(W, lh, get_display(line), new_x="LMARGIN", new_y="NEXT", align="R")

for raw in summary.splitlines():
    raw = raw.rstrip()
    if raw.startswith("### "):
        pdf.set_font("Arial", "B", 13)
        pdf.set_text_color(30, 30, 30)
        pdf.multi_cell(W, 8, raw[4:], align="L")
        pdf.ln(2)
    elif raw.startswith("*") and raw.endswith("*") and not raw.startswith("**"):
        pdf.set_font("Arial", "I", 10)
        pdf.set_text_color(100, 100, 100)
        pdf.multi_cell(W, 6, raw.strip("*"), align="L")
        pdf.ln(2)
    elif raw.startswith("**") and raw.endswith("**"):
        render_rtl(raw.strip("*"), style="B", size=11, lh=7, color=(50, 80, 140))
        pdf.ln(1)
    elif raw.startswith("- ") or raw.startswith("* "):
        render_rtl("- " + raw[2:], lh=6)
    elif raw and raw[0].isdigit() and ". " in raw[:4]:
        render_rtl(raw, lh=6)
    elif raw == "---":
        pdf.set_draw_color(220, 220, 220)
        pdf.line(10, pdf.get_y() + 2, 200, pdf.get_y() + 2)
        pdf.ln(5)
    elif raw:
        render_rtl(raw.replace("**", ""), lh=6)
    else:
        pdf.ln(3)

pdf.output(output_path)
print(f"Saved: {output_path}")
```

---

## Phase 4: File Paper and Summary

After summarizing, use the summary content (not just the title) to determine the correct subfolder.

**Step 1** — Read current folder structure:
```bash
python -c "import os; [print(d) for d in os.listdir('pdfs') if os.path.isdir(os.path.join('pdfs', d))]"
```

**Step 2** — Based on the summary's Methods, Contributions, and Context sections, decide which folder fits. Use the full summary, not just the title.

**Step 3** — If confident (clear match): move both files silently:
```bash
Move-Item "pdfs\<paper>.pdf" "pdfs\<folder>\"
Move-Item "pdfs\<paper>_summary.pdf" "pdfs\<folder>\"
```

**Step 4** — If not confident (paper spans multiple themes, folder doesn't exist, or genuinely ambiguous): ask the user:
```
איפה לשמור את "<title>"?
קיימות: [folder1], [folder2], [folder3]
או צור תיקייה חדשה
```

**Step 5** — After all papers are processed, report a summary table:

```
סיכום:
✓ Godar 2014        → Geopolitical
✓ Lu 2021           → hydrological models
✓ Gallwey 2020      → remote sensing
? Meyfroidt 2017    → שאלתי אותך
✗ Wang 2024         → לא הורד (VPN נדרש)
```

---

## Integrity Rules

- Do not fill in missing data with plausible-sounding content.
- If the paper is abstract-only, do not invent methodology or findings — label clearly.
- If a paper fails to download, report it and skip — do not block the rest of the batch.
- Always file based on summary content, not title alone.
