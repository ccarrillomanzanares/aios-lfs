# AIOS Work Plan — 22 Aug 2026

Verified against the actual state of the tree (`~/aios-work/squashfs-root`) and the `sre-agent` repo on 22 Aug 2026.

## Closed (no work needed)
- **Dual glibc**: RESOLVED. The tree has a single glibc **2.44** in `/usr/lib`, and `/lib64/{libc.so.6,ld-linux-x86-64.so.2}` are internal symlinks to `/usr/lib`. `ldd` in chroot = 2.44. No trace of Ubuntu.

## Dropped / pending (not touched for now)
- Block 0 (PipeWire, microcode, wireless-regdb, i3 binds): forgotten for now.
- Firefox/YouTube: Carlos tests and reports.
- Daemon/watchdog (1.5), restic backup (1.6), `aios-update` (2.1), live persistence (2.3), CI (3.1), tests (3.2): no.

## Milestones

### Milestone 1 — Remove hybrid mode
- No longer in `setup.py`; remains in `agent.py` (lines 117, 122, 173, 339), `chat.py` (docstring + `--mode hybrid` flag + branches 376-395-465), `scripts/launch_llama.py`, docs (`README.md`, `CHANGELOG.md`, `docs/ejecutivo.md`).
- Remove `hybrid` branches and simplify conditionals to `local`/`cloud`; update docs.
- **Verification**: `grep -ri hybrid` = 0 in `*.py`; `py_compile` everything; local and cloud flows intact.

### Milestone 2 — Tool `web_extract`
- Reads a URL and returns plain text (manpages, issues, package docs). Reuse Firecrawl scraping if available; otherwise `lynx -dump` or `urllib` + conversion.
- **Verification**: `web_extract` on a real URL returns readable content.

### Milestone 3 — Persistent user memory
- `~/.aios/user_memory.json` + load on startup + `remember`/`recall` tools for stable preferences ("use sven", "port 8083", "respond in Spanish").
- Injected into the system prompt, separate from procedural memory (which stays the same).
- **Verification**: the agent remembers a preference across restarts.

### Milestone 4 — Versioned skills
- Directory `~/.aios/skills/*.md` + `list_skills`/`load_skill` tools.
- The agent can load a skill on demand instead of relying only on the procedural JSON.
- **Verification**: a sample skill is listed and loaded correctly.

### Milestone 5 — Cloud vision `describe_screen`
- `screenshot()` (already exists) + upload the PNG to the cloud endpoint (extending `cloud_reasoning`, already present) so a VLM **describes** the image — not just OCR.
- Only active in cloud mode; local OCR/screenshot/xdotool stay the same.
- **Verification**: `describe_screen` in cloud mode returns a semantic description of a capture.

### Milestone 5.5 — Deep review of squashfs (safe cleanup)
- Walk the tree `~/aios-work/squashfs-root` looking for things that can be safely cleaned: build leftovers (vboxadd, `.cache`, internal backups, duplicated firmware, test docs/PDFs, unused packages, debug session artifacts), without touching anything the boot or agent depends on.
- Before deleting anything: inventory + deletion proposal with justification, and explicit confirmation from Carlos.

### Milestone 6 — UEFI (very carefully)
- Separate milestone, at the end. First investigate how the ISO is packaged today (`grub-mkrescue` without EFI), then plan EFI **with rollback** and isolated testing before touching the stable ISO. Nothing until we review it together.

## Note (future, not now)
- Broken keys: brightness, forward/reverse/play-pause, Print Screen → missing i3 `bindsym`s (`XF86MonBrightnessUp/Down`, `XF86AudioNext/Prev/Play`, `Print`). Volume already works (those binds exist). Not included in this plan unless explicitly ordered.

## Order
1 → 2 → 3 → 4 → 5 (agent code, low risk, in one batch); 5.5 and 6 separate.
