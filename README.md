# Research Article Analysis Agent

A two-script pipeline for analyzing academic PDFs against your research proposal using Claude.

---

## Setup

### 1. Install dependencies
```bash
pip install pdfplumber anthropic
```

### 2. Set your Anthropic API key
```bash
# Mac/Linux
export ANTHROPIC_API_KEY="sk-ant-..."

# Windows
set ANTHROPIC_API_KEY=sk-ant-...
```
Get your key at: https://console.anthropic.com

### 3. Add your research proposal
Create a file called `proposal.txt` in the same directory and paste your full proposal text into it.

---

## Usage

### Analyze a single article
```bash
python analyze.py --pdf path/to/article.pdf
```

With a custom proposal path:
```bash
python analyze.py --pdf article.pdf --proposal my_proposal.txt
```

Output is saved automatically to `results/articlename_timestamp.json`

---

### Query across all analyzed articles
```bash
# Ask a specific question
python query.py "which papers address the turbidity proxy?"
python query.py "what methods are used for ASM detection?"
python query.py "which papers have reusable data or code?"
python query.py "what do papers say about governance and weak institutions?"

# Generate a full synthesis report
python query.py --report
```

---

## File Structure
```
research_agent/
├── analyze.py          # Main analysis pipeline
├── query.py            # Cross-paper query tool
├── README.md           # This file
├── proposal.txt        # Your research proposal (you create this)
└── results/            # Auto-created, stores JSON analyses
    ├── paper1_20260318_143200.json
    ├── paper2_20260318_150100.json
    └── ...
```

---

## Output Format

Each analysis is saved as a JSON file with 6 sections:

```json
{
  "title": "...",
  "authors": "...",
  "year": "...",
  "journal": "...",
  "core_argument": "...",
  "methodology": {
    "research_design": "...",
    "data_sources": ["...", "..."],
    "analytical_methods": ["...", "..."],
    "geographic_scope": "...",
    "time_period": "..."
  },
  "key_findings": ["...", "..."],
  "critical_evaluation": {
    "main_strength": "...",
    "main_weakness": "...",
    "most_questionable_assumption": "...",
    "not_addressed": "..."
  },
  "relevance_to_proposal": {
    "pillar": "Detection / Physical Model / Turbidity / Governance / Other",
    "contribution": "...",
    "contradicts_or_complicates": "...",
    "data_or_code_reusable": "Yes / No / Partially",
    "data_or_code_reusable_explanation": "..."
  },
  "bottom_line": "...",
  "_meta": {
    "source_pdf": "...",
    "analyzed_at": "...",
    "model": "claude-sonnet-4-6"
  }
}
```

---

## Notes

- PDFs longer than ~60,000 words are automatically truncated from the end. For very long papers, consider passing only the relevant sections.
- The `results/` folder is your persistent knowledge base. Back it up.
- Run `query.py --report` after every 5-10 new papers to get a fresh synthesis.
