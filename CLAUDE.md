# CLAUDE.md — Project AROC (ke4con-44net-technical-library)

> Project context and working agreement for Project AROC. Read this first at the start of
> every session so we stay consistent and don't re-decide settled questions.
> **When a decision changes, update this file** — it is the single source of truth.

---

## 1. What Project AROC is

**Project AROC (Amateur Radio Operations Center)** — a long-term engineering,
documentation, and software development project to design, build, and operate a modern
amateur radio communications center for **KE4CON**. It is not a documentation project
about someone else's system; the technical library it produces documents a real
operations center this project is also building (network, servers, software, radio
operations).

- **Local path:** `C:\Dev\ke4con-44net-technical-library`
- **Repo:** `github.com/KE4CON/ke4con-44net-technical-library` (public)
- **Motto:** *Build with Purpose. Document with Precision. Learn without End.*
- **Combines:** 44Net networking, Raspberry Pi servers, Linux/Windows/macOS
  administration, web server technologies, amateur radio communications, emergency
  communications, network engineering, systems engineering, and professional technical
  documentation.
- **Full charter:** `README.md` (project overview, goals, development philosophy).
- **Audience (decided 2026-08-25):** written for two readers at once — James (KE4CON)
  building this specific center, and anyone else who wants to learn from and implement
  the same concepts for their own station. Write every book/standard/runbook so a
  stranger could actually follow it, not as private notes that happen to be public. See
  §7 Licensing for what makes that legally real, not just aspirational.
- **The primary deliverable is the knowledge, not the software (decided 2026-08-25).**
  Project AROC's software (APRS-Command, FieldCommand-IMS, etc.) and hardware (Kestrel,
  Phoenix) are built and *referenced* here as real, working proof that the engineering
  explained in the library actually works — but the library itself, not any one app, is
  the point. The stated ambition: "the ultimate amateur radio RF knowledge base." See §8
  for the depth/rigor standard that ambition implies.

---

## 2. Origin — this was a ChatGPT project before it was a Claude one

Every file from Milestone 0003A (the only work that exists so far) was produced in a
**ChatGPT** chat session on 2026-06-30, then hand-committed as finished `.docx`/`.pdf`
files — no source markdown, no build script, no Claude or Claude Code involvement at all.
2026-08-25 is this project's **first contact with Claude Code**. There is no lost Claude
session to recover (searched — none exists); what's recoverable is only what the shipped
artifacts themselves document. Full detail: `docs/internal/planning/project-origin.md`.

**Practical effect:** treat every Rev0.1 claim (palette, logo, template files) as a draft
made without build/test verification and without Claude's involvement, not as an
established Claude-side convention being violated. The Rev0.1 originals are preserved,
not deleted, at `99 Archive/0003A-chatgpt-draft-rev0.1/`.

---

## 3. Current status

**Phase 0 — Project Foundation**

- ✅ Release 0001 — Initial Project Charter
- ✅ Release 0002 — Project Vision and Roadmap
- ✅ Milestone 0003A — Publishing Framework (originally ChatGPT-drafted Rev0.1; migrated
  to the Claude Code pipeline and the shared KE4CON navy+gold house style as Rev0.2 on
  2026-08-25)
- ✅ Milestone 0003B — Engineering Standards (`AROC-STD-0002`, written 2026-08-25:
  document numbering, folder structure, revision control, file naming, figure/table
  numbering, diagram standards)
- ⏳ Milestone 0003C — Project Charter Version 1.0 (not started)
- 🟡 First technical library content — **Book 7 (APRS), Chapter 1** drafted 2026-08-25
  as the pilot for the depth/rigor standard in §8 (`01 Publications/Book 7 - APRS/`,
  `AROC-BOOK-0007`, Rev0.1, Draft — awaiting the user's review before more chapters or
  books are started in the same style). All other books: not started.
- ⏳ `02 Operations`, `03 Software Development` — **do not exist yet**; also still open:
  whether the standalone software repos (APRS-Command, FieldCommand-IMS, etc.) get
  absorbed into `03 Software Development` or stay independent and just get linked/
  documented from here (raised 2026-08-25, undecided)

The README's own "Current Status" section should always **link here**, not restate this
list — this file is authoritative; update it in the same commit that completes a
milestone.

---

## 4. Documentation standards for this repo

This repo follows the global KE4CON documentation standard (house pipeline, per-chapter
JSON, Markdown as living source of truth), with two repo-specific choices made
2026-08-25 (see `docs/internal/planning/project-origin.md` for the reasoning):

1. **Keep the numbered top-level folders** (`00 Engineering` … `99 Archive`) as the
   library's actual published content — that IS what Project AROC ships. Do **not**
   migrate them under a generic `docs/` root; that pattern is for software repos with a
   fixed three-document set, and doesn't fit an 11-book library.
2. **`docs/` here holds only pipeline tooling and repo-internal notes** —
   `docs/docs_generators/style.py` (the one shared house-style renderer this repo's
   documents import) and `docs/internal/` (planning/origin notes, nothing a library reader
   needs). See `docs/README.md`.

**House style: shared KE4CON navy+gold**, not a unique AROC identity. Full spec:
`00 Engineering/AROC-BRAND-0001 Project AROC Visual Identity Guide Rev0.2.docx`.
Fonts: Segoe UI (body/heading), Consolas (code). Palette lives in both the Visual
Identity Guide and `05 Media/Project_AROC_Color_Palette.json` — keep them in sync.

