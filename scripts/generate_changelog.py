#!/usr/bin/env python3
"""Generate changelogs from git commit history."""

import argparse
import os
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime

# Null byte delimiter — safe against any commit message content
FIELD_SEP = "\x00"
RECORD_SEP = "\x01"

CONVENTIONAL_MAP = {
    "feat": "Added",
    "fix": "Fixed",
    "docs": "Documentation",
    "refactor": "Changed",
    "style": "Changed",
    "perf": "Performance",
    "test": "Tests",
    "chore": "Maintenance",
    "ci": "Maintenance",
    "build": "Maintenance",
    "revert": "Removed",
    "deprecate": "Deprecated",
}

CATEGORY_ORDER = [
    "Breaking Changes",
    "Added",
    "Fixed",
    "Changed",
    "Deprecated",
    "Removed",
    "Performance",
    "Security",
    "Documentation",
    "Tests",
    "Maintenance",
    "Other",
]

CONV_PATTERN = re.compile(
    r"^(?P<type>\w+)(?:\((?P<scope>[^)]*)\))?(?P<bang>!)?:\s*(?P<desc>.+)$"
)


def run_git(*args):
    result = subprocess.run(["git"] + list(args), capture_output=True, text=True)
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def get_latest_tag():
    return run_git("describe", "--tags", "--abbrev=0")


def get_first_commit():
    return run_git("rev-list", "--max-parents=0", "HEAD")


def get_commits(from_ref, to_ref, no_merges=False):
    fmt = FIELD_SEP.join(["%H", "%s", "%an", "%ai", f"%b{RECORD_SEP}"])
    args = ["log", f"{from_ref}..{to_ref}", f"--pretty=format:{fmt}"]
    if no_merges:
        args.append("--no-merges")
    output = run_git(*args)
    if not output:
        return []
    commits = []
    for record in output.split(RECORD_SEP):
        record = record.strip()
        if not record:
            continue
        parts = record.split(FIELD_SEP, 4)
        if len(parts) == 5:
            commits.append(
                {
                    "hash": parts[0][:8],
                    "subject": parts[1],
                    "author": parts[2],
                    "date": parts[3][:10],
                    "body": parts[4].strip(),
                }
            )
    return commits


def parse_commit(commit):
    subject = commit["subject"]
    body = commit.get("body", "")
    m = CONV_PATTERN.match(subject)
    if m:
        ctype = m.group("type")
        scope = m.group("scope") or ""
        bang = m.group("bang")
        desc = m.group("desc")
        category = CONVENTIONAL_MAP.get(ctype, "Other")
        if bang or "BREAKING CHANGE" in subject or "BREAKING CHANGE" in body:
            category = "Breaking Changes"
        return {**commit, "category": category, "scope": scope, "description": desc}
    return {**commit, "category": "Other", "scope": "", "description": subject}


def group_commits(commits):
    grouped = defaultdict(list)
    for c in commits:
        parsed = parse_commit(c)
        grouped[parsed["category"]].append(parsed)
    return grouped


def format_keepachangelog(commits, from_ref, to_ref):
    grouped = group_commits(commits)
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [f"## [{to_ref}] - {today}\n"]

    for cat in CATEGORY_ORDER:
        if cat in grouped:
            lines.append(f"### {cat}\n")
            for c in grouped[cat]:
                scope = f"**{c['scope']}**: " if c["scope"] else ""
                lines.append(f"- {scope}{c['description']} ({c['hash']})")
            lines.append("")

    return "\n".join(lines)


def format_conventional(commits, from_ref, to_ref):
    grouped = group_commits(commits)
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [f"# {to_ref} ({today})\n"]

    for cat in CATEGORY_ORDER:
        if cat in grouped:
            lines.append(f"### {cat}\n")
            for c in grouped[cat]:
                scope = f"**{c['scope']}:** " if c["scope"] else ""
                lines.append(f"* {scope}{c['description']} ([{c['hash']}])")
            lines.append("")

    return "\n".join(lines)


