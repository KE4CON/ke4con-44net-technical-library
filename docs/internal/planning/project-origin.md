# Project AROC — origin & recovery notes

> Written 2026-08-25, the day this repository first moved into Claude Code. Companion to
> the "Current Status" and "Chat-to-Claude-Code migration" sections of the root
> `CLAUDE.md` — this file has the detail that doesn't need to live in the always-loaded
> context file.

## What actually happened, as best it can be reconstructed

Project AROC's git history has exactly three commits before this session, all dated
2026-06-29: `Initial commit`, `Milestone 0003` (adds the publishing-framework files),
`Milestone 0003A final` (a follow-up polish pass), plus a same-day `Update README.md`
commit that added the full project charter. Every file added in those commits is a
finished `.docx`/`.pdf`/binary artifact — there is no source markdown, no chapter JSON,
no build script. That's the signature of a chat-produced deliverable: something was
composed turn-by-turn in a chat window, exported, and the finished files were committed
directly.

**Confirmed, not inferred:** every document's own Document Control page states
**"Technical Author: ChatGPT"**, revision-dated 2026-06-30. This was built in a ChatGPT
conversation, not a Claude one. There is no Claude or Claude Code session — anywhere on
this machine — that touches Project AROC's creation; the earliest local Claude Code
session on record is 2026-07-31, over a month later. Searches for "AROC", "44net-technical-
library", "Publishing Standard", and "Milestone 0003" across every other local session's
transcripts turned up only incidental directory-listing mentions from unrelated projects
(e.g. a WordPress-site session that happened to `ls` this folder), never substantive
discussion of AROC itself.

**What this means practically:** there is no lost Claude transcript to recover, unlike
(for example) OpenTrack's `docs/opentrack-recovered-history.md`, which reconstructed a
genuinely lost *Claude Code* session. Project AROC's actual planning conversation — why
these specific 11 books, why this folder scheme, what else was discussed and not acted
on — exists only in the user's ChatGPT chat history, which Claude Code has no access to.
If that conversation matters, the only way to recover it is for the user to open
ChatGPT's own history/export feature and look for the "Project AROC" conversation
directly.

## What WAS reconstructed, and from where

Everything in `00 Engineering` (Rev0.2 of the Publishing Standard and Visual Identity
Guide) and the new `AROC-STD-0002 Engineering Standards` is grounded in:

- The full text of the Rev0.1 `AROC-STD-0001` and `AROC-BRAND-0001` PDFs (read directly —
  they are a genuinely complete record of what Milestone 0003A decided: document
  structure, the original navy/blue palette, typography, callout styles, the quality
  checklist).
- The Milestone 0003A Release Notes PDF, which explicitly states Milestone 0003B's scope
  (document numbering, folder structure, revision control, file naming, figure/table
  numbering, diagram standards) — never started until this session.
- The root `README.md`, which is the project charter: the AROC acronym, the motto, the
  11-book planned library, the top-level folder scheme, and the Phase 0 status list.

## Decisions made in this session (2026-08-25)

1. **Adopt the shared KE4CON navy+gold house style**, replacing the Rev0.1 draft
   navy/blue identity, so Project AROC's documents render from the same
   `docs_generators/style.py` as APRS-Command, OpenTrack, and ActivationPlanner. The
   original identity is archived, not deleted, at
   `99 Archive/0003A-chatgpt-draft-rev0.1/`.
2. **Keep the numbered `00`-`99` top-level folders** as the library's actual content
   structure (that's what Project AROC publishes), rather than moving everything under a
   generic `docs/` root. Add `docs/internal/` alongside it for repo-engineering-only
   material, per the global KE4CON documentation standard.
3. **Complete Milestone 0003B** (`AROC-STD-0002 Engineering Standards`) in this same
   session, since it directly formalizes the folder/numbering/pipeline choices being made
   anyway — leaving it as a stub would have meant redoing this work later.
4. **Broaden the planned "Book 3" from "Linux" to "Linux, Windows & macOS
   Administration"** — the Operations Center's admin surface won't be Linux-only (desktop
   clients and some AROC tooling will run on Windows/macOS too, matching how every other
   KE4CON app ships cross-platform).

## What's still genuinely open

- **Milestone 0003C** (Project Charter Version 1.0) — not started; the README's charter
  content is still the informal v0.x version.
- **No book content exists yet.** `01 Publications` doesn't exist as a folder. Everything
  shipped so far is documentation *about* documentation — the actual Operations Center
  build-out (Books 1-10, `02 Operations`, `03 Software Development`) hasn't begun.
- **The hardware/network side is undocumented here.** The Raspberry Pi / 44Net /
  networking work this project is ultimately about may already exist in the user's head
  or on physical hardware, but nothing about it has been captured in this repository yet.
