# Presenting Conference Talks

Generates conference presentation slides in Beamer LaTeX PDF and editable PPTX formats from research papers, complete with speaker notes and optional talk scripts.

## Talk Types

| Type | Slides | Duration |
|------|--------|----------|
| Poster-talk | 5–8 | 3–5 min |
| Spotlight | 8–12 | 5–8 min |
| Oral | 15–22 | 15–20 min |
| Invited | 25–40 | 30–45 min |

## Output Formats

- **Beamer LaTeX** — professional typesetting, math support, version control friendly
- **PPTX (python-pptx)** — easy last-minute edits, corporate template compatibility, animations

## Workflow

1. **Content Extraction** — Review paper; identify thesis, contributions, and key figures
2. **Outline Generation** — Select appropriate template structure and allocate time per slide
3. **Slide-by-Slide Creation** — Generate Beamer source with speaker notes and figures
4. **Polish & Review** — Verify timing, readability, and transitions

## Oral Presentation Structure (15–22 slides)

1. Title + teaser figure
2. Problem motivation (with concrete numbers)
3. Existing approaches and their limitations
4. Key insight / thesis statement
5. System overview / architecture diagram
6–12. Core technical contributions (one per slide)
13–15. Evaluation setup and key results
16–18. Ablation / microbenchmarks
19–20. Related work (brief)
21–22. Conclusion + future work

## Speaker Notes Approach (Dahlin Framework)

Layered structure at three levels:
- **Talk level**: outline → content → summary
- **Section level**: introduce section → deliver content → recap
- **Slide level**: say what you'll show → show it → reinforce key point

Recommended timing:
- Poster-talk: 30–60 sec/slide
- Spotlight: 30–60 sec/slide
- Oral: 45–75 sec/slide
- Invited: 60–120 sec/slide

## Systems Talk Specifics

- Include recorded demo backups (live demos are unreliable)
- Use progressive reveal animations for architecture walkthroughs
- Include 2–3 annotated evaluation figures with clear takeaways highlighted

## Color Schemes by Venue

| Venue | Suggested Palette |
|-------|------------------|
| USENIX (OSDI/NSDI) | Navy + Orange |
| ACM (SOSP/ASPLOS) | Red + Grey |
| NeurIPS | Purple + Teal |
| ICML | Blue + Green |
