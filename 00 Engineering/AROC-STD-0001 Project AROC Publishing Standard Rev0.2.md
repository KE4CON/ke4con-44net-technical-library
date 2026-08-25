# Project AROC Publishing Standard

*AROC-STD-0001 · Revision 0.2 · KE4CON Amateur Radio Operations Center*

*Generated August 25, 2026 · Markdown is the living source of truth.*


---


# 1. Purpose, Scope & Document Structure

*Why Project AROC has a publishing standard, and what every formal document must contain.*


## Purpose and Scope

This standard defines the official publishing system for Project AROC. It exists so every future Project AROC document looks, reads, and behaves like part of one coherent professional engineering library rather than a collection of unrelated files — whether that document is an installation guide, a network diagram set, an operations runbook, or a piece of the technical library (Books 0-10, see the repository `README.md`).

> **ENGINEERING NOTE** — The publishing framework is treated as infrastructure. Just as a Raspberry Pi, a switch, and network cabling support the technical system, this publishing framework supports the documentation system. A consistent document system reduces confusion, makes updates easier, and lets the Project AROC library grow for years without losing organization.


## Standard Document Structure

Every formal Project AROC publication shall use the following structure unless the document type makes a section unnecessary:

- Cover page
- Document control page (owner, author, status, applicability)
- Revision history page
- Table of contents
- Main body, organized into numbered chapters
- Appendices, if applicable
- Glossary, if applicable
- Index, if applicable


## Document Numbering

Every formal document carries a document number in the form `AROC-<TYPE>-<NUMBER>`, where `<TYPE>` identifies the document category and `<NUMBER>` is a 4-digit sequence assigned in order within that category:

| Prefix | Category | Example |
| --- | --- | --- |
| **STD** | Publishing / engineering standards | AROC-STD-0001 |
| **BRAND** | Visual identity / branding references | AROC-BRAND-0001 |
| **REL** | Milestone / release notes | AROC-REL-0003A |
| **BOOK** | Technical library volumes (Books 0-10) | AROC-BOOK-0007 (APRS) |

Full engineering-standards detail — folder structure, revision-control conventions, file naming, and figure/table numbering — lives in **AROC-STD-0002 Engineering Standards** (Chapter 3 of this standard gives the short version that applies to publishing specifically).


## Status Labels

Every document control page carries one of the following statuses:

| Status | Meaning |
| --- | --- |
| **Draft** | In progress; content may still change materially |
| **Final / Approved for Review** | Content-complete and ready to be read; not yet a locked reference |
| **Approved** | Locked as the authoritative version of that revision |
| **Superseded** | Replaced by a later revision; kept for history in `99 Archive` |


# 2. Branding, Typography & Color Palette

*The shared KE4CON visual identity Project AROC documents are built on.*


## Project AROC Branding

Project AROC branding identifies every document as part of the KE4CON Amateur Radio Operations Center library. Branding shall remain consistent across every formal document.

- Project name: **Project AROC**
- Expanded name: **Amateur Radio Operations Center**
- Station identity: **KE4CON**
- Motto: *Build with Purpose. Document with Precision. Learn without End.*
- Primary visual theme: professional engineering, amateur radio, network infrastructure, long-term maintainability

> **DESIGN DECISION — HOUSE STYLE ADOPTED** — Milestone 0003A (2026-06-30, drafted in ChatGPT chat) shipped Project AROC with its own draft navy/blue identity (`#1F4E79` / `#2E86C1`) and a custom radio-tower logo. As part of moving the project onto the Claude Code documentation pipeline (2026-08-25), Project AROC adopted the **shared KE4CON navy + gold house style** — the same one used by APRS-Command, OpenTrack, and ActivationPlanner — so every KE4CON project's documents look like one family. See **AROC-BRAND-0001 Rev0.2** for the full rationale; the original draft identity is preserved in `99 Archive/0003A-chatgpt-draft-rev0.1/` for history.


## Color Palette

The house palette is implemented in `docs/docs_generators/style.py` and used automatically by every document's build script — authors never pick colors by hand.

