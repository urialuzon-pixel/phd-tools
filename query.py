"""
Cross-Paper Query Agent — Phase 2
===================================
Query across all analyzed articles stored in the results/ directory.

Usage:
    python query.py "which papers address the turbidity proxy?"
    python query.py "what do all papers say about governance and weak institutions?"
    python query.py "summarize the methodological landscape across all papers"
    python query.py --report   # generate a full synthesis report
"""

import argparse
import json
import sys
from pathlib import Path

import anthropic

RESULTS_DIR = Path("results")
MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 4000


def load_all_results() -> list[dict]:
    """Load all JSON analysis files from results directory."""
    if not RESULTS_DIR.exists() or not list(RESULTS_DIR.glob("*.json")):
        print("No results found. Run analyze.py on some PDFs first.")
        sys.exit(1)

    results = []
    for path in sorted(RESULTS_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            results.append(data)
        except Exception as e:
            print(f"Warning: could not load {path.name}: {e}")

    print(f"Loaded {len(results)} analyzed article(s).\n")
    return results


def build_corpus_summary(results: list[dict]) -> str:
    """Build a compact text representation of all analyzed papers."""
    parts = []
    for i, r in enumerate(results, 1):
        part = f"""
PAPER {i}: {r.get('title', 'Unknown')} ({r.get('year', '')})
Authors: {r.get('authors', '')}
Journal: {r.get('journal', '')}
Core Argument: {r.get('core_argument', '')}
Data Sources: {', '.join(r.get('methodology', {}).get('data_sources', []))}
Methods: {', '.join(r.get('methodology', {}).get('analytical_methods', []))}
Geographic Scope: {r.get('methodology', {}).get('geographic_scope', '')}
Key Findings: {' | '.join(r.get('key_findings', []))}
Main Strength: {r.get('critical_evaluation', {}).get('main_strength', '')}
Main Weakness: {r.get('critical_evaluation', {}).get('main_weakness', '')}
Proposal Pillar: {r.get('relevance_to_proposal', {}).get('pillar', '')}
Contribution to Proposal: {r.get('relevance_to_proposal', {}).get('contribution', '')}
Complicates: {r.get('relevance_to_proposal', {}).get('contradicts_or_complicates', '')}
Reusable Data/Code: {r.get('relevance_to_proposal', {}).get('data_or_code_reusable', '')} — {r.get('relevance_to_proposal', {}).get('data_or_code_reusable_explanation', '')}
Bottom Line: {r.get('bottom_line', '')}
"""
        parts.append(part.strip())

    return "\n\n" + ("─" * 60 + "\n\n").join(parts)


SYNTHESIS_REPORT_PROMPT = """
Based on all the analyzed papers above, generate a structured synthesis report with the following sections:

1. LITERATURE LANDSCAPE
   What is the overall state of the field? What is well-established vs. still open?

2. BY PILLAR — what each pillar of the proposal is supported by
   - Detection pillar: which papers, what they contribute, what's missing
   - Physical Model pillar: which papers, what they contribute, what's missing
   - Turbidity pillar: which papers, what they contribute, what's missing
   - Governance pillar: which papers, what they contribute, what's missing

3. METHODOLOGICAL PATTERNS
   What methods recur across papers? Any consensus on best practices?

4. KEY GAPS IN THE LITERATURE
   What has no one done yet? Where is the proposal most novel?

5. DATA REUSE OPPORTUNITIES
   Which datasets or codebases from these papers can be directly used?

6. RISKS TO THE PROPOSAL
   Based on the literature, what are the biggest threats to the proposal's feasibility or novelty?

7. RECOMMENDED NEXT READS
   Based on the gaps identified, what kinds of papers should still be found and read?

Be specific. Reference papers by author and year. Be honest about weaknesses.
"""


def query_corpus(question: str, corpus: str) -> str:
    """Answer a question about the corpus of analyzed papers."""
    client = anthropic.Anthropic()

    if question == "--report":
        user_content = f"Here are all analyzed papers:\n{corpus}\n\n{SYNTHESIS_REPORT_PROMPT}"
    else:
        user_content = f"""Here are all analyzed papers:\n{corpus}

Question: {question}

Answer the question precisely and concisely, referencing specific papers by title/author where relevant.
If no papers address the question, say so clearly."""

    message = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system="You are a rigorous academic research assistant. Answer only based on the papers provided. Be specific, cite papers, and be honest when coverage is thin.",
        messages=[{"role": "user", "content": user_content}]
    )

    return message.content[0].text


def main():
    parser = argparse.ArgumentParser(description="Query across all analyzed articles.")
    parser.add_argument("question", nargs="?", help="Question to ask about the literature")
    parser.add_argument("--report", action="store_true", help="Generate a full synthesis report")
    args = parser.parse_args()

    if not args.question and not args.report:
        parser.print_help()
        sys.exit(1)

    results = load_all_results()
    corpus = build_corpus_summary(results)

    question = "--report" if args.report else args.question
    answer = query_corpus(question, corpus)

    print("=" * 60)
    if args.report:
        print("SYNTHESIS REPORT")
    else:
        print(f"Q: {question}")
    print("=" * 60)
    print(answer)
    print()


if __name__ == "__main__":
    main()
