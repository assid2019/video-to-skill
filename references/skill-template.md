# Generated skill template

Copy this skeleton into `<name>/SKILL.md` and adapt it. Remove sections that do not apply (e.g. "Methods" for a pure CLI tutorial).

Order of work: **A. score** (before writing) → write with **B. execution tags** → **C. self-check** → `validate_skill.py` → **D. dry run**.
A–D adapt Stages 2, 4, 5 (items 12–18) and 6 of [jalaalrd/video-to-skill](https://github.com/jalaalrd/video-to-skill) (MIT). Its MCP tool-verification stage (3C) is deliberately left out: these skills target device-level steps (shell, SSH, device CLI), not MCP connectors.

## A. Four-way scoring (before writing anything)

Score the video from your working notes, i.e. narration **and** frames (the screen wins), on four criteria, each HIGH / MEDIUM / LOW:

| Criterion | Question | HIGH | LOW |
|---|---|---|---|
| **Completeness** | Does it cover the whole process, or are there "and then you just…" gaps / cuts? | every step shown, start to verified result | major steps skipped or cut |
| **Specificity** | Real commands, values, menu paths, or vague "configure it"? | exact commands / values readable on screen | only vague descriptions |
| **Accuracy** | Are the steps current and correct (deprecated syntax, old UI, a step that does not do what the video claims)? | matches current docs | outdated or contradicts docs |
| **Executability** | How much can Claude itself run in the target environment (Claude Code by default)? | mostly shell / CLI / code / device CLI reachable over SSH | mostly GUI clicks, physical actions, drag-and-drop |

Decision rules:
- **All HIGH** → write the skill.
- **Any MEDIUM** → fill the gaps first: official docs for every vague, missing or outdated step, each marked `➕ added (source: <URL>)` and actually checked (open the page), or marked `unchecked`.
- **Any LOW** → judge whether it can be salvaged. Completeness or Specificity LOW with nothing recoverable → no skill: write the short "not instructional" report from SKILL.md §3. Never invent steps to fill a skill.
- **Executability LOW** → still write the skill, as a guided checklist (mostly `[HAND OFF]`), and say so in the final message with the approximate share of hand-offs. Do not ask the user: the run has no questions besides cookies.

Write the result in the skill, right under the Verification block (see the skeleton).

## B. Execution tags

Tag **every** step heading with exactly one tag, at the end of the heading: `### 3. Add DHCP for the IoT network [EXECUTE]`. Timestamp citations `[t=MM:SS]` stay where they are (end of the step / success line).

- **`[EXECUTE]`**: Claude runs it itself, from the environment the skill runs in: local shell, code, file edits, or a device CLI reached through a session Claude controls (`ssh user@device '<command>'`, a REST API). Write it as an instruction **to Claude**, with the exact command.
- **`[HAND OFF]`**: Claude cannot do it: physical action (plug a cable, press a button), a GUI with no CLI/API equivalent, a device with no remote access, anything needing the user's eyes or hands. Write the **exact** click path or the exact command to paste, then end with: "Wait for confirmation before continuing."
- **`[DECIDE]`**: needs the user's judgment (which port, which subnet, which trade-off). Present the options with their trade-off, the user picks, Claude continues. Use this instead of "adjust as needed".

Device commands: tag them `[EXECUTE]` and add, in **Before starting**, an access check (e.g. `ssh <user>@<router> '/system resource print'`). Then state the fallback: "If Claude has no shell access to the device, steps N–M become `[HAND OFF]`: give the user the exact commands to paste into the device terminal."

## C. Self-check before `validate_skill.py`

Go through every item; fix each failure, then run the validator.

- [ ] **12.** Every step is tagged `[EXECUTE]`, `[HAND OFF]` or `[DECIDE]`: no untagged step.
- [ ] **13.** No step tells the user to do something Claude could execute → rewrite as `[EXECUTE]`.
- [ ] **14.** No step tells the user to write, generate or create content Claude could produce (config file, script, rule) → Claude produces it.
- [ ] **15.** No "configure as needed", "adjust to your preferences", "set up appropriately" → give the exact value, or make it a `[DECIDE]` with options.
- [ ] **16.** Every `[HAND OFF]` has the exact click path or command **and** ends with "Wait for confirmation before continuing."
- [ ] **17.** A "When the user returns" section exists with a persistence strategy (what to re-check, what to keep in a config file).
- [ ] **18.** Read the skill as Claude about to execute it. Wherever you would think "I could do this myself", fix it.

## D. Dry run (after validation)

Replay **only the safe bash steps** in a throwaway folder, never in the user's files:
```bash
DRY=$(mktemp -d) && cd "$DRY"    # Windows/Git Bash: mktemp -d works too
```
- **Safe** = runs on this machine, writes only inside `$DRY`, needs no `sudo`/admin, does not change network, firewall, services or system settings, and touches no remote device or account.
- **Never replayed**: device commands (RouterOS, SSH to a real host, etc.), anything destructive or irreversible, `[HAND OFF]` and `[DECIDE]` steps. Walk through those on paper instead: "Step 3 [EXECUTE]: I would run …; expected result: …".
- Every failure found → fix the step or add it to Troubleshooting.
- Write the outcome in the Verification block, counted honestly: `> Verification: dry run 2/2 safe bash steps OK on YYYY-MM-DD; steps 1–5 (device CLI) walked through, not executed.` If there was no safe bash step: "dry run: no safe local step; not verified by execution". Never a misleading badge.

Then delete `$DRY`.

## Skeleton

~~~markdown
---
name: <short-kebab-case>
description: <What the skill lets you do, in one sentence.> Use when <situations / trigger phrases: "…", "…">.
---

# <Action-oriented title>

> Verification: <dry run N/M safe bash steps OK on YYYY-MM-DD | not verified by execution>;
> <what could not be verified and why>.
> Assessment: Completeness <H/M/L> · Specificity <H/M/L> · Accuracy <H/M/L> · Executability <H/M/L> (target: <Claude Code | …>)
> Steps: <X> [EXECUTE] · <Y> [HAND OFF] · <Z> [DECIDE]

<1–2 sentences: what Claude executes, and what the user ends up with.>

## Prerequisites
- <tool> <version seen on screen> [t=0:42]
- <account / access / file needed>

## Before starting   ← dependency and access checks
- <check command, e.g. `ssh <user>@<device> '<status command>'`> → if it fails: <fallback, e.g. steps N–M become [HAND OFF]>

## Steps   ← for a procedure

### 1. <Verb + object> [EXECUTE]
<instruction to Claude>
```bash
<exact command copied from the screen>
```
✔ Success: <what should be displayed / exist> [t=1:05]

### 2. <Verb + object> [HAND OFF]
Tell the user: "<exact click path / command to paste>". Wait for confirmation before continuing. [t=…]

### 3. <Verb + object> [DECIDE]
Present the options:
- <Option A> — best for <trade-off>
- <Option B> — best for <trade-off>
Continue with the user's choice. [t=…]

### 4. …
⚠ uncertain: <what is unclear and why> [t=3:12]
➕ added: <step missing from the video but needed> (source: <official docs URL>)

## Method map   ← for a course / know-how (especially long videos)
| Problem / situation | Method | Details |
|---|---|---|
| <what the user wants to do> | <method name> | [references/01-<theme>.md](references/01-<theme>.md) |

## Methods
### <Actionable name: verb + object>
- When to use it: <situation>
- Steps: 1. … [t=…]  2. … [t=…]
- Decision rules: if … → … [t=…]
- Why it works: … [t=…]
- Example from the video: … [t=…]
- Mistakes to avoid: … — <reason> [t=…]

## Worked example
<an example from the video, redone step by step> [t=…]

## Variants
- <alternative case shown or mentioned> [t=…]

## Troubleshooting
- <symptom> → <cause> → <fix> [t=…]

## When the user returns
- Same session: reuse the values already chosen (<list>), skip the checks already passed, go straight to the next step.
- New session: re-run "Before starting", then read the current state (<read-only status command>) before changing anything. Offer to save the chosen values in `<name>-config.md` so setup can be skipped next time.

## Going further
- [Concepts](references/concepts.md) — theory explained in the video

## Source
- Video: "<title>" — <channel/author>, <date> — <URL>
- Transcript: <manual subtitles | auto-captions | whisper small | none>
- Extracted on <YYYY-MM-DD> with video-to-skill
~~~

## Good and bad examples

| ❌ Narration | ✅ Instruction |
|---|---|
| "So what we're gonna do now is install the thing" | "Install the package: `pip install requests` [t=0:31]" |
| "He types something like sum" (audio) | "Enter `=SUM(B3:B10)` in B11 [t=2:14]" (screen) |
| "And there you go, it works!" | "✔ Success: the terminal prints `200`" |
| Step invented to fill a gap | `⚠ uncertain: the video cuts between [t=4:01] and [t=4:20]` |
| "### 2. Configure the port as needed" | "### 2. Choose the IoT port [DECIDE]: ether5 (spare) or another free port …" |
| "### 3. Open WinBox and add the address" (Claude has SSH) | "### 3. Add the address [EXECUTE]: `ssh admin@<router> '/ip address add …'`" |