| Name | Hex | Usage |
| --- | --- | --- |
| **navy** | #1F3A5F | Cover panel, chapter-number block, headings, header text |
| **gold** | #D9A521 | Marquee rules under headers/covers, subtitle text on the cover |
| **accent2 (medium blue)** | #2E6DA4 | Section (H2) headings, bullet markers |
| **panel** | #EAF0F6 | Pale chapter-title banner fill |
| **ink** | #222B38 | Body text |
| **muted** | #64748B | Captions, footer text, subtitles |

Callout colors (note / tip / important / warning) are listed in Chapter 3, §"Callout Styles."


## Typography

- Primary body font: **Segoe UI**, 10.5 point
- Heading font: **Segoe UI Semibold**
- Code / configuration font: **Consolas**
- Body line spacing: 1.15, with spacing after each paragraph
- Avoid decorative fonts in technical content

> **WHY SEGOE UI** — The original draft specified Arial/Aptos. Segoe UI is the font the shared `style.py` renders with across every KE4CON document — it ships with Windows, reads cleanly on screen and in print, and keeps Project AROC visually identical to the rest of the library without requiring a font install step for anyone reading a generated `.docx`.


# 3. Page Types, Callouts & the Build Pipeline

*How a Project AROC document is actually assembled, and the quality bar before it ships.*


## Headers and Footers

Headers identify the project and document title; footers identify ownership and carry automatic page numbers ("Page X of Y"). Headers and footers are intentionally conservative — their purpose is navigation and identification, not decoration. A reader should always know which Project AROC document is open and where it belongs in the library.


## Standard Page Types

- **Cover page** — title, document kind, revision, project owner, motto (navy panel, gold marquee rule)
- **Document control page** — document number, owner, author, status, applicability
- **Revision history page** — revision, date, author, description, status
- **Table of contents** — auto-generated from chapter headings
- **Chapter pages** — each opens with a numbered navy block + gold rule, an optional "In This Chapter" summary


## Callout Styles

Four callout kinds are available, matching the shared house style. Use the kind whose intent matches what you're writing — the visual style (fill, border, label color) is applied automatically:

| Kind | Use for | Color |
| --- | --- | --- |
| `note` | Engineering Notes — technical reasoning a reader benefits from understanding | Blue |
| `important` | Design Decisions — why one approach was chosen over another | Amber/gold |
| `tip` | Future Expansion — ideas deferred to a later milestone, not blocking current work | Green |
| `warning` | Cautions and pitfalls — things that will break something if skipped | Red |


## Figure and Table Presentation

- Figure format: `Figure <chapter>-<number>: <caption>`
- Table format: `Table <chapter>-<number>: <caption>`
- Every diagram shall have a title and a stated purpose
- Screenshots shall be cropped for readability and annotated when needed
- Diagrams are authored as SVG where practical (renders cleanly, stays editable, no binary diffing)


## The Build Pipeline

**Markdown is the living source of truth.** Every formal document is authored as JSON chapter files under a `chapters/` folder next to a `build.py` script. Running `build.py` regenerates both a `.md` (source-of-record) and a styled `.docx` from scratch — nothing is hand-edited in Word, so a document can always be rebuilt exactly from its source.

```
cd "00 Engineering/<document folder>"
python build.py
```

`build.py` imports the shared renderer from `docs/docs_generators/style.py` (one copy, used by every document in this repository) and turns each chapter's `blocks` array into styled Word content. Supported block types: `h1`, `h2`, `p`, `steps`, `bullets`, `callout`, `screenshot`, `code`, `table`. Inline text supports `**bold**`, `` `code` ``, and `*italic*`.

> **NO AUTOMATIC PDF** — The pipeline produces `.md` and `.docx` only — there is no PDF step (no LibreOffice/Word automation is installed). Export a PDF from Word by hand (File > Save As > PDF) when a document is ready to publish, if a PDF copy is wanted.


## Quality Checklist

Before a document is marked **Approved**:

- Cover page present and correct (title, document number, revision)
- Document control page present (owner, author, status)
- Revision history entry added for this revision
- Document number and revision match the filename
- Headers, footers, and page numbers render correctly
- Callout kinds used consistently with Chapter 3's table above
- Figures and tables numbered per the `<chapter>-<number>` convention
- `build.py` runs clean with no errors and the `.md` / `.docx` are both committed
- Superseded prior revisions moved to `99 Archive/`, not deleted
