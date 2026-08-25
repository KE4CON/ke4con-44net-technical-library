# docs/ — repo-engineering material

This folder holds the tooling and internal notes that help build and maintain this
repository. It is **not** part of the published Project AROC technical library — that
lives in the numbered top-level folders (`00 Engineering` through `99 Archive`; see the
root `README.md` and `AROC-STD-0002 Engineering Standards` for what each one is for).

- **`docs_generators/style.py`** — the one shared house-style renderer (navy+gold,
  matching every other KE4CON repo). Every formal document's `build.py`, wherever it
  lives in this repo, imports this one file. There is exactly one copy — never fork it
  per document.
- **`internal/`** — engineering-only material: recovered project history, planning
  notes, anything a reader of the published library doesn't need to see. See
  `internal/README.md`.
