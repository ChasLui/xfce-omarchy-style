# Contributing

## What this repository is

One file. `README.md` is the entire guide: how to make XFCE behave like Omarchy, aimed at
an xrdp remote session on the Xorg (xorgxrdp) backend. There is no installer, no `bin/`,
no scripts on disk — the shell in the guide is meant to be read and copied, and that is
deliberate.

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

1. The nine tables under `## Keybindings`
2. The base apply block under `## Applying the Keybindings`
3. The `### Tier A` and `### Tier B` override blocks
4. Both ASCII cards under `## Quick Reference Card`

The ASCII cards have a fixed 60-character row width. If a label changes length, re-pad the
row — do not eyeball it.

For how accelerator strings must be written — `<Primary>` rather than `<Control>`,
canonical modifier order, lowercase letter keys — see
[A note on the accelerator syntax](README.md#a-note-on-the-accelerator-syntax) and the
verification steps under [Troubleshooting](README.md#troubleshooting). Those rules live in
the guide and are not repeated here, because a fifth copy is a fifth thing to keep in
sync.

New bindings must also avoid the keys an RDP client keeps for itself; the list is under
[RDP Client Setup](README.md#rdp-client-setup).

## Before you commit

Markdown must lint clean. The configuration is in `.markdownlint-cli2.jsonc`:

```bash
markdownlint-cli2 README.md CONTRIBUTING.md
```

Shell must pass ShellCheck. The guide's fenced `bash` blocks are fragments, not standalone
scripts, so extract them and check each one on its own:

````bash
TMP=$(mktemp -d)
awk -v d="$TMP" '/^```bash$/{n++;f=sprintf("%s/blk-%03d.sh",d,n);next} /^```/{f="";next} f{print > f}' README.md
shellcheck -S warning -s bash "$TMP"/blk-*.sh
rm -rf "$TMP"
````

That must exit clean. At `-S style` it reports one SC2016 in the `.bash_profile` line that
appends to `PATH` — the single quotes there are intentional, since `$HOME` and `$PATH` are
meant to reach the file unexpanded. Do not "fix" it.
