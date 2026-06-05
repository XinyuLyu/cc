---
name: ml-paper-writing
description: Write publication-ready ML papers for top venues (NeurIPS, ICML, ICLR, ACL, AAAI, COLM). Use for drafting abstracts, introductions, sections, narrative structure, and verifying citations.
---

# ML Paper Writing Skill Documentation

This is a comprehensive guide for writing publication-ready machine learning papers for top-tier venues like NeurIPS, ICML, ICLR, ACL, AAAI, and COLM.

## Core Philosophy

The skill emphasizes **proactive collaboration**: Claude should deliver complete first drafts rather than waiting for approval on each section. As the documentation states, "Paper writing is collaborative, but Claude should be proactive in delivering drafts."

## Key Principles

**The Narrative Principle** stands central: "Your paper is not a collection of experiments—it's a story with one clear contribution supported by evidence." Papers must crystallize around three pillars:
- What novel claims are made
- What evidence supports them
- Why the community should care

**Citation Integrity** receives paramount attention. The skill warns that "AI-generated citations have a ~40% error rate" and establishes an absolute rule: never generate BibTeX entries from memory. All citations must be programmatically verified through Semantic Scholar, CrossRef, or DOI lookups before inclusion.

## Practical Workflow

The guidance structures paper writing as an iterative process:

1. Explore repository and understand the project
2. Identify existing citations and search for additional literature
3. Deliver a complete first draft proactively
4. Refine through feedback cycles
5. Verify all citations programmatically

## Time Allocation

Following Neel Nanda's framework, writers should spend roughly equal effort on abstracts, introductions, figures, and all remaining content combined—acknowledging that most reviewers form judgments before reaching methods sections.

## Venue-Specific Requirements

Each major conference has distinct page limits (ranging from 7-9 pages), mandatory sections (checklists, limitations, impact statements), and LaTeX templates provided in the skill's directory.

## Abstract Structure (Farquhar)

Achievement → Importance → Approach → Evidence → Key Result

## Narrative Framework (Nanda)

Establish clear:
- **What**: the claims being made
- **Why**: the evidence supporting them
- **So What**: significance to the community

## Reader-First Design (Gopen & Swan)

- Subject-verb proximity
- Stress positions for key information
- Topic placement for continuity
- Action-based verbs

## Critical Safety Rule

**Never cite papers you haven't verified**. If verification fails, mark as `[CITATION NEEDED]` and explicitly inform the researcher.
