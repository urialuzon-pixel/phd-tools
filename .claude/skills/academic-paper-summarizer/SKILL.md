# academic-paper-summarizer

## Description
Summarizes a single academic paper into a structured, readable summary. Trigger when the user pastes a paper, shares a URL to one, or says: "summarize this paper", "analyze this article", "what does this paper say", "סכם את המאמר", "נתח את המחקר".

---

## Core Principles

- Extract only what is explicitly stated in the paper. Do not infer or fabricate.
- Preserve the author's framing — especially methodological choices and stated limitations.
- Negative results and null findings are as important as positive ones — always report them.
- No external searches. Work only from the content provided.

---

## Phase 0: Receive the Paper

Accept input in any of these forms:
- **Pasted text** — abstract, excerpts, or full paper
- **URL** — use WebFetch to retrieve the content

If the input is abstract-only, proceed but label the summary as "Abstract-based summary" and note that full-text analysis was not possible.

---

## Phase 1: Write the Summary

Output in the following format. Total length ~300–500 words.

---

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
Numbered list of main results. Include statistics where stated. If findings are contested within the paper, note that.

**Negative Results / Null Findings**
State explicitly if the paper found null results or if hypotheses were rejected. If none — omit this section.

**Limitations**
Bullet list as stated by the authors. Add [inferred] for obvious gaps they didn't mention.

**Contributions**
What this paper adds — theoretical, empirical, or methodological.

---

## Optional: Relevance to Research Question

Only include this section if the user explicitly provides a research question or asks to connect the paper to their work.

If requested, add:

**Relevance to Your Research Question**
2–3 sentences on how this paper connects to the stated question — what it supports, contradicts, or leaves open.

---

## Integrity Rules

- Do not fill in missing data with plausible-sounding content.
- If the paper is abstract-only, do not invent methodology or findings.
- If the paper is inaccessible, say so and summarize only what was retrieved.
