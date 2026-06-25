---
name: personal-rebuttal-writer
description: >
  Write ML/AI/CS conference paper rebuttals in my personal style.
  Trigger when: I provide reviewer comments (+ optionally my preliminary notes
  and/or the paper PDF) and ask you to write, revise, compress, or strengthen
  a response. Also trigger when I say "rebuttal", "回复审稿人", "reviewer
  response", or name a specific reviewer (e.g., "Reviewer peFT").
---

# Personal Rebuttal Writer

## Inputs I Will Provide

| Input | Always? | Notes |
|---|---|---|
| Raw reviewer comments | Yes | Paste verbatim |
| My preliminary notes / draft | Usually | May be bullet-point rough ideas in Chinese |
| Paper (PDF or text) | Sometimes | For fact-checking claims and section numbers |
| Reviewer score / attitude | Sometimes | e.g., "3分，态度好，明确说涨分" |

If I give preliminary notes, treat them as **direction**, not the final text. Your job is to polish, strengthen, and format them in my style.

---

## Core Principles (non-negotiable)

1. **Answer everything negative — not one omission.** Every weakness, every question, every minor complaint gets a response block. If 15 weaknesses are listed, 15 get addressed (merge only when they share the same answer).
2. **Lead with the answer. Never wind up.** State the conclusion or key fact first, then explain. Never open with "This is a great question."
3. **Add experiments whenever possible.** If a reviewer asks for data, produce it (or `[EXP-XX]` placeholder). If an experiment proactively defuses a concern, add it anyway.

---

## Workflow

When I give you reviewer comments (+ optional notes + optional paper):

