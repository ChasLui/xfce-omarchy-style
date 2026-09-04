# AGENTS.md

## What you are editing

`README.md` is the entire guide — one file, ~2500 lines, on making XFCE behave like
Omarchy over an xrdp session. `tools/` is repository tooling and is not part of the
guide. Read [CONTRIBUTING.md](CONTRIBUTING.md) once; it holds the rules, and they are
not repeated here.

## Run this before you finish

```bash
python3 tools/check.py
```

No dependencies beyond `python3`. It reports `SKIP` when `markdownlint-cli2` or
`shellcheck` is absent, so a green run on a machine without them is not a full run; CI
uses `--strict`, where a skip fails.

Do not hand-roll a one-off checker in your scratch directory. Every check below was
written that way at least once and thrown away. If something is worth verifying twice,
add it to `tools/check.py` instead.

## What the machine already decides

markdownlint · ShellCheck over each fenced `bash` block, including the one intentional
SC2016 · fence pairing · unambiguous heading anchors · every internal link · the table of
contents · reference-card row width · accelerator syntax · the
[four-place keybinding sync](CONTRIBUTING.md#changing-a-keybinding-touches-four-places).

`tools/keybindings.tsv` is the inventory that last check reads: 125 rows, tab separated,
one per accelerator plus one per table row that has no binding. **Read it instead of
parsing the Markdown** when you need to know what this guide binds. Change a binding and
you change the TSV in the same commit, or the sync check fails — which is the point, since
that sync has silently broken before.

## What the machine cannot decide — so it is on you

The checker proves the guide is *consistent*. It cannot prove it is *true*, and nothing
here has ever been run on real hardware. Before you assert anything, read
[Nothing here has been run on real hardware](CONTRIBUTING.md#nothing-here-has-been-run-on-real-hardware)
and [Claims need sources](CONTRIBUTING.md#claims-need-sources). What you cannot cite is
written as a suggestion or labelled *Untested here*.

The guide links its own material heavily rather than restating it. Keep doing that: every
copy is another thing to keep in sync, and this file is deliberately not a second copy of
`CONTRIBUTING.md`.

## No upstream

This repository has diverged from `justnorriel/xfce-omarchy-style`. There is no upstream
remote and nothing is rebased onto it. The only external source tracked is
<https://omarchy.org/manual/>. Do not propose syncing with the fork parent.
