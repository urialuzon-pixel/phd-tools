"""
Research Article Analysis Agent — Phase 1
==========================================
Usage:
    python analyze.py --pdf path/to/article.pdf
    python analyze.py --pdf path/to/article.pdf --proposal path/to/proposal.txt

Requirements:
    pip install pdfplumber anthropic
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

import pdfplumber
import anthropic

# ── Configuration ─────────────────────────────────────────────────────────────

RESULTS_DIR = Path("results")
PROPOSAL_FILE = Path("proposal.txt")
MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 4000

# ── Prompt ────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a rigorous academic research assistant helping a PhD student 
analyze academic papers in relation to their research proposal.

You read carefully, think critically, and always ground your analysis in what the paper 
actually says — not what you assume. You are direct, concise, and honest about weaknesses.

You must ALWAYS respond in valid JSON matching the exact schema provided. No prose outside the JSON."""


def build_analysis_prompt(proposal: str, article_text: str) -> str:
    return f"""
=== RESEARCH PROPOSAL ===
{proposal}
=== END RESEARCH PROPOSAL ===

=== ACADEMIC ARTICLE ===
{article_text}
=== END ACADEMIC ARTICLE ===

Analyze this article in relation to the research proposal above.
Respond ONLY with a valid JSON object matching this exact schema:

{{
  "title": "Full title of the paper",
  "authors": "Author names as they appear",
  "year": "Publication year as string",
  "journal": "Journal or venue name",

  "core_argument": "One paragraph. The central claim of this paper and the question it answers.",

  "methodology": {{
    "research_design": "Brief description of overall study design",
    "data_sources": ["List", "each", "dataset", "explicitly", "by", "name"],
    "analytical_methods": ["List", "each", "method", "used"],
    "geographic_scope": "Where was the study conducted?",
    "time_period": "What time period does the data cover?"
  }},

  "key_findings": [
    "Finding 1 — results only, no interpretation",
    "Finding 2",
    "Finding 3",
    "Finding 4 (optional)",
    "Finding 5 (optional)"
  ],

  "critical_evaluation": {{
    "main_strength": "The single most valuable contribution of this paper",
    "main_weakness": "The most significant limitation or flaw",
    "most_questionable_assumption": "The assumption most likely to be wrong or unstated",
    "not_addressed": "The most important thing the authors failed to examine"
  }},

  "relevance_to_proposal": {{
    "pillar": "One of: Detection / Physical Model / Turbidity / Governance / Other",
    "contribution": "What this paper specifically contributes to the research proposal",
    "contradicts_or_complicates": "What this paper contradicts or makes more difficult in the proposal",
    "data_or_code_reusable": "Yes / No / Partially",
    "data_or_code_reusable_explanation": "Explain what exactly can be reused and how"
  }},

  "bottom_line": "One sentence. The single most important thing to remember from this paper for the research proposal."
}}

Return ONLY the JSON. No markdown, no explanation, no preamble.
"""


# ── PDF Extraction ─────────────────────────────────────────────────────────────

def extract_pdf_text(pdf_path: Path) -> str:
    """Extract text from PDF, handling common academic PDF quirks."""
    text_parts = []

    with pdfplumber.open(pdf_path) as pdf:
        print(f"  Pages: {len(pdf.pages)}")
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text:
                text_parts.append(text)

    full_text = "\n\n".join(text_parts)

    # Basic cleanup
    full_text = re.sub(r'\n{3,}', '\n\n', full_text)  # collapse excess newlines
    full_text = re.sub(r'-\n(\w)', r'\1', full_text)   # fix hyphenated line breaks

    word_count = len(full_text.split())
    print(f"  Extracted: ~{word_count:,} words")

    # Truncate if extremely long (Claude context limit safety)
    if word_count > 60000:
        print(f"  ⚠ Article very long — truncating to first 60,000 words")
        full_text = " ".join(full_text.split()[:60000])

    return full_text


# ── Proposal Loader ────────────────────────────────────────────────────────────

def load_proposal(proposal_path: Path) -> str:
    """Load the research proposal from a text file."""
    if not proposal_path.exists():
        print(f"\n⚠ Proposal file not found at: {proposal_path}")
        print("  Create a file called 'proposal.txt' in the same directory,")
        print("  or pass --proposal path/to/your/proposal.txt\n")
        sys.exit(1)

    text = proposal_path.read_text(encoding="utf-8")
    print(f"  Proposal loaded: ~{len(text.split()):,} words")
    return text


