# proposal-generator

## Description
Doctoral research proposal writing agent. Works directly from the output of `literature-review-helper` (already in context), or accepts a research topic independently and builds from scratch using Consensus searches. Produces a structured Word document (~2,000 words) covering all standard sections of an internal doctoral proposal. Trigger when the user says: "write a research proposal", "create a doctoral proposal", "build a proposal from the literature review", "draft a PhD proposal".

---

## Core Principles

Every claim in the proposal must be grounded in papers that Consensus returned during this session. Do not fabricate paper details, authors, or findings. If a paper did not come from a Consensus search in this session, it may not be cited without the label [Model knowledge — not verified via Consensus] and must be excluded from the bibliography.

---

## Phase 0: Input Collection

### A. Determine what is already available

Check whether `literature-review-helper` was run in this session:

- **Yes — literature review exists in context**: Extract the following sections directly from what Claude already knows from this session:
  - Section 1 (Topic Overview) → background material
  - Section 2 (Priority Reading) → related work
  - Section 4 (Sub-area Guides) → methodology vocabulary and approaches
  - Section 5 (Key Research Groups) → field positioning
  - Section 6 (Open Questions & Gaps) → research questions and justification

- **No — starting from scratch**: Ask the user for the research topic in one short question, then run Phase 0B before proceeding.

### B. If no literature review exists — run targeted searches

Run 4 sequential Consensus searches to gather minimum viable grounding:
1. Broad topic search
2. Methods/approaches in this area
3. Recent reviews or meta-analyses
4. Known gaps or critiques

Wait at least 1 second between searches. On failure: wait 3 seconds, retry once, log the failure.

After searches complete, proceed to Phase 1 using these results as the source material.

---

## Phase 1: Map Literature to Proposal Sections

Extract and internally store the following before writing anything:

| Source | Maps to |
|--------|---------|
| Topic overview / broad search results | Chapter 1: Background |
| Priority papers / reviews | Chapter 3: Related Work |
| Sub-area approaches / methods papers | Chapter 4: Methodology |
| Key research groups | Chapter 3: Field positioning |
| Open questions and gaps (Section 6 or inferred) | Chapter 2: Research Questions |

If Section 6 is absent and no gaps are explicitly stated: identify 2–3 gaps independently from the literature gathered, and flag them to the user at the checkpoint as inferred rather than stated.

---

## Phase 2: Checkpoint — Confirm Before Writing

Before drafting a single word of the proposal, output the following to chat. Keep it concise and scannable:

**Proposed Research Questions**
List 1 main research question and 2–3 sub-questions derived from the identified gaps. Number them.

**Methodological Approach**
Two sentences describing the general approach (empirical / computational / mixed / qualitative).

**Grounding Papers**
A short list of the papers from Consensus that will anchor the proposal, with author and year. Flag any section where coverage is thin.

**Gaps Flagged**
If any gaps were inferred (not from Section 6), name them explicitly and note they are inferred.

Then ask:
> "Do these research questions reflect the direction you want? Anything to adjust before I write the proposal?"

Wait for the user's response. Do not proceed to Phase 3 until the user confirms or requests changes. If the user requests changes, update the research questions and/or approach, confirm again briefly in chat, then proceed.

---

## Phase 3: Write the Proposal

Target: ~2,000 words total across all prose sections. The timeline table does not count toward word targets.

### Chapter 1: Background (300–400 words)

Open with what is known and established in the field. Move from broad context to specific problem. End with a clear statement of the gap that this research addresses. Cite grounding papers throughout using (Author, Year) format.

Do not use bullet points in this chapter — write in connected paragraphs.

### Chapter 2: Research Questions (100–150 words)

State the primary research question in one sentence. Follow with 2–3 sub-questions, numbered. If a hypothesis is appropriate for the field, include it as one additional sentence. Keep this chapter short and precise — clarity matters more than length here.

### Chapter 3: Positioning in the Literature (200–250 words)

Describe what has already been done by key research groups in this area. Then state explicitly what this study adds that existing work does not provide. This is the "why this and why now" chapter. Reference key research groups from Section 5 if available.

Avoid vague claims like "this area is understudied." Be specific: what exactly is missing, and why does it matter.

### Chapter 4: Methodology (300–400 words)

Structure as follows:
1. **Research design** — overall approach and rationale for choosing it
2. **Data** — sources, access, scale, format
3. **Analytical steps** — numbered list of 3–5 concrete steps
4. **Tools and methods** — specific techniques, software, frameworks

Draw from Section 4 sub-area guides if available. Be specific enough that a reader could evaluate feasibility.

### Chapter 5: Expected Contributions (150–200 words)

Divide into two parts:
- **Theoretical contribution** — what new understanding does this add to the field?
- **Practical / applied contribution** — who benefits and how?

If the topic has policy relevance, add a third part: **Policy contribution** (2–3 sentences).

Avoid claiming contributions that are not justified by the research questions.

### Chapter 6: Timeline (table)

Produce a 3-year table divided into semesters (6 rows). For each semester, list:
- Primary activity
- Key milestone or deliverable

Keep milestone descriptions concrete (e.g., "Complete data collection", "Submit Chapter 2 draft") rather than vague (e.g., "Continue research").

### Chapter 7: Bibliography

List every paper cited in the proposal, alphabetically by first author's last name. Format each entry as:

Author, A., & Author, B. (Year). Title of paper. *Journal Name*. [View on Consensus](url)

Only include papers that were returned by Consensus in this session. If a paper was mentioned as [Model knowledge — not verified via Consensus], include it in a separate subsection titled "Additional References (unverified)" at the end.

---

## Phase 4: Generate the .docx File

Before generating the document, read the docx skill at `/mnt/skills/public/docx/SKILL.md`.

Generate using JavaScript with the `docx` npm package.

File name: `doctoral_proposal_[topic].docx`
Save to: `/mnt/user-data/outputs/`

```javascript
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
        AlignmentType, LevelFormat, ExternalHyperlink, HeadingLevel,
        BorderStyle, WidthType } = require('docx');

// Page: A4, 2.5cm margins
properties: {
  page: {
    size: { width: 11906, height: 16838 },
    margin: { top: 1418, right: 1418, bottom: 1418, left: 1418 }
  }
}
```

After saving, report to the user in chat:
- File path
- Word count per chapter
- Total word count
- Number of Consensus-verified citations included

---

## Integrity Rules

- Research questions must be falsifiable — if a question cannot in principle be answered with evidence, revise it.
- The timeline must be realistic — a 3-year plan must not promise more than a 3-year PhD allows.
- Do not pad chapters to meet word targets by repeating points from other chapters.
- If a chapter cannot be written with adequate grounding (too few papers, unclear methodology), say so in chat and ask the user how to proceed rather than filling with generic text.
