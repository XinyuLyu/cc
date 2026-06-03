---
name: academic-plotting
description: Generate publication-quality figures for ML/AI papers - architecture diagrams and matplotlib/seaborn data charts with venue-specific sizing and colorblind-safe palettes.
---

# Academic Plotting Tool

Specialized tool for researchers creating publication-quality figures for ML/AI conference submissions.

## Core Workflows

**Workflow 1: Diagram Generation** — Use Gemini's image generation to create architecture diagrams, system workflows, and pipeline visualizations from descriptive text. Best for figures with "boxes and arrows."

**Workflow 2: Data Visualization** — Use matplotlib and seaborn to transform experimental results into charts, plots, and heatmaps. Best for figures with numerical axes.

## Key Workflow Features

Start by analyzing provided context (paper section, results table, or conceptual description):
- For diagrams: identify system components and their relationships
- For data figures: categorize metrics and determine optimal visualization types

## Visual Style Options

Choose **one style per paper** to maintain visual coherence:

1. **Hand-Drawn Sketch** — Warm, approachable aesthetic using soft colors and irregular line quality
2. **Modern Minimal** — Clean geometric shapes with bold color blocks and rounded corners
3. **Illustrated Technical** — Icon-rich components with curved connections and annotation badges
4. **Classic Accent Bar** — Traditional academic style with horizontal section bands

## Publication Standards

Venue-specific sizing guidelines for major conferences:
- **NeurIPS, ICML, ICLR**: single column = 3.25in, double column = 6.75in
- **ACL, AAAI**: verify from current CFP

Typography: use serif fonts (Computer Modern, Times) for body text; sans-serif for labels.

Default palette: **"Ocean Dusk"** (colorblind-safe). Always use colorblind-safe palettes.

## Implementation

- Save generation scripts for reproducibility
- For Gemini-based diagrams: generate 3 attempts, select highest quality
- Export as both **PDF** (vector, preferred) and **PNG** (raster)
- Extract exact terminology from source materials; avoid generic decorative elements

## Common Chart Patterns

- Line plots for training curves and time-series metrics
- Bar charts for discrete method comparisons
- Heatmaps for attention weights, correlation matrices
- Scatter plots for embedding space visualization

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Font rendering issues | Use `matplotlib.rcParams['font.family'] = 'serif'` |
| Color visibility in print | Test with grayscale conversion |
| Figure too small in paper | Check venue column width; use `figsize` accordingly |
