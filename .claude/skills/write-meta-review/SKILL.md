---
name: write-meta-review
description: "Draft, revise, or critique conference Area Chair meta-reviews from reviewer opinions containing comments, scores/recommendations, and confidence, plus the authors' rebuttal/response; when a paper abstract is provided, start with a one-sentence contribution summary. Use when the user asks how to write a meta-review, needs an accept/reject recommendation rationale, wants templates for unanimous or split reviews, or asks whether experimental weakness, novelty, missing SOTA baselines, unresolved major concerns, or reviewer disagreement justify rejection."
---

# Write Meta Review

## Core Standard

Write meta-reviews as evidence-weighted AC judgments, not vote counts. Base the recommendation on the two required inputs: reviewer opinions and the authors' rebuttal. Use reviewer scores and confidence as context, but prioritize the substance of the reviewer arguments and whether the rebuttal resolves central concerns. When post-rebuttal final ratings are incomplete, do not infer consensus from the final/current rating list alone.

Default to conference-ready English unless the user asks for another language. Keep the meta-review concise by default: normally 1 short paragraph, or about 50-100 words. Use impersonal language: "The AC", "The ACs", "the reviewers", "the authors"; avoid "I" and "you".

Use a plain AC style, not polished AI-sounding prose. Prefer direct phrases such as "Initially, this paper was reviewed by...", "The paper was reviewed by five reviewers...", "Some major concerns were raised, including...", "The authors provided a rebuttal; however...", "After the rebuttal...", "Specifically, reviewer X stated...", "the rebuttal did not provide a convincing explanation for...", "the results still lack comparison with...", and "Therefore, the AC suggests rejection/acceptance." Avoid stiff abstractions such as "the central empirical claim requires stronger alignment between the stated objective, evaluation metric, and baseline comparisons" when a concrete sentence about the unresolved concern is possible.

For reject recommendations, be direct. Do not include generic positive framing such as "the topic is important", "the paper is relevant", or "the idea is interesting" unless that positive point is necessary to explain a split decision. Focus on the decisive rejection reasons and the rebuttal status.

For easy reject cases, be ultra-compact. If all reviewer recommendations are negative, or if the authors did not submit a rebuttal and the reviews are already negative or mostly negative, do not enumerate detailed technical concerns. State the negative reviewer consensus, state that no rebuttal was provided or concerns remain unaddressed, and recommend rejection.

When mentioning reviewer recommendations, list them individually in reviewer order. Do not aggregate repeated ratings as "three Weak Rejects" or "two Accepts". Prefer "the reviewer recommendations were Borderline, Weak Reject, Weak Reject, and Weak Reject" or "R1: Borderline; R2: Weak Reject; R3: Weak Reject; R4: Weak Reject".

Treat `Final Rating` as reviewer update evidence, not as a vote-count shortcut. If a reviewer does not provide a final rating, keep that reviewer's original concerns active unless the rebuttal clearly resolves them. If some reviewers raise scores but another reviewer has convincing central concerns that remain unresolved, the final recommendation can still be rejection.

When the user provides an abstract, start the meta-review with one concise sentence summarizing the paper's contribution. Derive this sentence only from the abstract or paper summary provided by the user. Do not invent a contribution when no abstract or paper summary is provided, and do not ask for an abstract if the decision can already be drafted. Prefer the form "This paper [investigates/proposes/introduces/studies] [problem/method/contribution]."

Ratings-only easy cases are allowed. If the user provides only the reviewer scores/recommendations and they are all positive or all negative, do not ask for full reviewer comments. Use the appropriate unanimous template directly. If the user also says there was no rebuttal, use the no-rebuttal variant.

Follow the user's preferred template logic. True mixed-rating cases should explicitly compare positive and negative comments, state how the rebuttal changed each side, identify which reviewer concerns or positive arguments are decisive, and apply CT-specific standards. Mention AC triplet discussion only if discussion information is provided or the user asks for an internal process note. Unanimous and one-sided borderline cases should follow reviewer consensus and use a shorter template.