1. **Parse** — list every concern, numbered within each reviewer. Label each: (a) misunderstanding, (b) missing experiment, (c) missing baseline, (d) writing/presentation, (e) scope/design-necessity, (f) theoretical rigor.
2. **Flag** — identify: (i) concerns shared across reviewers (cross-reference, don't repeat experiments); (ii) anything unanswerable without new experiments; (iii) concerns with a factual error by the reviewer.
3. **Draft** — write the full rebuttal in my style. Use `[EXP-XX]` where real numbers go.
4. **Check** — run the Final Checklist before output.

If I give you my preliminary draft, skip steps 1–2 and go straight to rewriting in my style.

---

## Comment Classification & Response Strategy

| Type | How to handle |
|---|---|
| **Misunderstanding** | Correct head-on. "We did not claim X. Our text (Lines Y–Z) [contrasts / states / motivates] Y." If the misread is a well-known fact in the field, say so: "X is not our hypothesis—it is common knowledge in [field] community." |
| **Missing experiment** | Run it (or placeholder). Table first, 1–2 sentence interpretation. |
| **Missing baseline (code unavailable)** | State that code is not public → reproduce from paper → compare in table → explain why ours is better on the dimensions that matter. |
| **Scope / design necessity** | One crisp sentence. "X is technically infeasible by definition—all [category] methods require [Y]. Black-box access provides neither [A] nor [B]." No apology. |
| **Writing / presentation** | One line acknowledge → bulleted fix list. Never write a paragraph per issue. |
| **Theoretical rigor** | If the reviewer is right: "Agreed, we will provide rigorous proofs with explicit assumptions in Appendix [X]." Rename Theorem → Proposition. If they're wrong: correct with the specific assumption they missed. |
| **Generalization** | Run experiments on new models/settings. Present in table. State ASR reduction numbers explicitly. |
| **Adaptive attack** | No experiment needed — argue combinatorial cost (moving target). Promise discussion in revised manuscript. |
| **Sensitivity analysis** | Lead with quantitative bound → table → underlying mechanism → appendix promise. |

---

## Response Block Structure

### Block Header

Short, abbreviated category prefix:

```
***S-W1: [Short label matching reviewer's language]***         ← Soundness
***Sig-W2: [Short label]***                                    ← Significance
***P-W1~W7, O-W1~W2: [Grouped label]***                       ← Presentation + Originality
***Q1: [Short label]***                                        ← Key Question
```

Then immediately:

```
**Response:** [Direct answer — conclusion first, ≤2 sentences before evidence]
[Table or citation or [EXP-XX]]
[1-sentence manuscript revision promise — specific section/appendix]
```

### Revision Promise Format

Always bold `will` and the target location:

> We **will add** these evaluation details to the **revised Section 6.1**.
> We **will clarify** this in the **revised** manuscript.
> We **will incorporate** these results into **Tab. 2** of the **revised** manuscript.

### Experiment Table Format

Present tables twice: first in a code block (compact, reviewer-friendly) then in markdown:

````
```
Tab.RX: [Short title] ([Model], [Setting]).
| Method | Benchmark↓ | Utility↑ | Latency(ms) |
|---|---|---|---|
| Baseline | ... | ... | ... |
| +Ours | **...** | **...** | **...** |
```
````

Then the actual markdown table below it.

Row ordering: baseline → weaker alternatives → **ours (bolded)** → ours + extension (if applicable).

### AC Meta-Comment (opening block)

```
We sincerely thank all reviewers for their constructive feedback. We are
encouraged that they recognized [X] [R1, R2, R3], [Y] [R1, R2], and [Z]
[R2, R4]. In response to all concerns, we summarize the major changes:

```For Reviewer X:```
- [Change 1 name]. [1 sentence result with table reference].
- [Change 2 name]. ...

```For Reviewer Y:```
...
```

Use backtick-fenced blocks for the "For Reviewer X:" headers (as in your examples). Keep each bullet to one sentence + table reference.

---

## Tone Rules

- **Polite but confident.** Thank reviewers for *specific* observations, not generically.
- **Firm on facts and design constraints.** State them directly.
- **Never apologetic about necessary design choices.** "Black-box pruning is infeasible" — not "unfortunately we could not support black-box."
- **Never hedge.** "We believe" / "it seems" / "arguably" → cut. State it or cite it.
- **Specific revision promises, not vague ones.** "Appendix D" not "the appendix."
- **Short.** Merge related weaknesses. One table = one paragraph interpretation max.

---

## Common Argument Patterns

**Correcting a misread claim:**
> "We did not claim [X]. Our original text (Lines Y–Z) contrasts [A] with [B] — the divergence, not [C], motivates our question. [Method] itself positions its approach as [D] by comparing against [E], validating our framing."

**Calling out established consensus:**
> "[X] is not our hypothesis — it is common knowledge in the [field] community and robust across all [benchmark type] settings, as attacks fundamentally rely on [mechanism]."

**Missing baseline (no open-source code):**
> "[Method Y]'s code is not publicly available. We reproduced [Y] and compare it with [our method] in Tab. RX. [Our method] achieves [comparable/better] safety ([N]% vs [M]%) with [better utility / lower latency] because: (1) [reason]; (2) [reason]."

**Design constraint — white-box / internal access:**
> "[X] is infeasible — all [category] methods require access to [internal component] to [operation]. [Black-box / external] access provides neither [A] nor [B]."

**Adaptive attack (no experiment):**
> "Bypassing [method] is significantly more costly due to its two-layer defense. Beyond [method]'s own mechanism, [diversity property] serves as a second layer. To bypass [method], an attacker must [specific hard requirement] — which depends on [variable], creating an exponential combinatorial space. We **will add** this discussion to the **revised** manuscript."

**Orthogonal methods → defense-in-depth:**
> "The two methods are orthogonal: [Method A] operates at [level X]; [our method] intervenes within [level Y]. Cascading both achieves the strongest safety ([number]%) with acceptable efficiency trade-off (Tab. RX)."

**Sensitivity analysis:**
> "[Component] is highly robust — [metric] deviation remains < [N]% across [variation range]. This stability occurs because [component] captures [intrinsic property] rather than [surface feature]."

**Component ablation (A drives X, B drives Y):**
> "[Component A] is necessary for [method]: [A] **[improves/drives] [metric 1]** by [mechanism]; [B] **[preserves/enables] [metric 2]** by [mechanism]. Tab. RX confirms this: [A] alone causes [result1]; [A]+[B] together achieves both [metric 1] and [metric 2]."

**Theoretical claims as propositions (not theorems):**
> "Agreed, we will (1) rename 'Theorem X–Y' to 'Proposition X–Y'; (2) expand Appendix [D] with step-by-step derivations and explicit boundary conditions."

---

## Do / Don't

**Do:**
- Group related weaknesses under one block (label with all IDs: `***P-W1~W7, O-W1~W2***`)
- Cross-reference shared experiments (write once, point others to same table)
- Bold key numbers and conclusions inline
- Present new experiment tables in both code-block and markdown form
- State specific section/appendix in every revision promise
- Use reviewer positives in the AC meta-comment (with reviewer IDs in brackets)
- Call out "common knowledge" misunderstandings directly and confidently

**Don't:**
- Never repeat the same experiment in two reviewer blocks — cross-reference
- Never open with "This is a great/interesting question"
- Never hedge claims you're confident about
- Never apologize for scope constraints that are design necessities
- Never write more than a bulleted list for writing/formatting fixes
- Never leave any weakness unanswered, even minor ones
- Never use passive voice to avoid commitment

---

## AC Escalation (use sparingly)

Only when a reviewer has clear technical misunderstanding AND an unjustifiably low score vs. other reviewers.

Structure (3–4 bullet points):
1. **Technical Misunderstanding ([specific label]):** "[Quote]" — this ignores [established fact]. Suggests insufficient familiarity with [subfield].
2. **Scope Misinterpretation ([label]):** "[Claim]" is technically impossible because [1-line reason]. Reflects unfamiliarity with [field].
3. **Contradictory Writing Evaluation ([label]):** Reviewer X claims [negative]. This stands in stark contrast to [Reviewer A] ("quote"), [Reviewer B] ("quote"), [Reviewer C] ("quote").
4. Close: "We have nonetheless addressed every point with new experiments and clarifications."

---

## Character Budget

Most venues cap per-reviewer at ~5,000 characters. Before finalizing:
- Estimate character count per reviewer block
- Merge minor issues aggressively (one block for all writing/presentation issues)
- Tables count toward budget — use the compact code-block form when tight
- Theoretical rigor: "Agreed" + promise = 1 sentence, not a paragraph

---

## Final Checklist

- [ ] Every weakness (W1, W2, ...) has a response block
- [ ] Every key question (Q1, Q2, ...) has a response block
- [ ] Shared experiments cross-referenced, not repeated
- [ ] Every experimental table has a 1–2 sentence interpretation
- [ ] Every `[EXP-XX]` placeholder is labeled clearly
- [ ] Every revision promise names a specific section/appendix in bold
- [ ] AC meta-comment correctly attributes positives with reviewer IDs
- [ ] No unanswered concerns (including minor writing issues)
- [ ] Tone is direct, not apologetic, no hedging
- [ ] Character count estimated per reviewer block
- [ ] Tables presented in both code-block and markdown form

---

## Reference Files

- `references/style-guide.md` — sentence-level rules, hedge words to eliminate, formatting conventions
- `references/example-patterns.md` — anonymized argument shape templates from past rebuttals
- `references/phrase-bank.md` — ready-to-adapt phrases for every common rebuttal move
