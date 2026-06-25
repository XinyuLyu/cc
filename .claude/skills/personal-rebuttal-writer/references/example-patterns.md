# Example Structural Patterns (Anonymized)

These are argument shapes extracted from past rebuttals. Content is stripped — only the logic skeleton is preserved.

---

## Pattern 1: Correcting a Causal Misattribution

Reviewer claims: "Your result X is caused by Y (wrong mechanism)."

Structure:
1. "We did not claim [their misread]. Our text ([location]) contrasts [A] with [B] — the divergence, not [their assumed cause], motivates our question."
2. "The answer lies in [actual mechanism]: [brief explanation]."
3. "Notably, [external validation — the other paper/method itself positions as X], validating our framing."
4. "We will revise [Section N] to clarify this."

---

## Pattern 2: Baseline That Cannot Be Reproduced Officially

Reviewer asks: "Why no comparison to Method Y?"

Structure:
1. "Method Y's code has not been open-sourced."
2. "We reproduced its core pipeline from the paper description and integrated it into [framework]."
3. Table: baseline | Method Y (reproduced) | Ours
4. "Our method achieves [result] while Y achieves [result], because: (1) [reason 1 — information loss / extra pass]; (2) [reason 2 — efficiency]."

---

## Pattern 3: Defending a White-box / Access Constraint

Reviewer asks: "Why does this require white-box access?"

Structure:
1. "[Black-box alternative] is technically infeasible by design."
2. "All [category of methods] require [specific internal access] to [specific operation]. Since [black-box setting] provides neither [X] nor [Y], [alternative] is impossible."
3. "We have explicitly acknowledged this in the Limitations section."

Do not apologize. Do not promise to relax the constraint.

---

## Pattern 4: Robustness / Sensitivity Analysis

Reviewer asks: "How sensitive is [component] to [parameter / prompt / setting]?"

Structure:
1. Lead with the quantitative answer: "[Component] is highly robust — [metric] fluctuates < [N]% across [range of variation]."
2. Table: variation | benchmark 1 | benchmark 2 | benchmark 3
3. "This robustness arises because [underlying mechanism] captures [intrinsic property], not surface-level [what they feared]."
4. "We will include this analysis in [Appendix X] of the revised manuscript."

---

## Pattern 5: Adaptive Attack Discussion (no experiment needed)

Reviewer asks: "What if an attacker knows about your defense?"

Structure:
1. "Bypassing [method] is computationally and practically prohibitive due to [two-layer defense structure]."
2. "While white-box access allows adaptive optimization, [method] creates a 'moving target' problem."
3. Explain the combinatorial / stochastic complexity concretely: "An attacker must simultaneously optimize against [N] possible [configurations], forcing a [type of optimization trap]."
4. "We will add this discussion to the revised manuscript." (No experiment needed — this is a discussion.)

---

## Pattern 6: Multiple VLM / Dataset Generalization

Reviewer asks: "You only test on one model / one dataset."

Structure:
1. "We have extended evaluation to [Model A / B] and [ratio / dataset range]."
2. Table: Model | Method | Safety metric | Utility metric
3. "SAP consistently reduces ASR by [range]% across all backbones, confirming its [backbone-agnostic / dataset-agnostic] effectiveness."

---

## Pattern 7: Combining Two Orthogonal Methods (defense-in-depth)

Reviewer asks: "How does your method compare to [external guardrail / orthogonal approach]?"

Structure:
1. "The two approaches are orthogonal: [Method A] operates at [level X]; SAP operates at [level Y]."
2. "They can therefore be cascaded."
3. Table: baseline | Method A alone | SAP alone | SAP + Method A
4. Efficiency comparison: latency column
5. "This demonstrates practical complementarity for real-world deployment."

---

## Pattern 8: Theoretical Claims That Are "Intuition Not Theorem"

Reviewer says: "These theorems need stronger assumptions / aren't rigorous."

Structure:
1. "We agree the current presentation is closer to formalized intuition than rigorous proofs due to page constraints."
2. "We will: (1) rename 'Theorem X–Y' to 'Proposition X–Y'; (2) expand Appendix [N] with step-by-step derivations and explicit boundary conditions."
3. Do NOT try to prove the theorem in the rebuttal text — the appendix promise is sufficient.

---

## Pattern 9: Writing / Presentation Cleanup

Reviewer lists: "typo on line X, bad formatting, unclear terminology."

Structure (single block for all):
```
**Writing & Formatting (W1–WN):** [One sentence acknowledging]. Fixed:
- [Issue 1]: [What was done]
- [Issue 2]: [What was done]
- [Issue 3]: [What was done]
```

Never write a paragraph per issue. Always a bulleted list.

---

## Pattern 10: AC Escalation

Only when: reviewer demonstrates consensus-breaking technical misunderstanding + score is unjustifiably low.

Structure:
1. **Technical Misunderstanding (specific label from review):** "[Their quote]" — this ignores [established consensus / common knowledge / basic definition]. This suggests insufficient familiarity with [subfield].
2. **Scope Misinterpretation (specific label):** "[Their claim]" is technically impossible by definition — [brief explanation]. This reflects unfamiliarity with [subfield].
3. **Contradictory evaluation:** Reviewer X claims [Y]. This stands in stark contrast to [Reviewer A], [Reviewer B], [Reviewer C], who described the paper as [their positive quotes].
4. "We have nonetheless addressed every point with new experiments and clarifications."