## Input Contract

Expect two required inputs from the user, plus an optional abstract when available:

1. **Reviewer opinions**: reviewer comments, concrete positive/negative points, scores or accept/reject recommendations, and reviewer confidence. Paper title, paper ID, declared CT, and post-rebuttal reviewer updates may be included here if available, but are not separate required inputs. For unanimous easy cases, this input may be only reviewer scores/recommendations.
2. **Author rebuttal/response**: the authors' response to reviewer concerns. If there is no response, the input should explicitly say "no rebuttal" or equivalent.

Optional **abstract or paper summary** may be provided before, after, or inside the reviewer-opinion input. Use it only to write the one-sentence contribution summary as the first sentence of the meta-review. Treat the abstract as supporting material, not as a third required input.

Do not ask for a third required input. Do not invent reviewer positions, rebuttal content, discussion outcomes, AC triplet outcomes, SAC input, paper metadata, or CT. If a useful field is missing, either proceed with a neutral phrase such as "based on the provided reviews" or use a placeholder.

Do not ask for detailed comments when ratings alone are sufficient for a unanimous or one-sided borderline template. Ask for reviewer comments only when ratings are truly mixed, the decision is unclear, or the user wants a substantive hard-case rationale.

When parsing the reviewer opinions, extract:

- Each reviewer's score/recommendation and confidence.
- The paper's main contribution from any provided abstract or paper summary: problem, method/system/dataset/theory contribution, and claimed evidence. Compress this into one sentence for the meta-review.
- Each reviewer's initial `Rating` and, if present, post-rebuttal `Final Rating`.
- If a review includes `Final Rating` after rebuttal, treat that as the reviewer's current recommendation when reporting that reviewer's stance. Still base the final AC decision on whether the rebuttal resolves the central concerns.
- Track score changes explicitly: which reviewers raised, lowered, or kept their scores, and which reviewers did not provide final ratings.
- If a `Final Rating` is followed by a `Justification`, use that justification as high-priority evidence for the AC's own assessment. Integrate its substance into the AC judgment without explicitly saying "the final Weak Reject reviewer maintained..." or making the AC appear to defer to one reviewer.
- If a reviewer does not provide a final rating, do not assume the reviewer was satisfied by the rebuttal. Preserve that reviewer's major concerns as unresolved unless the rebuttal directly and convincingly addresses them.
- If final-stage comments say concerns were addressed, mostly resolved, partially resolved, or unresolved, report this explicitly by reviewer ID when helpful.
- Preserve reviewer-order recommendation labels for the meta-review.
- Shared strengths and reviewer-specific strengths.
- Shared weaknesses and reviewer-specific major concerns.
- Whether reviews are unanimous, one-sided borderline, or true mixed.
- Whether high-confidence reviews support or oppose the paper, without treating confidence as decisive by itself.

When parsing the rebuttal, determine whether it:

- Resolves the central concern.
- Partially addresses but leaves the concern material.
- Clarifies a minor issue only.
- Fails to address the main concern.
- Promises future work without current evidence.

Preferred rebuttal language:

- "Initially, the reviewer ratings were [initial ratings]."
- "After the rebuttal, [reviewer IDs] provided final ratings, while [reviewer IDs] did not provide final ratings."
- "After the rebuttal, two reviewers did not provide final ratings, while three reviewers provided final ratings."
- "Specifically, reviewer [ID] raised his/her score from [initial] to [final] because [short reason]."
- "Specifically, reviewer [ID] claimed that his/her major concerns were addressed, and reviewer [ID] claimed that his/her concerns were mostly resolved."
- "Reviewer [ID] kept his/her score and stated that [concern] remained unresolved."
- "Reviewer [ID] stated that his/her concerns were addressed/mostly resolved/partially resolved."
- "After the rebuttal, R[ ]'s concerns were fully resolved."
- "After the rebuttal, R[ ]'s concerns were partially resolved."
- "The rebuttal clarifies [point], but [concern] remains insufficiently addressed."
- "[Concern from Final Rating Justification] remains unresolved after rebuttal."
- "R[ ] did not provide a final recommendation."
- "After the rebuttal, [concern] remains insufficiently addressed."

