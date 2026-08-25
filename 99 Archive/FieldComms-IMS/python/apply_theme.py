#!/usr/bin/env python3
"""
apply_theme.py — FieldComms Theme Consistency Tool
====================================================
Scans all HTML files in the web frontend and verifies / applies the
standard FieldComms dark theme CSS variables.  Can also patch a single
file or a directory of files.

Usage
-----
  # Check all HTML files for missing/wrong theme variables
  python3 apply_theme.py --check

  # Apply the canonical theme to all HTML files that are missing it
  python3 apply_theme.py --apply

  # Apply to a single file
  python3 apply_theme.py --apply --file /opt/fieldcomms/html/mypage.html

  # Show diff without writing
  python3 apply_theme.py --diff --file /opt/fieldcomms/html/mypage.html

  # List all files that are missing at least one required variable
  python3 apply_theme.py --missing

K9ESV · McHenry County Emergency Services Volunteers
     and McHenry County Emergency Management Agency (MCESV/MCEMA)
FieldComms Incident Management System v1.0
"""

import sys
import os
import re
import argparse
import difflib
from pathlib import Path

# ── Canonical theme block ────────────────────────────────────────────────────
THEME_VARS = """:root {
  --bg:#0d1117;      /* page background */
  --panel:#161b22;   /* card / panel background */
  --panel2:#21262d;  /* raised panel / input background */
  --txt:#c9d1d9;     /* primary text */
  --muted:#6e7681;   /* secondary / muted text */
  --line:#30363d;    /* border / divider */
  --eoc:#1a3a6b;     /* EOC blue — primary brand */
  --eoc-lt:#2d6ab4;  /* EOC light blue — links / accents */
  --amber:#e3b341;   /* amber — warnings / alerts */
  --green:#3fb950;   /* green — success / online */
  --red:#f85149;     /* red — error / danger */
  --blue:#58a6ff;    /* blue — info / interactive */
  --purple:#bc8cff;  /* purple — ICS / forms */
  --font-hd:'Courier New',monospace;  /* header / monospace accent font */
}"""

# Required variable names — every page must define these
REQUIRED_VARS = [
    '--bg', '--panel', '--panel2', '--txt', '--muted', '--line',
    '--eoc', '--eoc-lt', '--amber', '--green', '--red', '--blue',
    '--purple', '--font-hd',
]

# The theme block is inserted inside the first <style> tag found
STYLE_OPEN  = re.compile(r'<style[^>]*>', re.IGNORECASE)
ROOT_BLOCK  = re.compile(r':root\s*\{[^}]*\}', re.DOTALL)

# Default search path
DEFAULT_HTML_DIR = Path('/opt/fieldcomms/html')


# ── Helpers ──────────────────────────────────────────────────────────────────

def find_html_files(directory: Path) -> list[Path]:
    """Return all .html files under directory, recursively."""
    return sorted(directory.rglob('*.html'))


def get_defined_vars(html: str) -> set[str]:
    """Return the set of CSS variable names defined in :root blocks."""
    defined = set()
    for block in ROOT_BLOCK.finditer(html):
        for m in re.finditer(r'(--[\w-]+)\s*:', block.group()):
            defined.add(m.group(1))
    return defined


def missing_vars(html: str) -> list[str]:
    """Return required variables not defined in the HTML."""
    defined = get_defined_vars(html)
    return [v for v in REQUIRED_VARS if v not in defined]


def has_root_block(html: str) -> bool:
    return bool(ROOT_BLOCK.search(html))


def replace_root_block(html: str) -> str:
    """Replace existing :root block with the canonical theme."""
    return ROOT_BLOCK.sub(THEME_VARS, html, count=1)


def insert_root_block(html: str) -> str:
    """Insert canonical :root block inside the first <style> tag."""
    m = STYLE_OPEN.search(html)
    if not m:
        # No <style> tag — insert one before </head>
        head_close = html.lower().find('</head>')
        if head_close == -1:
            return html  # can't safely insert
        insertion = f'\n<style>\n{THEME_VARS}\n</style>\n'
        return html[:head_close] + insertion + html[head_close:]
    insert_pos = m.end()
    return html[:insert_pos] + '\n' + THEME_VARS + '\n' + html[insert_pos:]


