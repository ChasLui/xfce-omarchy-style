# Contributing

## What this repository is

One file. `README.md` is the entire guide: how to make XFCE behave like Omarchy, aimed at
an xrdp remote session on the Xorg (xorgxrdp) backend. The guide ships no installer and
no `bin/`: its shell is meant to be read and copied, and that is deliberate. `tools/`
holds repository tooling, which is not part of the guide and is never installed by it.
Agents should start from [AGENTS.md](AGENTS.md).

The only external source this guide tracks is <https://omarchy.org/manual/>. This
repository has diverged from `justnorriel/xfce-omarchy-style`: there is no upstream
remote, nothing gets rebased onto it, and no wording is kept merely to stay aligned with
it.

Propose changes as a pull request or an issue against `main`.

## Nothing here has been run on real hardware

The maintainer works on macOS. That machine has no XFCE, no X11 and no xrdp, so **no
snippet in this guide has been executed end to end**. Every behavioural claim comes from
reading upstream source or official documentation, not from observing a running system.

This is the single most important thing to know before you trust — or extend — anything
below. Keep it true: if you cannot cite it, do not assert it.

## Claims need sources

Anything the guide states about xrdp behaviour must trace back to upstream source or
official documentation — `neutrinolabs/xrdp`, `neutrinolabs/xorgxrdp`, the ArchWiki Xrdp
page, or Microsoft Learn. Cite the file and line where it helps.

What you cannot cite gets written as a suggestion, or labelled *Untested here*, with the
reason given. The guide already does this in several places; match that tone rather than
upgrading a guess into a fact.

Two specific traps:

- **Anything about gamma or the night light must stay scoped to the Xorg (xorgxrdp)
  backend.** The finding that `rdpRRCrtcSetGamma()` is a stub was verified against that
  driver only. The Xvnc backend was never examined, so do not let a claim spread to cover
  it.
- **RDP client behaviour differs per client.** A statement true of `mstsc` is usually not
  true of FreeRDP, and vice versa. Say which.

## Changing a keybinding touches four places

The guide describes each binding four times. A previous revision shipped with three of
them disagreeing, so treat this as a checklist, not a suggestion:

1. The tables under `## Keybindings`
2. The base apply block under `## Applying the Keybindings`
3. The `### Tier A` and `### Tier B` override blocks
4. Both ASCII cards under `## Quick Reference Card`

The ASCII cards have a fixed 60-character row width. If a label changes length, re-pad the
row — do not eyeball it, and do not measure it in bytes: the box-drawing characters are
multibyte, so `awk` and `wc -c` both report the wrong width.

`tools/keybindings.tsv` is the inventory all four places are checked against. Update it in
the same commit as the binding, and `tools/check.py` will prove the four agree.

For how accelerator strings must be written — `<Primary>` rather than `<Control>`,
canonical modifier order, lowercase letter keys — see
[A note on the accelerator syntax](README.md#a-note-on-the-accelerator-syntax) and the
verification steps under [Troubleshooting](README.md#troubleshooting). Those rules live in
the guide and are not repeated here, because a fifth copy is a fifth thing to keep in
sync.

New bindings must also avoid the keys an RDP client keeps for itself; the list is under
[RDP Client Setup](README.md#rdp-client-setup).

## Before you commit

```bash
python3 tools/check.py
```

That runs everything a machine can decide: markdownlint against
`.markdownlint-cli2.jsonc`, ShellCheck over every fenced `bash` block extracted on its
own (they are fragments, not standalone scripts), the four-place keybinding sync above,
the card widths, the accelerator syntax, and every internal link. It needs nothing but
`python3`, and reports `SKIP` rather than passing quietly when `markdownlint-cli2` or
`shellcheck` is missing. CI runs the same script with `--strict`, where a skip fails.

One ShellCheck finding is deliberate. At `-S style` the `.bash_profile` line that appends
to `PATH` reports SC2016: the single quotes there are intentional, since `$HOME` and
`$PATH` are meant to reach the file unexpanded. The script asserts that it stays the only
one. Do not "fix" it.