## Decision Workflow

1. Identify the case type.
   - Unanimous accept or unanimous reject: follow reviewer consensus after a sanity check. Ratings-only input is sufficient for this case.
   - All-negative, or mostly-negative with no rebuttal: use the ultra-compact easy-reject template; do not list detailed concerns.
   - Borderline plus negative ratings only: treat as a negative-leaning case, not mixed. Use an easy or compact rejection template depending on rebuttal/comments.
   - Borderline plus positive ratings only: treat as a positive-leaning case, not mixed. Use an easy or compact acceptance template depending on rebuttal/comments.
   - True mixed ratings: only when explicit positive and explicit negative recommendations both appear. Reconcile arguments, not ratings. Use the mixed-case structure below.
   - Post-rebuttal incomplete ratings: if only some reviewers provide final ratings, do not reclassify the case as positive-leaning solely because several final/current ratings are positive. Preserve the original disagreement and decide whether the rebuttal resolves the most convincing negative concerns.
   - Against majority: explicitly justify why the central argument outweighs the number of positive or negative recommendations.

2. Check CT-specific criteria.
   - Algorithms / General: missing relevant SOTA baselines, inadequate ablations, unsupported methodological claims, or insufficient novelty can be central.
   - Applied / Systems: limited algorithmic novelty may be acceptable if the system contribution, deployment/evaluation, reliability, and practical impact are strong.
   - Datasets / Benchmarks: prioritize data quality, benchmark design, reproducibility, release/access plan, licensing, documentation, ethics/privacy, and community value. A non-novel baseline model is often secondary.
   - Concept & Feasibility: do not require full SOTA benchmarking or deployment by default. Require coherent originality, realistic feasibility evidence, and claims proportional to evidence.
   - Theory / Foundational: do not reject for lack of experiments alone. Focus on proof soundness, assumptions, formal claims, and theoretical contribution.

3. Evaluate rebuttal impact.
   - State if there was no rebuttal.
   - Say whether the rebuttal removed, narrowed, partially addressed, or failed to resolve the central concern.
   - If reviewers provide `Final Rating` and post-rebuttal `Justification`, state who provided final ratings, who did not, and whether the final comments say concerns were addressed, mostly resolved, partially resolved, or unresolved. Use these statements as evidence for the AC's own assessment of rebuttal impact, but do not simply defer to one reviewer.
   - If a reviewer does not provide a final rating, keep their original major concerns in the AC assessment unless the rebuttal clearly answers them.
   - If positive final-rating updates coexist with an unresolved central concern from another reviewer, explicitly say that the AC checked all comments and the rebuttal and found that the unresolved concern remains convincing.
   - Do not treat promises of future work as resolved evidence unless the venue permits and the issue is minor.

4. Use reviewer discussion for hard cases.
   - If the reviewer opinions include post-rebuttal reviewer updates or discussion outcomes, summarize the substantive outcome.
   - If reviewers strongly disagree and no discussion outcome is provided, do not claim that discussion occurred. Add an internal action note that reviewer discussion and AC triplet discussion are needed before finalizing.
   - If a draft recommendation goes against the reviewer majority and no triplet/SAC information is provided, label it as a draft rationale and recommend AC triplet/SAC clearance.

