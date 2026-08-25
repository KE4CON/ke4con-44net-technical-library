# Engineering Standards

*AROC-STD-0002 · Revision 1.0 · KE4CON Amateur Radio Operations Center*

*Generated August 25, 2026 · Markdown is the living source of truth.*


---


# 1. Document Numbering & Folder Structure

*Milestone 0003B — how anything in this repository is identified and where it lives.*


## Document Numbering

Every formal document carries a number in the form `AROC-<TYPE>-<NUMBER>`. `<NUMBER>` is a 4-digit sequence, assigned in order within its `<TYPE>`, never reused even if a document is retired. A milestone-scoped document (a release, a phase deliverable) may append a letter suffix (`0003A`, `0003B`, `0003C`, ...) for sub-parts of the same milestone.

| Prefix | Category | Numbering scope |
| --- | --- | --- |
| **STD** | Publishing / engineering standards | Sequential, never reused (AROC-STD-0001, -0002, ...) |
| **BRAND** | Visual identity / branding | Sequential (typically stays at 0001 — revised in place via Revision History, not renumbered) |
| **REL** | Milestone / release notes | One per milestone, letter-suffixed for sub-releases (AROC-REL-0003A) |
| **BOOK** | Technical library volumes | Matches the Book number in the README (AROC-BOOK-0001 = Book 1, ...) |
| **OPS** | Operations runbooks (Book 6 material) | Sequential per runbook |


## Top-Level Folder Structure

The `README.md` repository-structure list is the authoritative folder set. Each folder's purpose:

| Folder | Purpose |
| --- | --- |
| `00 Engineering` | Formal engineering documents: publishing/engineering standards, branding, standards for the library itself — each formal document gets its own sub-folder holding `chapters/` + `build.py`, with the built `.md`/`.docx` one level up |
| `01 Publications` | The technical library itself once it exists — Books 0-10, one sub-folder per book |
| `02 Operations` | Runbooks, checklists, and standard operating procedures for running the actual Operations Center |
| `03 Software Development` | Any AROC-specific software (dashboards, automation, integrations) — not the general-purpose apps that live in their own separate repos |
| `04 Website` | Source for any AROC-facing web presence, if it ends up separate from the main KE4CON website |
| `05 Media` | Logos, diagrams source files, palettes, and other reusable media assets referenced by documents or the website |
| `06 Downloads` | Point-in-time release packages handed to readers (e.g. Milestone Release Notes) — historical snapshots, not living documents |
| `07 Templates` | Reusable starting points — today that means the chapters/build.py pattern itself (see AROC-STD-0001 Chapter 3), not hand-edited `.docx` templates |
| `99 Archive` | Superseded material, kept for history via `git mv` rather than deleted — e.g. `99 Archive/0003A-chatgpt-draft-rev0.1/` |


## Repo-Engineering-Only Material

Material that exists to help build/maintain this repository but is not itself part of the published library — pipeline planning notes, recovered project history, audit checklists — lives under `docs/internal/`, per the global KE4CON documentation standard. It is deliberately kept out of the numbered `00`-`99` structure so a reader of the library never has to wonder whether a numbered folder holds real content or repo housekeeping.

| Path | Holds |
| --- | --- |
| `docs/docs_generators/style.py` | The one shared house-style renderer, imported by every document's `build.py` in this repo |
| `docs/internal/` | Repo-engineering-only material — see `docs/internal/README.md` |
| `docs/internal/planning/` | Project history/origin notes, milestone planning |


# 2. Revision Control, File Naming & Figure Numbering

*Keeping the library consistent as it grows past a handful of documents.*


## Revision Control

Git is the authoritative revision history for every source file (`.json` chapters, `.py` build scripts, `.md`). The **Revision History table** inside each formal document is the authoritative history for *that document's meaning to a reader* — it should read clearly on its own, without needing `git log`.

- A revision number bumps (`0.1` → `0.2` → `1.0`) only when the built `.docx`/`.md` actually changes for a reader — not for every commit.
- Whole-number revisions (`1.0`, `2.0`, ...) mark a document reaching **Approved** status for the first time, or a rewrite substantial enough to treat as a new baseline.
- Decimal revisions (`0.1`, `0.2`, ...) are drafts and in-progress updates.
- Every revision bump gets one row in the Revision History table: revision, date, author, one-line description, status.
- Superseded formal `.docx`/`.pdf`/`.md` files move to `99 Archive/` via `git mv` — never deleted, so the reasoning behind an old revision stays readable.


## File and Folder Naming

| What | Convention | Example |
| --- | --- | --- |
| Formal document source folder | `<DOC-NUMBER> <Document Title>` under `00 Engineering` | `AROC-STD-0002 Engineering Standards/` |
| Chapter JSON files | `<2-digit order>-<kebab-case-slug>.json` | `01-numbering-folders.json` |
| Built `.docx`/`.md` | `<DOC-NUMBER> <Document Title> Rev<Revision>.<ext>` | `AROC-STD-0002 Engineering Standards Rev1.0.docx` |
| Media / palette / template assets | `Project_AROC_<Purpose>.<ext>` (underscores) | `Project_AROC_Color_Palette.json` |
| Archived material | Original filename, unchanged, under a dated sub-folder | `99 Archive/0003A-chatgpt-draft-rev0.1/...` |


## Figure and Table Numbering

- Figures: `Figure <chapter>-<number>: <caption>` — numbered per chapter, restarting at each chapter
- Tables: `Table <chapter>-<number>: <caption>` — same rule
- Diagrams are authored as SVG under `05 Media/diagrams/` where practical (create that folder when the first diagram is needed) — text-diffable, no binary churn, easy to edit
- Every diagram states its purpose in one sentence directly below its caption — a reader should never have to guess why a diagram exists
