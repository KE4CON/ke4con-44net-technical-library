"""
AROC-BRAND-0001 Project AROC Visual Identity Guide — builder.

Markdown is the living source of truth; a styled .docx (navy+gold house style, matching
every KE4CON repo) is generated from the same chapter JSON under ./chapters/*.json.

Run:  python build.py
  -> writes "../AROC-BRAND-0001 Project AROC Visual Identity Guide Rev0.2.md"
  -> writes "../AROC-BRAND-0001 Project AROC Visual Identity Guide Rev0.2.docx"
"""
import os
import sys
import glob
import json
import re
import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "docs", "docs_generators")))
import style as S  # noqa: E402

DOC_NUMBER = "AROC-BRAND-0001"
DOC_TITLE = "Project AROC Visual Identity Guide"
REVISION = "0.2"
OUT_BASENAME = f"{DOC_NUMBER} {DOC_TITLE} Rev{REVISION}"
OUT_DIR = os.path.abspath(os.path.join(HERE, ".."))


def load_chapters():
    out = []
    for path in sorted(glob.glob(os.path.join(HERE, "chapters", "*.json"))):
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        ch = raw.get("chapter", raw)
        order = int(raw.get("order", ch.get("order", 999)))
        out.append((order, ch))
    out.sort(key=lambda x: x[0])
    return out


def _md_inline(text):
    return re.sub(r"__(.+?)__", r"*\1*", str(text))


def _md_blocks(blocks):
    lines = []
    for blk in blocks:
        if not isinstance(blk, dict):
            continue
        if "h1" in blk:
            lines.append(f"\n## {blk['h1']}\n")
        elif "h2" in blk:
            lines.append(f"\n### {blk['h2']}\n")
        elif "p" in blk:
            lines.append(_md_inline(blk["p"]) + "\n")
        elif "steps" in blk:
            lines += [f"{i}. {_md_inline(s)}" for i, s in enumerate(blk["steps"], 1)]
            lines.append("")
        elif "bullets" in blk:
            lines += [f"- {_md_inline(b)}" for b in blk["bullets"]]
            lines.append("")
        elif "callout" in blk:
            c = blk["callout"] if isinstance(blk["callout"], dict) else {}
            label = c.get("label", c.get("kind", "NOTE").upper())
            lines.append(f"> **{label}** — {_md_inline(c.get('text', ''))}\n")
        elif "screenshot" in blk:
            lines.append(f"> _[Figure: {blk['screenshot']}]_\n")
        elif "code" in blk:
            code = blk["code"]
            code = "\n".join(code) if isinstance(code, list) else str(code)
            lines.append("```\n" + code + "\n```\n")
        elif "table" in blk:
            t = blk["table"] if isinstance(blk["table"], dict) else {}
            headers = [str(h) for h in t.get("headers", [])]
            rows = t.get("rows", [])
            if headers:
                lines.append("| " + " | ".join(headers) + " |")
                lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
                for r in rows:
                    lines.append("| " + " | ".join(_md_inline(c) for c in r) + " |")
                lines.append("")
    return "\n".join(lines)


def to_markdown(chapters):
    parts = [
        f"# {DOC_TITLE}\n",
        f"*{DOC_NUMBER} · Revision {REVISION} · KE4CON Amateur Radio Operations Center*\n",
        f"*Generated {datetime.date.today().strftime('%B %d, %Y')} · Markdown is the living source of truth.*\n",
        "\n---\n",
    ]
    for number, (_order, ch) in enumerate(chapters, 1):
        parts.append(f"\n# {number}. {ch.get('title', 'Untitled')}\n")
        if ch.get("subtitle"):
            parts.append(f"*{_md_inline(ch['subtitle'])}*\n")
        parts.append(_md_blocks(ch.get("blocks", [])))
    return "\n".join(parts)


def build_docx(chapters):
    doc = S.new_document(
        header_title=f"Project AROC — {DOC_TITLE}",
        header_sub=f"{DOC_NUMBER} · Revision {REVISION} · KE4CON Amateur Radio Operations Center",
        footer_left="Project AROC  ·  KE4CON Technical Library and Engineering System",
    )
    S.cover(
        doc,
        kicker="PROJECT AROC",
        big_title="Project AROC",
        subtitle=DOC_TITLE,
        doc_kind=f"{DOC_NUMBER}  ·  REV {REVISION}",
        version="Approved for Review",
        tagline="Build with Purpose. Document with Precision. Learn without End.",
        author="James  ·  KE4CON",
        date_str=datetime.date.today().strftime("%B %d, %Y"),
    )
    S.section_title(doc, "Document Control")
    S.table(doc,
        ["Field", "Value"],
        [
            ["Document Number", DOC_NUMBER],
            ["Title", DOC_TITLE],
            ["Revision", REVISION],
            ["Status", "Approved"],
            ["Owner", "James / KE4CON"],
            ["Technical Author", "Claude (Claude Code)"],
            ["Applies To", "Project AROC Technical Library and Engineering Documentation"],
        ],
        [S.Inches(2.0), S.Inches(4.5)],
    )
    S.section_title(doc, "Revision History")
    S.table(doc,
        ["Rev", "Date", "Author", "Description", "Status"],
        [
            ["0.1", "2026-06-30", "ChatGPT", "Initial Milestone 0003A draft identity (navy/blue palette, custom logo)", "Superseded"],
            ["0.2", datetime.date.today().strftime("%Y-%m-%d"), "Claude (Claude Code)",
             "Adopted the shared KE4CON navy+gold house style; retired the draft palette and document-cover logo use", "Approved"],
        ],
        [S.Inches(0.6), S.Inches(1.1), S.Inches(1.5), S.Inches(2.7), S.Inches(0.9)],
    )
    S.section_title(doc, "Contents")
    S.toc(doc)
    for number, (_order, ch) in enumerate(chapters, 1):
        S.render_chapter(doc, ch, number)
    out = os.path.join(OUT_DIR, OUT_BASENAME + ".docx")
    doc.save(out)
    return out


def main():
    chapters = load_chapters()
    if not chapters:
        print("No chapters found in ./chapters/*.json — nothing to build yet.")
        return
    md = to_markdown(chapters)
    md_path = os.path.join(OUT_DIR, OUT_BASENAME + ".md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md)
    docx_path = build_docx(chapters)
    print(f"OK — {len(chapters)} chapter(s)")
    print(f"  Markdown: {md_path}")
    print(f"  Word:     {docx_path}")


if __name__ == "__main__":
    main()