5. Write the final recommendation.
   - Accept/reject based on the merits of the submission, not batch ranking, acceptance quota, score averages, or "excitement" alone.
   - Do not accept a mixed case merely because final/current ratings have a positive majority. Accept only when the rebuttal satisfactorily resolves central negative concerns or makes them non-rejection-level.
   - For easy rejection, do not name detailed rejection reasons. For hard rejection, briefly name only the main rejection reasons and acknowledge the rebuttal. Omit routine strengths and venue-fit statements. Mention discussion only if discussion information is present in the reviewer-opinion input.
   - For acceptance, do not mention poster/oral/award recommendation unless the user explicitly asks for an internal note.

## Preferred Template Logic

Use these patterns to match the user's preferred AC meta-review style.

### Human Template Wording

When comparing against the user's provided human-written templates, follow these wording habits:

- For mixed post-rebuttal cases, use this default five-part order: (1) one sentence on the paper contribution from the abstract, (2) one sentence on initial reviewer ratings and major concerns, (3) one sentence on post-rebuttal final-rating updates and reviewer statements, (4) one or more sentences on the AC's assessment of the rebuttal and the most convincing remaining concerns, and (5) one final recommendation sentence.
- Prefer "the final recommendation is acceptance/rejection" over "the AC's final recommendation is acceptance/rejection".
- Use "the AC recommends acceptance/rejection" or "the AC suggests rejection" only when the surrounding paragraph naturally uses Area Chair as the subject.
- Prefer "remaining unresolved concerns" or "these issues remain unresolved" over heavier phrases such as "major unresolved concerns" unless the template explicitly uses "major".
- For broad concern lists, use "Several major concerns were raised, including ..., etc." or "Some major concerns were raised, such as ..., etc." Do not over-specify every reviewer point.
- For rebuttal impact, use "The authors provided a rebuttal; however, it only partially addressed the major concerns raised by the reviewers" for rejection, and "The authors provided a detailed rebuttal" for acceptance.
- For acceptance after rebuttal, prefer "most of the major concerns have been satisfactorily resolved" and "The remaining issues are relatively minor and can be adequately addressed in the final camera-ready version."
- When an abstract is provided, start with a plain one-sentence contribution summary such as "This paper investigates [problem] and proposes [method/framework]." This is the first sentence before reviewer ratings and concerns.
- If no reviewer submitted final ratings, write "Although the reviewers did not submit final ratings, the Area Chair carefully examined both the reviewers' comments and the authors' responses."
- If final ratings are present in a split case, explicitly say who provided final ratings and who did not; then mention only the final-stage reviewer statements that matter for the decision.
- In split cases with incomplete final ratings, prefer the logic: "After the rebuttal, [number] reviewers did not provide final ratings, while [number] reviewers provided final ratings. Specifically, reviewer [ID] claimed that his/her major concerns were addressed, and reviewer [ID] claimed that his/her concerns were mostly resolved. Therefore, the AC checked all the comments and the rebuttal and found that the concerns raised by reviewer [ID] were quite convincing."
- For rejection after partial score improvements, use concrete unresolved-rebuttal sentences such as "The rebuttal did not provide a convincing explanation regarding [central concern]" and "[the results / added experiments] still lack [key comparison / evidence / analysis]."
- Avoid unusual or overly polished expressions such as "positive-leaning reviewer assessment", "strengthened rebuttal", "central empirical claim", or "claim-evidence alignment" unless the user uses those words.

When a discussion request is needed, append it after the meta-review exactly in this simple format:

```text
Need Discussion
Please discuss whether the rebuttal sufficiently addresses the above concerns, and submit your final ratings.
```

### Rating Categories

Do not treat every borderline case as mixed.

- **Negative-leaning one-sided borderline**: ratings contain only Borderline/Borderline Reject/Borderline Accept plus negative recommendations such as Weak Reject/Reject. Use rejection-style consensus language.
- **Positive-leaning one-sided borderline**: ratings contain only Borderline/Borderline Reject/Borderline Accept plus positive recommendations such as Weak Accept/Accept. Use acceptance-style consensus language.
- **True mixed**: ratings contain at least one explicit positive recommendation (Weak Accept/Accept) and at least one explicit negative recommendation (Weak Reject/Reject). Use the mixed-rating structure.

