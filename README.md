# XFCE with Omarchy-Style Configuration

Turn a stock XFCE desktop into something that behaves like [Omarchy](https://omarchy.org).

Omarchy is an Arch-based distribution built on Hyprland (a tiling Wayland compositor)
and Quickshell. XFCE is a stacking window manager on X11. Some of Omarchy's behaviour
maps over cleanly, some has to be simulated with scripts, and some cannot be reproduced
at all. This document is explicit about which is which — see the
[Compatibility Matrix](#compatibility-matrix).

**Tracking:** [Omarchy Manual](https://omarchy.org/manual/) as of 2026-09-03
([hotkey reference](https://omarchy.org/manual/hotkeys)).

## Table of Contents

- [Compatibility Matrix](#compatibility-matrix)
- [Prerequisites](#prerequisites)
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

Every binding in this document falls into one of three buckets:

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
| Night light | — | `redshift` |
| Reminders, notices | — | `notify-send` wrappers |

### What is not possible

| Omarchy feature | Why XFCE cannot do it | Third-party option |
| ----------------- | ---------------------- | -------------------- |
| Dwindle auto-tiling (new windows split automatically) | xfwm4 is a stacking WM with manual tiling only | None packaged in Arch repos or the AUR |
| Scrolling layout (`Super + L`) | No such concept | None |
| Window grouping / tabs (`Super + G`) | xfwm4 has no window groups | None |
| Screen zoom (`Super + Ctrl + Z`) | No compositor-level zoom | `magnus` or `xzoom` (AUR), standalone magnifiers |
| Fullscreen-inside-window (`Super + Ctrl + F`) | Hyprland-specific | None |
| Quickshell top bar (bar, menu, notifications, lock screen as one process) | XFCE panel is a separate plugin system | XFCE panel, approximated |
| Omarchy CLI, theme ecosystem, system snapshots | Part of the Omarchy distribution itself | Not applicable |

---

## Prerequisites

```bash
# CachyOS / Arch / any Arch derivative running XFCE
sudo pacman -Syu
```

Everything below assumes XFCE 4.18 or newer on X11.

---

## Required Packages

Grouped by what they are for, so you can skip the parts you do not want.

### Core

```bash
sudo pacman -S picom rofi maim xclip xdotool wmctrl \
  playerctl brightnessctl pamixer btop
```

| Package | Used for |
| --------- | ---------- |
| `picom` | Compositing (transparency, blur, shadows) — replaces the XFCE compositor |
| `rofi` | Application launcher (`Super + Space`) |
| `maim` `xclip` | Screenshots and clipboard piping |
| `xdotool` `wmctrl` | Window queries used by the helper scripts |
| `playerctl` `brightnessctl` `pamixer` | Media and hardware keys |
| `btop` | Activity monitor (`Super + Ctrl + T`) |

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
| `redshift` | Night light | `Super + Ctrl + N` |
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
[Autostart](#7-autostart-applications)).

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
        notify-send "Battery" "$(acpi -b | head -n1)"
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
| `Super + Escape` | System menu | `xfce4-session-logout` | Native |
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
| `Print` | Screenshot | `omarchy-screenshot-file` | Emulated |
| `Alt + Print` | Screen recording | `omarchy-screenrecord` | Emulated |
| `Super + Print` | Colour picker | `omarchy-color-picker` | Emulated |
| `Super + Ctrl + Print` | Text extraction (OCR) | `omarchy-ocr` | Emulated |
| `Shift + Print` | Screenshot to clipboard only | `omarchy-screenshot-selection` | Emulated |

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
| `Super + Backspace` | Toggle window transparency | one-liner below | Emulated |
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

### Toggles

| Omarchy | Function | XFCE | Status |
| --------- | ---------- | ------ | -------- |
| `Super + Ctrl + N` | Night light | `omarchy-toggle-nightlight` | Emulated |
| `Super + Shift + Space` | Toggle the bar | `omarchy-toggle-bar` | Emulated |
| `Super + Ctrl + I` | Stay awake (no idle lock) | `xfconf-query -c xfce4-session -p /shutdown/LockScreen -T` | Emulated |
| `Super + Shift + Backspace` | Window gaps | *(xfwm4 has no gaps)* | Not possible |

### Notices

| Omarchy | Function | XFCE | Status |
| --------- | ---------- | ------ | -------- |
| `Super + Ctrl + Alt + T` | Time as a notification | `omarchy-notice time` | Emulated |
| `Super + Ctrl + Alt + B` | Battery as a notification | `omarchy-notice battery` | Emulated |
| `Super + Ctrl + Alt + W` | Weather as a notification | `omarchy-notice weather` | Emulated |

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
| `XF86MonBrightnessUp` | `brightnessctl set +5%` |
| `XF86MonBrightnessDown` | `brightnessctl set 5%-` |

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

echo "Done. Log out and back in if anything does not respond."
```

### Verify

```bash
xfconf-query -c xfce4-keyboard-shortcuts -lv | grep -i super | sort
```

If a binding does nothing, the accelerator string is almost always the cause — check the
modifier order and that Ctrl is spelled `<Primary>`.

---

## Configuration Files

### 1. Picom

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

Disable the XFCE compositor:

```bash
xfconf-query -c xfwm4 -p /general/use_compositing -s false
```

### 2. Rofi

**Location:** `~/.config/rofi/config.rasi`

| Setting | Value |
| --------- | ------- |
| Background | `#1e1e2e` |
| Foreground | `#cdd6f4` |
| Font | `JetBrainsMono Nerd Font 11` |
| Width | 600 |
| Border radius | 0 |

### 3. Alacritty

**Location:** `~/.config/alacritty/alacritty.toml`

| Setting | Value |
| --------- | ------- |
| Opacity | 0.9 |
| Font | `JetBrainsMono Nerd Font 11` |
| Background | `#1e1e2e` |
| Foreground | `#cdd6f4` |

Omarchy's default terminal is Foot, which is Wayland-only and cannot run on XFCE.
Alacritty is one of Omarchy's supported alternatives and is the closest match here.

### 4. XFCE Panel

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

### 5. Window Manager

**Location:** *Settings → Window Manager*

| Setting | Value |
| --------- | ------- |
| Theme | Adwaita-dark |
| Title font | `JetBrainsMono Nerd Font 10` |
| Compositor | **Disabled** (picom instead) |

### 6. Workspaces

Four, to match Omarchy.

### 7. Autostart Applications

**Location:** *Settings → Session and Startup → Application Autostart*

| Application | Command |
| ------------- | --------- |
| Picom | `picom --config ~/.config/picom/picom.conf` |
| Clipman | `xfce4-clipman` |
| Notification daemon | started on demand by D-Bus; no entry needed |

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
║ Super + Ctrl + N           = Night light                 ║
║ Super + Shift + Space      = Toggle the panel            ║
║ Super + Ctrl + R           = Set a reminder              ║
║ Super + Ctrl + Alt + T/B/W = Time / Battery / Weather    ║
║                                                          ║
║ MEDIA                                                    ║
║ Volume, Play, Brightness   = Hardware keys               ║
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

---

## Credits

- **Omarchy** — the design this guide imitates
- **XFCE** — the desktop environment doing the imitating
- **Hyprland** — the tiling model Omarchy is built on

---

**Tracks:** Omarchy Manual as of 2026-09-03
**Configuration version:** 2.0
