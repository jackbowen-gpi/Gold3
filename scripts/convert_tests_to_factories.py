"""
Codemod: convert simple Site/User creation calls in test files to factory helpers.

This script searches for test modules under apps/**/tests and replaces
- `Site.objects.create(` -> `create_site(`
- `User.objects.create_user(` -> `create_user(`

It also inserts `from tests.factories import create_site, create_user` if not present.

It creates a .bak copy for each changed file.

Use with: python scripts/convert_tests_to_factories.py --apply

Without --apply it will only print candidates.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TEST_GLOB = "**/tests/*.py"

SITE_PATTERN = re.compile(r"\bSite\.objects\.(create|get_or_create)\(")
USER_PATTERN = re.compile(r"\bUser\.objects\.(create_user|get_or_create)\(")
IMPORT_LINE = "from tests.factories import create_site, create_user\n"


def find_test_files() -> list[Path]:
    files = []
    exclude_dirs = (".history", ".venv", "backups", "backend/apps/workflow/backups")
    for p in ROOT.glob(TEST_GLOB):
        if not p.is_file():
            continue
        sp = str(p)
        if any(ex in sp for ex in exclude_dirs):
            continue
        files.append(p)
    return files


def needs_import(text: str) -> bool:
    return "from tests.factories import" not in text


def transform_text(text: str) -> tuple[str, bool]:
    orig = text
    changed = False

    if SITE_PATTERN.search(text):
        text = SITE_PATTERN.sub("create_site(", text)
        changed = True
    if USER_PATTERN.search(text):
        text = USER_PATTERN.sub("create_user(", text)
        changed = True

    if changed and needs_import(text):
        # Insert import after initial block of imports
        lines = text.splitlines(keepends=True)
        insert_at = 0
        for i, line in enumerate(lines):
            if line.strip().startswith("from") or line.strip().startswith("import"):
                insert_at = i + 1
            elif line.strip() == "":
                # blank line encountered after imports — break
                if insert_at:
                    break
        lines.insert(insert_at, IMPORT_LINE)
        text = "".join(lines)
    return text, text != orig


def main(apply: bool):
    files = find_test_files()
    modified = []
    for f in files:
        text = f.read_text(encoding="utf-8")
        new_text, changed = transform_text(text)
        if changed:
            modified.append(str(f))
            print("WILL MODIFY:", f)
            if apply:
                bak = f.with_suffix(f"{f.suffix}.bak")
                f.write_text(new_text, encoding="utf-8")
                bak.write_text(text, encoding="utf-8")
                print("MODIFIED & BACKUPED:", f, "->", bak)
    print("\nSummary: modified files:")
    for m in modified:
        print(m)
    print(f"Total candidates: {len(modified)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="apply changes to files")
    args = parser.parse_args()
    main(args.apply)