For one-sided borderline cases, do not write "The ratings are mixed" and do not automatically mention AC triplet discussion unless the case is genuinely disputed or the provided reviewer discussion says it occurred.

### True Mixed Ratings

For true mixed positive/negative/borderline ratings, write in this order:

1. If an abstract is provided, summarize the paper's contribution in one opening sentence.
2. State the initial reviewer opinions in one sentence: number of reviewers, mixed/consistent ratings, individual ratings in reviewer order, and the main concerns in a compact "Some major concerns were raised, such as ..., etc." clause.
3. State post-rebuttal reviewer updates in one sentence: how many reviewers did not provide final ratings, how many provided final ratings, and which reviewers claimed their concerns were addressed/mostly resolved/partially resolved/unresolved.
4. State the AC's rebuttal assessment in one or two sentences: the AC checked all comments and the rebuttal, identifies the most convincing remaining concern, and explains concretely why the rebuttal did or did not resolve it.
5. State the AC recommendation in one final sentence.
   - If reviewers provide `Final Rating` and `Justification`, integrate the substance of that justification as the AC's post-rebuttal assessment.
   - If final ratings are incomplete or only partially improved, compare the score-improvement statements against the strongest remaining negative review. State when a concern from a reviewer without a positive update remains convincing.
   - State which reviewer concerns or positive arguments are decisive, without using "the AC finds that".
6. Add the CT-specific standard when useful inside the AC assessment sentence:
   - Concept & Feasibility: does not necessarily require large-scale experiments, SOTA results, exhaustive ablations, or deployment; still needs a clear key message, realistic evaluation, and credible alignment between claims and evidence.
   - Applied / Systems: central question is whether the work provides a meaningful, technically sound, and realistically evaluated system contribution; writing and claim-clarity issues can often be fixed in the final version if the system evidence is strong.
   - Algorithms / General: requires solid experiments, fair comparisons with relevant recent methods, adequate ablations, and evidence supporting the claimed technical contribution.
7. Mention AC triplet discussion only if the reviewer-opinion input says discussion occurred or the user asks for an internal process note.

True mixed rejection template:

```text
[If abstract is provided: This paper [contribution sentence from abstract].] Initially, this paper was reviewed by [number] reviewers, with mixed ratings including [R1 initial rating], [R2 initial rating], [R3 initial rating], and [R4 initial rating]. Some major concerns were raised, such as [concern list], etc. After the rebuttal, [number] reviewers did not provide final ratings, while [number] reviewers provided final ratings. Specifically, reviewer [ID] claimed that his/her major concerns were addressed, and reviewer [ID] claimed that his/her concerns were mostly resolved. Therefore, the AC checked all the comments and the rebuttal and found that the concerns raised by reviewer [ID] were quite convincing. The rebuttal did not provide a convincing explanation regarding [decisive concern]. [The added results / rebuttal evidence] still lack [key comparison/evidence/analysis]. Therefore, the AC suggests rejection.
```

True mixed acceptance template:

```text
[If abstract is provided: This paper [contribution sentence from abstract].] Initially, this paper was reviewed by [number] reviewers, with mixed ratings including [R1 initial rating], [R2 initial rating], [R3 initial rating], and [R4 initial rating]. Some major concerns were raised, such as [concern list], etc. After the rebuttal, [number] reviewers did not provide final ratings, while [number] reviewers provided final ratings. Specifically, reviewer [ID] claimed that his/her major concerns were addressed, and reviewer [ID] claimed that his/her concerns were mostly resolved. The AC checked all the comments and the rebuttal and found that most of the major concerns have been satisfactorily resolved. The remaining issues are relatively minor and can be adequately addressed in the final camera-ready version. The final recommendation is acceptance.
```

## Unanimous Template

Use a short version when all reviewers agree.