def format_grouped(commits, from_ref, to_ref):
    by_date = defaultdict(list)
    for c in commits:
        by_date[c["date"]].append(c)

    lines = [f"# Changes: {from_ref} -> {to_ref}\n"]
    for date in sorted(by_date.keys(), reverse=True):
        lines.append(f"## {date}\n")
        for c in by_date[date]:
            lines.append(f"- {c['subject']} ({c['hash']}, {c['author']})")
        lines.append("")

    return "\n".join(lines)


FORMATTERS = {
    "keepachangelog": format_keepachangelog,
    "conventional": format_conventional,
    "grouped": format_grouped,
}


def prepend_to_file(filepath, new_content):
    """Insert new changelog entries below the first H1 header, above existing entries."""
    if not os.path.exists(filepath):
        with open(filepath, "w") as f:
            f.write(f"# Changelog\n\n{new_content}\n")
        return

    with open(filepath, "r") as f:
        existing = f.read()

    h1_match = re.search(r"^# .+\n", existing)
    if h1_match:
        insert_pos = h1_match.end()
        while insert_pos < len(existing) and existing[insert_pos] == "\n":
            insert_pos += 1
        updated = (
            existing[:insert_pos] + "\n" + new_content + "\n\n" + existing[insert_pos:]
        )
    else:
        updated = new_content + "\n\n" + existing

    with open(filepath, "w") as f:
        f.write(updated)


def main():
    parser = argparse.ArgumentParser(description="Generate changelog from git history")
    parser.add_argument(
        "--from", dest="from_ref", help="Start ref (default: latest tag)"
    )
    parser.add_argument(
        "--to", dest="to_ref", default="HEAD", help="End ref (default: HEAD)"
    )
    parser.add_argument("--format", choices=FORMATTERS.keys(), default="keepachangelog")
    parser.add_argument("--output", help="Output file path")
    parser.add_argument(
        "--version",
        dest="version_label",
        help="Version label for the changelog header (e.g. v1.3.0)",
    )
    parser.add_argument(
        "--prepend",
        action="store_true",
        help="Prepend to existing file instead of overwriting (requires --output)",
    )
    parser.add_argument(
        "--no-merges", action="store_true", help="Exclude merge commits"
    )
    parser.add_argument(
        "--exclude-types",
        dest="exclude_types",
        help="Comma-separated commit types to exclude (e.g. chore,ci,test)",
    )
    args = parser.parse_args()

    if args.prepend and not args.output:
        print("Error: --prepend requires --output.", file=sys.stderr)
        sys.exit(1)

    from_ref = args.from_ref
    if not from_ref:
        from_ref = get_latest_tag()
        if not from_ref:
            from_ref = get_first_commit()
            if not from_ref:
                print("Error: No tags or commits found.", file=sys.stderr)
                sys.exit(1)
            print(f"No tags found, using first commit: {from_ref[:8]}", file=sys.stderr)

    commits = get_commits(from_ref, args.to_ref, args.no_merges)
    if not commits:
        print("No commits found in range.", file=sys.stderr)
        sys.exit(0)

    if args.exclude_types:
        excluded = {t.strip() for t in args.exclude_types.split(",")}
        filtered = []
        for c in commits:
            m = CONV_PATTERN.match(c["subject"])
            if m and m.group("type") in excluded:
                continue
            filtered.append(c)
        commits = filtered

    if not commits:
        print("No commits remaining after filtering.", file=sys.stderr)
        sys.exit(0)

    print(
        f"Processing {len(commits)} commits ({from_ref}..{args.to_ref})",
        file=sys.stderr,
    )

    formatter = FORMATTERS[args.format]
    label = args.version_label or args.to_ref
    output = formatter(commits, from_ref, label)

    if args.output:
        if args.prepend:
            prepend_to_file(args.output, output)
            print(f"Changelog prepended to {args.output}", file=sys.stderr)
        else:
            with open(args.output, "w") as f:
                f.write(output)
            print(f"Changelog written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
