#!/usr/bin/env python3
"""Machine-checkable invariants for this repository.

CONTRIBUTING.md states these rules in prose; this script is the part a machine can
decide. Run it before every commit:

    python3 tools/check.py

Exit status is 0 only when every check passed or was skipped for a missing external
tool. External tools that are absent are reported as SKIP, never silently ignored.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
TSV = ROOT / "tools" / "keybindings.tsv"
# Every Markdown file at the top level, so a new one cannot escape the lint.
MD_FILES = sorted(p.name for p in ROOT.glob("*.md"))

# GTK canonical modifier order. A binding may use any subsequence of this.
MOD_ORDER = ["<Shift>", "<Primary>", "<Alt>", "<Super>"]
# Keys written as X keysyms rather than a bare character.
NAMED_KEYS = {
    "Return", "space", "Print", "Tab", "Escape", "grave", "BackSpace",
    "Delete", "comma", "period", "Left", "Right", "Up", "Down", "minus", "equal",
}
# Card rows that summarise a group of bindings rather than naming one. Each is
# assigned to its accelerators through the `card` column of the TSV; the empty
# label belongs to the wrapped mstsc setting, which is not a binding at all.
CARD_PROSE_LABELS = {""}

lines = README.read_text(encoding="utf-8").split("\n")


def _fence_mask() -> list[bool]:
    """True for every line inside a fenced block. Shell comments look exactly like
    Markdown headings, so heading scans have to skip code."""
    mask, inside = [], False
    for ln in lines:
        if re.match(r"^```(?!`)", ln):
            inside = not inside
            mask.append(True)
        else:
            mask.append(inside)
    return mask


IN_FENCE = _fence_mask()


def heading_at(i: int) -> re.Match | None:
    if IN_FENCE[i]:
        return None
    return re.match(r"^(#{1,6}) (.+)$", lines[i])


results: list[tuple[str, str, list[str]]] = []


def report(status: str, name: str, detail: list[str] | None = None) -> None:
    results.append((status, name, detail or []))


# --------------------------------------------------------------------------- #
# Region locators. Everything is found by heading text, never by line number.
# --------------------------------------------------------------------------- #

def section(heading: str) -> tuple[int, int]:
    """Line range of a section, from its heading to the next heading of the same
    or a higher level."""
    start = lines.index(heading)
    level = len(heading) - len(heading.lstrip("#"))
    end = start + 1
    while end < len(lines):
        m = heading_at(end)
        if m and len(m.group(1)) <= level:
            break
        end += 1
    return start, end


def fenced(start: int, end: int, lang: str) -> list[tuple[int, int]]:
    """Line ranges of the fenced blocks of one language inside a region."""
    out, i = [], start
    while i < end:
        if lines[i].strip() == "```" + lang:
            j = i + 1
            while j < end and lines[j].strip() != "```":
                j += 1
            out.append((i + 1, j))
            i = j
        i += 1
    return out


def shebang_block(heading: str) -> tuple[int, int]:
    """The `#!/bin/bash` block of a section. Tier B opens with a different bash
    block, so 'the first block' is not good enough."""
    a, b = section(heading)
    for i, j in fenced(a, b, "bash"):
        if lines[i].strip() == "#!/bin/bash":
            return i, j
    raise SystemExit(f"no #!/bin/bash block under {heading!r}")


APPLY = "### Apply"
TIER_A = "### Tier A — Print-key aliases"
TIER_B = "### Tier B — no-Super fallback"
BLOCKS = [("base", APPLY), ("A", TIER_A), ("B", TIER_B)]

BIND_RE = re.compile(r"""^\s*(wm|cmd)\s+(['"])(?P<accel>.+?)\2\s+(?P<target>.+?)\s*$""")


def unquote(s: str) -> str:
    s = s.strip()
    if len(s) > 1 and s[0] in "'\"" and s[-1] == s[0]:
        return s[1:-1]
    return s


def readme_bindings() -> set[tuple[str, str, str, str]]:
    """(tier, accel, kind, target) for every binding the guide applies.

    `for i in 1 2 3 4` loops are expanded, since that is the only shell control
    flow these three blocks use."""
    out = set()
    for tier, heading in BLOCKS:
        a, b = shebang_block(heading)
        for line in lines[a:b]:
            if line.lstrip().startswith(("wm()", "cmd()")):
                continue
            m = BIND_RE.match(line)
            if not m:
                continue
            accel, target = m.group("accel"), unquote(m.group("target"))
            if "$i" in accel:
                for i in "1234":
                    out.add((tier, accel.replace("$i", i), m.group(1),
                             target.replace("${i}", i)))
            else:
                out.add((tier, accel, m.group(1), target))
    return out


def table_rows() -> dict[str, list[str]]:
    """First column of every keybinding table, keyed by its `###` heading."""
    out: dict[str, list[str]] = {}
    a, b = section("## Keybindings")
    cur, in_table = None, False
    for line in lines[a:b]:
        if line.startswith("### "):
            cur, in_table = line[4:].strip(), False
            continue  # tables never sit inside a fence, so a plain scan is fine
        if not line.startswith("| "):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells[0] in ("Omarchy", "Key"):
            in_table = True
            continue
        if cells[0].startswith("-") or not in_table or cur is None:
            continue
        out.setdefault(cur, []).append(cells[0])
    for heading in (TIER_A, TIER_B):
        name = heading[4:]
        a, b = section(heading)
        in_table = False
        for line in lines[a:b]:
            if not line.startswith("| "):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if cells[0] == "Alias":
                in_table = True
                continue
            if cells[0].startswith("-") or not in_table:
                continue
            out.setdefault(name, []).append(cells[0])
    return out


def card_rows() -> list[str]:
    a, b = section("## Quick Reference Card")
    return [ln for ln in lines[a:b] if ln.startswith("║")]


def card_labels() -> list[str]:
    return [ln[1:].split("=")[0].strip() for ln in card_rows() if "=" in ln]


def read_tsv() -> list[dict[str, str]]:
    raw = TSV.read_text(encoding="utf-8").rstrip("\n").split("\n")
    header = raw[0].split("\t")
    return [dict(zip(header, r.split("\t"))) for r in raw[1:]]


# --------------------------------------------------------------------------- #
# Checks
# --------------------------------------------------------------------------- #

def check_markdownlint() -> None:
    if not shutil.which("markdownlint-cli2"):
        report("SKIP", "markdownlint", ["markdownlint-cli2 is not installed"])
        return
    p = subprocess.run(["markdownlint-cli2", *MD_FILES], cwd=ROOT,
                       capture_output=True, text=True)
    if p.returncode == 0:
        report("PASS", "markdownlint")
    else:
        report("FAIL", "markdownlint", (p.stdout + p.stderr).strip().split("\n"))


def check_shellcheck() -> None:
    """Every ```bash block on its own. They are fragments, not scripts.

    At -S style the guide reports exactly one SC2016, on the line that appends to
    ~/.bash_profile: the single quotes there are deliberate, so $HOME and $PATH
    reach the file unexpanded. CONTRIBUTING.md says not to 'fix' it; this asserts
    that it is still the only one."""
    if not shutil.which("shellcheck"):
        report("SKIP", "shellcheck", ["shellcheck is not installed"])
        return
    with tempfile.TemporaryDirectory() as tmp:
        blocks, n = [], 0
        for a, b in fenced(0, len(lines), "bash"):
            n += 1
            f = Path(tmp) / f"blk-{n:03d}.sh"
            f.write_text("\n".join(lines[a:b]) + "\n", encoding="utf-8")
            blocks.append(f)
        args = [str(f) for f in blocks]
        p = subprocess.run(["shellcheck", "-S", "warning", "-s", "bash", *args],
                           capture_output=True, text=True)
        if p.returncode != 0:
            report("FAIL", f"shellcheck ({n} bash blocks)",
                   (p.stdout + p.stderr).strip().split("\n")[:40])
            return
        q = subprocess.run(["shellcheck", "-S", "style", "-f", "gcc", "-s", "bash", *args],
                           capture_output=True, text=True)
        sc2016 = [ln for ln in q.stdout.split("\n") if "SC2016" in ln]
        bad = [ln for ln in sc2016 if "bash_profile" not in _source_line(ln, tmp)]
        if len(sc2016) != 1 or bad:
            report("FAIL", f"shellcheck ({n} bash blocks)",
                   ["expected exactly one SC2016, on the ~/.bash_profile line",
                    *sc2016])
            return
    report("PASS", f"shellcheck ({n} bash blocks)")


def _source_line(gcc_line: str, tmp: str) -> str:
    m = re.match(r"^(.+?):(\d+):", gcc_line)
    if not m:
        return ""
    try:
        return Path(m.group(1)).read_text(encoding="utf-8").split("\n")[int(m.group(2)) - 1]
    except (OSError, IndexError):
        return ""


def check_fences() -> None:
    opens = [i for i, ln in enumerate(lines) if re.match(r"^```(?!`)", ln)]
    if len(opens) % 2 == 0:
        report("PASS", f"code fences ({len(opens) // 2} pairs)")
    else:
        report("FAIL", "code fences",
               [f"{len(opens)} fence markers, an odd number — one is unclosed"])


def slug(text: str) -> str:
    """GitHub's heading anchor. Each space becomes one hyphen, so a heading with a
    ' — ' in it legitimately produces a double hyphen."""
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)   # links -> their text
    t = t.replace("`", "").replace("*", "").replace("_", "")
    t = t.lower()
    t = re.sub(r"[^\w\- ]", "", t)
    return t.replace(" ", "-")


def check_duplicate_headings() -> None:
    seen: dict[str, int] = {}
    dupes = []
    for i in range(len(lines)):
        m = heading_at(i)
        if not m or len(m.group(1)) not in (2, 3):
            continue
        s = slug(m.group(2))
        if s in seen:
            dupes.append(f"{s!r} appears {seen[s] + 1}x — GitHub would number the anchors")
        seen[s] = seen.get(s, 0) + 1
    if dupes:
        report("FAIL", "unique heading anchors", dupes)
    else:
        report("PASS", f"unique heading anchors ({len(seen)} headings)")


def _anchors_of(name: str) -> set[str]:
    text = (ROOT / name).read_text(encoding="utf-8").split("\n")
    out, inside = set(), False
    for ln in text:
        if re.match(r"^```(?!`)", ln):
            inside = not inside
            continue
        if inside:
            continue
        if (m := re.match(r"^#{1,6} (.+)$", ln)):
            out.add(slug(m.group(1)))
    return out


def check_anchors() -> None:
    """Every `](#x)` and every `](other.md#x)` across the top-level Markdown files.
    Cross-file links rot the fastest, since no single file's history shows the break."""
    anchors = {name: _anchors_of(name) for name in MD_FILES}
    dead, n = [], 0
    for name in MD_FILES:
        for i, ln in enumerate((ROOT / name).read_text(encoding="utf-8").split("\n"), 1):
            for target in re.findall(r"\]\((?:([\w.-]+\.md))?#([^)]+)\)", ln):
                n += 1
                where, frag = target[0] or name, target[1]
                if where not in anchors:
                    dead.append(f"{name}:{i}  links into {where}, which is not checked")
                elif frag not in anchors[where]:
                    dead.append(f"{name}:{i}  {where}#{frag}")
    if dead:
        report("FAIL", "internal links", dead)
    else:
        report("PASS", f"internal links ({n} resolve across {len(MD_FILES)} files)")


def check_toc() -> None:
    a, b = section("## Table of Contents")
    listed = [m.group(1) for ln in lines[a:b] if (m := re.match(r"^- \[.+\]\(#(.+)\)$", ln))]
    tops = [slug(lines[i][3:]) for i in range(len(lines))
            if (m := heading_at(i)) and len(m.group(1)) == 2
            and lines[i][3:] != "Table of Contents"]
    stop = tops.index(slug("Uninstall")) + 1 if slug("Uninstall") in tops else len(tops)
    expected = tops[:stop]
    missing = [t for t in expected if t not in listed]
    extra = [t for t in listed if t not in expected]
    if missing or extra:
        report("FAIL", "table of contents",
               [f"missing: {m}" for m in missing] + [f"unexpected: {e}" for e in extra])
    else:
        report("PASS", f"table of contents ({len(listed)} entries)")


def check_card_width() -> None:
    """CONTRIBUTING.md: 'a fixed 60-character row width ... do not eyeball it'.
    Counted in codepoints — the box-drawing characters are multibyte, so byte
    counting reports the wrong width."""
    bad = [f"width {len(r)}, expected 60: {r}" for r in card_rows() if len(r) != 60]
    if bad:
        report("FAIL", "reference card row width", bad)
    else:
        report("PASS", f"reference card row width ({len(card_rows())} rows at 60)")


def check_accel_syntax() -> None:
    """Scoped to ```bash blocks on purpose: the prose forbidding <Ctrl> has to be
    able to spell <Ctrl>."""
    problems = []
    for a, b in fenced(0, len(lines), "bash"):
        for n, line in enumerate(lines[a:b], a + 1):
            for accel in re.findall(r"(?:<[A-Za-z]+>)+[A-Za-z0-9$_{}]*", line):
                mods = re.findall(r"<[A-Za-z]+>", accel)
                # `<url>`, `<command>` and friends are usage-string placeholders,
                # not accelerators. Only look at runs that name a real modifier.
                if not any(m in MOD_ORDER or m in ("<Ctrl>", "<Control>") for m in mods):
                    continue
                key = accel[len("".join(mods)):]
                for m in mods:
                    if m in ("<Ctrl>", "<Control>"):
                        problems.append(f"README.md:{n}  {accel}  — Ctrl is <Primary>")
                    elif m not in MOD_ORDER:
                        problems.append(f"README.md:{n}  {accel}  — unknown modifier {m}")
                known = [m for m in mods if m in MOD_ORDER]
                if known != [m for m in MOD_ORDER if m in known]:
                    problems.append(
                        f"README.md:{n}  {accel}  — modifier order must be "
                        + "".join(MOD_ORDER))
                if "$" in key or not key:
                    continue
                if len(key) == 1:
                    if key.isalpha() and not key.islower():
                        problems.append(f"README.md:{n}  {accel}  — letter keys are lowercase")
                elif key not in NAMED_KEYS and not key.startswith("XF86"):
                    problems.append(f"README.md:{n}  {accel}  — unknown keysym {key!r}")
    if problems:
        report("FAIL", "accelerator syntax", sorted(set(problems)))
    else:
        report("PASS", "accelerator syntax")


def check_keybinding_sync() -> None:
    """CONTRIBUTING.md: changing a keybinding touches four places, and a previous
    revision shipped with three of them disagreeing. tools/keybindings.tsv is the
    inventory all four are checked against."""
    tsv = read_tsv()
    problems = []

    want = {(r["tier"], r["accel"], r["kind"], r["target"]) for r in tsv if r["accel"]}
    have = readme_bindings()
    for row in sorted(want - have):
        problems.append(f"in the TSV but not applied by the guide: {row}")
    for row in sorted(have - want):
        problems.append(f"applied by the guide but missing from the TSV: {row}")

    tables = table_rows()
    for r in tsv:
        if not r["table"]:
            continue
        if r["table"] not in tables:
            problems.append(f"TSV names a table that does not exist: {r['table']!r}")
        elif r["keys"] not in tables[r["table"]]:
            problems.append(f"{r['keys']} is not a row of the {r['table']!r} table")
    claimed = {(r["table"], r["keys"]) for r in tsv}
    for name, rows in tables.items():
        for keys in rows:
            if (name, keys) not in claimed:
                problems.append(f"table row absent from the TSV: [{name}] {keys}")

    labels = card_labels()
    for r in tsv:
        for label in filter(None, r["card"].split("|")):
            if label not in labels:
                problems.append(f"TSV names a card row that does not exist: {label!r}")
    on_card = {label for r in tsv for label in filter(None, r["card"].split("|"))}
    for label in labels:
        if label not in on_card and label not in CARD_PROSE_LABELS:
            problems.append(f"card row absent from the TSV: {label!r}")

    if problems:
        report("FAIL", "keybinding sync (four places)", problems)
    else:
        report("PASS", f"keybinding sync ({len(want)} bindings, "
                       f"{len(tables)} tables, {len(labels)} card rows)")


def main(argv: list[str]) -> int:
    strict = "--strict" in argv  # CI: a missing external tool must not pass quietly
    check_markdownlint()
    check_shellcheck()
    check_fences()
    check_duplicate_headings()
    check_anchors()
    check_toc()
    check_card_width()
    check_accel_syntax()
    check_keybinding_sync()

    failed = 0
    for status, name, detail in results:
        print(f"{status:4}  {name}")
        for d in detail:
            print(f"        {d}")
        if status == "FAIL":
            failed += 1
    skipped = sum(1 for s, _, _ in results if s == "SKIP")
    print(f"\n{len(results) - failed - skipped} passed, {failed} failed, {skipped} skipped")
    if skipped and strict:
        print("--strict: a skipped check counts as a failure")
        return 1
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