def apply_theme(html: str) -> str:
    """Apply canonical theme to HTML string. Returns modified string."""
    if has_root_block(html):
        return replace_root_block(html)
    return insert_root_block(html)


def show_diff(original: str, modified: str, filename: str) -> None:
    diff = difflib.unified_diff(
        original.splitlines(keepends=True),
        modified.splitlines(keepends=True),
        fromfile=f'{filename} (original)',
        tofile=f'{filename} (patched)',
        n=3,
    )
    sys.stdout.writelines(diff)


# ── Main actions ─────────────────────────────────────────────────────────────

def action_check(files: list[Path]) -> int:
    """Check files and report issues. Returns number of files with issues."""
    issues = 0
    for fpath in files:
        html = fpath.read_text(encoding='utf-8', errors='replace')
        mv = missing_vars(html)
        if mv:
            print(f'MISSING  {fpath.name:40s}  {", ".join(mv)}')
            issues += 1
        else:
            print(f'OK       {fpath.name}')
    print(f'\n{len(files)} files checked — {issues} with missing variables.')
    return issues


def action_missing(files: list[Path]) -> None:
    """Print only files with missing variables."""
    for fpath in files:
        html = fpath.read_text(encoding='utf-8', errors='replace')
        mv = missing_vars(html)
        if mv:
            print(f'{fpath}  →  missing: {", ".join(mv)}')


def action_apply(files: list[Path], dry_run: bool = False) -> int:
    """Apply canonical theme to files that need it. Returns count patched."""
    patched = 0
    for fpath in files:
        html = fpath.read_text(encoding='utf-8', errors='replace')
        mv = missing_vars(html)
        if not mv:
            continue
        modified = apply_theme(html)
        if dry_run:
            print(f'[dry-run] Would patch: {fpath}')
        else:
            fpath.write_text(modified, encoding='utf-8')
            print(f'Patched: {fpath}')
        patched += 1
    print(f'\n{patched} file(s) {"would be " if dry_run else ""}patched.')
    return patched


def action_diff(files: list[Path]) -> None:
    """Show unified diff of what would change."""
    for fpath in files:
        html = fpath.read_text(encoding='utf-8', errors='replace')
        mv = missing_vars(html)
        if not mv:
            continue
        modified = apply_theme(html)
        show_diff(html, modified, str(fpath))


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='FieldComms theme consistency tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument('--dir', default=str(DEFAULT_HTML_DIR),
                        help='HTML directory to scan (default: /opt/fieldcomms/html)')
    parser.add_argument('--file', help='Process a single HTML file instead of a directory')
    parser.add_argument('--check',   action='store_true', help='Check all files and report')
    parser.add_argument('--missing', action='store_true', help='List files with missing variables')
    parser.add_argument('--apply',   action='store_true', help='Apply theme to files that need it')
    parser.add_argument('--diff',    action='store_true', help='Show diff without writing')
    parser.add_argument('--dry-run', action='store_true', help='With --apply: show what would change without writing')
    args = parser.parse_args()

    # Resolve file list
    if args.file:
        fpath = Path(args.file)
        if not fpath.exists():
            print(f'Error: file not found: {args.file}', file=sys.stderr)
            sys.exit(1)
        files = [fpath]
    else:
        html_dir = Path(args.dir)
        if not html_dir.exists():
            print(f'Error: directory not found: {args.dir}', file=sys.stderr)
            sys.exit(1)
        files = find_html_files(html_dir)
        print(f'Found {len(files)} HTML files in {html_dir}\n')

    if not any([args.check, args.missing, args.apply, args.diff]):
        # Default: check
        args.check = True

    if args.check:
        sys.exit(0 if action_check(files) == 0 else 1)
    if args.missing:
        action_missing(files)
    if args.diff:
        action_diff(files)
    if args.apply:
        action_apply(files, dry_run=args.dry_run)


if __name__ == '__main__':
    main()
