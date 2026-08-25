# Project AROC Visual Identity Guide

*AROC-BRAND-0001 · Revision 0.2 · KE4CON Amateur Radio Operations Center*

*Generated August 25, 2026 · Markdown is the living source of truth.*


---


# 1. Identity & Brand History

*What Project AROC's visual identity communicates, and how it got here.*


## Identity

Project AROC is the KE4CON Amateur Radio Operations Center. Its visual identity should communicate technical competence, reliability, amateur radio heritage, and long-term maintainability.


## Brand History

Milestone 0003A shipped Project AROC's first visual identity on 2026-06-30, drafted in a **ChatGPT** chat session (not Claude) — a navy/blue palette (`#1F4E79` navy, `#2E86C1` blue, plus light-blue/gray/green/orange/purple support colors) and a custom radio-tower logo mark, delivered as hand-produced `.docx`/`.pdf` files with no editable source.

> **DESIGN DECISION 0003A→CC-01** — When Project AROC moved onto the Claude Code documentation pipeline (2026-08-25), the project adopted the **shared KE4CON navy + gold house style** in place of its own draft palette, so every KE4CON project's documents render from the exact same `docs_generators/style.py` and look like one family. This trades a unique AROC look for consistency across the whole KE4CON library — the AROC project name, motto, and station identity (KE4CON) are unchanged; only the color palette, typography, and cover layout changed. The original Rev0.1 identity is preserved for history in `99 Archive/0003A-chatgpt-draft-rev0.1/`.


## What Stayed the Same

- Project name: **Project AROC**
- Expanded name: **Amateur Radio Operations Center**
- Station identity: **KE4CON**
- Motto: *Build with Purpose. Document with Precision. Learn without End.*
- The radio-tower **logo mark** (PNG/SVG in `05 Media/`) — kept for the website and non-document uses; document covers no longer use a raster logo (see Chapter 3, Cover Page Design)


# 2. Color Palette & Typography

*The navy + gold house identity, in full.*


## Color Palette

```
{
  "aroc_navy":   "#1F3A5F",
  "aroc_gold":   "#D9A521",
  "aroc_blue":   "#2E6DA4",
  "aroc_panel":  "#EAF0F6",
  "aroc_ink":    "#222B38",
  "aroc_muted":  "#64748B"
}
```

This is the authoritative copy of `05 Media/Project_AROC_Color_Palette.json`, which is regenerated in place whenever this table changes — the JSON file and this chapter must always agree.


### Mapping from the Rev0.1 draft palette

| Rev0.1 (ChatGPT draft) | Rev0.2 (house style) |
| --- | --- |
| `aroc_navy` #1F4E79 | `aroc_navy` #1F3A5F |
| `aroc_blue` #2E86C1 | `aroc_blue` #2E6DA4 |
| `aroc_light_blue` #D6EAF8 | `aroc_panel` #EAF0F6 |
| `aroc_gray` #F2F4F4 / `aroc_dark_gray` #444444 | `aroc_muted` #64748B / `aroc_ink` #222B38 |
| `aroc_orange` #CA6F1E (design decisions) | `aroc_gold` #D9A521 (marquee rules, cover accents, `important` callouts) |
| `aroc_green` #1E8449 / `aroc_purple` #6C3483 | Retired — the house callout set uses `tip` (green) and `warning` (red) instead; see AROC-STD-0001 Chapter 3 |


## Typography

- Body text: **Segoe UI**, 10.5pt — prioritizes readability over decoration
- Headings: **Segoe UI Semibold**, high contrast, easy to scan
- Technical examples / code: **Consolas** (monospaced)
- Line spacing: 1.15 with spacing after paragraphs


# 3. Cover Page Design & Callout Styles

*How the identity actually renders on the page.*


## Cover Page Design

The standard cover is a full-bleed **navy panel** (`#1F3A5F`) topped and internally divided by a **gold marquee rule** (`#D9A521`). It carries, top to bottom: a small gold kicker (project name), the big white document title, a gold subtitle + revision line, a gold rule, the document kind in white, a muted tagline, and the author/date in white/faint gold-gray at the bottom. Covers are visually consistent across the entire library because every document calls the same `style.cover()` function — no cover is ever hand-built.


## Callout Styles

| Kind | Fill | Border/Label |
| --- | --- | --- |
| `note` | #E7F0FA (pale blue) | #2E6DA4 |
| `important` | #FFF4CC (pale amber) | #E0A800 |
| `tip` | #E8F5E9 (pale green) | #43A047 |
| `warning` | #FDECEA (pale red) | #D9534F |

Usage guidance for these four kinds, and how they map to the old Engineering Note / Design Decision / Future Expansion vocabulary, is in **AROC-STD-0001 Chapter 3**.
