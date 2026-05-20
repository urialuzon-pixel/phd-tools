#!/usr/bin/env python3
"""
Usage: python summarize_paper.py <path_to_paper.pdf>
Generates a summary PDF in the same folder as the input file.
"""

import sys
import os
import textwrap
from pypdf import PdfReader
import anthropic
from fpdf import FPDF

SUMMARY_PROMPT = """You are an academic paper summarizer. Summarize the paper below using this exact structure. Write in Hebrew.

### [Title] — [Authors, Year]

**Research Question**
One sentence stating the central question or hypothesis.

**Context**
2–3 sentences on the problem setting and where this paper fits in the literature.

**Data & Methods**
- Data source(s) and scope
- Analytical approach
- Key tools or frameworks

**Key Findings**
Numbered list of main results. Include statistics where stated.

**Limitations**
Bullet list as stated by the authors. Add [inferred] for obvious gaps they didn't mention.

**Contributions**
What this paper adds — theoretical, empirical, or methodological.

Rules:
- Extract only what is explicitly stated. Do not fabricate.
- Preserve the author's framing.
- If there are negative/null results, include them under Key Findings.
- Total length: 300–500 words.

---

PAPER:
{text}
"""


def extract_text(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)
    pages = []
    for page in reader.pages:
        t = page.extract_text()
        if t:
            pages.append(t)
    return "\n".join(pages)


def get_summary(text: str) -> str:
    client = anthropic.Anthropic()
    # Trim to ~80k chars to stay within context limits
    trimmed = text[:80000]
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        messages=[{"role": "user", "content": SUMMARY_PROMPT.format(text=trimmed)}],
    )
    return message.content[0].text


class SummaryPDF(FPDF):
    FONT_PATH = r"C:\Windows\Fonts\arial.ttf"
    FONT_BOLD_PATH = r"C:\Windows\Fonts\arialbd.ttf"

    def __init__(self):
        super().__init__()
        self.add_font("Arial", "", self.FONT_PATH)
        self.add_font("Arial", "B", self.FONT_BOLD_PATH)
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        self.set_font("Arial", "B", 10)
        self.set_text_color(120, 120, 120)
        self.cell(0, 8, "Academic Paper Summary", align="C")
        self.ln(4)
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")


def write_line(pdf: SummaryPDF, line: str, page_width: float):
    """Write a single markdown-ish line with basic formatting."""
    line = line.rstrip()

    if line.startswith("### "):
        pdf.set_font("Arial", "B", 14)
        pdf.set_text_color(30, 30, 30)
        pdf.multi_cell(0, 8, line[4:])
        pdf.ln(2)

    elif line.startswith("**") and line.endswith("**"):
        pdf.set_font("Arial", "B", 11)
        pdf.set_text_color(50, 80, 140)
        pdf.multi_cell(0, 7, line.strip("*"))
        pdf.ln(1)

    elif line.startswith("- ") or line.startswith("* "):
        pdf.set_font("Arial", "", 10)
        pdf.set_text_color(40, 40, 40)
        pdf.set_x(18)
        pdf.multi_cell(page_width - 18, 6, "•  " + line[2:])

    elif line and line[0].isdigit() and ". " in line[:4]:
        pdf.set_font("Arial", "", 10)
        pdf.set_text_color(40, 40, 40)
        pdf.set_x(18)
        pdf.multi_cell(page_width - 18, 6, line)

    elif line == "---":
        pdf.set_draw_color(220, 220, 220)
        pdf.line(10, pdf.get_y() + 2, 200, pdf.get_y() + 2)
        pdf.ln(5)

    elif line:
        # inline bold: strip ** markers for now
        cleaned = line.replace("**", "")
        pdf.set_font("Arial", "", 10)
        pdf.set_text_color(40, 40, 40)
        pdf.multi_cell(0, 6, cleaned)

    else:
        pdf.ln(3)


def generate_pdf(summary: str, output_path: str):
    pdf = SummaryPDF()
    pdf.add_page()
    page_width = pdf.w - pdf.l_margin - pdf.r_margin

    for line in summary.splitlines():
        write_line(pdf, line, page_width)

    pdf.output(output_path)


def main():
    if len(sys.argv) < 2:
        print("Usage: python summarize_paper.py <path_to_paper.pdf>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    if not os.path.exists(pdf_path):
        print(f"File not found: {pdf_path}")
        sys.exit(1)

    print(f"[1/3] Extracting text from {os.path.basename(pdf_path)}...")
    text = extract_text(pdf_path)
    if not text.strip():
        print("Could not extract text from PDF (may be scanned/image-based).")
        sys.exit(1)

    print("[2/3] Generating summary via Claude API...")
    summary = get_summary(text)

    base = os.path.splitext(pdf_path)[0]
    output_path = base + "_summary.pdf"
    print(f"[3/3] Writing PDF to {output_path}...")
    generate_pdf(summary, output_path)

    print(f"\nDone. Summary saved to:\n  {output_path}")


if __name__ == "__main__":
    main()
