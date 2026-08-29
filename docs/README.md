# AIOS LFS v11

Live ISO of **Linux From Scratch 13.0-systemd** with the **AIOS** agent (wargame/CTF). Designed to boot silently from CD/USB, offer a minimal graphical session (i3 + xterm), and allow installing the system to hard disk while keeping the same boot look.

- **Version**: v11 (August 2026)
- **Kernel**: 6.18.10-lfs #5 (distro kernel: wifi, DRM, NVMe, ALSA)
- **Base**: LFS 13.0-systemd
- **Init**: systemd
- **Desktop environment**: X11 + i3 + xterm
- **License**: MIT

---

## Description

AIOS LFS is a minimalist live distribution built from scratch following the LFS 13.0-systemd book. The goal is to have a self-contained, lightweight environment with a wargame/CTF aesthetic for running the AIOS agent.

v10 fixes all problems detected during the summer of 2026: hangs in the setup menu due to DNS without timeout, Plymouth loops blocking login, Unicode box mojibake in xterm, and the visual difference between live and installed boot.

---

## Features

- Live system with fully writable OverlayFS in RAM.
- Silent boot: black background, no kernel/systemd messages, AIOS banner shown from initrd.
- Kernel compiled with host VPS gcc 15.2.0, verified in `/proc/version`.
- Setup menu centered on screen (`print_box` with horizontal and vertical padding).
- API key validation in a thread with a 12 s timeout (fixes DNS resolution hang).
- `setup.py` → `aios` automatic flow in the same xterm window.
- Disk installer with option to change root and aios passwords.
- **Distro kernel (#5)**: wifi drivers (iwlwifi, rtlwifi/rtl8723be, rtw88/89, ath9k/10k/11k, brcmfmac), DRM (i915/amdgpu/nouveau), NVMe, UAS, I2C_HID_ACPI, ethernet (r8169/e1000e/igb), and ALSA HDA + USB, with linux-firmware integrated.
- **Option 5 WIFI SETUP** in the setup: network scanning, wpa_supplicant, internet verification (urllib), and persistence across boots via systemd-networkd (DHCP on wl*).
- **Complete operating system on real hardware** (HP Notebook AMD + Realtek): wifi with IP at boot, touchpad, audio, and native resolution (verified 4 Aug 2026).
- Firefox included to obtain the API key from the chosen provider.
- Minimalist AIOS client with Matrix style in TTY/terminal.
- `nokaslr` removed in live and installer for security.
- Plymouth definitively discarded.

---

## Requirements

| Environment | Requirements |
|---|---|
| VirtualBox recommended | 2 vCPU, 4 GB RAM, 20 GB disk to install, VBoxVGA or VMSVGA graphics controller |
| Real hardware | x86_64, BIOS/UEFI with boot from USB/CD support |
| Without network | AIOS **LOCAL** mode works if a GGUF model is downloaded beforehand |
| With network | Allows using AIOS in cloud mode without downloading the LLM |

---

## Default users

| User | Password | Notes |
|---|---|---|
| `root` | `root` | System administrator |
| `aios` | `aios` | User for running the agent |

> After installing to disk, `aios-install v1.1.1` allows changing both passwords. If the user chooses not to change them, the final summary shows `Login: aios/aios or root/root`; if they are changed, the warning is omitted for security.

---

## Disk installation

1. Boot the live ISO.
2. Log in as `aios`/`aios` or `root`/`root`.
3. Run `setup.py` and choose **`4) INSTALL TO DISK`** (or launch `/usr/local/bin/aios-install` directly).
4. Follow the installer instructions.
5. At the end, `aios-install` asks:

   ```text
   Change root password? [y/N]:
   Change aios password? [y/N]:
   ```

   It uses `getpass` and validates a minimum of 8 characters. The change is applied via `chpasswd` inside the chroot of the newly installed disk (stdin).

6. Confirm reboot (`reboot`).

The installed system boots exactly like the live one: black background, no messages, AIOS banner, and login on `tty1`.

---

## Components

| Component | Path in live | Path after disk install |
|---|---|---|
| Kernel | `/boot/vmlinuz-6.18.10-lfs` (also in squashfs `boot/vmlinuz-6.18.10-lfs`) | `/boot/vmlinuz` |
| Initrd | `/boot/initrd.img` (also in squashfs `boot/initrd.img`) | `/boot/initrd.img` |
| Root filesystem | `live/lfs.squashfs` + OverlayFS in RAM | Real ext4 partition |
| Agent repository | `/usr/local/bin/aios-agent/` | `/usr/local/bin/aios-agent/` |
| AIOS client | `/usr/local/bin/aios` | `/usr/local/bin/aios` |
| Installer | `/usr/local/bin/aios-install` | not applicable |
| Setup wrapper | `/usr/local/bin/setup.py` or `setup.py` in PATH | not applicable |
| AIOS config | `~/.aios/config.yaml` and `~/.aios/.env` | `~/.aios/config.yaml` and `~/.aios/.env` |
| llama.cpp server | `/usr/local/bin/llama-server` | `/usr/local/bin/llama-server` |

### v10 novelty: kernel and initrd inside the squashfs

The squashfs now includes:

```text
boot/vmlinuz-6.18.10-lfs
boot/initrd.img
```

This allows the installer to copy them to disk without extracting them from the ISO at install time.

---

## Boot sequence

1. GRUB loads `/boot/vmlinuz` + `/boot/initrd.img`.
2. The kernel starts with `quiet loglevel=3 systemd.show_status=false vt.global_cursor_default=0`.
3. The initrd:
   - Mounts `proc`, `sysfs`, `devtmpfs`, `tmpfs`.
   - Clears the screen immediately (`clear` + hide cursor).
   - Shows the AIOS banner.
   - Locates the live ISO, mounts the squashfs, creates the overlay (`lowerdir` + `upperdir` + `workdir`), and executes `switch_root` to `/sbin/init`.
4. systemd starts in `multi-user.target`.
5. `agetty` opens `tty1`.
6. When logging in to `tty1`, the session script (`scripts/aios-session`) runs:
   - Launches `setup.py` if `~/.aios/config.yaml` does not exist.
   - After configuration, starts X11 (`startx`) → i3 → xterm with the agent.

---

## Silent boot and AIOS banner

### Live GRUB

```text
set default=0
set timeout=0
menuentry "AIOS LFS v10" {
    linux /boot/vmlinuz quiet loglevel=3 systemd.show_status=false vt.global_cursor_default=0
    initrd /boot/initrd.img
}
```

> `nokaslr` is not used anywhere.

### Initrd

The initrd performs `clear` + `hide cursor` before searching for the live medium:

```sh
/bin/busybox printf "\033[2J\033[H" > /dev/tty0
/bin/busybox printf "\033[?25l" > /dev/tty0
```

Then it prints the AIOS banner (ASCII/Unicode text) and mounts the root system.

### Installed to disk

The installer generates a new initrd (`build_disk_initrd`) that:

- Keeps the same clear + cursor + banner routines.
- Replaces the ISO search loop with a direct `mount` of the real root partition.
- Ends with `switch_root /sbin/init`.

The disk GRUB configuration uses `timeout=0` and the same silent parameters as the live one, pointing `root=` to the real partition.

---

## systemd services

```text
/usr/lib/systemd/system/
├── aios-llama.service    # llama-server (disabled at boot)
├── aios-agent.service    # chat.py interactive (disabled, i3 launches it)
└── getty@tty1.service    # login on tty1
```

- `aios-llama.service` is enabled/started only when setup.py selects `local` or `hybrid` mode.
- `sshd` is disabled by default in the ISO.
- There is no Plymouth service.

---

## SSH

`sshd` does not start by default. To activate it manually in live mode:

```bash
/etc/rc.d/init.d/sshd start
```

Host keys are regenerated automatically on first use. The service is controlled by the traditional LFS SysV script, not by systemd.

---

## Firefox

Firefox ESR is included in `/opt/firefox/`, with a symlink in `/usr/local/bin/firefox`. It is used so the user can obtain the API key from their provider (OpenAI, Anthropic, DeepSeek, etc.) without depending on another machine. The required GTK3 dependencies are installed manually from `archive.archlinux.org` when current mirrors fail due to corrupt checksums.

To launch it from i3:

```text
exec --no-startup-id /usr/local/bin/firefox about:blank
```

---

## ldconfig library configuration

After installing extra packages (Firefox, GTK3, llama.cpp, etc.), run:

```bash
ldconfig
```

Also, create or update `/etc/ld.so.conf.d/` as needed:

```text
/usr/local/lib
/usr/local/lib/llama
/opt/firefox
```

---

## ISO generation

Summary of steps on the build host:

```bash
# 1. Prepare ISO directory
mkdir -p /tmp/iso/{boot/grub,live}

# 2. Copy kernel and initrd
sudo cp ~/aios/boot/vmlinuz /tmp/iso/boot/vmlinuz
sudo cp ~/aios/boot/initrd.img /tmp/iso/boot/initrd.img

# 3. GRUB
sudo tee /tmp/iso/boot/grub/grub.cfg << 'GRUBEOF'
set default=0
set timeout=0
menuentry "AIOS LFS v10" {
    linux /boot/vmlinuz quiet loglevel=3 systemd.show_status=false vt.global_cursor_default=0
    initrd /boot/initrd.img
}
GRUBEOF

# 4. Squashfs (includes kernel and initrd copied inside)
sudo mksquashfs /lfs-rw /tmp/iso/live/lfs.squashfs -comp zstd -b 128K -noappend

# 5. ISO
sudo grub-mkrescue -o aios-lfs-v10.iso /tmp/iso
```

**If the ISO exceeds 4 GB**, add `-iso-level 3`.

---

## GRUB fix on disk installation

The `aios-install` installer automatically generates `grub.cfg` for the disk with:

```text
set default=0
set timeout=0
menuentry "AIOS LFS v10" {
    linux /boot/vmlinuz root=/dev/sda2 quiet loglevel=3 systemd.show_status=false vt.global_cursor_default=0
    initrd /boot/initrd.img
}
```

- `root=` points to the real partition selected during installation.
- `nokaslr` is not used.
- The disk initrd is a variant of the live one generated by `build_disk_initrd`.

---

## Agent repository

The AIOS agent is deployed in `/usr/local/bin/aios-agent/` inside the squashfs. Its main parts are:

| File | Function |
|---|---|
| `setup.py` | Provider/model configuration wizard |
| `chat.py` | Interactive client with robust EOF/error handling |
| `agent.py` | Function calling loop |
| `scripts/aios-session` | Graphical session startup in the ISO |
| `scripts/aios-install` | Disk installer v1.1.1 |

### v10 changes in setup.py

- `validate_api_key` runs in a daemon thread with `join(timeout=12)`; inside the thread, `urlopen(..., timeout=5)` limits API wait. This fixes the hang caused by `getaddrinfo` without a limit (Ctrl+C also didn't respond due to `SA_RESTART`).
- The API key is saved in `~/.aios/.env` (not in `config.yaml`).
- At the end of the script `os._exit(0)` is used so residual threads don't keep the process open.
- LOCAL menu updated:
  - Default model: `Qwen3-8B-Instruct`.
  - Text: `1) LOCAL (no internet) / Simple tasks`.
  - Removed the phrase `Works 100% offline`.
- Menus are drawn centered using `os.get_terminal_size()` with horizontal and vertical padding.

### v10 setup → agent flow

After completing the configuration, setup.py automatically runs `aios` in the same window:

```bash
xterm -fa 'Adwaita Mono' -fs 11 -bg black -fg green -cr green \
  -e "cd /usr/local/bin/aios-agent && python3 setup.py && [ -f \$HOME/.aios/config.yaml ] && aios || exec bash"
```

- `-hold` is not used: avoids the menu appearing to hang after finishing.
- If setup is cancelled, an interactive bash shell opens.

### v10 xterm in i3

```text
xterm -fa 'Adwaita Mono' -fs 11 -bg black -fg green -cr green ...
```

The `Adwaita Mono` font contains the double-line glyphs (`╔═╗`) that previously rendered as mojibake.

---

## Kernel #4

Actual configuration of kernel 6.18.10-lfs #4:

```text
CONFIG_X86_VERBOSE_BOOTUP=n
CONFIG_OVERLAY_FS=y
CONFIG_FB_VESA=y
```

Without:

```text
# CONFIG_DRM_VMWGFX is not set
# CONFIG_DRM_VBOXVIDEO is not set
# CONFIG_DRM_FBDEV_EMULATION is not set
```

- Compiled with host VPS gcc 15.2.0 (verified in VM `/proc/version`).
- `make olddefconfig` and normal compilation; `LD=/mnt/sq/usr/bin/ld` is NOT used (the LFS ld needs `libbfd` which is not available outside the chroot).

---

## Locale

The live/installed system uses:

```text
LANG=C.UTF-8
LC_ALL=C.UTF-8
```

in `/etc/locale.conf`. `es_ES.UTF-8` is not generated in the base system; if defined without generating it, glibc falls back to `C` and xterm interprets the box characters in Latin-1, producing mojibake (``). The adopted solution is to fix `C.UTF-8`, which is available and correctly supports Unicode.

If full Spanish is desired, generate the locale before setting it:

```bash
localedef -i es_ES -f UTF-8 es_ES.UTF-8
```

---

## Plymouth definitively discarded

Plymouth was tested with multiple configurations (VBoxVGA+vesafb, VMSVGA+vmwgfx, gfxpayload). In all cases the result was a black screen or invisible logo. The root cause in v10 is definitive:

- Kernel #4 does not include `vmwgfx`, `vboxvideo`, or `fbdev-emulation`.
- VirtualBox with VMSVGA does not offer classic VBE.
- `vesafb` cannot create `/dev/fb0` nor `/dev/dri`.
- `plymouthd` finds no renderer, waits for the systemd timeout, and on death retains the VT blocking login.

**Adopted alternative**: ASCII/Unicode banner shown directly from the initrd, with black background and hidden cursor.

---

## v11 fix — panic when booting from disk (2 Aug 2026)

### Symptom

After installing AIOS LFS to hard disk, the system showed a **kernel panic** on boot:

```
Attempted to kill init! exit code=0x7f00
```

(`0x7f00` = 127). It occurred after the AIOS logo, before reaching the login.

### Root cause

The panic came from three accumulated failures in `build_disk_initrd`, the `aios-install` function that transforms the live initrd for booting from disk:

1. **Octal escape `\1` → SOH in the generated init.** The `sed` pattern used with `tail` was written in Python with a single backslash: `'s/.*root=\([^ ]*\).*/\1/p'`. Python interprets `\1` as the SOH control character (`0x01`), which was written literally in the generated `init` script. When executed, `sed` returned a non-existent root device, and `mount -t ext4` failed.
2. **Fallback to non-existent `/bin/sh`.** When `mount` failed, the initrd executed `exec /bin/sh`, but the transformed initrd did not include `/bin/sh`: it only contained `init` and `bin/busybox`, without applet symlinks. The `exec` returned 127, init died, and the kernel raised the panic.
3. **No wait for the root device.** The root device might not be ready when init tried to mount it, making the failure intermittent.

### Solution (aios-install v1.1.2)

- Fixed the `sed`/`tail` pattern with a **double backslash** (`\\(` and `\\1`) so the generated `init` contains `\(` and `\1` correctly, and `sed` extracts the real root device.
- Added a **wait loop of up to 30 seconds** until the root device appears in `/dev`.
- Changed the fallback to **`exec /bin/busybox sh`**, which is available in the initrd.
- Uses **`exec /bin/busybox switch_root /root /sbin/init`** to hand control to the installed system.
- Included a **static `/bin/busybox` (2.1 MB, extracted from the initrd)** in the live system squashfs, because `build_disk_initrd` needs it and the live system did not have it.

### Verification

Reinstalling AIOS LFS to disk, booting from disk works correctly: the AIOS logo appears and the system reaches the login prompt.

> **Note:** the GRUB message `'Welcome to GRUB!'` is still shown. It remains pending to polish in the future using `timeout_style=hidden` and `quiet_boot=1`.

## v12 milestone — AIOS on physical hardware (2 Aug 2026)

### Symptom

When booting the AIOS LFS ISO from USB on a real laptop, the system stopped with a kernel panic because the initrd live init did not find the boot device.

### Causes

- The init script did not wait for the kernel to enumerate block devices, so the USB medium did not yet exist when the live system was searched.
- The list of candidate devices was too short and did not include modern controllers such as NVMe or MMC.
- When Rufus was used in ISO mode, the USB partition was formatted as FAT32, while the init looked for an iso9660 filesystem, causing a silent failure.

### Solution

- Added a wait loop of up to 30 seconds in the initrd live init, checking `[ -b <device> ]` and exiting with `break 2` when found.
- Expanded the search device list: `sdc`, `sdd`, `hd*` disks, `nvme*`, and `mmcblk*`.
- Replaced the kernel panic with a readable message: `AIOS: boot media not found`, followed by a busybox emergency shell for diagnosis.
- Documented that, meanwhile, the ISO must be written with Rufus in DD mode so the init finds an iso9660 volume.

### Verification

- ISO written to USB with Rufus in DD mode.
- Successful live USB boot on a physical laptop with SATA SSD.
- AIOS LFS installation to the SSD disk completed.
- Reboot and boot from disk with AIOS banner and login prompt working.

### Pending (historical — resolved with kernel #7)
- ~~Support Rufus ISO mode (FAT32)~~ → resolved: Rufus in DD mode is the documented method
- ~~Prepare kernel #5 with NVMe and UAS drivers~~ → resolved with kernel #7 (Ubuntu 6.18.10 config, 7 Aug)

## 6 Aug 2026 — Local LLM on laptop: SIGILL (RESOLVED 8 Aug)

**Historical symptom**: `aios-llama.service` repeatedly failed with `status=4/ILL` (SIGILL core dump) on the HP AMD A8-7410 (no AVX2/FMA3/AVX-512). Causes discarded at the time: corrupt GGUF, ggml ISA (AVX1+F16C builds), mixed glibc.

**Resolution (8 Aug)**: the SIGILL was resolved with glibc alignment (single 2.44 from sven, `/lib64` → `/usr/lib`) + the sven package `llama-cpp` (b10221, x86-64-baseline). Verified: the LLM loads and generates **~1.2 tok/s** on the A8. Full investigation detail in the `aios-iso-build` skill.

## 6 Aug 2026 — AIOS agent on VPS with local Qwen (works)

- Local server: `nohup env LD_LIBRARY_PATH=~/llama.cpp/build/bin ~/llama.cpp/build/bin/llama-server -m /home/ccmai/models/Qwen_Qwen3-8B-Q4_K_M.gguf -c 65536 -t 14 --host 127.0.0.1 --port 8083` + `~/.aios/config.yaml` with `mode: local` → `cd ~/sre-agent && python3 chat.py`.
- The `chat.py` "hang" was the **session history**: `~/sre-agent/data/session_local.json` (20 KB → prompt ~6.2K tokens → ~2 min prompt processing at ~52 tok/s). `rm session_local.json` → responses in 30-60 s.
- The VPS build is **SSE-only** (cache: `GGML_AVX=OFF`) → 17 tok/s gen / 31-57 tok/s prompt is the SSE floor; with `GGML_NATIVE=ON` on EPYC ~2x (pending decision; only for local build, never for distribution).
- The slow `import yaml` was transient (CPU contention with model loading).

## 7 Aug 2026 — Cleanup: kernel #7 (Ubuntu 6.18.10 config) + 157 MB modules + fixes

**Kernel #7 — Ubuntu config for the SAME kernel (6.18.10)** (Carlos's idea: instead of the manual =m list, use the config Ubuntu uses for that kernel — the mainline build `v6.18.10` from kernel.ubuntu.com; the config is INSIDE the `linux-headers-*` .deb). Brings ALL distro drivers (rtlwifi/rtl8723be, i915, amdgpu SI/CIK, HP_WMI, iwlwifi, snd-hda...) already included. Adjustments: `OVERLAY_FS=y`, `SQUASHFS=y` (live), `LOCALVERSION=""`, `SYSTEM_TRUSTED_KEYS=""` (the config references `debian/canonical-certs.pem` — does not exist in the tree), BTF off, and **boot drivers =y** (ISO9660, SATA_AHCI, NVME, USB_STORAGE, XHCI/EHCI/OHCI — the AIOS initrd does not load modules). Build host deps: libdwarf-dev + libdw-dev + dwarf.h symlinks (gendwarfksyms).

**Validated: boots in VM and on BOTH laptops** (the old A8-7410 and the new HP).

**Module size: 8.1 GB → 157 MB** (better than Ubuntu: 172 MB), official kernel mechanism:
1. `MODULE_COMPRESS_ZSTD=y` → compression during `modules_install` (8.1 → 2.2 GB; requires clean rebuild to regenerate auto.conf)
2. `INSTALL_MOD_STRIP=1` → removes the DWARF5 debug from the mainline config (2.2 GB → 157 MB) — same rtl8723be module: 6.29 MB → 82.5 KB

**Cleanup fixes**:
- Single aligned glibc 2.44 (`/lib64` → `/usr/lib`, zero Ubuntu) + protected in sven
- LLM: sven `llama-cpp` package (b10221, baseline, GLIBC 2.34) — scripts adapted (`/usr/bin/llama-server`, no LD_LIBRARY_PATH); manual builds removed (no fallback)
- Setup restored (a test config.yaml in the tree made the wizard skip); aios-install v1.1.3 (groups, passwords, silent boot disk); GRUB without nokaslr
- Historical pending: final ISO ~1.5 GB (without model — the 4.7 GB GGUF copied separately) — surpassed: the full firmware (416 MB) brings the ISO to ~1.5-1.8 GB; the LLM model goes separately.

## 8 Aug 2026 — Hardware validated (ISO #7 + LLM)

| Laptop | Model | CPU | RAM | Result |
|---|---|---|---|---|
| Old (installed) | HP with **AMD A8-7410** | AMD A8-7410 @ 2.2 GHz, 4C (Jaguar, no AVX2) | 8 GB (6.7 GiB visible — iGPU shares) | ✅ Boots + LLM loads and generates **~1.2 tok/s** (DDR3L single-channel limit); **SIGILL resolved** |
| New (tested from USB, not installed) | **HP Laptop 15s-fq1xxx** | **Intel Core i5-1035G1** @ 1.0 GHz (boost 3.6), 4C/8T (Ice Lake, AVX2/AVX-512) | **8 GB** | ✅ Boots and works; model load from USB **7-8 min**; generates at ~typing speed (usable) |

**Notes (8 Aug)**:
- The 7-8 min bottleneck is **loading the model from USB** (4.7 GB at ~10-15 MB/s). From the NVMe SSD (SK hynix BC511 512 GB) it will be ~100x faster (seconds).
- The i5-1035G1 (AVX-512) takes much more advantage of ggml CPU variants than the Jaguar (AVX1) — performance on the new HP will be far superior to the 1.2 tok/s of the old one.
- Carlos's observation: "it replies at approximately the speed of an average person typing" (the old one).

## 19-21 Aug 2026 — Stuck boot, full GPU/firmware, conditional vbox, full theme, installer

### Stuck boot on logo (resolved)
- **Symptom**: after installing to disk, the system stayed on the logo (~2 min) and then booted. **Root cause**: partial installation due to the `harden_sudo` bug (`glob` returns strings → `is_file()` failed → installer aborted BEFORE `persist_wifi`) → disk without wifi → `systemd-networkd-wait-online` blocked boot.
- **Fixes (in tree and ISO)**:
  - `systemd-networkd-wait-online` **disabled** in the tree → boot never depends on network
  - `options rtl8723be ips=0 fwlps=0` in `/etc/modprobe.d/rtl8723be.conf` → no wifi soft lockups
  - Installer fixed: revert autologin/harden_sudo + fix `Path.glob` + **aborts with `sys.exit(1)`** (before exit 0 → setup said "installation complete" without having installed) + **menu that re-asks on invalid input** (setup.py and aios-install)
- Boot verified: **6.3 s** to multi-user, desktop up, wifi connected (persistence OK).

### GPU: radeon MULLINS firmware (resolved — root cause of the "green bar"/frozen scrot)
- The tree had a **partial** firmware copy (only amdgpu, 534 MB, from 3 Aug) → the A8 APU radeon (MULLINS) did not have its `.bin` → `Fatal error during GPU init` → no `/dev/dri` → X without native driver → frozen vesa render (scrot always returned the same image; the "green bar" was an old frame, not the real bar).
- **Fix (official route)**: `sven install linux-firmware` (full Arch package, `.zst` — kernel 6.18.10 has `CONFIG_FW_LOADER_COMPRESS=y`) → `/usr/lib/firmware` 416 MB with EVERYTHING (radeon, amdgpu, iwlwifi, brcm, atheros…) + `regulatory.db` preserved. The old `/lib/firmware` (534 MB) was moved to backup (`~/aios-work/backups/backup-firmware-lib-20260821/`) → **~530 MB less ISO**.
- **Build rule**: firmware is ALWAYS installed with the complete sven `linux-firmware` package (never partial manual copies).
- Verified live: `radeon` initialized (`/dev/dri/card0` + `renderD128`), fresh render, correct bar.
- **CPU microcode**: `amd-ucode` + `intel-ucode` (sven packages) in the tree — CPU patches for any machine.

### vboxadd: conditional on VirtualBox (not garbage, adaptive)
- The `vboxadd.service`, `vboxadd-service.service`, `vboxservice.service` units have a drop-in with **`ConditionVirtualization=oracle`** → on real hardware they do not activate (clean boot, no degraded); in real VirtualBox they come up with the distro kernel modules (`vboxguest.ko.zst` from 6.18.10 — the 7.2.6 Guest Additions modules, incompatible, were moved to backup).

### Full color theme (see "Color themes" below)
- `aios-theme` central + `status.py` reads the theme + i3 with `colors.conf` included — the 4 themes change EVERYTHING instantly (verified on the laptop).

### Push to GitHub (lesson learned)
- The VPS token had expired → recent pushes "seemed" to work because of the `| tail -1` that **masked the error** (same pitfall as with xorriso). Fix: new token in `~/.git-credentials` on the VPS, remotes without username in the URL (`https://github.com/...`), store helper in both repos. **Rule: never end a push with `| tail -1` without verifying the result.**

## 21 Aug 2026 (evening) — Web v1.4, access stats by email, WarGames phrases, ISO 1.4

### Publication and web (ccmai.org)
- **ISO v1.4 published** at `/var/www/ccmai.org/releases/aios-1.4.iso` (1.9 GB, 21 Aug 20:36) — 1.3 stays on the server without link (Carlos's decision).
- **Backup of the website** at `~/aios-work/backups/web-ccmai-20260821/` (usual pattern).
- **Full wargames/AIOS redesign**: black background, Matrix green (`#00ff00`/`#006400`), mono typography, **SVG** hexagon (thick 8 border + filled circle — replaces the ASCII halftone, no pixelation), "Greetings, Professor Falken" with **typewriter + 850 Hz/35 ms beep** (Web Audio API, 8 rotating phrases every ~6 s, 🔊/🔇 toggle at bottom right — browser requires first click for audio), solid blinking block cursor, subtle CRT scanlines (desktop), SVG favicon with hexagon+circle, meta description + Open Graph (image `assets/hex.svg`).
- **Final structure**: hexagon → AIOS → "Artificial Intelligence Operating System" → rotating phrase → mission (2 phrases + "Made with a nostalgic nod to WarGames (1983)") → download (without aios-install, with physical/VirtualBox mention) → GitHub links (corrected to `ccarrillomanzanares`; **sre-agent removed**) → footer (v1.4 badge · x86-64 + disclaimer "Proof of concept — beta stage · use at your own risk").
- **Web versioned in repo**: `aios-lfs/web/` (index.html + releases/index.html + assets/hex.svg) — before it only lived on the server.

### Access statistics (ccmai.org)
- **Script `~/scripts/ccmai-stats-mail.py`**: daily report (requests, unique IPs, statuses, top routes, ISO downloads with bytes/completed, suspicious scans) in **responsive HTML** (KPIs, bars, mobile media query) + plain text alternative; sent via **Zoho SMTP** (`smtp.zoho.eu:587`, app password in `~/info.txt` — absolute path because cron runs as root).
- **Daily root cron**: `30 7 * * *` (07:30) → email to `ccarrillo@ccmai.org`.
- Relevant data: ~86% of traffic is 404 from automated scans (`/.env`, `/.git/config`, `.aws/credentials`); the ISO is downloaded in partial chunks (none complete in 15 days); behind Cloudflare (edge IPs, not real ones — `CF-Connecting-IP` pending if desired).

### Rotating WarGames phrases (web + AIOS)
- 8 classic phrases: "Greetings, Professor Falken", "Shall we play a game?", "Would you prefer a nice game of chess?", "A strange game. The only winning move is not to play.", "How about Global Thermonuclear War?", "What's the difference?", "To win the game.", "You are a hard man to reach."
- **AIOS**: `setup.py` (wg with typewriter+beep) and `chat.py` (`_greet`) choose a random phrase on each boot — commit `dba187e`. **The published ISO v1.4 does NOT carry this** (it will be regenerated later).
- **Web**: JS typewriter + beep per character.

### Intermittent 522 incident (Carlos's mobile)
- Symptom: 522 from Cloudflare + certificate error ONLY from the mobile (wifi, no wifi, and mobile data); laptop OK.
- Diagnosis: origin healthy (localhost 200 in 0.0008 s, workers OK, firewall open, global DNS points to Cloudflare on router/8.8.8.8/1.1.1.1); certificates valid (CF: Let's Encrypt until Nov 2026; VPS: self-signed). The 522s do not reach Apache (no access log line at the time).
- Conclusion: **mobile issue** (DNS cache / private DNS / time / VPN with TLS inspection) or intermittent edge-CF→VPS route. Pending: verify on the mobile (other https, private DNS, time, reboot) — not the server.

## 21-22 Aug 2026 (early morning) — Four chained bugs after firmware and their fixes (final ISO 07:38)

### 1. Broken ISO: vanilla kernel only looks for /lib/firmware
- **Symptom** (2014 laptop, live): wifi "is found" but does not come up or scan; dmesg: `Direct firmware load for rtlwifi/rtl8723befw.bin failed with error -2` (ENOENT) — also radeon, regulatory.db, bluetooth.
- **Cause**: when moving the old `/lib/firmware` (534 MB) to backup, the tree was left with firmware only in `/usr/lib/firmware` (sven package). The distro kernel (vanilla 6.18.10 + Ubuntu config, **without the Ubuntu code patch that adds /usr/lib/firmware**) only searches `/lib/firmware`. Process error: assuming the path without verifying it + publishing the ISO without booting it.
- **Fix (in tree)**: `sudo ln -s ../usr/lib/firmware $R/lib/firmware` — symlink, no duplication (same inode); `sven install` keeps installing in /usr/lib. Verified with `stat -c %i` and `unsquashfs -ll`.
- **Lesson**: the `/lib/firmware` → `/usr/lib/firmware` bridge is MANDATORY in the tree (rule added to the aios-distro-kernel skill).

### 2. Partial theme after install: colors.conf root:root
- **Symptom**: the chosen theme applied in xterm and status.py but NOT in the i3 border / workspace rectangle (stayed wargames green).
- **Cause**: `colors.conf` was copied to the tree with `sudo cp` (after the phase 2.2 chown) → `root:root` → `aios-theme` (runs as aios) could not write it → PermissionError; and the script **did not check the error** (it said "Theme applied" with exit 0, and the setup swallowed it with capture_output).
- **Fix**: `chown -R 1000:1000` on `.config/i3/` in the tree + `set -e` in aios-theme (now fails loudly). Theme check: `head -4 /home/aios/.config/i3/colors.conf` must have `(white)`/`(amber)`… on the first line.

### 3. Dead desktop: udev-trigger vs udevd race (intermittent)
- **Symptom**: boot logo, autologin, X "starts" and nothing else. Xorg.0.log: `(EE) open /dev/dri/card0: No such file or directory` + `Fatal server error`.
- **Cause**: the kernel initializes radeon fine (firmware OK), but **/dev/dri/card0 is created by udev** when processing the uevent. The unit `systemd-udev-trigger.service` (systemd upstream) only has `After=` for the udevd **sockets**, not the **daemon** → on slow boots (2014 HDD) the trigger runs `udevadm trigger` before udevd is listening → uevents are lost → no /dev/dri → X dies. **Intermittent race** (previous ISOs happened to win by chance).
- **Live diagnosis**: `udevadm trigger --subsystem-match=drm` creates card0 instantly (proof of cause); journal shows `Finished systemd-udev-trigger.service` BEFORE `Started systemd-udevd.service`.
- **Fix (in tree)**: drop-in `/etc/systemd/system/systemd-udev-trigger.service.d/order.conf` with `[Unit]\nAfter=systemd-udevd.service`.

### 4. Xterm does not appear: -sr does not exist in the build xterm
- **Symptom**: after adding scroll, the live starts the desktop but the menu xterm is not shown.
- **Cause**: `xterm: bad command line option "-sr"` — the right-scrollbar CLI option does not exist in the LFS build xterm.
- **Fix**: right scrollbar configured via **X resource**: `-xrm "*rightScrollBar: true"` (tested, exit 0). Final wrapper: `xterm -fa "Adwaita Mono" -fs 11 ... -sb -sl 2000 -xrm "*rightScrollBar: true"`.

### Final ISO of the round
- `~/aios.iso` → `releases/aios-1.4.iso` (22 Aug 07:38, 1.9 GB): includes the 4 fixes + accessible firmware + theme + WarGames phrases + microcode + adaptive vbox + corrected installer.
- Systematic post-build verification this round: `unsquashfs -cat/-ll` of the squashfs (symlink, drop-in, aios-xterm, colors.conf permissions) before publishing.

## 22 Aug 2026 (morning) — Final round: hardened login, audio, imagemagick, early microcode — ⚠️ OPEN PROBLEM in boot

### Done and verified (in tree, repo, and laptop where applicable)
- **Hardened disk login (plan point 4)**: `harden_login` in `aios-install` — removes `/etc/sudoers.d/wheel-nopasswd` and the `getty@tty1` autologin (by file, no globs — 19 Aug lesson), after `set_passwords`, with `visudo -c` verification. **Tested on the 2014 laptop (disk)**: sudo asks password ("a password is required") + getty asks for login. Live keeps autologin+NOPASSWD (Carlos's decision). Backups from the test: `/root/backup-login-20260822/` on the disk. Temporary passwords pending change by Carlos.
- **Audio / beep**: `/etc/asound.conf` → `pcm.!default { type plug; slave.pcm "plughw:1,0" }` + `ctl card 1` (without this aplay went to HDMI — the beep was lost; "Host is down" with simple `defaults.pcm.card`, plug+plughw works). Tested on live: audible beep.
- **Persistent volume**: `/etc/alsa/asound.state` (Master 64%, card "Generic" ALC3227) + **alsa-restore enabled** (the unit was static without `[Install]` → symlink in `multi-user.target.wants` — without this restore never ran).
- **Imagemagick**: `sven install imagemagick` (magick v7) in the tree.
- **.bak out of tree**: 11 files → `~/aios-work/backups/bak-arbol-20260822/` (including `vmlinuz-6.18.10-lfs.bak-k6`).
- Repos: `aios-agent` `c438861` (early microcode installer) · `aios-lfs` `1d66b62` (asound.state + alsa-restore).

### ✅ RESOLVED (22 Aug evening) — early microcode was the culprit in boot
- **Confirmed isolation**: control ISO without early microcode (original 1.1 MB initrd `a349e10d`, everything else equal) → **boots on the 2014**. The 19 MB initrd (newc cpio with microcode before gzip) broke the `mounting /dev/loop0 on /squashfs failed`.
- **Action**: initrd with early → `~/aios-work/backups/initrd-originales/initrd.img-con-early-20260822` (19 MB, kept); the tree `~/aios/boot/initrd.img` uses the good one (`a349e10d`). The installer copies the tree initrd → `build_disk_initrd` is without early microcode by default (revisit if early microcode is ever retried the correct way).

## 22 Aug 2026 (evening-night) — New ISO installed OK, wifi fix, theme, cool chat, bar, NTP, web by products

### 🔧 RTL8723BE wifi broken with full firmware (RESOLVED)
- **Symptom**: wlo1 exists but DOWN; `rtl8723be: Using firmware rtlwifi/rtl8723befw_36.bin` → `Polling FW ready fail!! REG_MCUFWDL:0x00000006` → `Firmware is not ready to run!` (only at boot; reloads did not repeat the fail → red herring).
- **Cause**: the distro kernel 6.18.10 driver **prefers `rtl8723befw_36.bin` when the file exists**; the 2014 8723BE chip does not boot with it. The previous firmware (manual subset) did not have it → used the base and worked. The full sven `linux-firmware` package (21 Aug) added it → sudden regression.
- **Fix**: `rtl8723befw_36.bin.zst` removed from the tree → `backups/backup-firmware-lib-20260821/`. The driver falls back to the base (`Loading alternative firmware rtlwifi/rtl8723befw.bin`) and the radio works (validated live: `ip link set wlo1 up` + `iw dev wlo1 scan` → sees networks).
- **ISO 10:52 `933ecbd7`** with the fix → written by Carlos (Rufus DD) → **installed OK on the 2014**.

### 🎨 Partial theme after install (RESOLVED, real cause)
- **Symptom**: xterm and bottom bar in amber (read config.yaml) but window titles in green (disk colors.conf = wargames from tree).
- **Real cause**: the INSTALL flow (`_install_flow` → `aios-install --theme`) wrote config.yaml but **nobody generated colors.conf on the disk** (the call to `aios-theme` only existed in post-install flows, which do not run after installing).
- **Fix** (commit `20a150f`): `apply_theme(target, theme)` in aios-install — `chroot <target> env HOME=/home/aios aios-theme <theme>` + chown of colors.conf and config.yaml to aios uid/gid.
- **Pitfall**: LFS does NOT have `su`/`runuser`/`setpriv` (the book disables them) → to run as aios from root: `sudo -u aios <cmd>` (root does not ask for password).
- Manual fix on already installed disk: `sudo -u aios aios-theme amber` + `sudo -u aios env DISPLAY=:0 i3-msg reload`.

### 💬 Chat and typewriter
- **Clean startup** (be8a467): removed the technical banner (`[LOCAL/CLOUD/HYBRID]...`, `Independent session`, `Type your query...`, `(Local model: EN, ZH...)`) and `[Session resumed...]` (agent.py). Left: `AIOS/1.4 — date` (BBS) + movie phrase with typewriter.
- **Skip with SPACE** (a65c0ae): pressing space writes the pending text at once. ⚠️ On 22 Aug it did NOT work on a real terminal (select() in cooked mode does not see the key until Enter); **FIXED on 23 Aug** with cbreak — see 23 Aug section.
- **Cool batch** (17013ba):
  - ~~Hexagon in chat startup~~ → **REMOVED on 23 Aug** (the logo only lives in the initrd): chat starts with `AIOS/1.4 — date` + phrase.
  - **Keyboard with ticks**: `_input_tic()` — termios raw, tick per key (typewriter), backspace, Ctrl+C/D, history ↑/↓ in session. Disabled with `/sound` (controls output and input).
  - **23 phrases** (WarGames + Matrix + Tron + 2001), **random without repeating the immediately previous one** (like the web). Cross-checked against Wikiquote via Firecrawl (tunnel 3002): corrected `Greetings, Programs!` (with S); `Daisy, Daisy, give me your answer, do...` (HAL's song); `Wake up, Neo...` and `I fight for the Users!` are not in Wikiquote but Carlos personally verified them → included.
  - **`/health`**: LOAD / MEM / DISK / UP / TEMP / NET / latest journal errors.
  - **`/reset`** (clean session) and **`/stats`** (messages/tokens/% of limit).
  - **No internet warning** in cloud mode at startup.

### 📊 i3 bar (b424263)
- `AIOS` → **`Help:F1`** (first block; from 23 Aug — Carlos verified the real key).
- **WiFi coverage %** in the WiFi block (signal dBm → %, `_get_signal_pct`): `WiFi <ssid> <ip> 60%`.
- **NET**: no traffic shows the **link** (`NET 100M`); with usage, the % as before (colors preserved).

### 🕐 NTP (04657cd)
- NTP (23 Aug): no longer a main menu option — it is asked **inside the installation flow** (option 2): `Configure NTP time sync (external server)? (y/N)` → `setup_ntp(standalone=False)` writes `/etc/systemd/timesyncd.conf` (default `pool.ntp.org`), enables+restarts timesyncd, `timedatectl set-ntp true`, shows status.
- **`persist_ntp(target)`** in aios-install: copies live config to disk + enables the service (persist_wifi pattern). Note: on already installed disk there is no way from the chat (Carlos rejected /wifi and /ntp).

### 🧹 Single setup.py
- There were TWO setup.py: the official one (`/usr/local/bin/aios-agent/setup.py`) and a **relic from 4 Aug** in `/usr/local/bin/setup.py` (wizard with boxes) that ran when typing `setup.py` (PATH). Moved to `backups/setup.py-antiguo-20260822` — nothing referenced it (i3 uses the full path).
- **Local requirements** (e389fab, phrase retouched 23 Aug): `_check_local_requirements()` compares real cores/RAM with the minimum (4 cores / 8 GB) and shows `This machine could run it (N cores, X GB RAM)` or `I have reviewed this machine's resources: N cores, X GB RAM. They are below the minimum required... Better not to use local mode.` in live and install flows.

### 🖼️ Art and login
- **The logo ONLY lives in the initrd** (23 Aug): chat art removed (chat.py without `ART_FILE`) and `configs/aios-ascii.txt` deleted from the repo (git rm, `60d9d83`). The boot banner remains the halftone ▒▓░ (Carlos's 29-line art did not fit in the initrd — revert attempted, see 23 Aug).
- **`/etc/issue` EMPTY** (d2dd217): clean login without text. (Pending decision: center the prompt with ANSI in the issue — option A proposed.)

### 🌐 ccmai.org web — product structure
- **ccmai.org = parent; AIOS = product at `/aios/`** (936b51b): moved index.html, assets/, releases/ to `/var/www/ccmai.org/aios/`; `huerta/` intact.
- **Apache redirects** (http+ssl vhosts): `^/$` → `/aios/` and `^/releases(/.*)?$` → `/aios/releases$1` (301). Verified locally and through Cloudflare. Backup: `web-ccmai-20260822c`.
- **Web phrases** (572187c): 23 phrases with typewriter+beep (already random without repeat: `Math.random` + do-while against idx) + `Made with nostalgia for classic AI movies (WarGames · The Matrix · Tron · 2001)`.
- Repo: `aios-lfs/web/aios/` (git mv). Skill `ccmai-web-maintenance` updated.

### 📦 Pending (next session)
- **ISO 6.7 GB (23 Aug 18:48)** with EVERYTHING inside (Qwen3-8B Q4_K_M model + day fixes) — pending write (Rufus DD) and test on the 2014; do not deploy anything to the laptop before.
- **Tick audio** — sounds like a "broken speaker" on the laptop → pending A/B/C/D test (script `audio-test.sh` + WAV in aios-tmp).
- **Centered login** (ANSI idea) — paused.
- **Temporary passwords** on the 2014 disk pending change by Carlos.
- **ffmpeg** installed in the tree (23 Aug) — pending x11grab recording test; chafa/mpv/cmus on standby (Carlos's decision).

## 23 Aug 2026 — Qwen LLM in the ISO, chat without hexagon, SPACE skip fixed, NTP to installer

### 🧠 Local LLM in the ISO (model returns)
- **Qwen3-8B Q4_K_M** (`Qwen_Qwen3-8B-Q4_K_M.gguf`, 4.7 GB, md5 `1f7c1dfa…`) copied to the tree in `/usr/local/share/aios/models/` — the exact path expected by llama-server (`MODELS_DIR` in `scripts/launch_llama.py` and `LOCAL_MODELS[0]["file"]` in setup.py).
- **ISO ~6.7 GB** with `grub-mkrescue -iso-level 3` (mandatory >4 GB) — first ISO with LLM since July.
- **ffmpeg installed in the tree** (sven): first attempt failed with checksum mismatch (truncated downloads — outdated sven bases); **`sven sync`** resolved it. Pending x11grab test.

### ✂️ Chat: hexagon out (the logo only lives in the initrd)
- `_greet()` no longer reads art: no `ART_FILE`, no hexagon. Chat starts with `AIOS/1.4 — date` (header **left-aligned**, without the 3 spaces) + movie phrase.
- `configs/aios-ascii.txt` removed from the repo (git rm, `60d9d83`) and the tree. The boot art (initrd) is NOT touched.

### ⏩ SPACE skip — FIXED (lesson: select + cooked)
- `_skip_pressed()` (select on stdin) **only detects the key in cbreak/raw mode**; in cooked mode the character is held until Enter → skip did not work in any typewriter despite being implemented (a65c0ae).
- Fix (commit `9aacd15`): helpers `_cbreak_on()`/`_cbreak_off()` in agent.py (`tty.setcbreak` + try/except, safe without tty) used in `wg()`/`wg_input()` (setup.py), the stream (agent.py), and `_greet()` (chat.py — which also had no skip).
- Empirical verification (pty): cooked 1.51 s vs cbreak 0.53 s.

### ⚙️ NTP inside the installation flow
- The main menu stays with 2 options (live / install). NTP is asked in `_install_flow` (option 2) before launching `aios-install`: `setup_ntp(standalone=False)`.

### 🖥️ Bar and shortcuts
- Bar: **`Help:F1`** (status.py).
- New phrase in setup.py and aios-install: **`Press F1 anytime to view the keyboard shortcuts`**; `shortcuts.txt` and config comment also point to F1. Zero remnants of Super+F1 (grep verified).

### 📦 Backups and commits (23 Aug)
- Backups: `lfs.squashfs-20260822-2234fixes.bak` · `aios-20260822-2253.iso.bak` · `aios-20260822-2144.iso.bak` · `initrd.img-20260822-1000-semitonos.bak` (the good one) · initrd art attempt at `~/aios-work/tmp/initrd-new.img`.
- Commits: `sre-agent` `9aacd15` · `aios-lfs` `60d9d83` (plus `05a818f` and `b909411` from 22).

## 24 Aug 2026 — Web v2 (terminal, no sound), partner badges, Blade Runner phrases published, final ISO, ISO cleanup

### 🌐 Web v2 — the web IS the AIOS terminal (published at `/aios/`, commit `34ddd4c`)
- Full redesign, developed separately in `/aios-dev/` (test page that remains versioned). Terminal box `aios@ccmai — /aios` (**WITHOUT the 3 circles** — Carlos: "they don't appear in AIOS"), 150px hexagon, AIOS title, rotating typewriter phrase (28 phrases), `$ curl -O …aios-1.4.iso` + big download button, NVIDIA Inception badge (50px) + Lambda (36px) above small GitHub links, terminal footer. All on one screen (natural scroll if viewport is small — "not a must, nice to have").
- **No sound**: removed the beep (Web Audio) and the 🔊 speaker button — Carlos's decision. 0 remnants verified.
- **Responsive** (<760px): box flows (height auto, never cuts), logo 100px, button full-width, curl word-break, badges adjusted.
- Meta/OG/favicon correct. Backup of the old one: `backups/web-ccmai-20260824/index-antiguo.html`.

### 🏅 Partner badges (official assets, commit `d6bd11f`)
- **NVIDIA Inception**: official badge from Carlos's ZIP (`Downloads/Inception Badges.zip` → `for-screen/rgb-for-screen.svg`) → `assets/inception-badge.svg` (links to nvidia.com/startups).
- **Lambda**: official lambda.ai wordmark (`logo-white` SVG) → `assets/lambda-logo.svg` (links to lambda.ai).
- ⚠️ **Lesson**: SVGs as **base64 data URIs were not visible** (NVIDIA badge invisible in browser) — serve them as **files** in `assets/` (and in dev, relative paths). HTML can be corrupted by mass replacements — verify structure (balanced tags) after each change.

### 🎬 Blade Runner phrases (agent + web)
- 5 phrases (23 → **28**): complete "Tears in rain" monologue (42 words, verified via Wikipedia), "The light that burns twice as bright burns half as long.", "I want more life, father!", "It's too bad she won't live! But then again, who does?", "Wake up! Time to die!".
- Web nostalgia: `(WarGames · The Matrix · Tron · 2001 · Blade Runner)`. Commits: sre-agent `b1c51a5`, aios-lfs `a064f63`.

### 💿 Final ISO published (24 Aug 16:58, md5 `d1828ce0…`)
- 6.7 GB, `-iso-level 3`, with: Qwen3-8B Q4_K_M model + all fixes + Blade Runner phrases. Published at `releases/aios-1.4.iso` (200 via CF). Release table: only 1.4, date 2026-08-24 (`0ed1977`).
- **Cleanup**: deleted ALL old ISOs (16 files, ~40 GB) — only `~/aios.iso` and the release one remain. (Squashfs and old web kept in backups.)

### 🔧 Firecrawl self-hosted (VPS, `/opt/firecrawl`, docker compose)
- The stack was **stopped since 09:40 UTC on 23 Aug** (clean shutdown: logs with "Goodbye!", exit 0 — not a crash; probably manual/script stop) + local tunnel 3002 down → web tools broken.
- Fix: `cd /opt/firecrawl && sudo docker compose up -d` (compose is in `/opt/firecrawl/docker-compose.yaml`, NOT in ~) + SSH background tunnel `-L 3002:localhost:3002`.
- Nous portal for web: **discarded** (Carlos: "we won't use nousportal; when needed we'll use firecrawl") — `web.use_gateway: false`.
- Note: the ollama-hardened stack (webuillama) was also stopped (~23 Aug, 59 min before) — **NOT touched** (Carlos's decision).

### 🔐 VPS + web security (24 Aug — audit applied)
- **Firecrawl**: bind changed from `0.0.0.0:3002` → `127.0.0.1:3002` (was exposed to the Internet; Contabo provider was blocking it, but no local firewall) + strong `BULL_AUTH_KEY` (was CHANGEME) → **stopped and disabled** (`docker compose stop` + `docker update --restart=no`) — Carlos: "leave it stopped; when needed we start it" (`cd /opt/firecrawl && sudo docker compose up -d`). **Hermes web_search/web_extract NO LONGER depend on it**: configured the **Nous Tool Gateway** (active subscription — `hermes status`: "Web tools ✓ included by subscription"): `web.backend=firecrawl`, `web.provider=firecrawl`, `web.firecrawl_api_url=''` (no direct config → provider uses the managed gateway), `web.use_gateway=true`, `web.search_backend=''`. Verified: search and extract work. Alternative canonical path: `hermes tools` → Reconfigure provider → Web Search → "Nous Subscription".
- **Firewall**: NOT touched (Carlos: "we use Contabo's").
- **fail2ban**: installed and active (sshd jail, maxretry 5, bantime 10m, findtime 10m). Carlos's dynamic IP: not a problem (at most 10 min banned if it fails 5 times; `sudo fail2ban-client set sshd unbanip <ip>`).
- **Apache**: `ServerTokens Prod` + `ServerSignature Off` (verified: `Server: Apache` without version) + `headers` module enabled.
- **Web headers**: HSTS (`max-age=31536000`) + `X-Content-Type-Options: nosniff` in the SSL vhost (verified via CF). Backup: `backups/ccmai-ssl-20260824.bak`.
- **`/aios-dev/`**: moved to `backups/aios-dev-20260824/` → 404 (Carlos: "don't serve it; when needed we load it in apache config"). Still versioned in the repo (`web/aios-dev/`).

### 📦 Pending (24 Aug)
- **Neo browser screen (Matrix)** — idea on standby: retro "Global Search" replica with Morpheus photo in ASCII + "Searching..." + news ("Morpheus eludes Police at Heathrow Airport") — before the "Wake up, Neo" contact. ⚠️ Check copyright (movie images = protected derivative; Carlos's decision).
- **Write the final ISO** (Rufus DD) and test on the 2014 — includes model + phrases + fixes.
- Laptop tick audio (A/B/C/D, `audio-test.sh`) — still pending.
- Centered login (ANSI) — paused. Temporary passwords on the 2014 disk — pending.
- chafa/mpv/cmus — on standby (Carlos's decision). UEFI (milestone 6) and remaining plan milestones — pending.

## 25 Aug 2026 — External tests: Arnold (VirtualBox) — feedback and improvement plan

First external user testing AIOS in VirtualBox (ISO 1.4 final, live + installation attempt).

### 🐞 Reported problems → improvements (plan)
- **P1-1 · Installer does not return to menu** on failure (wrong disk / ABORTED) — VM must be rebooted. **CONFIRMED with screenshot (12:08)**: after `Aborted.`/`Installation aborted or failed` and *"Press Enter to return to the menu..."*, Enter falls to shell `[aios@lfs aios-agent]$` — not to the menu. → error handling → return to menu.
- **P1-2 · No progress bar** during installation (~30 min without knowing if it advances). → progress feedback (numbered steps or bar).
- **P1-3 · "Stopped at format disc because I couldn't write it"** — disk input (typo without backspace) aborts. → validation with retry.
- **P1-4 · Agent in LOOP** listing directories (the anti-loop of 3 identical repetitions did not catch it — calls varied). → detect repeated base command.
- **P1-5 · Agent tries commands without sudo** and fails. **CONFIRMED with screenshot (13:23)**: `dmesg | grep firefox` → "Opération non permise" (dmesg requires root; NOPASSWD available). → sudo rule in agent prompt.
- **P1-6 · NEW (screenshots 13:17/13:23) — Firefox never opens**: agent launches GUI in FOREGROUND (`run_command({"command":"firefox"})`) → tool waits 30s and kills (3× timeout). → agent must launch GUI apps in BACKGROUND (`setsid firefox >/dev/null 2>&1 &`) or have a background tool.
- **P2-6 · No backspace/ESC/SUPPR** in input (only ctrl+backspace). Known, no fix yet.
- **P2-7 · F1 does not work** on his keyboard (Win+F1 does). → bind BOTH in i3 (`bindsym F1` + `$mod+F1`); text to decide ("F1 / Win+F1").
- **P2-8 · VirtualBox** — NAT network DOES work (enp0s3 10.0.2.15/24 UP, screenshot 13:23); Arnold's "no internet" was the agent's web_search (no backend in live), NOT the network. VBox guide: Linux/Oracle 64-bit, NAT, 8 GB RAM with LLM.
- **P3-9 · "WarGames is probably unknown to young IT people"** → explanatory subtitle.
- **P3-10 · Firefox starts in 15 s and closes** → probable root cause = P1-6 (tool timeout, not real startup). Re-test after fix.
- **P3-11 · Small local context** (Qwen3-8B on CPU/VM) → forgets things; possible user warning.

### ✅ What DID work (validated in VM, video 11:02)
- Happy-path installer: menu → "Installing AIOS to the hard disk..." → agent mode (LOCAL Qwen3-8B, requirements shown) → "Select the color theme:" (1 Wargames / 2 Amber / 3 White).
- Live mode + local LLM: agent responds and executes (change keyboard to French, list files, which firefox).
- The LLM in VM is slow but usable ("it's very slow in VM but works").
- Real interest: Arnold asked for the link for a friend; Carlos will give him a DeepSeek API key (meet in the evening).

### ✅ Applied on 25 Aug (commits: sre-agent `e5df97f` · aios-lfs `a4994ed`)
- **A.1** Sudo rule in `_RULES_COMMON`: "if it fails with Permission denied, retry with sudo (passwordless)".
- **A.2** GUI background: **DISCARDED** by Carlos ("graphical applications obviously have to be seen in i3"). The Firefox timeout in VM = insufficient resources (2 GB), not a bug (verified on real hardware it works).
- **B** Anti-loop by **base command** (`ls` even if args vary) + threshold **4** — tested: 4/4 cases (Arnold's loop triggers on the 5th; 3 legitimate ls + cat do not trigger; 3× identical does not trigger; different commands do not trigger).
- **C.1** Menu with `0) Exit to shell`; after live or installation **returns to menu** (only 0 exits); `returncode 2` = "Installation cancelled.".
- **C.2** Installer with steps `[1/7]…[7/7]`.
- **C.3** `select_disk`: empty → cancellation (exit 2); name not found → retry (max 3) → cancellation. Tested: 5/5 cases.
- **D** i3: binds `F1` + `$mod+F1` (texts "F1" kept — now F1 works universally).
- **E** `docs/VIRTUALBOX.md` (Linux/Oracle 64-bit, NAT, 8 GB RAM, 20 GB disk, ~30 min installation, note about agent web_search).
- Note: these changes are in the tree → **next ISO** (the currently published one does not have them).

### ✅ Applied 2nd batch on 25 Aug (commits: sre-agent `ea239a8` · aios-lfs `5de58bc`) — layouts + Carlos/Arnold feedback
- **Keyboard layouts**: new setup screen (`Select keyboard layout: 1) US 2) French/AZERTY 3) Spanish 4) German 5) Other`) → applies `loadkeys` (TTY) + `setxkbmap` (X) instantly, persisted in `config.yaml` (`keyboard:`) and reapplied on every i3 boot via the new script `/usr/local/bin/aios-keyboard` (reads config → setxkbmap). Solves AZERTY/QWERTZ user problems.
- **Disk selection by NUMBER** in the installer (`Select disk [1-N]`, fallback: name) — no typing → layout does not matter at the critical step. Tested: 6/6.
- **Format confirmations: 3 → 2** — merged #2 and #3: `WARNING: This will DESTROY all data on this disk (type 'format disk' to confirm)` (Arnold's request: too many questions).
- **Fix Enter after install failure**: `wg_input` now does `tcflush(TCIFLUSH)` before `input()` — discards residual Enter from subprocess (the prompt really waits).
- **Super+Shift+E (exit i3)**: nagbar with official i3 format (the previous `-m Exit? -B Yes i3-msg exit` did not respond when Yes was pressed).
- **shortcuts.txt**: `F1/Super+F1`, alignment corrected (the "Show..." was 2 cols offset), and note "In this list: press q (or Super+q) to close".
- Note: ISO was NOT regenerated (Carlos's decision) — changes are in the tree for the next one.

### ✅ Applied 3rd batch on 25 Aug (commits: sre-agent `d1a1f58`, `47d1d92`, `11ce11f`, `b081a60`, `1bf5a4e` · aios-lfs `ff73c31`)
- **Fix NTP NameError** (`b081a60`): `setup_ntp` used `print_box` without defining the alias (only existed in `setup_wifi`) → crashed installation when answering "y" to NTP. Confirmed with Carlos's screenshot.
- **Clear NTP phrase** (`1bf5a4e`): "Set the correct time automatically using an internet time server? (y/N)" (before "Configure NTP time sync (external server)?" — "too pro", Carlos's request).
- **Robust input `_read_line()`** (`11ce11f`, setup.py + aios-install): raw mode with manual handling — backspace ALWAYS works (no `^`/weird letters, ctrl+backspace no longer needed), **the `>` prompt is inviolable** (buffer starts empty), Ctrl+C interrupts, Ctrl+D = EOF. Solves P2-6 (reported 3 times).
- **loadkeys with sudo** (`11ce11f`): the TTY layout needs root — before it silently failed (only setxkbmap worked in X).
- **Greeting reordered** (`d1a1f58`): movie phrase → "You have just booted..." → "Press F1 or Super+F1 (Super = the Windows key) to view the keyboard shortcuts" → Select keyboard layout → clean menu.
- **Monotonic progress bar** (`47d1d92`): rsync `--info=progress2` % was recalculated (estimated total) and went down (90→40→70…) → now only goes up; ends at 100%.
- **umount/sudo**: reported by Carlos and discarded by him ("forget the umount thing") — the inventory of binaries with sudo is complete (all exist in the tree; secure_path correct).

### 💿 ISOs 25 Aug 23:47 (with all fixes; NOT downloaded by request)
- `~/aios.iso` (with LLM): 6.7 GB · md5 `899325f5d5b120468d6332f22b146801`
- `~/aios-nollm.iso` (without LLM): 2.1 GB · md5 `16986c5b25e7bb5f207426cf67dd1a77`
- Backups: `aios-20260825-2219.iso.bak` · `aios-nollm-20260825-2221.iso.bak` · served 1.4/nollm `-20260825-2.iso.bak`.
- The web still serves the 22:22 ones (md5 `7f59d9d4` / `e3162f28`) — the new ones have not been published.

### 📝 26 Aug session (commits: sre-agent `b081a60`→`8589eed` · aios-lfs `5d9e37c`→`e1ec0dc`)

**Global backspace (reported 3 times, resolved)**: tty erase char ≠ key → "^ and letters" in sudo/getpass/login. Fix in 4 layers: `/etc/profile.d/aios-tty.sh` (stty erase ^?), `/home/aios/.bashrc`, `_fix_erase()` in setup.py+aios-install (VERASE=b"\x7f" at startup — tested in real chroot pty: ^H→^? OK), and `keycode 14 = Delete` in `_apply_layout` (console with fr/es sends ^H). Full coverage: console, xterm, setup, installer (getpass included).

**Robust internet check + cloud/local logic** (`4c2e892`, `3a6649b`): TCP to 6 destinations + **DNS UDP** as last resort (networks with filtered TCP — the 2014 "I have IP but no connection" case). `_net_summary()` shows IP/Gateway on failure (absolute ip routes — /usr/sbin outside Debian user PATH). Fallback cloud→local now ASKS (Y/n) instead of surprising. Tested 4/4 scenarios (Windows + real Linux VPS).

**Definitive progress bar** (`578ad4c`): goodbye global % (rsync recalculates and oscillates) → `--out-format=%f` shows the CURRENT file + counter, all on one line (tested with real rsync).

**sven update/upgrade (investigated in depth)**: upgrade DOES work (70 packages applied in 2 batches; 1st attempt failed due to transient truncated checksums — retry resolves). The "cycle of 35" is COSMETIC: those are the **LFS/BLFS** packages (acl, krb5, openssl, nettle, glibc, libgcc...) that sven adopted without installing → "skipped strict version checks" → re-offers them always even if up to date (To Download: 0). **DO NOT reinstall** (would break the LFS chain — glibc lesson 4 Aug). ⚠️ The upgrade DID replace glibc/libgcc/libffi/systemd-libs with Arch versions (duality /lib64 LFS vs /usr/lib Arch — the tree is NOT usrmerge) → **PENDING DECISION: rollback the tree to pre-upgrade snapshot or keep** (recommendation: rollback + fresh DB; usrmerge as a planned future migration).

**Tree backup for migration**: `backups/bak-arbol-20260826-usrmerge.tar.zst` (zstd tar, excludes 4.7G model — intact in ~/models — and sven cache; tree = 9.0 GB, backup ~4.5 GB; VPS with 104 GB free).

**Screen recording** (from laptop — `feat/grabacion-pantalla` branch merged `e8134c5`): `scripts/grabar.sh` (ffmpeg x11grab → /tmp/grabacion.mp4), `toggle-grabacion.sh`, `parar_grabacion.sh`, `instalar-grabacion.sh`. Incorporated into the tree + `$mod+Print` binding in i3 + shortcut in help + LLM personality ("e.g. /tmp/grabacion.mp4").

**aios-update** (`8589eed` → fix `060e98d`): official system installed update script (git clone/pull + manifest md5-sync + backups + warnings). ✅ **BUG RESOLVED (26 Aug evening)**: manifest split `${entry%% *}`/`${entry#* }` with alignment spaces left spaces attached to `dst` → `[ -f '       /path' ]` false → never updated. **Fix applied: `read -r src dst <<< "$entry"`** (collapses spaces; destination paths have no spaces → safe). **Verified in chroot**: corrupted chat.py → aios-update detected it, backup in `/var/backups/aios-update/<date>/` and restore (md5 = repo); it also updated agent.py and aios-session that were out of sync with the tree. Test cache/backups cleaned (test originals 1542/1543/1548 remain).

**Persistent keyboard on disk (fix 26 Aug, commit `065a3d9`)**: the layout chosen in live did NOT reach the disk — console used the tree's `KEYMAP=es` (`/etc/vconsole.conf`) and X11 fell back to "us" (the disk's local config.yaml was created without `keyboard:`). Symptom: login (console, tree vconsole.conf) seemed to have the keyboard and the desktop did not. Fix: `setup.py` passes `--layout _KB_LAYOUT` to the installer; `aios-install` accepts `--layout`, `setup_aios_config` writes `keyboard:` in the disk config (local and cloud — also fixed the latent cloud bug: it read `Path.home()`=/root instead of `/home/aios`, so it didn't even copy the live config), and new `persist_keyboard()` replaces `KEYMAP=` in the disk `/etc/vconsole.conf` preserving `FONT=` (with validation: if the keymap does not exist in the tree, warns and keeps the current one). Verified with fake target (5 cases: fr valid, zz invalid, local, cloud/no-layout via `_live_layout()`, None conservative).

**sven — COSMETIC CYCLE RESOLVED AT THE ROOT (26 Aug evening, commits + tree)**: the "Ready to upgrade 35 forever" was NOT (only) the protection — it was a **sven 2.1.1 bug**: `register()` creates the new dir in `installed/` **without deleting the old one** → 64 packages with DUPLICATES → `LocalDB.load()` resolves by `readdir` order (arbitrary) → sometimes the OLD version won → re-offered the eternal upgrade. Known bug by the author (haroldmth/sven issue #2: "extracting for already-installed packages (reinstall/update)"), no fix (2.1.1 = latest release, Jul 2026). **Fix applied**: ① `scripts/sven-dedup.py` (new, embedded vercmp) removed 64+1 duplicates → 393 unique entries; ② `sven.conf` `protected_packages` reduced to `filesystem linux-api-headers linux-firmware ca-certificates` (the rest of the base is managed as normal packages); ③ **usrmerge applied** (`/bin /sbin /lib` → symlinks to `/usr/*`; `/lib64` was already aligned via symlinks); ④ `sven upgrade` applied (31 packages + llama-cpp to release 0.2.0-1) → **"Everything is up to date"**. The "skipped strict version checks" warning disappeared. ⚠️ Pitfall of dedup: embedded vercmp fails on alpha-vs-numeric (`b10221-1` vs `0.2.0-1`) — rare cases resolve manually. ⚠️ **Tree backup `bak-arbol-20260826-usrmerge.tar.zst` TRUNCATED** (9.7 GB, killed mid-write 19:34 — it was from the previous session in background) → **discarded by Carlos (won't redo for now)**. VPS rebooted at 19:41 (external cause; no data loss). Hygiene: tree `/dev` cleaned of 459 host VPS device nodes (bind from 23 Aug) and static nodes recreated (null/console/zero/full/random/urandom/tty/ptmx).

**Live boot order (fix 26 Aug night, commit `e1c9888`)**: `aios-session` ran setup on the CONSOLE (tty1) before startx when there was no config (design since 24 Jul, commit `c5f7a1f`) → menu appeared without i3. Removed setup-before-X: live boots **autologin → startx+i3 → setup in xterm** (i3 config line 54). The tree does NOT carry config.yaml (only disk installation creates it via `setup_aios_config`). Login font: `FONT=ter-232n` ONLY on disk (persist_keyboard); live keeps `ter-112n`. Final ISOs of the day: `aios-1.4.iso` 6.0 GB + `aios-nollm.iso` 1.4 GB, published and TESTED by Carlos (nollm, 26 Aug night).

**Pending**: discarded by Carlos on 26 Aug (agent visibility and laptop access included) — no active list.

**ISO publication 26 Aug (night)**: with the final tree of the day (usrmerge, sven DB 393, keyboard, FONT=ter-232n, clean /dev) the ISOs `aios-1.4.iso` (**6.0 GB**, with LLM) and `aios-nollm.iso` (**1.4 GB**, without LLM) were generated and published in `/var/www/ccmai.org/aios/releases/` (backups of the served ones in `backups/aios-*-servida-20260826.iso.bak`; web index+releases updated to the new sizes/dates, repo `web/` synced `9b59414`). ⚠️ **Size lesson**: the sven cache (`var/cache/sven/pkgs`, ~950 MB after upgrades) gets packaged into the ISO — clean it BEFORE mksquashfs (`rm -rf var/cache/sven/pkgs/*`) or the ISOs grow ~1 GB. The nollm was downloaded to Carlos's PC as `aios.iso` (previous → `aios.iso.anterior-20260826`) for testing.

## Changelog

### v10 — August 2026

- **setup.py**: API key validation in a thread with a 12 s timeout (fixes hang due to DNS without limit and Ctrl+C not responding due to SA_RESTART).
- **setup.py**: API key saved in `~/.aios/.env` instead of `config.yaml`.
- **setup.py**: `os._exit(0)` at the end to finish without waiting for residual threads.
- **setup.py**: LOCAL menu updated to `Qwen3-8B-Instruct` and text `1) LOCAL (no internet) / Simple tasks`; removed `Works 100% offline`.
- **setup.py** and **aios-install**: menus centered on screen using `os.get_terminal_size()` with horizontal and vertical padding.
- **Setup → agent flow**: after completing setup, `aios` runs automatically in the same xterm window without `-hold`, using `&& [ -f $HOME/.aios/config.yaml ] && aios || exec bash`.
- **aios-install v1.1.1**: at the end asks whether to change root and aios passwords, with 8-character validation via `getpass` and `chpasswd` through stdin inside the disk chroot.
- **Silent boot on disk**: the installed system boots like the live one (black background + AIOS banner). New initrd generated by `build_disk_initrd` that mounts the real partition and does `switch_root`.
- **Squashfs**: now includes `boot/vmlinuz-6.18.10-lfs` and `boot/initrd.img` to facilitate disk installation.
- **Security**: removed `nokaslr` from live and disk installer.
- **Real kernel #4**: compiled with host VPS gcc 15.2.0; config with `CONFIG_X86_VERBOSE_BOOTUP=n`, `CONFIG_OVERLAY_FS=y`, `CONFIG_FB_VESA=y`; without `VMWGFX`/`VBOXVIDEO`/`FBDEV_EMULATION`.
- **Locale**: `/etc/locale.conf` set to `LANG=C.UTF-8` to avoid box-character mojibake.
- **xterm**: `Adwaita Mono` font at 11 pt, without `-hold`.
- **Plymouth**: definitively discarded due to lack of framebuffer in the VM with kernel #4.

### v9 and earlier

- Base LFS 13.0-systemd with rw OverlayFS.
- Sven integration for Arch packages.
- OpenSSH, X11, i3, xterm installation.
- AIOS wargame client with Matrix style.
- Initial disk installer (`aios-install`).
- Previous attempts at Plymouth and kernel logo.

---

## License

MIT — see the `LICENSE` file in the repository.

## WarGames menu and agent — v12 changes (Aug 2026)

### Boot menu (setup.py)
- **"Greetings, Professor Falken"** greeting with typewriter effect: 850 Hz / 35 ms tick per character (PCM synthesized via `aplay` persisted through stdin — no audio files)
- The greeting is shown **ALWAYS**: at setup boot and **every time chat starts** (aios-agent)
- **Reliable beep from the first character**: minimum ALSA buffer/period (512 frames ~11.6 ms) + **0.2 s silence warm-up** when opening aplay (forces ALSA to open the device before the first tick — otherwise the first ticks accumulate in the pipe and sound late)
- **`/sound`** in chat: enables/disables the tick (`SOUND_ON` is an `Agent` class attribute)
- The greeting is **directly followed by the menu** (without clearing the screen): `Greetings, Professor Falken` → `You have just booted Artificial Intelligence Operating System.`
- **No boxes** (`print_box` removed from all menus; `aios-install` too — only the inert definition remains)
- **Insistent initial menu**: an invalid option repeats the question (`Invalid option. Please choose 1 or 2.`) — never falls to live
- **Reliable backspace**: `readline` with `^H` and `DEL` mapped to `backward-delete-char` (setup.py and chat.py — covers the two codes sent by terminals)

### Honest internet check
- **Cascade of 6 TCP destinations**: 1.1.1.1:443, 1.0.0.1:443, 8.8.8.8:53, google.com:443, google.es:443, archlinux.org:443 — IPs without DNS + real domains with DNS (a network that filters IPs — like Carlos's — does not give a false negative)
- **OpenDNS** (208.67.222.222 / 208.67.220.220) across the system: live and installed, eth + wifi (`.network` with `[DHCP] UseDNS=no` + wizard wifi `_ensure_dns` + installer `persist_wifi`)

### Color themes (completed 21 Aug 2026)
- **4 themes**: `wargames` (dark green `#006400`, default), `amber` (`#ffb000`), `white` (`#ffffff`), `cyan` (`#00cccc`)
- **`aios-theme <theme>`** (central script in `/usr/local/bin`): writes `theme:` in `~/.aios/config.yaml`, generates `~/.config/i3/colors.conf` (`client.*` colors + bar) and **applies instantly** (restarts bar `status.py` + `i3-msg reload`) — a single path for EVERYTHING
- **Wrapper `/usr/local/bin/aios-xterm`**: reads `theme:` from `config.yaml` and launches xterm with the colors — used by the menu, chat, and `$mod+Return`
- **`status.py`** (i3 bar): reads `theme:` from `config.yaml` and emits the theme colors (red/orange alerts preserved — semantics)
- **i3 config**: colors live in `include /home/aios/.config/i3/colors.conf` (generated by aios-theme)
- Selection: **setup** (asks for the theme while configuring and applies it), **`/theme`** in chat (**applies instantly**, no restart), or `aios-theme <theme>` manually
- The installer accepts **`--theme`** (the disk keeps the chosen theme)

### "Other" provider
- **Option 8) Other** in the provider menu: name + endpoint URL (chat completions) + model + **API key validated against that endpoint** (`GET <base>/models`)
- The config saves `cloud.base_url` and chat uses it (custom endpoint instead of `CLOUD_ENDPOINTS`)

### Agent context (agent.py)
- **Prompt per mode**: `cloud` = full identity (what AIOS is, LFS + sven, capabilities: commands/files/processes, web search, vision OCR/screenshots/xdotool, sven packages, network, services, local LLM at 8083); `local` = very summarized (1 line of identity + essential capabilities) — the context limit is that of the chosen provider
- Language rule: **"Always respond in the same language the user writes in"** — the LLM responds in the user's language
- All interface text in **English** (models, messages, docstrings); the agent prompt in English

### Disk installation (aios-install) — login and sudo
- ⚠️ **REVERTED on 19 Aug 2026**: the installed disk **keeps live autologin and NOPASSWD** (disk = live). The hardening attempt (disable_autologin + harden_sudo) was reverted because it introduced a bug (`harden_sudo` with `glob` → `is_file()` failed) that **aborted the installer halfway** → disk without persisted wifi → `systemd-networkd-wait-online` blocked boot (logo stuck ~2 min). The corrected installer (21 Aug) no longer touches autologin or sudoers.
- The installer is **UNIQUE**: `/usr/local/bin/aios-install` (versioned in the `sre-agent` repo; the one in `scripts/` was an obsolete duplicate — removed)

### LOCAL requirements note
- In the menu (live and install):
```
  1) LOCAL - the built-in Qwen3-8B model (no internet needed)
     Requires: CPU at least like an Intel i5-1035G1 (4 cores / 8 threads,
     1.0 GHz base / 3.6 GHz boost, 6 MB cache), 8 GB RAM.
     Note: runs slow, about human typing speed.
```

### Initrd (banner)
- The banner remains the **original halftone ▒▓░** (md5 `a349e10d`). On 23 Aug an attempt was made to put Carlos's art (█ + AI*OS, 29 lines) → **broke boot** (logo visible, autologin, then black screen — overflow of ~25 screen lines) → REVERTED. Procedure to retry with art that fits: `build_initrd_art.py` (extract gzip+cpio, replace the `\033[2J`→`\033[0m` block, repack).
