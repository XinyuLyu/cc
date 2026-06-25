# Style Guide: Personal Rebuttal Writing

---

## Block Header Format

Short abbreviation prefix — match what's in the reviewed paper's venue form:

| Category | Prefix | Example |
|---|---|---|
| Soundness | `S-` | `***S-W2 & Q2: No comparison with SafePTR***` |
| Significance | `Sig-` | `***Sig-W1: White-box access***` |
| Presentation | `P-` | `***P-W1~W7, O-W1~W2: Writing and related work***` |
| Originality | `O-` | (usually merged with P) |
| Key Question | `Q` | `***Q1: Foreground-localized malicious semantics***` |

Group multiple related concerns under one block. List all IDs in the header.

---

## Sentence-Level Rules

### Lead with the conclusion
Wrong: "This is an interesting observation. Let us first clarify what we mean by X, then..."
Right: "Foreground-localized malicious semantics is not our hypothesis — it is **common knowledge** in the MLLM safety community."

### Bold the key fact or number, not the entire sentence
Wrong: **"SAP achieves state-of-the-art safety performance with significantly lower latency."**
Right: "SAP outperforms LLaVAGuard on FigStep (ASR: **47.80%** vs. **49.40%**) with **substantially lower latency** (57.19 ms vs. 160.09 ms)."

### Hedge words to cut entirely
| Word | Replace with |
|---|---|
| "we believe" | state it or cite it |
| "it seems" | either it is or it isn't |
| "arguably" | state the argument |
| "to some extent" | quantify it |
| "we hope" | "we will" |
| "relatively" | give the actual number |
| "in some sense" | cut |
| "unfortunately" (for design constraints) | just state the constraint |

---

## Paragraph Length by Concern Type

| Type | Target length |
|---|---|
| Misunderstanding | 3–5 sentences |
| Missing experiment | 2 sentences + table |
| Missing baseline (reproduced) | 3–4 sentences + table |
| Scope/design necessity | 1–2 sentences |
| Writing/presentation | 1 sentence + bulleted list |
| Theoretical rigor | 1–2 sentences + appendix promise |
| Sensitivity analysis | 2 sentences + table + 1 sentence on mechanism |
| Adaptive attack | 3–4 sentences (no table needed) |

---

## Table Format

**Present every new table twice:**
1. Code-block version (compact, reviewer-friendly display)
2. Actual markdown table below it

**Row ordering:**
1. Baseline (vanilla, no defense)
2. Competing methods (in ascending order of performance)
3. **Our method (bolded)**
4. Our method + extension/cascade (if applicable, bolded)

**Column headers:**
- Safety: `Benchmark↓` (lower is better, use ↓)
- Utility: `Benchmark↑` (higher is better, use ↑)  
- Efficiency: `Latency(ms)` (no arrow — context-dependent)

**Table title format:** `Tab.RX: [Short title] ([Model], [Setting]).`

---

## Revision Promise Format

Always follow this exact pattern:

```
We **will [verb]** [what] to the **revised [Section X / Appendix Y / Tab. Z]**.
```

Examples:
- `We **will add** these evaluation details to the **revised Section 6.1**.`
- `We **will expand** **Appendix D** with step-by-step derivations.`
- `We **will incorporate** these results into **Tab. 2** of the **revised** manuscript.`
- `We **will clarify** this in the **revised** manuscript.`

---

## Cross-Referencing Shared Experiments

When two reviewers raise the same concern (e.g., model generalization):
- Write the full experiment once (under the reviewer who mentioned it first, or the one with the most context)
- In the other reviewer's block: "As shown in Tab. RX (see also our response to Reviewer [Y])..."
- Never duplicate the table or the interpretation paragraph

---

## What NOT to Write

| Pattern | Why |
|---|---|
| "We thank the reviewer for their thorough and insightful feedback." | Generic opening. Instead, thank them for *the specific observation*. |
| "This is a great/interesting/perceptive question." | Never. Go straight to the answer. |
| "We believe our method is..." | Hedge. State it or cite it. |
| "Unfortunately, due to [constraint]..." | Apologetic. "X is technically infeasible because Y." |
| Multi-paragraph response to a typo/formatting issue | Bulleted list, one sentence total. |
| Restating the reviewer's concern before answering | Skip the recap. Answer immediately. |
| "In future work, we plan to..." | This is a rebuttal, not a paper. Only promise if you can deliver in the revision period. |

---

## Tone Calibration by Reviewer Attitude

| Situation | Tone |
|---|---|
| Reviewer says "will raise score if concerns addressed" | Thorough, specific, grateful for each concern |
| Reviewer is clearly positive (4–5 score) | Efficient. Don't over-explain. Table + 2 sentences. |
| Reviewer has many concerns (15+), some are minor | Merge aggressively. Address all but spend words on major ones. |
| Reviewer misunderstands a well-known fact | Correct directly. "This ignores established consensus in [community]." |
| Reviewer's concern reveals they didn't read a section | Point to exact lines. "Our original text (Lines Y–Z) states..." |
| Multiple reviewers contradict each other | Use in AC comment if useful. Don't call it out to the reviewer directly. |
