#!/usr/bin/env python3
"""
validate_skill.py — lint a generated skill folder before installing it.

  python validate_skill.py path/to/skill-dir

Errors (exit 1): missing/invalid frontmatter, bad name, description too long, secrets,
broken relative links; in a skill that uses execution tags, a step under "## Steps"
without exactly one of [EXECUTE] / [HAND OFF] / [DECIDE] in its heading.
Warnings: no timestamp citations, video narration left in, body too long, no Source
section, no execution tags at all (skill written before the tagging rule), self-check
items 12-18 not recorded ("Self-check: 12 ✔ · 13 ✔ · … · 18 ✔") or recorded as failed (✘).
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import utf8_console  # noqa: E402

SECRET_PATTERNS = [
    (r"sk-[A-Za-z0-9_-]{20,}", "OpenAI/Anthropic-style API key"),
    (r"ghp_[A-Za-z0-9]{30,}", "GitHub token"),
    (r"AKIA[0-9A-Z]{16}", "AWS key"),
    (r"xox[baprs]-[A-Za-z0-9-]{10,}", "Slack token"),
    (r"(?i)(password|passwd|mot de passe|secret|api[_-]?key)\s*[:=]\s*['\"]?[^\s'\"<>{}]{6,}", "plain-text password / secret"),
    (r"-----BEGIN [A-Z ]*PRIVATE KEY-----", "private key"),
]
# narration patterns (English and French videos)
NARRATION = [
    r"(?i)\bin this video\b", r"(?i)\bdans cette vid[ée]o\b", r"(?i)\bsubscribe\b", r"(?i)\babonnez\b",
    r"(?i)\bsmash (that|the) like\b", r"(?i)\blike and subscribe\b", r"(?i)\bso what we'?re gonna do\b",
    r"(?i)\balors ce qu'on va faire\b", r"(?i)\bas you can see\b", r"(?i)\bcomme vous pouvez (le )?voir\b",
]
TAG_RE = re.compile(r"\[(EXECUTE|HAND OFF|DECIDE)\]")
SELF_CHECK_ITEMS = range(12, 19)


def step_headings(body):
    """(line number, heading) for every ### heading inside the "## Steps" section(s)."""
    steps, in_steps, fence = [], False, False
    for i, line in enumerate(body.splitlines(), 1):
        if line.lstrip().startswith(("```", "~~~")):
            fence = not fence
            continue
        if fence:
            continue
        if re.match(r"^##\s", line):
            in_steps = bool(re.match(r"^##\s+Steps\b", line, re.I))
        elif in_steps and re.match(r"^###\s", line):
            steps.append((i, line.strip()))
    return steps


def check_tags(body, errors, warns):
    steps = step_headings(body)
    if not steps:
        return
    counts = [(ln, h, len(TAG_RE.findall(h))) for ln, h in steps]
    if not any(c for _, _, c in counts):
        warns.append(f"no execution tag on any of the {len(steps)} steps: tag each heading "
                     "[EXECUTE], [HAND OFF] or [DECIDE] (skill written before the tagging rule?)")
        return
    for ln, h, c in counts:
        if c != 1:
            errors.append(f"step heading has {c} execution tags (exactly 1 expected): \"{h[:70]}\"")


def check_self_check(text, warns):
    m = re.search(r"(?im)^[>\s]*self-check\s*:(.*)$", text)
    if not m:
        warns.append("self-check items 12-18 not recorded: add \"> Self-check: 12 ✔ · 13 ✔ · … · 18 ✔\" "
                     "under the Verification block (✘ + reason for an unresolved item)")
        return
    marks = dict(re.findall(r"\b(1[2-8])\s*([✔✓✘✗])", m.group(1)))
    missing = [str(i) for i in SELF_CHECK_ITEMS if str(i) not in marks]
    failed = [i for i, s in marks.items() if s in "✘✗"]
    if missing:
        warns.append(f"self-check line does not mark item(s) {', '.join(missing)}")
    if failed:
        warns.append(f"self-check item(s) {', '.join(sorted(failed))} marked as failed (✘): fix or explain in the skill")


def parse_frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None, text
    fm = {}
    for line in m.group(1).splitlines():
        mm = re.match(r"^([A-Za-z_-]+):\s*(.*)$", line)
        if mm:
            fm[mm.group(1)] = mm.group(2).strip().strip('"').strip("'")
    return fm, text[m.end():]


def main():
    utf8_console()
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    root = Path(sys.argv[1])
    skill = root / "SKILL.md" if root.is_dir() else root
    root = skill.parent
    errors, warns = [], []
    if not skill.exists():
        sys.exit(f"ERROR: {skill} not found")
    text = skill.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)

    if fm is None:
        errors.append("YAML frontmatter missing (--- name/description --- at the top of the file)")
        fm = {}
    name, desc = fm.get("name", ""), fm.get("description", "")
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name or ""):
        errors.append(f"invalid name \"{name}\": lower-case kebab-case expected")
    if len(name) > 64:
        errors.append("name > 64 characters")
    if re.search(r"claude|anthropic", name):
        errors.append("name must not contain 'claude' or 'anthropic'")
    if name and root.name != name and root.name not in ("", "."):
        warns.append(f"folder \"{root.name}\" does not match name \"{name}\"")
    if not desc:
        errors.append("empty description")
    elif len(desc) > 1024:
        errors.append(f"description too long ({len(desc)} > 1024)")
    elif len(desc) < 60:
        warns.append("very short description: say WHEN to use the skill (triggers)")
    if "<" in desc or ">" in desc:
        errors.append("description must not contain < or >")

    files = [skill] + [p for p in root.rglob("*") if p.is_file() and p != skill and p.suffix in (".md", ".txt", ".py", ".sh", ".json", ".yaml", ".yml")]
    for f in files:
        t = f.read_text(encoding="utf-8", errors="ignore")
        for pat, label in SECRET_PATTERNS:
            for m in re.finditer(pat, t):
                frag = m.group(0)
                if re.search(r"(?i)<[^>]+>|\$\{?[A-Z_]+|your[_-]|votre|xxx|\*\*\*|example|exemple|placeholder|changeme", frag):
                    continue
                errors.append(f"{f.relative_to(root)}: possible {label}: \"{frag[:24]}…\" → replace with a placeholder")

    for link in re.findall(r"\]\(([^)#\s]+)\)", body):
        if not re.match(r"^[a-z]+://", link) and not (root / link).exists():
            errors.append(f"broken relative link: {link}")

    n_lines = body.count("\n")
    if n_lines > 500:
        warns.append(f"SKILL.md has {n_lines} lines: move theory to references/ (target < 500)")
    cites = re.findall(r"\[t=\d+:\d{2}(?::\d{2})?\]", text)
    if not cites:
        warns.append("no [t=MM:SS] citation: steps cannot be traced back to the video")
    for pat in NARRATION:
        m = re.search(pat, body)
        if m:
            warns.append(f"video narration left in the text (\"{m.group(0)}\") → rewrite as an instruction")
    if not re.search(r"(?i)source|provenance", text):
        warns.append("no Source section (video URL/title)")
    check_tags(body, errors, warns)
    check_self_check(text, warns)

    print(f"Skill: {name or '?'}  |  {n_lines} lines  |  {len(cites)} timestamp citations  |  {len(files)} files")
    for w in warns:
        print(f"  ⚠  {w}")
    for e in errors:
        print(f"  ✗  {e}")
    if errors:
        print("FAILED")
        sys.exit(1)
    print("OK" + (" (with warnings)" if warns else ""))


if __name__ == "__main__":
    main()