```text
Declared CT: [CT]. Recommendation: [Accept/Reject].

The reviewers were consistent in their recommendations, and the AC confirmed that the provided reviews assessed the paper under the appropriate [CT] criteria. The main factors supporting the recommendation are [key strengths or weaknesses]. [There was no rebuttal / The rebuttal clarified ... / The rebuttal did not resolve ...]. The recommendation follows the reviewer consensus based on the merits of the submission.
```

For all-negative reviews:

```text
Recommendation: Reject.

[If abstract is provided: This paper [contribution sentence from abstract].] The reviewer recommendations were [R1 final rating], [R2 final rating], [R3 final rating], and [R4 final rating]. [No author rebuttal was provided / The rebuttal did not change the assessment]. Given the reviewer consensus and the absence of a response resolving the concerns, the AC recommends rejection.
```

When full comments are provided and there is a rebuttal, include at most one short sentence naming the main reasons:

```text
[If abstract is provided: This paper [contribution sentence from abstract].] The reviewer recommendations were [R1 final rating], [R2 final rating], [R3 final rating], and [R4 final rating]. The AC confirmed that the reviews assessed the paper under the appropriate [CT] criteria. The main reasons for rejection are [reason 1] and [reason 2]. After the rebuttal, these issues remain unresolved. The recommendation follows the reviewer consensus and is based on the merits of this submission.
```

For all-positive reviews:

```text
Recommendation: Accept.

[If abstract is provided: This paper [contribution sentence from abstract].] The reviewer recommendations were [R1 final rating], [R2 final rating], [R3 final rating], and [R4 final rating]. [No author rebuttal was provided / The rebuttal did not change the assessment]. Given the reviewer consensus, the AC recommends acceptance.
```

When full comments are provided, include one concise sentence on strengths and one on minor concerns/rebuttal:

```text
[If abstract is provided: This paper [contribution sentence from abstract].] The reviewer recommendations were [R1 final rating], [R2 final rating], [R3 final rating], and [R4 final rating]. The AC confirmed that the reviews assessed the paper under the appropriate [CT] criteria. The reviewers noted [main strengths]. After the rebuttal, [concerns were fully resolved / remaining concerns are minor and can be addressed in the final version]. The recommendation follows the reviewer consensus and is based on the merits of this submission. The final recommendation is acceptance.
```

## Split Or Borderline Template

Use the preferred true mixed-rating structure above only when explicit positive and explicit negative recommendations both appear. This older compact structure is acceptable only when the user wants a very short rationale.

```text
Declared CT: [CT]. Recommendation: [Accept/Reject].

The reviewers disagreed. [R1/R2] recommended [acceptance/rejection] because [main arguments]. [R3/R4] recommended [acceptance/rejection] because [main counterarguments]. The decisive consideration is [side/argument] because [CT-specific reason].

The rebuttal [resolved/partially addressed/did not address] the central concern: [specific concern]. [If discussion outcome is included in the reviewer opinions: In the reviewer discussion, [substantive discussion outcome]. This paper was discussed by the AC triplet.] [If evidence is insufficient for a final AC judgment or the user asks for a draft/internal note: Because the reviews are split/borderline, reviewer discussion and AC triplet discussion are recommended before finalizing.] On balance, the decisive factor is [central factor], and therefore the [final/draft] recommendation is [Accept/Reject].
```

## Rejection Patterns

Use rejection only when the unresolved issue is central to the paper's claims and CT. Keep rejection meta-reviews short. For easy reject cases, include only reviewer consensus, rebuttal status, and recommendation. For hard reject cases, include at most 1-2 decisive concerns. Do not list generic strengths before rejecting.

Easy reject template for all-negative or mostly-negative/no-rebuttal cases:

```text
Recommendation: Reject.

[If abstract is provided: This paper [contribution sentence from abstract].] The reviewer recommendations were [R1 rating], [R2 rating], [R3 rating], and [R4 rating]. No author rebuttal was provided, so the reviewers' concerns remain unaddressed. Given the reviewer consensus, the AC recommends rejection.
```

