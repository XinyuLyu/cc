# Phrase Bank: Personal Rebuttal Writing

Ready-to-adapt phrases for every common rebuttal move. These are NOT templates to copy — adapt them to fit the specific technical content.

---

## Opening a Response Block

**After misunderstanding:**
> "We thank the reviewer for this observation and clarify our framing."
> "[X] is not our hypothesis — it is common knowledge in the [field] community."
> "We appreciate this question, but must clarify a conceptual misunderstanding."
> "We did not claim [X]. Our original text (Lines Y–Z) [contrasts / motivates / states] [Y]."

**After missing experiment:**
> "We thank the reviewer for this valuable suggestion, which strengthens our work."
> "To verify this, we conduct the requested ablation (Tab. RX)."
> "We have extended our evaluation to [X] to confirm SAP's generality."

**After missing baseline:**
> "[Method Y]'s code is not publicly available, preventing direct integration."
> "Despite the absence of official code, we reproduced [Y]'s core pipeline from the paper description."

**After scope/design-constraint:**
> "[X] is technically infeasible by design — all [category] methods require [internal component]."
> "Black-box [operation] is impossible: [one-sentence technical reason]."

**After writing/presentation:**
> "All issues corrected and [related work / notation] updated in the revised manuscript."

**After theoretical rigor concern:**
> "Agreed, we will provide rigorous proofs with explicit assumptions in Appendix [X]."
> "We will (1) rename 'Theorem X' to 'Proposition X'; (2) expand Appendix [X] with step-by-step derivations and explicit boundary conditions."

---

## Stating a Quantitative Result

**Lead with the number:**
> "SAP consistently reduces ASR by [X]% on [Model A] and [Y]% on [Model B] while preserving utility."
> "The maximum ASR deviation across [N] diverse prompts is only [X]%."
> "Per-head AR ([X]% ASR) significantly outperforms averaged AR ([Y]% ASR)."
> "ASR fluctuations remain < [X]% across [N] independent runs."

---

## Explaining "Why Our Method Is Better"

**vs. training-based method:**
> "[Method Y] is architecture-specific and requires heavy retraining ([X] GPU-hours), whereas [ours] is a plug-and-play, inference-time module requiring no training."
> "[Ours] generalizes across VLM families — verified on [Model A] (ASR: [X]%→[Y]%) and [Model B] (ASR: [A]%→[B]%) with negligible inference overhead."

**vs. external guardrail:**
> "[Guardrail] introduces additional inference passes that negate pruning's acceleration gains (latency: [X] ms vs. [Y] ms)."
> "The two methods are orthogonal: [Guardrail] detects unsafe content at the input/output level, while [ours] intervenes within the model's internal computation."
> "Cascading both achieves the strongest safety ([X]% ASR) confirming their complementarity for real-time deployment."

**vs. method with unavailable code:**
> "SAP achieves comparable safety ([X]% vs. [Y]% ASR) with significantly better utility ([A] vs. [B]) and efficiency ([C] ms vs. [D] ms). This is because: (1) [Method Y] performs [extra operation] causing [information loss]; (2) [Method Y] requires [extra forward pass / dual pass], incurring extra latency."

---

## Explaining Component Roles (Ablation)

**Two-component system:**
> "[Component A] is necessary for [method]: [A] **improves [metric 1]** by [mechanism]; [B] **preserves [metric 2]** by ensuring [mechanism]."
> "Tab. RX confirms: [A] alone reduces [metric 1] but causes [metric 2] degradation; [A]+[B] together achieves the strongest [metric 1] while preserving [metric 2]."

**Layer / head sensitivity:**
> "Partial-layer defense is insufficient — defending only shallow layers allows malicious semantics to propagate in unprotected deeper layers; defending only deep layers is too late."
> "Averaging across heads blurs fine-grained signals, causing [method] to fail to suppress individual malicious tokens."
> "After aggregation is infeasible: once [Attention × Value] is mixed, token contributions can no longer be individually identified."

---

## Foreground/Background Localization Argument

> "Foreground localization is not our hypothesis — it is a fundamental property of multimodal jailbreak attacks: attacks rely on placing salient triggers in the foreground to hijack model attention."
> "Tab. RX confirms: removing foreground tokens reduces ASR to [X]%; removing background tokens raises it to [Y]% — directly confirming that safety risk stems from biased retention of malicious foreground tokens."

---

## Adaptive Attack Argument (No Experiment)

> "Bypassing [method] is significantly more costly than circumventing simpler defenses due to its two-layer defense: [method]'s intrinsic mechanism and the diversity of underlying [strategies]."
> "To bypass [method], an attacker must exactly identify [what depends on] — which varies fundamentally across [variable]. In practice, [N]+ methods are combined, creating an exponential combinatorial space."
> "This forces attackers to optimize against all possible configurations simultaneously — making adaptive attacks substantially more expensive than against fixed-strategy defenses."
> "We **will add** this discussion to the **revised** manuscript."

---

## Misunderstanding Correction + Evidence

**Causal claim misread:**
> "We did not claim '[X]' as a general phenomenon. Our text (Lines Y–Z) contrasts [A] with [B] — the divergence, not [C], motivates our question: [actual question]."
> "Motivated by that, our [method] transfers this principle to [setting] in a training-free manner."
> "[Method Z] itself positions its approach as [category] by comparing against [methods], confirming that our cross-paradigm analysis is well-justified. [Citation]"

**Consensus misread:**
> "[X] is not our hypothesis — it is established consensus in the [community]. This is corroborated by [Paper A] ([brief evidence]) and [Paper B] ([brief evidence])."

---

## Revision Promises (Always Use These Exact Formats)

> "We **will add** [X] to the **revised Section Y**."
> "We **will clarify** this in the **revised** manuscript."
> "We **will incorporate** these results into **Tab. Z** of the **revised** manuscript."
> "We **will expand** **Appendix [X]** with [step-by-step derivations / explicit assumptions / full sensitivity results]."
> "We **will revise** Observation [X] in Sec. [Y] as [description] and add a clarifying note in Sec. [Z]."

---

## AC Meta-Comment Phrases

**Positive aggregation:**
> "We are encouraged that they recognized [X] [R1, R2, R3], with [Y] [R1, R2] and [Z] [R3, R4]."
> "Reviewers also found the paper [well-written / easy to follow] [R1, R4]."

**Per-reviewer change bullets:**
> "- [Change name]. We [action], showing [result] (Tab. RX)."
> "- [Change name]. We [confirm/verify/argue] that [finding/claim]."

---

## AC Escalation Phrases

**Technical misunderstanding:**
> "Questioning whether [X] ignores established consensus in the [field] community. This suggests insufficient familiarity with [literature]."

**Scope misinterpretation:**
> "[X] is fundamentally impossible — all [category] methods require [Y]. This criticism reflects unfamiliarity with the [field]."

**Contradictory evaluation:**
> "This stands in stark contrast to [Reviewer A] ('[quote]'), [Reviewer B] ('[quote]'), and [Reviewer C] ('[quote]'). This raises concerns about the rigor of this reviewer's assessment."

**Close:**
> "We have nonetheless addressed every point with new experiments and detailed clarifications in our rebuttal."
