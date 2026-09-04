# XFCE with Omarchy-Style Configuration

Turn a stock XFCE desktop into something that behaves like [Omarchy](https://omarchy.org).

**This guide assumes the XFCE machine is reached over
[xrdp](https://github.com/neutrinolabs/xrdp).** That is the default throughout — package
lists, keybindings, and configuration are written for a remote session, and the
differences on a local physical desktop are called out inline.

Two consequences, both worth knowing before you start:

- **What survives the trip is Omarchy's keyboard workflow, not its looks.** Compositing,
  transparency, blur, and the night light all have to go. See
  [Works locally, degraded or dead over xrdp](#works-locally-degraded-or-dead-over-xrdp).
- **Almost every binding here depends on your RDP client forwarding `Super`.** Configure
  the client first, or none of this will appear to work. See
  [RDP Client Setup](#rdp-client-setup).

Omarchy is an Arch-based distribution built on Hyprland (a tiling Wayland compositor)
and Quickshell. XFCE is a stacking window manager on X11. Some of Omarchy's behaviour
maps over cleanly, some has to be simulated with scripts, and some cannot be reproduced
at all. This document is explicit about which is which — see the
[Compatibility Matrix](#compatibility-matrix).

**Tracking:** [Omarchy Manual](https://omarchy.org/manual/) as of 2026-09-03
([hotkey reference](https://omarchy.org/manual/hotkeys)).

**Target:** xrdp with the **Xorg / xorgxrdp** backend, XFCE 4.18 or newer, on X11. Every
remote-specific claim below was checked against the Xorg backend. The Xvnc backend is not
covered; where a finding depends on xorgxrdp internals, that is said at the point of use.

## Table of Contents

- [Compatibility Matrix](#compatibility-matrix)
- [Prerequisites](#prerequisites)
- [xrdp Server Setup and Tuning](#xrdp-server-setup-and-tuning)
- [RDP Client Setup](#rdp-client-setup)
- [Required Packages](#required-packages)
- [Scripts](#scripts)
- [Keybindings](#keybindings)
- [Applying the Keybindings](#applying-the-keybindings)
- [Configuration Files](#configuration-files)
- [Quick Reference Card](#quick-reference-card)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Backup and Restore](#backup-and-restore)
- [Uninstall](#uninstall)

---

## Compatibility Matrix

Every binding in this document falls into one of three buckets. **The status is judged
inside an xrdp session** — that is this guide's default environment. Where a binding
behaves differently on a local physical desktop, it is marked `†` and explained in
[Works locally, degraded or dead over xrdp](#works-locally-degraded-or-dead-over-xrdp).

| Status | Meaning |
| -------- | --------- |
| **Native** | xfwm4 or an XFCE component does this directly. One `xfconf-query` call, no script. |
| **Emulated** | Needs a helper script and usually an extra package. Close, but not identical. |
| **Not possible** | XFCE cannot do this. Explained below, with third-party options where any exist. |

### What xfwm4 gives you for free

xfwm4 exposes a fixed set of window-manager actions that can be bound directly. The
authoritative list comes from the `shortcut_values` table in
[`xfwm4/src/settings.c`](https://gitlab.xfce.org/xfce/xfwm4/-/blob/master/src/settings.c);
the ones this document uses are:

| Need | xfwm4 action |
| ------ | -------------- |
| Close window | `close_window_key` |
| Fullscreen | `fullscreen_key` |
| Maximize | `maximize_window_key` |
| Fill screen width (Omarchy's "full width") | `fill_horiz_key` |
| Tile half-screen | `tile_left_key`, `tile_right_key`, `tile_up_key`, `tile_down_key` |
| Tile quarter-screen | `tile_up_left_key`, `tile_up_right_key`, `tile_down_left_key`, `tile_down_right_key` |
| Switch to workspace N | `workspace_1_key` … `workspace_N_key` |
| Move window to workspace N | `move_window_workspace_1_key` … |
| Next / previous workspace | `next_workspace_key`, `prev_workspace_key` |
| Move window to next / previous workspace | `move_window_next_workspace_key`, `move_window_prev_workspace_key` |
| Cycle windows | `cycle_windows_key`, `cycle_reverse_windows_key` |
| Stick to all workspaces (≈ Omarchy's "pop out") | `stick_window_key` |
| Always on top | `above_key` |
| Show desktop | `show_desktop_key` |

Use these instead of writing scripts. Earlier versions of this guide shipped
`omarchy-workspace-switch` and `omarchy-window-move-workspace` helpers, and bound close
to `xdotool getactivewindow windowkill` — all three are unnecessary, and the last one is
actively harmful (see [Scripts](#scripts)).

### What has to be emulated

| Omarchy feature | Why | How |
| ----------------- | ----- | ----- |
| `Super + Arrow` directional focus | **xfwm4 has no "focus window in direction" action.** `left_key`/`right_key`/etc. in the action list are move/resize modifiers, not focus. | `omarchy-focus-direction` (geometry math over `wmctrl -lG`) |
| Screen recording | No built-in recorder | `omarchy-screenrecord` (`ffmpeg -f x11grab`) |
| Colour picker | — | `xcolor` |
| OCR text extraction | — | `maim` + `tesseract` |
| Scratchpad workspace | xfwm4 has no scratchpad | `xfce4-terminal --drop-down`, or `tdrop` for any app |
| System panels (audio/network/…) | No unified panel system | `omarchy-panel` dispatching to the standard XFCE/GTK dialogs |
| Theme switching | No theme engine spanning terminal + WM + launcher | `omarchy-theme-switch` |
| Night light | — | `redshift` — **but see below: this does nothing over xrdp** |
| Reminders, notices | — | `notify-send` wrappers |

### What is not possible

| Omarchy feature | Why XFCE cannot do it | Third-party option |
| ----------------- | ---------------------- | -------------------- |
| Dwindle auto-tiling (new windows split automatically) | xfwm4 is a stacking WM with manual tiling only | None packaged in Arch repos or the AUR |
| Scrolling layout (`Super + L`) | No such concept | None |
| Window grouping / tabs (`Super + G`) | xfwm4 has no window groups | None |
| Screen zoom (`Super + Ctrl + Z`) | No compositor-level zoom | Over RDP, use the client's own zoom. Locally, `magnus` or `xzoom` (AUR) |
| Fullscreen-inside-window (`Super + Ctrl + F`) | Hyprland-specific | None |
| Quickshell top bar (bar, menu, notifications, lock screen as one process) | XFCE panel is a separate plugin system | XFCE panel, approximated |
| Omarchy CLI, theme ecosystem, system snapshots | Part of the Omarchy distribution itself | Not applicable |

### Works locally, degraded or dead over xrdp

These are the rows marked `†` elsewhere in this guide. They work on a physical XFCE
desktop and do not survive the trip through RDP.

| Omarchy feature | Local XFCE | Over xrdp (Xorg backend) | Basis |
| ----------------- | ------------ | -------------------------- | ------- |
| Night light (`Super + Ctrl + N`) | Works | **Does nothing at all**, and exits 0 without an error | Verified in xorgxrdp source — see below |
| Blur and shadows (picom) | Works | Not worth it: software rendering, and every frame is re-encoded | Reasoned, see [Compositing](#compositing) |
| Window transparency | Works | Needs a compositor, so effectively unavailable | Reasoned |
| Brightness keys (`XF86MonBrightness*`) | Works | No backlight device exists in a virtual session | Reasoned |
| `omarchy-notice battery` | Works | A server usually has no battery for `acpi` to read | Reasoned |
| `Print` / `Alt + Print` capture | Works | **Windows clients only:** the client keeps these keys | [The Print key problem](#the-print-key-problem) |
| Everything bound to `Super` | Works | Client-dependent, and fixable client-side | [RDP Client Setup](#rdp-client-setup) |

**Why the night light cannot work.** xorgxrdp registers RandR gamma callbacks that do
nothing: `rdpRRCrtcSetGamma()` logs one trace line and returns `TRUE`, and the ramps it
allocates are commented `/* Create and initialise (unused) gamma ramps */`
(`module/rdpRandR.c`). No other gamma path exists in the driver either — there is no
VidMode hook and no `ChangeGamma` anywhere in its sources. Redshift tries its methods in
the order `drm → randr → vidmode → dummy` (`src/redshift.c`), the RandR call reports
success, so it stops there and never falls back. The result is a command that exits 0
while the screen stays exactly as it was. That is expected behaviour here, not a broken
install.

This was checked against the **Xorg / xorgxrdp** backend. The Xvnc backend was not
examined; do not assume the finding carries over.

---

## Prerequisites

```bash
# CachyOS / Arch / any Arch derivative running XFCE
sudo pacman -Syu
```

Everything below assumes XFCE 4.18 or newer on X11, reached over xrdp with the Xorg
(xorgxrdp) backend. On a local physical desktop, skip the next two sections entirely and
read the `†` notes as "does not apply to you".

---

## xrdp Server Setup and Tuning

### Installing xrdp

xrdp and its Xorg backend are both in the AUR, not the official repositories:

```bash
# with your preferred AUR helper
paru -S xrdp xorgxrdp
```

The `xrdp` package on its own only supports the Xvnc backend. `xorgxrdp` adds the Xorg
backend, which is what this guide targets throughout.

Unprivileged users must be allowed to start X, or clients such as Remmina connect to a
blank screen:

```ini
# /etc/X11/Xwrapper.config
allowed_users=anybody
needs_root_rights=no
```

Then start it:

```bash
sudo systemctl enable --now xrdp
```

Run the daemon as an unprivileged user. Create the account, point `xrdp.ini` at it, make
`sesman.ini`'s `SessionSockdirGroup` match the same group, and check the result:

```bash
sudo useradd xrdp -d / -c 'xrdp daemon' -s /usr/bin/nologin
# /etc/xrdp/xrdp.ini    ->  runtime_user=xrdp
#                           runtime_group=xrdp
# /etc/xrdp/sesman.ini  ->  SessionSockdirGroup=xrdp
sudo /usr/share/xrdp/xrdp-chkpriv
sudo systemctl restart xrdp
```

Optional GPU acceleration: `xorgxrdp-glamor` (Intel/AMD — OpenGL and Vulkan) or
`xorgxrdp-nvidia`, both AUR. Without one of them the session renders entirely in
software, which is the reason [Compositing](#compositing) is off by default here.

### Session startup

`/etc/xrdp/startwm.sh` behaves like `.xinitrc`: it reads `~/.xinitrc`, falling back to
`/etc/X11/xinit/xinitrc`. Start XFCE with its own D-Bus session:

```bash
# ~/.xinitrc
exec dbus-launch --exit-with-session xfce4-session
```

If you keep a distribution `~/.xinitrc` ending in `exec $(get_session "$1")`, note that
`$1` is empty when xrdp calls it, and an empty session name is a black screen. Give it a
default:

```bash
exec $(get_session "${1:-xfce}")
```

### Disconnect vs log out

**This is the one place in this guide where a keystroke can cost you the whole machine.**

xrdp keeps a session alive when you merely close the connection. Reconnect and you land
back in the same desktop with every application still running. The session is destroyed
only when the window manager itself exits.

`Super + Escape` is bound to `xfce4-session-logout`. That dialog does prompt before
acting — but its buttons include **Restart** and **Shut Down**, and from a remote session
those apply to the machine you are connected *through*. Power it off and you are done for
the day unless you have out-of-band access to it.

So: to step away and keep everything running, **close the RDP client window**. Do not log
out, and never bind `xfce4-session-logout --fast`, which skips the confirmation entirely.

If you would rather not have the binding at all:

```bash
xfconf-query -c xfce4-keyboard-shortcuts -p '/commands/custom/<Super>Escape' -r
```

### Tuning

`/etc/xrdp/xrdp.ini`:

| Setting | Suggested | What it does |
| --------- | ----------- | -------------- |
| `max_bpp` | `24` | Caps colour depth. `16` helps on a slow link; unset or `0` means unlimited. |
| `bitmap_cache` | `true` | Client-side bitmap cache. |
| `bitmap_compression` | `true` | Compresses bitmaps. |
| `bulk_compression` | `true` | Compresses bulk data. |
| `tcp_nodelay` | `true` | Turns off Nagle buffering. This is the one you feel as typing latency. |
| `tcp_keepalive` | `true` | Closes the socket when the link disappears without a proper close. |
| `use_fastpath` | `both` | Fastpath input and output. **Defaults to `none`**, so this is a real change. |

Two settings to leave alone:

- `tcp_send_buffer_bytes` / `tcp_recv_buffer_bytes` — the manual's own advice is not to
  set these on systems with dynamic TCP buffer sizing, which is every current Linux.
- `crypt_level` — lowering it trades away transport security for very little. Only
  defensible when the connection never leaves the host; see below.

Since 0.10.2 xrdp prefers H.264, tuned in `/etc/xrdp/gfx.toml` (`man gfx.toml`):

| Symptom | Try |
| --------- | ----- |
| Blocky or washed-out video | `preset = "medium"` |
| Fast network but everything feels late | `order = ["RFX", "H.264"]` |

#### Listening on localhost only

Rather than exposing 3389, bind it to the loopback interface and reach it over SSH:

```ini
# /etc/xrdp/xrdp.ini
port=tcp://.:3389
```

```bash
# on the client
ssh user@host -L 3389:localhost:3389
# then point the RDP client at 127.0.0.1:3389
```

### Making the session detectable

Several helpers in this guide need to know whether they are running remotely. Use two
checks, not one — the first needs a root-owned file edited, and if you skip it the second
still answers correctly:

```bash
in_rdp() {
    # 1. Explicit, and the only method that also covers the Xvnc backend.
    [ -n "${XRDP_SESSION:-}" ] && return 0
    # 2. xorgxrdp names its RandR outputs rdp0, rdp1, ... (module/rdpRandR.c).
    #    Xorg backend only; this does not detect an Xvnc session.
    xrandr --listmonitors 2>/dev/null | grep -q ' rdp[0-9]'
}
```

To set the variable, add it to sesman's session environment:

```ini
# /etc/xrdp/sesman.ini
[SessionVariables]
XRDP_SESSION=1
```

Log out and back in for it to take effect. The section already exists in the shipped
file, with `XRDP_USE_ACCEL_ASSIST` and `XRDP_NVIDIA_GRID` as commented examples.

The fallback check needs `xrandr` (`xorg-xrandr`), and
[Fonts and blanking](#fonts-and-blanking) needs `xset` (`xorg-xset`). Both are usually
already present; if `xrandr` is missing the check simply reports "not remote", so set
`XRDP_SESSION` rather than relying on it alone.

### Audio

```bash
paru -S pipewire-module-xrdp    # or pulseaudio-module-xrdp for PulseAudio
```

**Log out and back in afterwards** — the module is loaded when the session starts, so
installing it mid-session does nothing. Until it is in place there is no sink at all, and
`pamixer` (the volume keys) fails rather than doing nothing.

### Clipboard between client and server

Two separate mechanisms, easy to confuse:

| Want | Provided by | Notes |
| ------ | ------------- | ------- |
| Copy on the remote, paste on your local machine | `xrdp-chansrv`, via RDP's `cliprdr` channel | Started with the session; nothing to configure |
| Scroll back through what you copied *inside* the session | `xfce4-clipman` | `Super + Ctrl + V`, see [Required Packages](#required-packages) |

If cross-machine copy stops working, check that `xrdp-chansrv` is running before
suspecting clipman.

### Multiple monitors and dynamic resolution

xorgxrdp resizes the virtual screen when you resize the client window, and supports
multiple monitors when the client asks for them (`/multimon` in FreeRDP, the *Use all my
monitors* checkbox in mstsc).

Two knock-on effects on this guide:

- `omarchy-focus-direction` treats all monitors as one flat coordinate space, so
  `Super + Left` can jump across a screen edge rather than stopping at it.
- xfwm4 tiling snaps to whatever geometry the session currently has. Resizing the client
  window does not re-tile anything that is already placed.

---

## RDP Client Setup

**Read this before configuring any keybindings.** Most of what follows in this guide is
bound to `Super`, and whether `Super` reaches the remote desktop is decided entirely on
the client side.

There are two distinct problems here, and they have different answers:

| Problem | Fixable? |
| --------- | ---------- |
| `Super` combinations do not reach the session | **Yes**, in client settings |
| `Print` / `Alt + Print` do not reach the session | **Not on Windows clients.** Use the [Tier A aliases](#tier-a--print-key-aliases) |

### Forwarding Super

**Windows (mstsc / Windows App).** *Show Options → Local Resources → Keyboard → Apply
Windows key combinations*:

| Option | Effect |
| -------- | -------- |
| `On this computer` | Windows-key combinations stay local. **Nothing in this guide works.** |
| `On the remote computer` | They go to the session. **Use this.** |
| `Only when using the full screen` | They go to the session only while the client is full-screen. |

Note that hotkeys do not work at all inside nested RDP or RemoteApp sessions.

**FreeRDP / Remmina.** `grab-keyboard` is already on by default — "grab keyboard focus,
forward all keys to remote" — so `Super` and `Print` both arrive without extra work:

```bash
xfreerdp3 /v:host:3389 /u:user /dynamic-resolution /clipboard /sound +grab-keyboard
```

**macOS.** Check your client's keyboard mode; the mapping from `Command` to `Super`
varies by client and is not consistent enough to document here. Verify with `xev` (below)
rather than trusting a menu label.

### The Print key problem

Microsoft documents `Print Screen` and `Alt + Print Screen` as having in-session
equivalents, `Ctrl + Alt + Plus` and `Ctrl + Alt + Minus`, which put a snapshot on the
clipboard. The plain keys are handled by the local Windows machine.

*Inference, not a quoted guarantee:* `Print Screen` is not a "Windows key combination",
so setting *Apply Windows key combinations* to `On the remote computer` most likely does
**not** forward it either. Test it rather than assuming — run this in a remote terminal
and press `Print`:

```bash
xev | grep -i keysym
```

Nothing printed means the client kept the key, and you want the
[Tier A aliases](#tier-a--print-key-aliases). FreeRDP and Remmina forward `Print` fine
and need no aliases.

### Keys the RDP client keeps for itself

These never reach the session, so nothing in this guide may be bound to them:

| Key | Client action |
| ----- | --------------- |
| `Ctrl + Alt + End` | Ctrl+Alt+Del on the remote |
| `Ctrl + Alt + Home` | Activates the connection bar |
| `Ctrl + Alt + Break` / `Pause` | Toggles full-screen |
| `Ctrl + Alt + Plus` / `Minus` | Screenshot to the clipboard |
| `Alt + Page Up` / `Page Down` | Switch programs (stands in for `Alt + Tab`) |
| `Alt + Insert` | Cycle programs |
| `Alt + Home` | Start menu |
| `Alt + Delete` | System menu |

### Keyboard layout

xrdp maps scancodes with `/etc/xrdp/km-<langid>.toml` — `km-00000409.toml` is US English;
older `.ini` files of the same name still ship alongside. If the wrong characters arrive,
this is where to look, not in XFCE's keyboard settings.

---

## Required Packages

Grouped by what they are for, so you can skip the parts you do not want.

### Core

```bash
sudo pacman -S rofi maim xclip xdotool wmctrl playerctl pamixer btop
```

| Package | Used for |
| --------- | ---------- |
| `rofi` | Application launcher (`Super + Space`) |
| `maim` `xclip` | Screenshots and clipboard piping |
| `xdotool` `wmctrl` | Window queries used by the helper scripts |
| `playerctl` `pamixer` | Media keys |
| `btop` | Activity monitor (`Super + Ctrl + T`) |

`maim`, `xdotool`, `wmctrl`, and `xclip` are ordinary X11 clients. In a remote session
they read and drive the virtual display, so they work exactly as they do locally.

`picom` and `brightnessctl` used to be in this list. They are now under
[Local desktop only](#local-desktop-only).

### Remote session

Installed in [xrdp Server Setup and Tuning](#xrdp-server-setup-and-tuning); listed here so
the package inventory is complete.

```bash
paru -S xrdp xorgxrdp pipewire-module-xrdp
```

| Package | Provides |
| --------- | ---------- |
| `xrdp` | The RDP server itself (Xvnc backend only, on its own) |
| `xorgxrdp` | The Xorg backend this guide targets |
| `pipewire-module-xrdp` | Audio forwarding. Without it there is no sink and `pamixer` fails |

### Omarchy-parity features

```bash
sudo pacman -S xfce4-clipman-plugin xfce4-notifyd xcolor \
  tesseract tesseract-data-eng ffmpeg redshift \
  pavucontrol blueman network-manager-applet xfce4-power-manager \
  galculator rofimoji
```

| Package | Provides | Binding |
| --------- | ---------- | --------- |
| `xfce4-clipman-plugin` | Clipboard history (`xfce4-popup-clipman`) | `Super + Ctrl + V` |
| `xfce4-notifyd` | Notification daemon, do-not-disturb, notification log | `Super + Ctrl + ,` |
| `xcolor` | Colour picker | `Super + Print` |
| `tesseract` `tesseract-data-eng` | OCR text extraction | `Super + Ctrl + Print` |
| `ffmpeg` | Screen recording via `x11grab` | `Alt + Print` |
| `redshift` | Night light `†` — **no effect over xrdp**, see the [compatibility matrix](#works-locally-degraded-or-dead-over-xrdp) | `Super + Ctrl + N` |
| `pavucontrol` `blueman` `network-manager-applet` `xfce4-power-manager` | System panels | `Super + Ctrl + A/B/W/P` |
| `galculator` | Calculator | `Super + Ctrl + Q` |
| `rofimoji` | Emoji picker | `Super + Ctrl + E` |

Add `tesseract-data-chi_sim` (or another language pack) if you OCR non-English text.

### AUR packages

These are **not** in the official repositories:

```bash
# with your preferred AUR helper
paru -S tdrop localsend
```

| Package | Provides | Binding |
| --------- | ---------- | --------- |
| `tdrop` | Drop-down (scratchpad) for any application | `Super + S` |
| `localsend` | LAN file sharing, Omarchy's `Super + Ctrl + S` | `Super + Ctrl + S` |

`tdrop` is optional — `xfce4-terminal --drop-down` gives you a drop-down terminal with no
extra package. See [`omarchy-scratchpad`](#omarchy-scratchpad).

### Local desktop only

Skip both of these on a machine you only reach over RDP.

```bash
sudo pacman -S picom brightnessctl
```

| Package | Used for | Why not remotely |
| --------- | ---------- | ------------------ |
| `picom` | Compositing: transparency, blur, shadows | No GPU, and every composited frame gets re-encoded and shipped over the wire. See [Compositing](#compositing) |
| `brightnessctl` | `XF86MonBrightness*` keys | A virtual session has no backlight device |

### Fonts

```bash
sudo pacman -S ttf-jetbrains-mono-nerd noto-fonts noto-fonts-emoji
```

Omarchy uses **JetBrainsMono Nerd Font** as both terminal and system font. Earlier
versions of this guide used CaskaydiaMono (`ttf-cascadia-code-nerd`), which is still a
fine choice if you prefer it.

### Themes

```bash
sudo pacman -S adw-gtk-theme papirus-icon-theme
```

`arc-gtk-theme` was dropped from the official repositories and now lives only in the AUR;
`adw-gtk-theme` is the maintained alternative and sits closer to Omarchy's look.

### Wallpaper

No package needed. XFCE's own `xfdesktop` manages wallpapers — earlier versions of this
guide installed `nitrogen`, which is redundant here (and has itself been dropped from the
official repositories). Set it from *Settings → Desktop*, or from the shell:

```bash
xfconf-query -c xfce4-desktop -p /backdrop/screen0/monitor0/workspace0/last-image \
  -s ~/Pictures/wallpaper.png
```

### Terminal and browser

Omarchy's default terminal is now [Foot](https://codeberg.org/dnkl/foot), which is a
Wayland-only client and therefore unusable on XFCE/X11. Alacritty is the closest
equivalent that runs on X11, and is one of Omarchy's supported alternatives:

```bash
sudo pacman -S alacritty
```

Zen Browser is not in the official repositories — install `zen-browser-bin` from the AUR,
or substitute any browser you like and adjust `omarchy-launch-browser`.

---

## Scripts

All scripts live in `~/.local/bin/`. Every one starts with `set -euo pipefail` and passes
`shellcheck`.

### Removed in this revision

Three scripts from earlier versions of this guide are gone. If you have them, delete them:

| Script | Why |
| -------- | ----- |
| `omarchy-workspace-switch` | xfwm4's `workspace_N_key` action does this natively |
| `omarchy-window-move-workspace` | xfwm4's `move_window_workspace_N_key` action does this natively |
| `omarchy-lock-screen` | It was a one-line wrapper around `xflock4`; bind `xflock4` directly |

The old keybinding table also referenced `xfce4-workspace-switch --ws 0`. **That command
does not exist in XFCE** and never worked.

### Launching

#### `omarchy-launch-browser`

```bash
#!/bin/bash
# Launch the browser. Omarchy: Super + Shift + Return
set -euo pipefail

BROWSER_CMD="${OMARCHY_BROWSER:-zen-browser}"

if [ "${1:-}" = "--private" ]; then
    exec "$BROWSER_CMD" --private-window
else
    exec "$BROWSER_CMD"
fi
```

#### `omarchy-launch-webapp`

```bash
#!/bin/bash
# Open a URL as a standalone app window. Omarchy: Install > Web App
set -euo pipefail

if [ $# -lt 1 ]; then
    echo "usage: omarchy-launch-webapp <url>" >&2
    exit 1
fi

exec "${OMARCHY_BROWSER:-zen-browser}" --new-window --kiosk "$1"
```

#### `omarchy-launch-or-focus`

Focus a running window by WM class, or start the application if it is not running.

```bash
#!/bin/bash
# usage: omarchy-launch-or-focus <wm_class> <command> [args...]
set -euo pipefail

if [ $# -lt 2 ]; then
    echo "usage: omarchy-launch-or-focus <wm_class> <command> [args...]" >&2
    exit 1
fi

CLASS="$1"
shift

if wmctrl -lx | grep -qi -- "$CLASS"; then
    wmctrl -xa "$CLASS"
else
    exec "$@"
fi
```

The previous version used `eval "$CMD"`, which executed its argument through the shell —
a command-injection hazard when the argument comes from anywhere but your own config. It
also ran `grep` without `-q`, printing the match into the script's output. Both are fixed
above by taking the command as separate arguments and executing it directly.

#### `omarchy-launch-or-focus-webapp`

```bash
#!/bin/bash
# usage: omarchy-launch-or-focus-webapp <window_title> <url>
set -euo pipefail

if [ $# -lt 2 ]; then
    echo "usage: omarchy-launch-or-focus-webapp <window_title> <url>" >&2
    exit 1
fi

TITLE="$1"
URL="$2"

if wmctrl -l | grep -qi -- "$TITLE"; then
    wmctrl -a "$TITLE"
else
    exec omarchy-launch-webapp "$URL"
fi
```

> **This script was broken.** It previously called `hyprctl clients` and
> `hyprctl dispatch focuswindow`. `hyprctl` is Hyprland's IPC client — it does not exist
> on XFCE/X11, so the script failed on every invocation. It now uses `wmctrl`, matching
> `omarchy-launch-or-focus`.

#### `omarchy-menu`

```bash
#!/bin/bash
# Application launcher. Omarchy: Super + Space
set -euo pipefail
exec rofi -show drun
```

Omarchy distinguishes `Super + Space` (the full Omarchy menu: apps, settings, install,
capture, style) from `Super + Alt + Space` (apps only). XFCE has no equivalent of the
full menu; both keys are bound to `rofi -show drun` here.

### Screenshots and recording

Omarchy hangs everything off the Print Screen key. These four scripts reproduce that.

#### `omarchy-screenshot-selection`

```bash
#!/bin/bash
# Screenshot a region to the clipboard. Omarchy: Print
set -euo pipefail
maim --select --hidecursor | xclip -selection clipboard -t image/png
notify-send "Screenshot" "Copied to clipboard"
```

#### `omarchy-screenshot-file`

```bash
#!/bin/bash
# Screenshot a region to a file. Omarchy: Print (Omarchy saves to both)
set -euo pipefail

DIR="${OMARCHY_SCREENSHOT_DIR:-$HOME/Pictures/Screenshots}"
mkdir -p "$DIR"
FILE="$DIR/screenshot-$(date +'%Y-%m-%d_%H-%M-%S').png"

maim --select --hidecursor "$FILE"
xclip -selection clipboard -t image/png < "$FILE"
notify-send "Screenshot" "Saved to $FILE"
```

The previous version left `$(date …)` unquoted inside the path, and did not create the
directory before writing when `maim` was given the path directly.

#### `omarchy-screenrecord`

```bash
#!/bin/bash
# Toggle screen recording. Omarchy: Alt + Print
set -euo pipefail

DIR="${OMARCHY_SCREENRECORD_DIR:-$HOME/Videos}"
PIDFILE="${XDG_RUNTIME_DIR:-/tmp}/omarchy-screenrecord.pid"

if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
    kill -INT "$(cat "$PIDFILE")"
    rm -f "$PIDFILE"
    notify-send "Screen recording" "Stopped"
    exit 0
fi

mkdir -p "$DIR"
FILE="$DIR/screenrecording-$(date +'%Y-%m-%d_%H-%M-%S').mp4"
GEOMETRY=$(xdpyinfo | awk '/dimensions:/ {print $2; exit}')

ffmpeg -loglevel error -f x11grab -framerate 30 -video_size "$GEOMETRY" -i "$DISPLAY" \
    -c:v libx264 -preset ultrafast -pix_fmt yuv420p "$FILE" &
echo $! > "$PIDFILE"
notify-send "Screen recording" "Started: $FILE"
```

Records the full screen without audio. Omarchy's recorder additionally offers region
selection, desktop/microphone audio, a webcam overlay, and GPU encoding via
`gpu-screen-recorder`; none of that is reproduced here.

Over xrdp this records the virtual display, which works — but `libx264` and xrdp's own
encoder are then competing for the same CPU. Expect the session itself to get choppy
while a recording is running.

#### `omarchy-color-picker`

```bash
#!/bin/bash
# Pick a colour from the screen. Omarchy: Super + Print
set -euo pipefail
COLOR=$(xcolor)
printf '%s' "$COLOR" | xclip -selection clipboard
notify-send "Colour picker" "$COLOR copied to clipboard"
```

#### `omarchy-ocr`

```bash
#!/bin/bash
# Extract text from a screen region. Omarchy: Super + Ctrl + Print
set -euo pipefail

TEXT=$(maim --select --hidecursor | tesseract stdin stdout 2>/dev/null)

if [ -z "$TEXT" ]; then
    notify-send "Text extraction" "No text found"
    exit 0
fi

printf '%s' "$TEXT" | xclip -selection clipboard
notify-send "Text extraction" "Copied to clipboard"
```

Add `-l chi_sim` (and install the matching `tesseract-data-*` package) for other
languages.

### Clipboard

Omarchy makes `Super + C/X/V` work everywhere, including the terminal, where the
conventional bindings are `Ctrl + Shift + C/V`. These scripts forward the right
combination based on the focused window.

#### `omarchy-smart-copy`

```bash
#!/bin/bash
# Unified copy. Omarchy: Super + C
set -euo pipefail

CLASS=$(xdotool getactivewindow getwindowclassname 2>/dev/null || echo "")

case "$CLASS" in
    Alacritty|kitty|foot|Ghostty|*[Tt]erminal*|*[Cc]onsole*)
        xdotool key --clearmodifiers ctrl+shift+c
        ;;
    *)
        xdotool key --clearmodifiers ctrl+c
        ;;
esac
```

#### `omarchy-smart-paste`

```bash
#!/bin/bash
# Unified paste. Omarchy: Super + V
set -euo pipefail

CLASS=$(xdotool getactivewindow getwindowclassname 2>/dev/null || echo "")

case "$CLASS" in
    Alacritty|kitty|foot|Ghostty|*[Tt]erminal*|*[Cc]onsole*)
        xdotool key --clearmodifiers ctrl+shift+v
        ;;
    *)
        xdotool key --clearmodifiers ctrl+v
        ;;
esac
```

#### `omarchy-smart-cut`

```bash
#!/bin/bash
# Unified cut. Omarchy: Super + X (no-op in terminals, as in Omarchy)
set -euo pipefail

CLASS=$(xdotool getactivewindow getwindowclassname 2>/dev/null || echo "")

case "$CLASS" in
    Alacritty|kitty|foot|Ghostty|*[Tt]erminal*|*[Cc]onsole*)
        exit 0
        ;;
    *)
        xdotool key --clearmodifiers ctrl+x
        ;;
esac
```

Clipboard **history** (`Super + Ctrl + V`) needs no script — bind `xfce4-popup-clipman`,
provided by `xfce4-clipman-plugin`. Start `xfce4-clipman` at login (see
[Autostart](#autostart-applications)).

### Window management

#### `omarchy-focus-direction`

```bash
#!/bin/bash
# Move focus to the nearest window in a direction. Omarchy: Super + Arrow
set -euo pipefail

DIR="${1:-}"
case "$DIR" in
    left|right|up|down) ;;
    *)
        echo "usage: omarchy-focus-direction <left|right|up|down>" >&2
        exit 1
        ;;
esac

# _NET_ACTIVE_WINDOW is the EWMH source of truth and matches wmctrl's IDs.
# Normalise to the zero-padded form wmctrl prints.
ACTIVE=$(printf '0x%08x' "$(xprop -root _NET_ACTIVE_WINDOW | awk '{ print $NF }')")
DESKTOP=$(wmctrl -d | awk '$2 == "*" { print $1 }')

TARGET=$(wmctrl -lG | awk -v active="$ACTIVE" -v desk="$DESKTOP" -v dir="$DIR" '
    {
        id = $1; d = $2
        cx = $3 + $5 / 2; cy = $4 + $6 / 2
        if (id == active) { ax = cx; ay = cy; found = 1; next }
        if (d != desk && d != -1) next          # other workspace, and not sticky
        n++; nid[n] = id; nx[n] = cx; ny[n] = cy
    }
    END {
        if (!found) exit 0
        bestscore = -1
        for (i = 1; i <= n; i++) {
            dx = nx[i] - ax; dy = ny[i] - ay
            if (dir == "left"  && dx >= 0) continue
            if (dir == "right" && dx <= 0) continue
            if (dir == "up"    && dy >= 0) continue
            if (dir == "down"  && dy <= 0) continue
            adx = (dx < 0 ? -dx : dx); ady = (dy < 0 ? -dy : dy)
            # Distance along the axis of travel, penalising sideways offset.
            score = (dir == "left" || dir == "right") ? adx + 2 * ady : ady + 2 * adx
            if (bestscore < 0 || score < bestscore) { bestscore = score; best = nid[i] }
        }
        if (bestscore >= 0) print best
    }
')

if [ -n "$TARGET" ]; then
    wmctrl -ia "$TARGET"
fi
```

**Limitations.** This is geometry math over the window list, not a real focus model:

- Minimized windows still appear in `wmctrl -lG` and can be picked as targets.
- Windows on other monitors are treated as part of one flat coordinate space, so
  "right" can jump to the next monitor. That usually matches expectations, but it is a
  side effect rather than a design.
- Sticky windows (`-1` desktop) are always candidates.

Omarchy's `Super + Arrow` also warps the pointer to the newly focused window; this does
not.

#### `omarchy-scratchpad`

```bash
#!/bin/bash
# Toggle a drop-down terminal. Omarchy: Super + S / Super + Grave
set -euo pipefail

if command -v tdrop > /dev/null 2>&1; then
    exec tdrop -ma -w 100% -h 45% -y 0 alacritty
fi

# Zero-dependency fallback: xfce4-terminal has a built-in drop-down mode.
exec xfce4-terminal --drop-down
```

`tdrop` (AUR) works with any application; `xfce4-terminal --drop-down` needs no extra
package but only does terminals. Neither is a real scratchpad workspace — you cannot
*move an existing window* into it the way `Super + Alt + S` does in Omarchy.

### Toggle helpers

#### `omarchy-toggle-dnd`

```bash
#!/bin/bash
# Toggle do-not-disturb. Omarchy: Super + Ctrl + ,
set -euo pipefail

xfconf-query -c xfce4-notifyd -p /do-not-disturb -T

if [ "$(xfconf-query -c xfce4-notifyd -p /do-not-disturb)" = "true" ]; then
    # Nothing to announce — notifications are silenced.
    :
else
    notify-send "Notifications" "Enabled"
fi
```

`-T` toggles a boolean in place. The property must already exist; it is created the first
time you change the setting in *Settings → Notifications*, or explicitly:

```bash
xfconf-query -c xfce4-notifyd -p /do-not-disturb --create -t bool -s false
```

#### `omarchy-toggle-nightlight`

```bash
#!/bin/bash
# Toggle night light. Omarchy: Super + Ctrl + N (4000K / 6500K)
set -euo pipefail

# xorgxrdp's gamma callbacks are stubs -- rdpRRCrtcSetGamma() returns TRUE without
# applying anything, and the driver has no VidMode path either. Redshift picks RandR,
# is told it succeeded, and never falls back, so it exits 0 and changes nothing.
if [ -n "${XRDP_SESSION:-}" ] || xrandr --listmonitors 2>/dev/null | grep -q ' rdp[0-9]'; then
    notify-send "Night light" "Not available in an xrdp session"
    exit 0
fi

STATE="${XDG_RUNTIME_DIR:-/tmp}/omarchy-nightlight"

if [ -f "$STATE" ]; then
    redshift -x
    rm -f "$STATE"
    notify-send "Night light" "Off (6500K)"
else
    redshift -O 4000
    touch "$STATE"
    notify-send "Night light" "On (4000K)"
fi
```

`†` **The guard is not optional over xrdp.** Without it `redshift -O 4000` exits 0, the
notification claims the night light is on, and the screen never changes — which looks
like a broken script rather than a missing capability. The reasoning, with source
references, is in
[Works locally, degraded or dead over xrdp](#works-locally-degraded-or-dead-over-xrdp).

The `xrandr` half of the check covers people who have not added `XRDP_SESSION=1` to
`sesman.ini` yet; it detects the Xorg backend only. See
[Making the session detectable](#making-the-session-detectable).

#### `omarchy-toggle-bar`

```bash
#!/bin/bash
# Toggle the top panel. Omarchy: Super + Shift + Space
set -euo pipefail

PROP=/panels/panel-1/autohide-behavior
CURRENT=$(xfconf-query -c xfce4-panel -p "$PROP" 2>/dev/null || echo 0)

# 0 = never hide, 2 = always hide
if [ "$CURRENT" = "2" ]; then
    xfconf-query -c xfce4-panel -p "$PROP" --create -t int -s 0
else
    xfconf-query -c xfce4-panel -p "$PROP" --create -t int -s 2
fi
```

Omarchy removes the bar entirely; XFCE's closest equivalent is switching the panel to
always-hide. Adjust `panel-1` if your top panel has a different ID
(`xfconf-query -c xfce4-panel -p /panels -l` lists them).

### System panels

Omarchy's `Super + Ctrl + <letter>` panels are Quickshell popups. XFCE has no equivalent,
so this dispatches to the standard configuration dialogs — a heavier, less integrated
experience, but the same job.

#### `omarchy-panel`

```bash
#!/bin/bash
# usage: omarchy-panel <audio|bluetooth|network|display|power|calendar>
set -euo pipefail

case "${1:-}" in
    audio)     exec pavucontrol ;;
    bluetooth) exec blueman-manager ;;
    network)   exec nm-connection-editor ;;
    display)   exec xfce4-display-settings ;;
    power)     exec xfce4-power-manager-settings ;;
    calendar)  exec xfce4-popup-clock ;;
    *)
        echo "usage: omarchy-panel <audio|bluetooth|network|display|power|calendar>" >&2
        exit 1
        ;;
esac
```

`xfce4-popup-clock` only works when a Clock plugin is present on a panel; otherwise drop
the `calendar` case.

### Notices and reminders

Omarchy shows time, battery, and weather as transient notifications.

#### `omarchy-notice`

```bash
#!/bin/bash
# usage: omarchy-notice <time|battery|weather>
set -euo pipefail

case "${1:-}" in
    time)
        notify-send "$(date '+%H:%M')" "$(date '+%A, %d %B %Y')"
        ;;
    battery)
        BATT=$(acpi -b 2>/dev/null | head -n1 || true)
        if [ -n "$BATT" ]; then
            notify-send "Battery" "$BATT"
        else
            notify-send "Battery" "No battery reported by acpi"
        fi
        ;;
    weather)
        notify-send "Weather" "$(curl -sf --max-time 5 'wttr.in/?format=%l:+%c+%t+%w' \
            || echo 'Unavailable')"
        ;;
    *)
        echo "usage: omarchy-notice <time|battery|weather>" >&2
        exit 1
        ;;
esac
```

`acpi` needs the `acpi` package, and the weather line needs network access.

`†` A remote host usually has no battery, so `acpi -b` prints nothing. The explicit
branch above exists so you get a clear message instead of an empty notification.

#### `omarchy-reminder`

```bash
#!/bin/bash
# Set a countdown reminder. Omarchy: Super + Ctrl + R
set -euo pipefail

INPUT=$(rofi -dmenu -p "Remind me in (e.g. 25m walk the dog)" -l 0)
[ -n "$INPUT" ] || exit 0

DELAY="${INPUT%% *}"
MESSAGE="${INPUT#* }"
[ "$MESSAGE" = "$INPUT" ] && MESSAGE="Reminder"

case "$DELAY" in
    *[0-9]s|*[0-9]m|*[0-9]h) ;;
    *[0-9])   DELAY="${DELAY}m" ;;
    *)
        notify-send "Reminder" "Could not parse a delay from: $INPUT"
        exit 1
        ;;
esac

setsid --fork sh -c "sleep '$DELAY'; notify-send -u critical 'Reminder' '$MESSAGE'"
notify-send "Reminder set" "In $DELAY: $MESSAGE"
```

Reminders do not survive a reboot. Omarchy's also list (`Super + Ctrl + Alt + R`) and
clear (`Super + Ctrl + Shift + R`); that is not reproduced here.

### Theming

#### `omarchy-theme-switch`

```bash
#!/bin/bash
# Pick a theme. Omarchy: Super + Ctrl + Shift + Space
set -euo pipefail

THEME_DIR="$HOME/.config/omarchy/themes"
[ -d "$THEME_DIR" ] || { notify-send "Themes" "No themes in $THEME_DIR"; exit 1; }

THEME=$(find "$THEME_DIR" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' \
    | sort | rofi -dmenu -p "Theme")
[ -n "$THEME" ] || exit 0

SRC="$THEME_DIR/$THEME"

# Each theme directory supplies the files it wants to override.
[ -f "$SRC/alacritty.toml" ] && cp "$SRC/alacritty.toml" ~/.config/alacritty/theme.toml
[ -f "$SRC/rofi.rasi" ]      && cp "$SRC/rofi.rasi" ~/.config/rofi/theme.rasi
[ -f "$SRC/picom.conf" ]     && cp "$SRC/picom.conf" ~/.config/picom/theme.conf

if [ -f "$SRC/theme.conf" ]; then
    # shellcheck source=/dev/null
    . "$SRC/theme.conf"
    [ -n "${GTK_THEME:-}" ]  && xfconf-query -c xsettings -p /Net/ThemeName -s "$GTK_THEME"
    [ -n "${WM_THEME:-}" ]   && xfconf-query -c xfwm4 -p /general/theme -s "$WM_THEME"
    [ -n "${WALLPAPER:-}" ]  && xfconf-query -c xfce4-desktop \
        -p /backdrop/screen0/monitor0/workspace0/last-image -s "$WALLPAPER"
fi

notify-send "Theme" "Switched to $THEME"
```

You supply the theme directories yourself. Omarchy ships 22 coordinated themes that also
restyle Neovim, btop, Chromium, the lock screen, and the whole shell — that ecosystem has
no XFCE counterpart.

### Making the scripts executable

```bash
chmod +x ~/.local/bin/omarchy-*
```

Make sure `~/.local/bin` is on your `PATH`:

```bash
echo "$PATH" | tr ':' '\n' | grep -q "$HOME/.local/bin" || \
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bash_profile
```

---

## Keybindings

Grouped the same way as the [Omarchy hotkey reference](https://omarchy.org/manual/hotkeys)
so you can read them side by side.

**Status** is one of *Native* (an xfwm4 action or stock XFCE command), *Emulated* (one of
the scripts above), or *Not possible* (see the
[Compatibility Matrix](#compatibility-matrix)).

**Status is judged inside an xrdp session.** Rows marked `†` behave differently on a
local physical desktop; the footnote under each table says how. And all of it assumes
your client forwards `Super` — see [RDP Client Setup](#rdp-client-setup).

### A note on the accelerator syntax

XFCE stores shortcuts as GTK accelerator strings, which have two traps:

- **Ctrl is written `<Primary>`**, not `<Ctrl>` or `<Control>`.
- **Modifiers must appear in GTK's canonical order**: `<Shift><Primary><Alt><Super>`.
  A string in the wrong order is silently accepted and never fires.
- Letter keys are lowercase (`<Super>w`); named keys use X keysyms (`Return`, `space`,
  `Print`, `Tab`, `grave`, `comma`, `BackSpace`, `Escape`, `Delete`).

Two separate xfconf paths are involved:

| Path | Holds | Value |
| ------ | ------- | ------- |
| `/xfwm4/custom/<accel>` | Window-manager actions | An action name, e.g. `close_window_key` |
| `/commands/custom/<accel>` | Everything else | A shell command |

### Navigating

| Omarchy | Function | XFCE | Status |
| --------- | ---------- | ------ | -------- |
| `Super + Space` | Omarchy menu | `omarchy-menu` (rofi) | Emulated |
| `Super + Alt + Space` | Apps menu | `omarchy-menu` (same launcher) | Emulated |
| `Super + Escape` | System menu | `xfce4-session-logout` — **[read this first](#disconnect-vs-log-out)** | Native |
| `Super + Ctrl + L` | Lock | `xflock4` | Native |
| `Super + W` / `Super + Q` | Close window | `close_window_key` | Native |
| `Ctrl + Alt + Del` | Close all windows | *(XFCE binds this to the logout dialog)* | Not possible |
| `Super + F` | Fullscreen | `fullscreen_key` | Native |
| `Super + Alt + F` | Full width | `fill_horiz_key` | Native |
| `Super + Ctrl + F` | Fullscreen inside window | — | Not possible |
| `Super + O` | Pop out sticky + floating | `stick_window_key` | Native |
| `Super + 1…4` | Jump to workspace | `workspace_1_key` … `workspace_4_key` | Native |
| `Super + Shift + 1…4` | Move window to workspace | `move_window_workspace_1_key` … | Native |
| `Super + Tab` | Next workspace | `next_workspace_key` | Native |
| `Super + Shift + Tab` | Previous workspace | `prev_workspace_key` | Native |
| `Alt + Tab` | Cycle windows | `cycle_windows_key` | Native |
| `Alt + Shift + Tab` | Cycle backwards | `cycle_reverse_windows_key` | Native |
| `Super + Arrow` | Move focus directionally | `omarchy-focus-direction` | Emulated |
| `Super + Shift + Arrow` | Swap window | `tile_left_key` / `tile_right_key` / `tile_up_key` / `tile_down_key` — **tiles, does not swap** | Native (different semantics) |
| `Super + S` / `Super + Grave` | Scratchpad | `omarchy-scratchpad` | Emulated |
| `Super + Alt + S` | Move window to scratchpad | — | Not possible |
| `Super + T` | Toggle tiling/floating | *(every xfwm4 window already floats)* | Not possible |
| `Super + L` | Dwindle ↔ scrolling layout | — | Not possible |
| `Super + J` | Toggle window position | — | Not possible |
| `Super + P` | Pseudo window style | — | Not possible |
| `Super + G` | Window grouping | — | Not possible |
| `Super + Minus` / `Super + Equal` | Resize in steps | `resize_window_key` enters an interactive resize mode instead | Native (different semantics) |
| `Super + Ctrl + Z` | Screen zoom | — | Not possible |
| `Super + Ctrl + Tab` | Former workspace | — | Not possible |

Omarchy uses four workspaces. Set the same in *Settings → Workspaces*, or:

```bash
xfconf-query -c xfwm4 -p /general/workspace_count -s 4
```

Bonus: xfwm4 also tiles into quarters, which Omarchy has no equivalent for —
`tile_up_left_key`, `tile_up_right_key`, `tile_down_left_key`, `tile_down_right_key`.

### System controls

| Omarchy | Function | XFCE | Status |
| --------- | ---------- | ------ | -------- |
| `Super + Ctrl + A` | Audio panel | `omarchy-panel audio` (pavucontrol) | Emulated |
| `Super + Ctrl + B` | Bluetooth panel | `omarchy-panel bluetooth` (blueman) | Emulated |
| `Super + Ctrl + W` | Network panel | `omarchy-panel network` | Emulated |
| `Super + Ctrl + D` | Display panel | `omarchy-panel display` | Emulated |
| `Super + Ctrl + P` | Power panel | `omarchy-panel power` | Emulated |
| `Super + Ctrl + Alt + D` | Calendar | `omarchy-panel calendar` | Emulated |
| `Super + Ctrl + T` | Activity monitor | `alacritty -e btop` | Native |
| `Super + Ctrl + S` | Share (LocalSend) | `localsend` | Emulated |
| `Super + Ctrl + Q` | Calculator | `galculator` | Native |
| `Super + Ctrl + E` | Emoji picker | `rofimoji` | Emulated |
| `Super + Ctrl + C` | Capture menu | `omarchy-screenshot-selection` | Emulated |
| `Super + Ctrl + O` / `Super + Ctrl + H` | Toggle / hardware menu | *(no Omarchy menu to open)* | Not possible |
| `Super + Ctrl + .` | Transcode media | *(use `ffmpeg` directly)* | Not possible |

### Launching apps

| Omarchy | Function | XFCE | Status |
| --------- | ---------- | ------ | -------- |
| `Super + Return` | Terminal | `alacritty` | Native |
| `Super + Shift + Return` | Browser | `omarchy-launch-browser` | Emulated |
| `Super + Shift + Alt + B` | Browser (private) | `omarchy-launch-browser --private` | Emulated |
| `Super + Shift + F` | File manager | `thunar` | Native |
| `Super + Shift + N` | Editor | `code` (or your editor) | Native |
| `Super + Shift + G` | Messenger | `signal-desktop` | Native |
| `Super + Alt + Return` | Tmux terminal | `alacritty -e tmux` | Native |

Earlier versions of this guide bound the browser to `Super + Shift + B`; Omarchy moved it
to `Super + Shift + Return`, and the activity monitor from `Super + Shift + T` to
`Super + Ctrl + T`. The file manager was `nautilus`, which is GNOME's — `thunar` is
XFCE's own and is already installed.

### Universal clipboard

| Omarchy | Function | XFCE | Status |
| --------- | ---------- | ------ | -------- |
| `Super + C` | Copy | `omarchy-smart-copy` | Emulated |
| `Super + X` | Cut | `omarchy-smart-cut` | Emulated |
| `Super + V` | Paste | `omarchy-smart-paste` | Emulated |
| `Super + Ctrl + V` | Clipboard history | `xfce4-popup-clipman` | Native |

### Capture

| Omarchy | Function | XFCE | Status |
| --------- | ---------- | ------ | -------- |
| `Print` | Screenshot | `omarchy-screenshot-file` | Emulated `†` |
| `Alt + Print` | Screen recording | `omarchy-screenrecord` | Emulated `†` |
| `Super + Print` | Colour picker | `omarchy-color-picker` | Emulated `†` |
| `Super + Ctrl + Print` | Text extraction (OCR) | `omarchy-ocr` | Emulated `†` |
| `Shift + Print` | Screenshot to clipboard only | `omarchy-screenshot-selection` | Emulated `†` |

`†` **On Windows clients these keys never reach the session** — the client keeps
`Print` and `Alt + Print` for its own clipboard snapshots. Bind the
[Tier A aliases](#tier-a--print-key-aliases) instead. FreeRDP and Remmina forward them
normally, and so does a local desktop. Details in
[The Print key problem](#the-print-key-problem).

`Shift + Print` is not an Omarchy binding — Omarchy's single `Print` saves to a file *and*
copies to the clipboard. `omarchy-screenshot-file` does both, so the extra key is only
there if you want clipboard-only.

### Notifications

| Omarchy | Function | XFCE | Status |
| --------- | ---------- | ------ | -------- |
| `Super + Ctrl + ,` | Toggle do-not-disturb | `omarchy-toggle-dnd` | Emulated |
| `Super + Shift + Alt + ,` | Notification history | `xfce4-notifyd-config` (Log tab) | Emulated |
| `Super + ,` | Dismiss latest | — | Not possible |
| `Super + Shift + ,` | Dismiss all | — | Not possible |
| `Super + Alt + ,` | Invoke most recent | — | Not possible |

`xfce4-notifyd` writes its log to `~/.cache/xfce4/notifyd/log`, but only when logging is
enabled:

```bash
xfconf-query -c xfce4-notifyd -p /notification-log --create -t bool -s true
```

There is no CLI to pop up the log — `xfce4-notifyd-config` opens the settings dialog,
whose Log tab shows the last 100 entries.

### Style

| Omarchy | Function | XFCE | Status |
| --------- | ---------- | ------ | -------- |
| `Super + Ctrl + Shift + Space` | Pick a theme | `omarchy-theme-switch` | Emulated |
| `Super + Ctrl + Space` | Pick a background | one-liner below | Emulated |
| `Super + Backspace` | Toggle window transparency | one-liner below | **Not possible** `†` |
| `Super + Ctrl + Backspace` | Square single-window aspect | — | Not possible |

Random background from a directory:

```bash
xfconf-query -c xfce4-desktop -p /backdrop/screen0/monitor0/workspace0/last-image \
  -s "$(find ~/Pictures/wallpapers -type f | shuf -n 1)"
```

Toggle transparency on the focused window (picom reads `_NET_WM_WINDOW_OPACITY`;
`0xcccccccc` is 80%):

```bash
xprop -id "$(xdotool getactivewindow)" -f _NET_WM_WINDOW_OPACITY 32c \
  -set _NET_WM_WINDOW_OPACITY 0xcccccccc
```

Remove it again with `xprop -id … -remove _NET_WM_WINDOW_OPACITY`.

`†` `_NET_WM_WINDOW_OPACITY` is only a hint — something has to composite the window for
it to mean anything. With no compositor running (the default over xrdp, see
[Compositing](#compositing)) setting the property has no visible effect.

### Toggles

| Omarchy | Function | XFCE | Status |
| --------- | ---------- | ------ | -------- |
| `Super + Ctrl + N` | Night light | `omarchy-toggle-nightlight` | **Not possible** `†` |
| `Super + Shift + Space` | Toggle the bar | `omarchy-toggle-bar` | Emulated |
| `Super + Ctrl + I` | Stay awake (no idle lock) | `xfconf-query -c xfce4-session -p /shutdown/LockScreen -T` | Emulated |
| `Super + Shift + Backspace` | Window gaps | *(xfwm4 has no gaps)* | Not possible |

`†` The night light works on a local desktop (`redshift`). Under xorgxrdp the driver has
no gamma path at all, so it silently does nothing — the script detects the session and
says so rather than pretending. Not verified for the Xvnc backend. See
[Works locally, degraded or dead over xrdp](#works-locally-degraded-or-dead-over-xrdp).

### Notices

| Omarchy | Function | XFCE | Status |
| --------- | ---------- | ------ | -------- |
| `Super + Ctrl + Alt + T` | Time as a notification | `omarchy-notice time` | Emulated |
| `Super + Ctrl + Alt + B` | Battery as a notification | `omarchy-notice battery` | Emulated `†` |
| `Super + Ctrl + Alt + W` | Weather as a notification | `omarchy-notice weather` | Emulated `†` |

`†` A remote host normally has no battery, so this reports "No battery reported by acpi".
The weather line needs outbound network access from the *server*, not from your client.

### Reminders

| Omarchy | Function | XFCE | Status |
| --------- | ---------- | ------ | -------- |
| `Super + Ctrl + R` | Set a reminder | `omarchy-reminder` | Emulated |
| `Super + Ctrl + Alt + R` | List reminders | — | Not possible |
| `Super + Ctrl + Shift + R` | Clear reminders | — | Not possible |

### Media and hardware keys

Straight XFCE application shortcuts, unchanged from earlier versions of this guide.

| Key | Command |
| ----- | --------- |
| `XF86AudioRaiseVolume` | `pamixer -i 5` |
| `XF86AudioLowerVolume` | `pamixer -d 5` |
| `XF86AudioMute` | `pamixer -t` |
| `XF86AudioPlay` | `playerctl play-pause` |
| `XF86AudioNext` | `playerctl next` |
| `XF86AudioPrev` | `playerctl previous` |
| `XF86MonBrightnessUp` | `brightnessctl set +5%` `†` |
| `XF86MonBrightnessDown` | `brightnessctl set 5%-` `†` |

`†` Brightness only exists on a local desktop. A virtual session has no backlight device,
so `brightnessctl` fails; skip these two bindings on a remote host. Volume and playback
keys do work remotely, provided `pipewire-module-xrdp` is installed — see
[Audio](#audio).

---

## Applying the Keybindings

Adding forty-odd shortcuts through *Settings → Keyboard* one dialog at a time is not
realistic. Paste the block below into a terminal instead.

### Back up first

This overwrites existing bindings on the same keys.

```bash
xfconf-query -c xfce4-keyboard-shortcuts -lv > ~/xfce-shortcuts-backup.txt
```

### Apply

```bash
#!/bin/bash
set -euo pipefail

BIN="$HOME/.local/bin"
CH=xfce4-keyboard-shortcuts

# XFCE spawns these commands directly, not through a shell, so "~" and "$HOME"
# are NOT expanded at run time. Absolute paths are mandatory.

wm() { xfconf-query -c "$CH" -p "/xfwm4/custom/$1" --create -t string -s "$2"; }
cmd() { xfconf-query -c "$CH" -p "/commands/custom/$1" --create -t string -s "$2"; }

# --- Window manager actions -------------------------------------------------
wm '<Super>w'                 close_window_key
wm '<Super>q'                 close_window_key
wm '<Super>f'                 fullscreen_key
wm '<Alt><Super>f'            fill_horiz_key
wm '<Super>o'                 stick_window_key
wm '<Super>Tab'               next_workspace_key
wm '<Shift><Super>Tab'        prev_workspace_key

# Omarchy swaps windows with Super+Shift+Arrow; xfwm4 tiles instead.
wm '<Shift><Super>Left'       tile_left_key
wm '<Shift><Super>Right'      tile_right_key
wm '<Shift><Super>Up'         tile_up_key
wm '<Shift><Super>Down'       tile_down_key

for i in 1 2 3 4; do
    wm "<Super>$i"            "workspace_${i}_key"
    wm "<Shift><Super>$i"     "move_window_workspace_${i}_key"
done

# --- Launching --------------------------------------------------------------
cmd '<Super>Return'           'alacritty'
cmd '<Alt><Super>Return'      'alacritty -e tmux'
cmd '<Shift><Super>Return'    "$BIN/omarchy-launch-browser"
cmd '<Shift><Alt><Super>b'    "$BIN/omarchy-launch-browser --private"
cmd '<Shift><Super>f'         'thunar'
cmd '<Shift><Super>n'         'code'
cmd '<Shift><Super>g'         'signal-desktop'
cmd '<Super>space'            "$BIN/omarchy-menu"
cmd '<Alt><Super>space'       "$BIN/omarchy-menu"
cmd '<Super>Escape'           'xfce4-session-logout'
cmd '<Primary><Super>l'       'xflock4'

# --- Directional focus ------------------------------------------------------
cmd '<Super>Left'             "$BIN/omarchy-focus-direction left"
cmd '<Super>Right'            "$BIN/omarchy-focus-direction right"
cmd '<Super>Up'               "$BIN/omarchy-focus-direction up"
cmd '<Super>Down'             "$BIN/omarchy-focus-direction down"

# --- Scratchpad -------------------------------------------------------------
cmd '<Super>s'                "$BIN/omarchy-scratchpad"
cmd '<Super>grave'            "$BIN/omarchy-scratchpad"

# --- Clipboard --------------------------------------------------------------
cmd '<Super>c'                "$BIN/omarchy-smart-copy"
cmd '<Super>x'                "$BIN/omarchy-smart-cut"
cmd '<Super>v'                "$BIN/omarchy-smart-paste"
cmd '<Primary><Super>v'       'xfce4-popup-clipman'

# --- Capture ----------------------------------------------------------------
cmd 'Print'                   "$BIN/omarchy-screenshot-file"
cmd '<Shift>Print'            "$BIN/omarchy-screenshot-selection"
cmd '<Alt>Print'              "$BIN/omarchy-screenrecord"
cmd '<Super>Print'            "$BIN/omarchy-color-picker"
cmd '<Primary><Super>Print'   "$BIN/omarchy-ocr"
cmd '<Primary><Super>c'       "$BIN/omarchy-screenshot-selection"

# --- System panels ----------------------------------------------------------
cmd '<Primary><Super>a'       "$BIN/omarchy-panel audio"
cmd '<Primary><Super>b'       "$BIN/omarchy-panel bluetooth"
cmd '<Primary><Super>w'       "$BIN/omarchy-panel network"
cmd '<Primary><Super>d'       "$BIN/omarchy-panel display"
cmd '<Primary><Super>p'       "$BIN/omarchy-panel power"
cmd '<Primary><Alt><Super>d'  "$BIN/omarchy-panel calendar"
cmd '<Primary><Super>t'       'alacritty -e btop'
cmd '<Primary><Super>s'       'localsend'
cmd '<Primary><Super>q'       'galculator'
cmd '<Primary><Super>e'       'rofimoji'

# --- Notifications and toggles ---------------------------------------------
cmd '<Primary><Super>comma'      "$BIN/omarchy-toggle-dnd"
cmd '<Shift><Alt><Super>comma'   'xfce4-notifyd-config'
cmd '<Primary><Super>n'          "$BIN/omarchy-toggle-nightlight"
cmd '<Shift><Super>space'        "$BIN/omarchy-toggle-bar"

# --- Style ------------------------------------------------------------------
cmd '<Shift><Primary><Super>space' "$BIN/omarchy-theme-switch"

# --- Notices and reminders --------------------------------------------------
cmd '<Primary><Alt><Super>t'  "$BIN/omarchy-notice time"
cmd '<Primary><Alt><Super>b'  "$BIN/omarchy-notice battery"
cmd '<Primary><Alt><Super>w'  "$BIN/omarchy-notice weather"
cmd '<Primary><Super>r'       "$BIN/omarchy-reminder"

# --- Media and hardware keys ------------------------------------------------
cmd 'XF86AudioRaiseVolume'    'pamixer -i 5'
cmd 'XF86AudioLowerVolume'    'pamixer -d 5'
cmd 'XF86AudioMute'           'pamixer -t'
cmd 'XF86AudioPlay'           'playerctl play-pause'
cmd 'XF86AudioNext'           'playerctl next'
cmd 'XF86AudioPrev'           'playerctl previous'
cmd 'XF86MonBrightnessUp'     'brightnessctl set +5%'
cmd 'XF86MonBrightnessDown'   'brightnessctl set 5%-'

# Four workspaces, matching Omarchy
xfconf-query -c xfwm4 -p /general/workspace_count -s 4

# --- Remote-session window manager tuning -----------------------------------
# box_move and box_resize default to false upstream. Wireframe move/resize sends a
# rectangle instead of a live redraw, which is the difference between usable and not
# on a slow link. Compositing has to be off either way.
xfconf-query -c xfwm4 -p /general/use_compositing -s false
xfconf-query -c xfwm4 -p /general/box_move        -s true
xfconf-query -c xfwm4 -p /general/box_resize      -s true

echo "Done. Log out and back in if anything does not respond."
```

### Verify

```bash
xfconf-query -c xfce4-keyboard-shortcuts -lv | grep -i super | sort
```

If a binding does nothing, the accelerator string is almost always the cause — check the
modifier order and that Ctrl is spelled `<Primary>`.

### Tier A — Print-key aliases

**Bind these if you connect from a Windows client.** They are the only part of this guide
that cannot be fixed in client settings: `Print` and `Alt + Print` are consumed by the
client itself. Everything else that appears broken is a `Super`-forwarding problem, and
belongs in [RDP Client Setup](#rdp-client-setup) instead.

Five bindings, added alongside the `Print` ones — nothing is removed, so both work
wherever both arrive.

```bash
#!/bin/bash
set -euo pipefail

BIN="$HOME/.local/bin"
CH=xfce4-keyboard-shortcuts
cmd() { xfconf-query -c "$CH" -p "/commands/custom/$1" --create -t string -s "$2"; }

cmd '<Shift><Primary><Alt>p'  "$BIN/omarchy-screenshot-file"
cmd '<Shift><Primary><Alt>s'  "$BIN/omarchy-screenshot-selection"
cmd '<Shift><Primary><Alt>r'  "$BIN/omarchy-screenrecord"
cmd '<Shift><Primary><Alt>c'  "$BIN/omarchy-color-picker"
cmd '<Shift><Primary><Alt>o'  "$BIN/omarchy-ocr"
```

| Alias | Replaces | Action |
| ------- | ---------- | -------- |
| `Ctrl + Shift + Alt + P` | `Print` | Screenshot to a file |
| `Ctrl + Shift + Alt + S` | `Shift + Print` | Screenshot to the clipboard |
| `Ctrl + Shift + Alt + R` | `Alt + Print` | Toggle screen recording |
| `Ctrl + Shift + Alt + C` | `Super + Print` | Colour picker |
| `Ctrl + Shift + Alt + O` | `Super + Ctrl + Print` | OCR |

Three-modifier combinations were chosen deliberately: they collide with far less than
plain `Ctrl + Alt + <letter>` does, and none of them is on the
[list of keys the client keeps](#keys-the-rdp-client-keeps-for-itself).

To undo:

```bash
for k in p s r c o; do
    xfconf-query -c xfce4-keyboard-shortcuts \
      -p "/commands/custom/<Shift><Primary><Alt>$k" -r
done
```

### Tier B — no-Super fallback

**Only bind this if your client genuinely cannot forward `Super`** — a locked-down
Windows client, a browser-based gateway, or a nested RDP session, where Microsoft
documents hotkeys as not working at all. For everything else, fix the client; it is one
dropdown.

**Read the cost first.** This takes over `Ctrl + Alt + <letter>`, which on Linux is not
free space. JetBrains IDEs bind `Ctrl + Alt` with `L`, `S`, `O`, `V`, `T`, `F`, `C` and
`P` by default, among others. XFCE grabs shortcuts globally and wins, so the IDE simply
stops receiving them. Check what you would be shadowing before you run this:

```bash
# What is already bound on these keys
xfconf-query -c xfce4-keyboard-shortcuts -lv | grep -i 'Primary><Alt'
```

```bash
#!/bin/bash
set -euo pipefail

BIN="$HOME/.local/bin"
CH=xfce4-keyboard-shortcuts
wm()  { xfconf-query -c "$CH" -p "/xfwm4/custom/$1"   --create -t string -s "$2"; }
cmd() { xfconf-query -c "$CH" -p "/commands/custom/$1" --create -t string -s "$2"; }

# --- Window manager actions -------------------------------------------------
wm '<Primary><Alt>w'              close_window_key
wm '<Primary><Alt>f'              fullscreen_key
wm '<Primary><Alt>Left'           prev_workspace_key
wm '<Primary><Alt>Right'          next_workspace_key

for i in 1 2 3 4; do
    wm "<Primary><Alt>$i"         "workspace_${i}_key"
    wm "<Shift><Primary><Alt>$i"  "move_window_workspace_${i}_key"
done

# --- Commands ---------------------------------------------------------------
cmd '<Primary><Alt>Return'        'alacritty'
cmd '<Primary><Alt>t'             'alacritty'
cmd '<Primary><Alt>space'         "$BIN/omarchy-menu"
cmd '<Primary><Alt>l'             'xflock4'
cmd '<Primary><Alt>grave'         "$BIN/omarchy-scratchpad"
cmd '<Primary><Alt>v'             'xfce4-popup-clipman'

cmd '<Shift><Primary><Alt>Left'   "$BIN/omarchy-focus-direction left"
cmd '<Shift><Primary><Alt>Right'  "$BIN/omarchy-focus-direction right"
cmd '<Shift><Primary><Alt>Up'     "$BIN/omarchy-focus-direction up"
cmd '<Shift><Primary><Alt>Down'   "$BIN/omarchy-focus-direction down"
```

| Alias | Replaces | Action |
| ------- | ---------- | -------- |
| `Ctrl + Alt + Return`, `Ctrl + Alt + T` | `Super + Return` | Terminal |
| `Ctrl + Alt + Space` | `Super + Space` | Launcher |
| `Ctrl + Alt + W` | `Super + W` | Close window |
| `Ctrl + Alt + F` | `Super + F` | Fullscreen |
| `Ctrl + Alt + 1…4` | `Super + 1…4` | Switch workspace |
| `Ctrl + Shift + Alt + 1…4` | `Super + Shift + 1…4` | Move window to workspace |
| `Ctrl + Alt + Left` / `Right` | `Super + Tab` / `Super + Shift + Tab` | Previous / next workspace |
| `Ctrl + Shift + Alt + Arrow` | `Super + Arrow` | Move focus in a direction |
| `Ctrl + Alt + L` | `Super + Ctrl + L` | Lock |
| `Ctrl + Alt + Grave` | `Super + Grave` | Scratchpad |
| `Ctrl + Alt + V` | `Super + Ctrl + V` | Clipboard history |

`Ctrl + Alt + Left` / `Right` is XFCE's own traditional workspace binding, so this binds
it to the meaning it already had rather than repurposing it.

To undo:

```bash
CH=xfce4-keyboard-shortcuts
for k in w f Left Right 1 2 3 4 Return t space l grave v; do
    xfconf-query -c "$CH" -p "/xfwm4/custom/<Primary><Alt>$k"   -r 2>/dev/null || true
    xfconf-query -c "$CH" -p "/commands/custom/<Primary><Alt>$k" -r 2>/dev/null || true
done
for k in 1 2 3 4 Left Right Up Down; do
    xfconf-query -c "$CH" -p "/xfwm4/custom/<Shift><Primary><Alt>$k"   -r 2>/dev/null || true
    xfconf-query -c "$CH" -p "/commands/custom/<Shift><Primary><Alt>$k" -r 2>/dev/null || true
done
```

---

## Configuration Files

### Compositing

**Over xrdp, run no compositor at all.** That is the default assumed everywhere else in
this guide, and it is already applied by the
[keybinding script](#applying-the-keybindings):

```bash
xfconf-query -c xfwm4 -p /general/use_compositing -s false
```

Three points on a scale, so you can decide rather than just be told:

| | Cost over RDP | Verdict |
| --- | --------------- | --------- |
| Blur (`dual_kawase`) and shadows | Every frame is recomposited, then re-encoded and shipped. No GPU unless you installed `xorgxrdp-glamor`. | Don't |
| Plain transparency, `--backend xrender`, no blur, no shadows | Much cheaper, but still puts a compositor between every redraw and the wire | **Untested here.** Try it if you want it; measure before you keep it |
| No compositor | — | The default in this guide |

There is no XFCE-side switch that makes this free. If you want composited effects on a
remote desktop, the honest prerequisite is GPU acceleration in the session —
`xorgxrdp-glamor` or `xorgxrdp-nvidia` — not a lighter picom config.

#### Local desktop: picom configuration

**Location:** `~/.config/picom/picom.conf`

Compositing: transparency, shadows, blur. XFCE's own compositor must be off, or the two
will fight.

| Setting | Value |
| --------- | ------- |
| Backend | `glx` |
| Shadow radius | 16 |
| Inactive opacity | 0.95 |
| Blur method | `dual_kawase` |
| Blur strength | 5 |

### Rofi

**Location:** `~/.config/rofi/config.rasi`

| Setting | Value |
| --------- | ------- |
| Background | `#1e1e2e` |
| Foreground | `#cdd6f4` |
| Font | `JetBrainsMono Nerd Font 11` |
| Width | 600 |
| Border radius | 0 |

### Alacritty

**Location:** `~/.config/alacritty/alacritty.toml`

| Setting | Value |
| --------- | ------- |
| Opacity | `1.0` remotely, `0.9` locally |
| Font | `JetBrainsMono Nerd Font 11` |
| Background | `#1e1e2e` |
| Foreground | `#cdd6f4` |

Terminal opacity needs a compositor to mean anything. With none running — the default
over xrdp — `0.9` gets you an opaque window and a slightly odd-looking config file, so
set it to `1.0` and be explicit about it.

Omarchy's default terminal is Foot, which is Wayland-only and cannot run on XFCE.
Alacritty is one of Omarchy's supported alternatives and is the closest match here.

### XFCE Panel

**Location:** *Settings → Panel*

| Setting | Value |
| --------- | ------- |
| Height | 26 px |
| Background | `#1e1e2e` |
| Items | Workspace switcher, clock (centre), system monitors, audio, network, battery |

Add the **Clipman** and **Notification** plugins here — Clipman must be running for
`Super + Ctrl + V` to work.

This is the loosest approximation in the whole guide. Omarchy's bar is not a status bar
but part of the shell process that also draws the menu, notifications, OSD popups, and
lock screen, with left/right/middle click actions on nearly every widget.

### Window Manager

**Location:** *Settings → Window Manager*

| Setting | Value |
| --------- | ------- |
| Theme | Adwaita-dark |
| Title font | `JetBrainsMono Nerd Font 10` |
| Compositor | **Disabled** — see [Compositing](#compositing) |
| Move / resize | Wireframe (`box_move`, `box_resize`) |

Wireframe move and resize are off upstream. Turning them on trades a live preview for a
rectangle outline, which over a remote link is the difference between dragging a window
and watching a slideshow of it:

```bash
xfconf-query -c xfwm4 -p /general/box_move   -s true
xfconf-query -c xfwm4 -p /general/box_resize -s true
```

Skip both on a local desktop if you prefer the live preview.

### Fonts and blanking

Two settings that only matter remotely. Both are judgement calls rather than anything the
documentation mandates, so the reasoning is spelled out.

```bash
# Subpixel antialiasing puts coloured fringes on glyph edges. Lossy RDP codecs then
# amplify them into visible artefacts. Greyscale antialiasing avoids the whole problem.
xfconf-query -c xsettings -p /Xft/RGBA -s none

# Screen blanking and DPMS protect a monitor you are not looking at. There is no monitor,
# and a blanked virtual screen is one more thing that can go wrong on reconnect.
xset s off -dpms
```

`xset` does not persist. Put it in *Settings → Session and Startup → Application
Autostart* if you want it every session.

### Workspaces

Four, to match Omarchy.

### Autostart Applications

**Location:** *Settings → Session and Startup → Application Autostart*

| Application | Command | Remote? |
| ------------- | --------- | --------- |
| Clipman | `xfce4-clipman` | Yes |
| Disable blanking | `xset s off -dpms` | Yes |
| Picom | `picom --config ~/.config/picom/picom.conf` | **No — omit the entry** |
| Notification daemon | started on demand by D-Bus; no entry needed | — |

On a remote host, simply do not create the Picom entry. A guard inside the `Exec=` line
is the obvious-looking alternative, but desktop-entry quoting rules make
`Exec=sh -c '...$XRDP_SESSION...'` fragile enough that it is not worth the cleverness for
a checkbox you tick once.

`nitrogen` is no longer used — `xfdesktop` handles the wallpaper and is already running.

---

## Quick Reference Card

```text
╔══════════════════════════════════════════════════════════╗
║            XFCE OMARCHY-STYLE KEYBINDINGS                ║
╠══════════════════════════════════════════════════════════╣
║ LAUNCHING                                                ║
║ Super + Return             = Terminal                    ║
║ Super + Space              = App launcher                ║
║ Super + Shift + Return     = Browser                     ║
║ Super + Shift + F          = File manager                ║
║ Super + Shift + N          = Editor                      ║
║ Super + Escape             = Session menu                ║
║                                                          ║
║ WINDOWS                                                  ║
║ Super + W / Super + Q      = Close window                ║
║ Super + F                  = Fullscreen                  ║
║ Super + Alt + F            = Full width                  ║
║ Super + O                  = Stick to all workspaces     ║
║ Super + Arrow              = Focus in direction          ║
║ Super + Shift + Arrow      = Tile to that half           ║
║ Super + S                  = Scratchpad terminal         ║
║ Alt + Tab                  = Cycle windows               ║
║                                                          ║
║ WORKSPACES (4)                                           ║
║ Super + 1-4                = Switch workspace            ║
║ Super + Shift + 1-4        = Move window there           ║
║ Super + Tab                = Next workspace              ║
║ Super + Shift + Tab        = Previous workspace          ║
║                                                          ║
║ CLIPBOARD (works in the terminal too)                    ║
║ Super + C / X / V          = Copy / Cut / Paste          ║
║ Super + Ctrl + V           = Clipboard history           ║
║                                                          ║
║ CAPTURE                                                  ║
║ Print                      = Screenshot                  ║
║ Alt + Print                = Screen recording            ║
║ Super + Print              = Colour picker               ║
║ Super + Ctrl + Print       = Extract text (OCR)          ║
║                                                          ║
║ SYSTEM                                                   ║
║ Super + Ctrl + L           = Lock                        ║
║ Super + Ctrl + T           = Activity monitor            ║
║ Super + Ctrl + A/B/W/D/P   = Audio/BT/Net/Display/Power  ║
║ Super + Ctrl + Q           = Calculator                  ║
║ Super + Ctrl + E           = Emoji picker                ║
║ Super + Ctrl + S           = Share (LocalSend)           ║
║                                                          ║
║ TOGGLES & NOTICES                                        ║
║ Super + Ctrl + ,           = Do not disturb              ║
║ Super + Ctrl + N           = Night light (local only)    ║
║ Super + Shift + Space      = Toggle the panel            ║
║ Super + Ctrl + R           = Set a reminder              ║
║ Super + Ctrl + Alt + T/B/W = Time / Battery / Weather    ║
║                                                          ║
║ MEDIA                                                    ║
║ Volume / Play              = Hardware keys               ║
║ Brightness                 = Hardware keys, local only   ║
╚══════════════════════════════════════════════════════════╝
```

```text
╔══════════════════════════════════════════════════════════╗
║                 OVER XRDP - WHAT CHANGES                 ║
╠══════════════════════════════════════════════════════════╣
║ FIRST, IN THE RDP CLIENT                                 ║
║ mstsc: Local Resources > Keyboard >                      ║
║   Apply Windows key combinations                         ║
║   = On the remote computer                               ║
║ FreeRDP / Remmina: on by default, nothing to do          ║
║                                                          ║
║ TIER A - bind these on Windows clients                   ║
║ Ctrl + Shift + Alt + P     = Screenshot to file          ║
║ Ctrl + Shift + Alt + S     = Screenshot to clipboard     ║
║ Ctrl + Shift + Alt + R     = Screen recording            ║
║ Ctrl + Shift + Alt + C     = Colour picker               ║
║ Ctrl + Shift + Alt + O     = Extract text (OCR)          ║
║                                                          ║
║ DOES NOT WORK REMOTELY                                   ║
║ Super + Ctrl + N           = night light, no gamma path  ║
║ Super + Backspace          = needs a compositor          ║
║ Brightness keys            = no backlight device         ║
║                                                          ║
║ HANDLE WITH CARE                                         ║
║ Super + Escape             = its Shut Down button powers ║
║                              off the host you are using  ║
║                                                          ║
║ TIER B (Ctrl + Alt + ...) only if Super cannot be        ║
║ forwarded. It shadows JetBrains' Ctrl + Alt defaults.    ║
╚══════════════════════════════════════════════════════════╝
```

---

## Testing

### Script smoke test

```bash
# Each should do its thing without printing an error
~/.local/bin/omarchy-menu
~/.local/bin/omarchy-launch-browser
~/.local/bin/omarchy-screenshot-selection
~/.local/bin/omarchy-color-picker
~/.local/bin/omarchy-ocr
~/.local/bin/omarchy-focus-direction right
~/.local/bin/omarchy-notice time
```

If you edit any of them, check your work:

```bash
shellcheck ~/.local/bin/omarchy-*
```

### Dependencies

```bash
xcolor --version
tesseract --version
ffmpeg -version | head -n1
command -v xfce4-popup-clipman xfce4-notifyd-config pavucontrol blueman-manager
```

### Screen recording

```bash
# Three-second test capture
ffmpeg -loglevel error -f x11grab -framerate 30 \
  -video_size "$(xdpyinfo | awk '/dimensions:/ {print $2; exit}')" \
  -i "$DISPLAY" -t 3 /tmp/test.mp4 && echo OK
```

### Do not disturb

```bash
xfconf-query -c xfce4-notifyd -p /do-not-disturb   # should print true or false
```

If it errors with "Property does not exist", create it once:

```bash
xfconf-query -c xfce4-notifyd -p /do-not-disturb --create -t bool -s false
```

### Window queries

```bash
wmctrl -l          # all windows
wmctrl -d          # all workspaces, current marked with *
wmctrl -lG         # windows with geometry (what omarchy-focus-direction reads)
xprop -root _NET_ACTIVE_WINDOW
```

### In an xrdp session

Session detection — at least one of these must say yes, or the guards in the scripts
cannot fire:

```bash
echo "XRDP_SESSION=${XRDP_SESSION:-unset}"
xrandr --listmonitors        # expect an output named rdp0 on the Xorg backend
```

Audio, which needs `pipewire-module-xrdp` and a fresh login:

```bash
pactl info | grep -i 'server name\|default sink'
pamixer --get-volume
```

Which keys actually arrive. Run this, then press `Super`, `Print`, and `Alt + Print`:

```bash
xev | grep -i keysym
```

No `Super_L` means the client is not forwarding it — go to
[RDP Client Setup](#rdp-client-setup). No `Print` means you want the
[Tier A aliases](#tier-a--print-key-aliases).

Night light. **The correct result here is that nothing happens:**

```bash
redshift -O 4000    # exits 0, screen colour unchanged -- this is expected over xrdp
redshift -x
```

Recording and clipboard round-trip:

```bash
# Three seconds of the virtual display
ffmpeg -loglevel error -f x11grab -framerate 30 \
  -video_size "$(xdpyinfo | awk '/dimensions:/ {print $2; exit}')" \
  -i "$DISPLAY" -t 3 /tmp/test.mp4 && echo OK

# Copy here, then paste on your local machine. Needs xrdp-chansrv running.
echo "round trip" | xclip -selection clipboard
pgrep -a xrdp-chansrv
```

---

## Troubleshooting

### A keybinding does nothing

Almost always the accelerator string. Check it:

```bash
xfconf-query -c xfce4-keyboard-shortcuts -lv | grep -i super | sort
```

Three things to verify:

1. Ctrl is spelled `<Primary>`, not `<Ctrl>` or `<Control>`.
2. Modifiers are in GTK order: `<Shift><Primary><Alt><Super>`.
3. The command is an **absolute path**. XFCE does not run it through a shell, so `~` and
   `$HOME` stay literal and the command silently fails.

Confirm the key is even reaching X:

```bash
xev | grep -i -E 'keysym|super'
```

### Scripts are not found

```bash
ls -l ~/.local/bin/omarchy-*
chmod +x ~/.local/bin/omarchy-*
echo "$PATH" | tr ':' '\n' | grep '.local/bin'
```

Remember that the keybindings use absolute paths, so `PATH` only matters when you run
them yourself from a terminal.

### Over xrdp: the session is black, green, or blank

Each has a different cause and a documented fix:

| Symptom | Cause | Fix |
| --------- | ------- | ----- |
| Black screen after login | `~/.xinitrc` ends in `exec $(get_session "$1")` and `$1` is empty | `exec $(get_session "${1:-xfce}")` |
| Black screen, desktop environment only | D-Bus was never started | `exec dbus-launch --exit-with-session xfce4-session` |
| Green screen, nothing starts | `sesman.ini` cannot find Xorg | Change `param=Xorg` to `param=/usr/lib/Xorg` |
| Blank screen from Remmina and friends | Unprivileged users may not start X | `/etc/X11/Xwrapper.config`: `allowed_users=anybody`, `needs_root_rights=no` |
| Black box around the mouse pointer | Cursor rendering | `~/.Xresources-xrdp` with `Xcursor.core:1`, loaded via `xrdb` in `~/.xinitrc` |

### Over xrdp: no sound

```bash
pactl info          # if this fails there is no sink at all
```

Install `pipewire-module-xrdp` (or `pulseaudio-module-xrdp`) and **log out and back in** —
the module is loaded at session start, so installing it mid-session changes nothing.

### Over xrdp: the desktop is sluggish

In rough order of impact:

1. Compositing is still on. `xfconf-query -c xfwm4 -p /general/use_compositing -s false`
2. Something is running picom. See [Compositing](#compositing).
3. `use_fastpath` is still at its default of `none`, and `tcp_nodelay` is off. See
   [Tuning](#tuning).
4. H.264 is fighting your link. Try `order = ["RFX", "H.264"]` in `/etc/xrdp/gfx.toml`.
5. A screen recording is running and competing for CPU with xrdp's own encoder.

### Over xrdp: `Super` does nothing

The client is keeping it. This is a client setting, not an XFCE one — see
[Forwarding Super](#forwarding-super). Confirm with `xev` before changing anything in
XFCE.

### Over xrdp: `Print` does nothing

Expected on Windows clients: the client uses it for its own clipboard snapshots. Bind the
[Tier A aliases](#tier-a--print-key-aliases).

### Over xrdp: the night light does nothing

Also expected, and not a bug you can fix. xorgxrdp has no gamma path, so `redshift`
reports success and changes nothing; the reasoning and source references are in
[Works locally, degraded or dead over xrdp](#works-locally-degraded-or-dead-over-xrdp).
The shipped `omarchy-toggle-nightlight` detects the session and tells you instead of
pretending.

### Over xrdp: network or disk settings are greyed out

Remote sessions do not automatically inherit the polkit privileges a local seat gets.
NetworkManager and udisks both need explicit policy for this; the Arch wiki pages for
each cover the rules. If `podman` also misbehaves, xrdp's temporary D-Bus address is
usually why — re-export it in your shell profile:

```bash
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$UID/bus
export XDG_RUNTIME_DIR=/run/user/$UID
```

### Picom is not starting

```bash
killall picom
picom --config ~/.config/picom/picom.conf   # read the error it prints
```

If windows flicker or tear, the XFCE compositor is probably still on:

```bash
xfconf-query -c xfwm4 -p /general/use_compositing -s false
```

### Clipboard history is empty

`xfce4-clipman` has to be running:

```bash
pgrep -x xfce4-clipman || xfce4-clipman &
```

### Notification log is empty

Logging is off by default:

```bash
xfconf-query -c xfce4-notifyd -p /notification-log --create -t bool -s true
```

Entries then accumulate in `~/.cache/xfce4/notifyd/log`.

### `omarchy-focus-direction` picks the wrong window

It scores candidates by distance along the axis of travel plus twice the sideways offset.
Minimized windows are still candidates because `wmctrl -lG` lists them. Tune the scoring
in the `awk` block, or filter minimized windows out with `xprop _NET_WM_STATE`.

### Media keys are not recognised

```bash
xev | grep -i XF86
playerctl status
```

---

## Backup and Restore

### Backup

```bash
mkdir -p ~/xfce-omarchy-backup

cp -r ~/.config/picom     ~/xfce-omarchy-backup/
cp -r ~/.config/rofi      ~/xfce-omarchy-backup/
cp -r ~/.config/alacritty ~/xfce-omarchy-backup/
cp ~/.local/bin/omarchy-* ~/xfce-omarchy-backup/

for c in xfce4-keyboard-shortcuts xfwm4 xfce4-panel xfce4-notifyd xsettings xfce4-desktop; do
    xfconf-query -c "$c" -lv > "$HOME/xfce-omarchy-backup/$c.txt"
done
```

The `xfce-perchannel-xml` directory is the authoritative copy of all xfconf channels:

```bash
cp -r ~/.config/xfce4/xfconf/xfce-perchannel-xml ~/xfce-omarchy-backup/
```

The xrdp side lives outside your home directory, so back it up separately:

```bash
sudo cp /etc/xrdp/xrdp.ini /etc/xrdp/sesman.ini ~/xfce-omarchy-backup/
sudo cp /etc/xrdp/gfx.toml ~/xfce-omarchy-backup/ 2>/dev/null || true
cp ~/.xinitrc ~/xfce-omarchy-backup/ 2>/dev/null || true
```

### Restore

```bash
cp -r ~/xfce-omarchy-backup/picom     ~/.config/
cp -r ~/xfce-omarchy-backup/rofi      ~/.config/
cp -r ~/xfce-omarchy-backup/alacritty ~/.config/
cp ~/xfce-omarchy-backup/omarchy-*    ~/.local/bin/
chmod +x ~/.local/bin/omarchy-*
```

To restore xfconf channels, stop `xfconfd` first — it holds the settings in memory and
will overwrite the files on exit:

```bash
pkill xfconfd
cp -r ~/xfce-omarchy-backup/xfce-perchannel-xml ~/.config/xfce4/xfconf/
```

Log out and back in.

---

## Uninstall

```bash
# Scripts
rm -f ~/.local/bin/omarchy-*

# Configs
rm -rf ~/.config/picom ~/.config/rofi

# Re-enable the XFCE compositor
xfconf-query -c xfwm4 -p /general/use_compositing -s true

# Reset every keyboard shortcut to XFCE defaults
pkill xfconfd
rm -f ~/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-keyboard-shortcuts.xml

# Optionally remove the packages
sudo pacman -Rns picom rofi xcolor tesseract redshift galculator rofimoji
```

Log out and back in.

---

## Additional Resources

- [Omarchy Manual](https://omarchy.org/manual/) — what this guide tracks
- [Omarchy hotkey reference](https://omarchy.org/manual/hotkeys) — the source for every keybinding above
- [Xfce documentation](https://docs.xfce.org)
- [xfwm4 keyboard shortcuts](https://docs.xfce.org/xfce/xfwm4/keyboard_shortcuts)
- [xfconf-query](https://docs.xfce.org/xfce/xfconf/xfconf-query)
- [Arch Wiki — Xfce](https://wiki.archlinux.org/title/Xfce)
- [picom](https://github.com/yshui/picom)
- [rofi](https://github.com/davatorium/rofi)
- [Arch Wiki — Xrdp](https://wiki.archlinux.org/title/Xrdp) — the source for the setup and troubleshooting steps here
- [neutrinolabs/xrdp](https://github.com/neutrinolabs/xrdp) — `xrdp.ini` and `sesman.ini` reference
- [neutrinolabs/xorgxrdp](https://github.com/neutrinolabs/xorgxrdp) — the Xorg backend, and where the gamma finding comes from
- [Remote Desktop Services shortcut keys](https://learn.microsoft.com/en-us/windows/win32/termserv/terminal-services-shortcut-keys) — which keys a Windows client keeps

---

## Credits

- **Omarchy** — the design this guide imitates
- **XFCE** — the desktop environment doing the imitating
- **Hyprland** — the tiling model Omarchy is built on

---

**Tracks:** Omarchy Manual as of 2026-09-03
**Target:** xrdp with the Xorg (xorgxrdp) backend, XFCE 4.18+
**Configuration version:** 3.0
