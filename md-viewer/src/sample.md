# academic-paper-summarizer

## Description
Summarizes a single academic paper into a structured, research-grade summary. Trigger when the user says: "summarize this paper", "analyze this article", "break down this study", "what does this paper say", "סכם את המאמר", "נתח את המחקר", or pastes/links to an academic paper.

---

## Core Principles

- Extract only what is explicitly stated in the paper. Do not infer findings or fabricate statistics.
- Preserve the author's framing — especially methodological choices and stated limitations.
- Flag anything that is inferred or uncertain with [inferred].
- Negative results and null findings are as important as positive ones — always report them.

---

## Phase 0: Receive the Paper

Accept input in any of these forms:
- **Pasted text** — abstract, excerpts, or full paper
- **URL** — use WebFetch to retrieve the content
- **Title + DOI/authors** — search Consensus to locate the paper, then summarize from retrieved content

If the input is incomplete (e.g., abstract only), proceed but clearly label the summary as "Abstract-based summary" and note that full-text analysis was not possible.

If input is ambiguous (multiple possible papers), ask the user to clarify before proceeding.

---

## Phase 1: Extract Core Information

Internally extract the following before writing any output:

| Field | What to extract |
|-------|----------------|
| **Citation** | Authors, year, title, journal/conference, DOI if available |
| **Paper type** | Empirical / Review / Theoretical / Mixed methods / Policy analysis |
| **Research question** | The central question or hypothesis as stated by the authors |
| **Context** | The broader problem the paper addresses and where it sits in the literature |
| **Data & methods** | Data sources, sample size/scope, analytical approach, tools used |
| **Key findings** | Main results — quantitative where available, qualitative otherwise |
| **Negative results** | Null findings or failed hypotheses, if any |
| **Limitations** | As stated by the authors; supplement with [inferred] if obvious gaps exist |
| **Contributions** | What the paper adds — theoretical, empirical, methodological |
| **Follow-up references** | Key papers cited by the authors that are worth reading next |

---

## Phase 2: Write the Summary

Output in the following format. Sections should be concise — total length ~400–600 words.

---

### Paper: [Full Citation]
**Type:** [Empirical / Review / Theoretical / Mixed / Policy]

**Research Question**
One sentence stating the central question or hypothesis.

**Context**
2–3 sentences on the problem setting and where this paper fits in the literature.

**Data & Methods**
- Data source(s) and scope
- Analytical approach
- Key tools or frameworks used

**Key Findings**
Numbered list of main results. Include effect sizes or statistics where stated in the paper. If findings are contested within the paper, note that.

**Negative Results / Null Findings**
State explicitly if the paper found null results or if hypotheses were rejected. Do not omit or downplay these.

**Limitations**
Bullet list of limitations as stated by the authors. Add [inferred] for obvious gaps the authors did not mention.

**Contributions**
What this paper adds to the field — theoretical, empirical, or methodological.

**Relevance to Your Research**
1–2 sentences on how this paper connects to the user's PhD research on geopolitical impunity and extractive activity (geospatial anomaly detection, satellite data, mining in disputed territories). Skip this section if no clear connection exists.

**Worth Reading Next**
Up to 3 papers cited in this study that are most relevant, with author and year.

---

## Phase 3: Optional — Connect to Literature Review

If `literature-review-helper` was previously run in this session, add a section:

**Fits Into Literature Review**
Note which sub-area or thematic cluster from the existing literature review this paper belongs to. Flag if it contradicts, extends, or confirms papers already in the review.

---

## Integrity Rules

- Do not fill in missing data with plausible-sounding content.
- If the paper is abstract-only, do not invent methodology or findings beyond what the abstract states.
- If the paper appears to be behind a paywall or inaccessible, say so and summarize only what was retrieved.
- Citations in "Worth Reading Next" must come from the paper itself — do not add external suggestions.
