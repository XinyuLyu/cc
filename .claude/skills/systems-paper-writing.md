# Systems Paper Writing: Paragraph-Level Structural Blueprint

Fine-grained structural guidance for writing **10–12 page systems papers** targeting top systems venues: OSDI, SOSP, ASPLOS, NSDI, and EuroSys.

## When to Use

| Scenario | Use This Skill | Use ml-paper-writing Instead |
|----------|---------------|------------------------------|
| Structuring a 12-page OSDI/SOSP paper | ✅ | |
| Page budget and paragraph planning | ✅ | |
| Systems-specific evaluation structure | ✅ | |
| General ML paper writing philosophy | | ✅ |
| Citation verification workflow | | ✅ |
| NeurIPS/ICML/ICLR paper structure | | ✅ |

## 12-Page Blueprint

### Page Allocation

| Section | Pages | Purpose |
|---------|-------|---------|
| Abstract | ~0.25 | 150–250 words, 5-sentence structure |
| S1 Introduction | 1.5–2 | Problem → Gap → Insight → Contributions |
| S2 Background & Motivation | 1–1.5 | Terms + Production observations |
| S3 Design | 3–4 | Architecture + Module details + Alternatives |
| S4 Implementation | 0.5–1 | Prototype details, LOC, key engineering |
| S5 Evaluation | 3–4 | Setup + End-to-end + Microbenchmarks + Scalability |
| S6 Related Work | 1 | Grouped by methodology, explicit comparison |
| S7 Conclusion | 0.5 | 3-sentence summary |

### Abstract (5 sentences)

```
Sentence 1: Problem context and importance
Sentence 2: Gap in existing approaches
Sentence 3: Key insight / thesis ("X is better for Y in environment Z")
Sentence 4: Summary of approach and key results
Sentence 5: Broader impact or availability
```

### S1 Introduction (1.5–2 pages)

1. **Problem statement** (~0.5p) — Domain + why it matters, concrete numbers
2. **Gap analysis** (~0.5p) — Enumerate gaps G1–Gn, one sentence each with evidence
3. **Key insight** (1 para) — Thesis: "X is better for applications Y running in environment Z"
4. **Contributions** (~0.5p) — Numbered list of 3–5 concrete, testable contributions mapped to sections

### S2 Background & Motivation (1–1.5 pages)

1. **Technical background** (~0.5p) — Define terms (define-before-use)
2. **Production observations** (~0.5–1p) — O1, O2, O3 from real data, each leading to a design insight

### S3 Design (3–4 pages)

1. **Architecture overview** (~0.5p) — Architecture diagram first, one-paragraph walkthrough
2. **Module-by-module** (~2–2.5p) — Per module: what it does, design choice, alternatives considered, why this wins
3. **Design alternatives** (~0.5–1p) — Explicit discussion of rejected alternatives

### S4 Implementation (0.5–1 page)

1. Prototype: language, framework, LOC, integration
2. Key engineering decisions (non-obvious choices)

### S5 Evaluation (3–4 pages)

1. **Setup** (~0.5p) — Hardware, baselines, workloads, metrics (reproducible)
2. **End-to-end** (~1–1.5p) — X vs baselines for Y on Z
3. **Ablation** (~1–1.5p) — Isolate each design decision's contribution
4. **Scalability** (~0.5p) — Behavior as problem/cluster size increases

**Critical rule**: State every experimental conclusion **three times**:
- Section opening: hypothesis
- Section closing: conclusion with numbers
- Figure caption: evidence

### S6 Related Work (1 page)

- Group by methodology/approach, not individual papers
- Per group: what they do → limitation → how your work differs
- Use comparison table when comparing 4+ systems

### S7 Conclusion (3 sentences)

1. The hypothesis / problem addressed
2. The solution approach
3. The key result

## Writing Patterns

### Pattern 1: Gap Analysis (Lucid, ASPLOS'23)
Enumerate gaps G1–Gn in Introduction → map to answers A1–An in Design.

### Pattern 2: Observation-Driven (GFS)
Present O1–O3 in Motivation → derive design insights → build system around insights.

### Pattern 3: Contribution List (Blox, EuroSys'24)
Numbered contributions in Introduction, each mapping to a section.

### Pattern 4: Thesis Formula (Irene Zhang)
"X is better for applications Y running in environment Z." Introduction states it, Design explains how, Evaluation proves it.

## Conference Limits (2025/2026 CFPs — verify annually)

| Venue | Submission | Camera-Ready | References |
|-------|-----------|--------------|------------|
| OSDI | 12 pages | 14 pages | Unlimited |
| NSDI | 12 pages | 14 pages | Unlimited |
| SOSP | 12 pages | — | Unlimited |
| ASPLOS | 11 pages | 13 pages | Unlimited |
| EuroSys | 12 pages | — | Unlimited |

## Quick Checklist

- [ ] Thesis follows "X better for Y in Z" formula
- [ ] Introduction has numbered contributions (3–5)
- [ ] Each contribution maps to a section
- [ ] Design discusses alternatives for every major choice
- [ ] Every eval conclusion stated 3 times
- [ ] Related work grouped by methodology
- [ ] Page budget within venue limits
- [ ] All citations verified (no hallucinated references)

## Academic Integrity

- **Never generate citations from memory** — use ml-paper-writing's citation verification workflow
- Do NOT fabricate observations, results, or venue rules
- Do NOT copy paragraph-level text from reference papers
- Check each venue's AI disclosure policy in the current CFP
- Verify all venue information against the current year's CFP