Compact hard-rejection template:

```text
Recommendation: Reject.

The reviews were [split/borderline], but [concern 1] and [concern 2] are decisive for the paper's [claims/empirical validation/technical contribution]. [No rebuttal was provided / The rebuttal did not resolve these concerns]. Therefore, the AC recommends rejection.
```

Missing SOTA baseline or insufficient experiments for Algorithms / General:

```text
The decisive concern is that the main empirical claim is not adequately supported. The comparison omits the most relevant recent baseline, and the ablation does not isolate the claimed contribution. The rebuttal did not provide evidence that the omitted baseline is inapplicable or that the reported gains come from the proposed component. Because the central methodological claim needs adequate empirical support against relevant baselines, the recommendation is Reject.
```

Novelty concern:

```text
Limited novelty is decisive here because the paper is framed as an [CT] contribution, and the claimed contribution is close to prior work. The rebuttal did not sufficiently distinguish the method from relevant baselines or prior formulations. Therefore, the AC recommends rejection.
```

Major concern not addressed:

```text
The rebuttal clarified some points but did not resolve the main concern: [concern]. As a result, the central claim remains stronger than the evidence supports. The recommendation is Reject because the paper, as written, has a mismatch between claims and evidence.
```

Against positive majority:

```text
Although the reviewer recommendations were mostly positive, the negative concern is more central to the declared [CT]. The decisive factor is the strength of the technical argument, not the number of positive ratings. Since [central claim] remains insufficiently supported, the draft recommendation is Reject. Because this goes against the reviewer majority, AC triplet/SAC clearance should be obtained before finalizing unless such clearance is already included in the provided reviewer opinions.
```

## Acceptance Patterns

Use acceptance when the remaining weaknesses are secondary under the declared CT and the rebuttal does not reveal unresolved major concerns. In mixed cases with incomplete final ratings, accept only when the rebuttal directly resolves the strongest negative concerns or makes them clearly non-rejection-level; do not rely on improved scores alone.

```text
The positive arguments are more compelling. For [CT] papers, the central question is whether [CT-specific standard]. The remaining weakness, [weakness], is valid but not decisive because [reason]. The rebuttal clarified [issue] and did not reveal any remaining major concern. The recommendation is Accept.
```

## What To Avoid

- Do not decide by average score, score threshold, majority vote, or batch ranking.
- Do not decide by a final/current rating majority when final ratings are incomplete; unresolved central concerns can outweigh several positive or improved ratings.
- Do not request full reviewer comments for unanimous ratings-only cases unless the user asks for a detailed rationale.
- Do not treat reviewer confidence as a substitute for argument quality.
- Do not ignore `Final Rating` or its `Justification`; these are high-priority evidence for the post-rebuttal assessment and should override/supplement the initial review.
- Do not omit score-change information in mixed cases when final ratings are present. State which reviewers gave final ratings and which did not.
- Do not treat missing final ratings as acceptance, satisfaction, or silence in favor of the rebuttal.
- Do not hide final-stage reviewer statements about whether concerns were resolved. If reviewer IDs are available, name them briefly.
- Do not write as if the AC is merely reporting one reviewer's final judgment, e.g. avoid "the final Weak Reject reviewer maintained..." Integrate that reasoning into the decision rationale.
- Do not use first-person phrases or self-announcing judgment phrases such as "I find that..." or "the AC finds that...". State the decisive issue directly, e.g. "[concern] remains insufficiently addressed" or "the positive arguments are more compelling because...".
- Do not use unnatural meta-review filler such as "the central empirical claim needs clearer alignment" when concrete reviewer concerns can be stated directly.
- Do not aggregate reviewer ratings into counts such as "three Weak Rejects"; list each reviewer's rating separately.
- Do not invent a paper contribution summary from reviewer comments alone when no abstract, paper summary, or title-level contribution is provided.
- Do not classify Borderline + only negative ratings, or Borderline + only positive ratings, as mixed.
- Do not end true mixed cases without saying whether the final recommendation is acceptance or rejection.
- Do not write "remaining concerns are minor" unless the rebuttal actually resolves or downgrades the strongest negative concerns.
- Do not include routine positive statements in rejection meta-reviews, such as topic importance, venue fit, or a generally interesting idea, unless needed to explain why positive reviews are outweighed.
- Do not enumerate detailed technical concerns in easy reject cases where reviewers are all negative or mostly negative and there is no rebuttal.
- Do not make the meta-review long by summarizing every reviewer. Merge repeated concerns and keep only decisive points when a hard case requires explanation.
- Do not say the conference needs more or fewer papers of a type.
- Do not mention poster/oral/award status in a normal accept meta-review.
- Do not reject a paper under the wrong CT criteria, such as rejecting Theory for no SOTA experiments or Concept & Feasibility for no full deployment.
- Do not write generic statements like "the reviewers did not like it" without explaining which arguments mattered.
- Do not claim reviewer discussion, AC triplet discussion, or SAC clearance occurred unless that is included in the reviewer-opinion input.
- Do not append a `Need Discussion` request when the user asks for a final meta-review and the AC recommendation can be made from the provided reviews and rebuttal.
- Do not include unsupported claims about author intent, ethics, or misconduct.