# ── Claude API Call ────────────────────────────────────────────────────────────

def analyze_with_claude(proposal: str, article_text: str) -> dict:
    """Send article + proposal to Claude and get structured JSON analysis."""
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from environment

    prompt = build_analysis_prompt(proposal, article_text)

    print("  Sending to Claude API...")
    message = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}]
    )

    raw_response = message.content[0].text

    # Parse JSON — strip markdown fences if present
    clean = re.sub(r'^```json\s*', '', raw_response.strip())
    clean = re.sub(r'\s*```$', '', clean)

    try:
        result = json.loads(clean)
    except json.JSONDecodeError as e:
        print(f"\n⚠ JSON parse error: {e}")
        print("Raw response saved to debug_response.txt")
        Path("debug_response.txt").write_text(raw_response)
        sys.exit(1)

    return result


# ── Save Results ───────────────────────────────────────────────────────────────

def save_result(result: dict, pdf_path: Path) -> Path:
    """Save the analysis JSON to the results directory."""
    RESULTS_DIR.mkdir(exist_ok=True)

    # Build filename from PDF name + timestamp
    stem = pdf_path.stem.replace(" ", "_")[:50]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = RESULTS_DIR / f"{stem}_{timestamp}.json"

    # Add metadata
    result["_meta"] = {
        "source_pdf": str(pdf_path),
        "analyzed_at": datetime.now().isoformat(),
        "model": MODEL
    }

    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    return output_path


# ── Pretty Print ───────────────────────────────────────────────────────────────

def print_summary(result: dict):
    """Print a readable summary to the terminal."""
    sep = "─" * 60

    print(f"\n{sep}")
    print(f"📄  {result.get('title', 'Unknown title')}")
    print(f"    {result.get('authors', '')} ({result.get('year', '')})")
    print(f"    {result.get('journal', '')}")
    print(sep)

    print("\n🎯  CORE ARGUMENT")
    print(f"    {result.get('core_argument', '')}")

    print("\n🔬  METHODOLOGY")
    m = result.get("methodology", {})
    print(f"    Design:    {m.get('research_design', '')}")
    print(f"    Data:      {', '.join(m.get('data_sources', []))}")
    print(f"    Methods:   {', '.join(m.get('analytical_methods', []))}")
    print(f"    Scope:     {m.get('geographic_scope', '')}")
    print(f"    Period:    {m.get('time_period', '')}")

    print("\n📊  KEY FINDINGS")
    for finding in result.get("key_findings", []):
        print(f"    • {finding}")

    print("\n⚖️  CRITICAL EVALUATION")
    c = result.get("critical_evaluation", {})
    print(f"    Strength:    {c.get('main_strength', '')}")
    print(f"    Weakness:    {c.get('main_weakness', '')}")
    print(f"    Assumption:  {c.get('most_questionable_assumption', '')}")
    print(f"    Gap:         {c.get('not_addressed', '')}")

    print("\n🔗  RELEVANCE TO PROPOSAL")
    r = result.get("relevance_to_proposal", {})
    print(f"    Pillar:      {r.get('pillar', '')}")
    print(f"    Contributes: {r.get('contribution', '')}")
    print(f"    Complicates: {r.get('contradicts_or_complicates', '')}")
    print(f"    Reusable:    {r.get('data_or_code_reusable', '')} — {r.get('data_or_code_reusable_explanation', '')}")

    print(f"\n💡  BOTTOM LINE")
    print(f"    {result.get('bottom_line', '')}")
    print(f"\n{sep}\n")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Analyze an academic PDF against your research proposal.")
    parser.add_argument("--pdf", required=True, help="Path to the academic PDF")
    parser.add_argument("--proposal", default=str(PROPOSAL_FILE), help="Path to proposal text file")
    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    proposal_path = Path(args.proposal)

    if not pdf_path.exists():
        print(f"Error: PDF not found at {pdf_path}")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"Research Article Analysis Agent")
    print(f"{'='*60}")

    print(f"\n[1/4] Loading proposal...")
    proposal = load_proposal(proposal_path)

    print(f"\n[2/4] Extracting text from PDF...")
    article_text = extract_pdf_text(pdf_path)

    print(f"\n[3/4] Analyzing with Claude...")
    result = analyze_with_claude(proposal, article_text)

    print(f"\n[4/4] Saving results...")
    output_path = save_result(result, pdf_path)
    print(f"  Saved to: {output_path}")

    print_summary(result)


if __name__ == "__main__":
    main()
