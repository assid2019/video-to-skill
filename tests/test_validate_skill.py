#!/usr/bin/env python3
"""
test_validate_skill.py — tests for the execution-tag and self-check rules of scripts/validate_skill.py.

  python tests/test_validate_skill.py        (standard library only; exit 0 = all pass)

Each case writes a small skill into a temporary folder and runs the validator on it,
checking the exit code (0 = OK, 1 = FAILED) and the warnings it prints.
"""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VALIDATOR = ROOT / "scripts" / "validate_skill.py"
NAME = "sample-skill"

FULL_SELF_CHECK = "> Self-check: 12 ✔ · 13 ✔ · 14 ✔ · 15 ✔ · 16 ✔ · 17 ✔ · 18 ✔"


def make_skill(steps, self_check=FULL_SELF_CHECK, extra=""):
    """Build a SKILL.md body: valid frontmatter, a Steps section with the given headings, a Source section."""
    step_text = "\n\n".join(f"{h}\nRun `echo ok`. [t=0:0{i}]" for i, h in enumerate(steps, 1))
    return (
        "---\n"
        f"name: {NAME}\n"
        "description: Sample skill used by the validator tests. Use when testing that execution tags "
        "and the self-check record are checked.\n"
        "---\n\n"
        "# Sample\n\n"
        "> Verification: not verified by execution.\n"
        f"{self_check}\n\n"
        "## Steps\n\n"
        f"{step_text}\n\n"
        f"{extra}"
        "## Source\n- Video: test\n"
    )


TAGGED = ["### 1. First [EXECUTE]", "### 2. Second [HAND OFF]", "### 3. Third [DECIDE]"]


class ValidatorTagAndSelfCheckTests(unittest.TestCase):
    def run_validator(self, text):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / NAME
            d.mkdir()
            (d / "SKILL.md").write_text(text, encoding="utf-8", newline="\n")
            r = subprocess.run([sys.executable, str(VALIDATOR), str(d)], capture_output=True,
                               text=True, encoding="utf-8", errors="replace")
            return r.returncode, r.stdout + r.stderr

    def test_fully_tagged_with_self_check_passes_clean(self):
        code, out = self.run_validator(make_skill(TAGGED))
        self.assertEqual(code, 0, out)
        self.assertNotIn("⚠", out, out)

    def test_one_untagged_step_fails(self):
        code, out = self.run_validator(make_skill(TAGGED + ["### 4. Fourth"]))
        self.assertEqual(code, 1, out)
        self.assertIn("has 0 execution tags", out)

    def test_two_tags_on_one_step_fails(self):
        code, out = self.run_validator(make_skill(["### 1. First [EXECUTE] [DECIDE]", "### 2. Second [EXECUTE]"]))
        self.assertEqual(code, 1, out)
        self.assertIn("has 2 execution tags", out)

    def test_no_tags_at_all_only_warns(self):
        code, out = self.run_validator(make_skill(["### 1. First", "### 2. Second"]))
        self.assertEqual(code, 0, out)
        self.assertIn("no execution tag on any of the 2 steps", out)

    def test_heading_inside_code_block_is_not_a_step(self):
        fenced = "### 4. Fourth [EXECUTE]\n```bash\n### not a step\n```\n\n"
        code, out = self.run_validator(make_skill(TAGGED, extra=fenced))
        self.assertEqual(code, 0, out)
        self.assertNotIn("not a step", out)

    def test_missing_self_check_warns(self):
        code, out = self.run_validator(make_skill(TAGGED, self_check=""))
        self.assertEqual(code, 0, out)
        self.assertIn("self-check items 12-18 not recorded", out)

    def test_partial_self_check_warns_about_missing_items(self):
        code, out = self.run_validator(make_skill(TAGGED, self_check="> Self-check: 12 ✔ · 13 ✔ · 18 ✔"))
        self.assertEqual(code, 0, out)
        self.assertIn("does not mark item(s) 14, 15, 16, 17", out)

    def test_failed_self_check_item_warns(self):
        line = "> Self-check: 12 ✔ · 13 ✔ · 14 ✔ · 15 ✔ · 16 ✘ (path not documented) · 17 ✔ · 18 ✔"
        code, out = self.run_validator(make_skill(TAGGED, self_check=line))
        self.assertEqual(code, 0, out)
        self.assertIn("item(s) 16 marked as failed", out)

    def test_bundled_example_skill_passes_clean(self):
        r = subprocess.run([sys.executable, str(VALIDATOR), str(ROOT / "examples" / "python-venv-requests")],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("⚠", r.stdout, r.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