## Output Checklist

Before finalizing, ensure the meta-review:

- Names the declared CT if available.
- States the recommendation clearly.
- Lists reviewer ratings individually when ratings are mentioned, rather than aggregating repeated ratings.
- If an abstract or paper summary is provided, starts with one concise contribution sentence before reviewer ratings and concerns.
- Uses `Final Rating` to report the reviewer's current stance whenever available, while still grounding the AC decision in resolved or unresolved concerns.
- In mixed or disputed cases with final ratings, states the initial ratings, which reviewers provided final ratings, which reviewers did not, and any score changes.
- In mixed or disputed cases with incomplete final ratings, keeps concerns from reviewers without final ratings active unless the rebuttal convincingly resolves them.
- Mentions final-stage statements that concerns were addressed, mostly resolved, partially resolved, or unresolved when such statements are provided.
- Reflects the substance of the `Justification` following `Final Rating` when explaining rebuttal impact or remaining concerns, phrased as the AC's own assessment rather than direct deference to one reviewer.
- Uses ratings-only unanimous templates when the user provides only all-positive or all-negative ratings.
- Keeps the output concise, normally 1 short paragraph unless the user asks for more detail.
- Treats Borderline + only negative ratings as negative-leaning, and Borderline + only positive ratings as positive-leaning.
- Summarizes the strongest positive and negative arguments for true mixed cases.
- For easy reject decisions, avoids detailed concern lists and simply states consensus, rebuttal status, and recommendation.
- For hard reject decisions, omits generic strengths and focuses only on decisive unresolved concerns.
- Explains how rebuttal changed or did not change the assessment.
- For true mixed cases, states which reviewer concerns or positive arguments are decisive, without using "I find that" or "the AC finds that".
- For true mixed cases, mentions reviewer discussion or AC triplet discussion only when that information is present or the user asks for an internal process note.
- Uses reviewer scores and confidence as context, while grounding the decision in arguments.
- Summarizes reviewer discussion only if that information is present in the reviewer-opinion input.
- Recommends reviewer discussion or AC triplet/SAC clearance only when evidence is insufficient for a final AC judgment, when the recommendation goes against the reviewer majority, or when the user asks for a draft/internal note.
- Gives a CT-specific reason for the final recommendation.
- Uses objective AC language and avoids first/second person.
- Uses plain AC wording similar to: "Initially...", "After the rebuttal...", "Specifically...", "the rebuttal did not provide a convincing explanation...", "still lacks comparison with...", and "Therefore, the AC suggests...".