**Building a document:** every formal document is a folder under `00 Engineering/`
holding `chapters/*.json` + `build.py`. `python build.py` from inside that folder
regenerates the `.md` and `.docx` one level up. Full authoring rules (numbering,
callout kinds, figure/table format, quality checklist):
`00 Engineering/AROC-STD-0001 Project AROC Publishing Standard Rev0.2.docx` and
`00 Engineering/AROC-STD-0002 Engineering Standards Rev1.0.docx`.

**No automatic PDF** — the pipeline produces `.md` + `.docx` only (no LibreOffice/Word
automation installed). Export PDF from Word by hand when one is needed for release.

**Superseded formal documents move to `99 Archive/` via `git mv`** — never delete a prior
revision; the Revision History table plus the archived file together preserve the
reasoning.

---

## 5. Planned library (from the charter, `README.md`)

- Book 0 – Administration
- Book 1 – Planning, Architecture & Network Fundamentals *(decided 2026-08-25: gets a
  dedicated "AX.25 / Packet Radio Fundamentals" chapter — connected-mode sessions, the
  KISS protocol between TNC and computer, general digipeating/node networks (NET/ROM,
  packet BBS operation) — covering AX.25 as a protocol in general, not just the
  APRS-specific slice already written in Book 7 Ch.1. Book 4 (44Net), Book 7 (APRS), and
  Book 8 (Winlink) all reference back to this chapter instead of re-explaining AX.25 at
  three different depths.)*
- Book 2 – Hardware
- Book 3 – Linux, Windows & macOS Administration *(broadened 2026-08-25 from "Linux" —
  the Operations Center's admin surface isn't Linux-only)*
- Book 4 – 44Net
- Book 5 – Web Server
- Book 6 – Operations
- Book 7 – APRS
- Book 8 – Winlink
- Book 9 – AI Integration
- Book 10 – Emergency Communications

Book 7's Chapter 1 is drafted (§3) as the pilot for the §8 depth standard — pending
review, the rest of Book 7 and the other ten books follow the same template. Absent that
pilot, **Book 1 (Planning, Architecture & Network Fundamentals)** would be the natural
next pick, since everything else depends on it.

---

## 6. Working agreement

- **All future work on Project AROC happens through Claude / Claude Code — not ChatGPT.**
  Confirmed by the user 2026-08-25. ChatGPT produced Milestone 0003A (§2) and is not used
  going forward; there's no need to reconcile a parallel ChatGPT workflow or expect future
  hand-off `.docx` drops from chat.
- **Ground every claim in real source.** This project's one prior failure mode (per its
  own origin story) was chat-drafted content that was never verified against anything
  real. Any future book content describing actual hardware/network/config must be checked
  against the real thing, not drafted blind.
- **Markdown is the living source of truth** for every formal document — never hand-edit
  a `.docx` and call it done; edit the chapter JSON and rebuild.
- **Update this file's §3 Current Status in the same commit** that completes a milestone,
  book, or significant feature — never as a deferred follow-up.

---

## 7. Licensing

Dual-licensed by content type, decided 2026-08-25 — full detail in `LICENSING.md`:

- **Documentation & technical library** (`00 Engineering`, `01 Publications`,
  `02 Operations`, `05 Media`, `06 Downloads`, any book content): **CC BY-SA 4.0**.
- **Software** (`03 Software Development`, `docs/docs_generators/`, every `build.py`):
  **GPLv3**.
- **This is a default, not an absolute rule** — the project owner reserves the right to
  license a specific document or piece of software differently, case by case. When that
  happens, note the exception on that item's own Document Control page (or file header
  for code) — it overrides the table above for that item only.
- Full texts: `LICENSE` (GPLv3) and `LICENSE-CONTENT` (CC BY-SA 4.0), fetched verbatim
  from gnu.org / creativecommons.org, not reproduced from memory.

---

## 8. Content depth & rigor standard (decided 2026-08-25)

The library's ambition, in the user's own words: *"do it at a PhD thesis level but keep
the language such that everyone can understand it... the ultimate amateur radio RF
knowledge base."* Two things have to be true of every chapter at once, not traded off
against each other:

- **PhD-thesis-level rigor.** Technical claims are exact and grounded in real sources —
  actual specs, standards documents, and reference material, cited by name and URL in a
  "Sources & Further Reading" section — not written fluently from memory and assumed
  correct. Every design choice is explained by the real engineering problem it solves,
  not just stated as fact. Where a topic is real but out of scope for the current
  chapter, say so explicitly (a scope-boundary callout) rather than covering it shallowly
  just to seem complete.
- **Plain enough that everyone can follow it.** Define every piece of jargon inline the
  first time it's used. Build intuition with a plain-language explanation before (or
  alongside) any formal/technical statement. A beginner and a working engineer should
  both get real value from the same page — this is the same principle behind the global
  house standard's "define every acronym on first use," applied at a much greater depth.
- **Ground book content in the real software/hardware this project has built wherever
  possible** — e.g. connect an explained protocol or technique to exactly where it's
  implemented in APRS-Command, FieldCommand-IMS, etc. This is what makes the library
  provably not chat-drafted theory (§2's original failure mode) — the pattern this whole
  migration exists to break.
- **The pilot:** `01 Publications/Book 7 - APRS/chapters/01-what-aprs-is-and-how-it-works.json`
  (Book 7, Chapter 1) is the first chapter written to this standard — researched against
  aprs.org, TAPR, and a real AX.25 frame-structure reference, and grounded against
  APRS-Command's actual architecture. Read it before writing another chapter; match its
  depth, its citation habit, and its voice, not just its section structure.
- **Length is not the target — depth and correctness are.** A chapter runs as long as the
  material actually requires (Book 7 Ch.1 landed around 2,900 words); padding to hit a
  word count, or cutting real content to stay short, are both wrong moves.
