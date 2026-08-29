# Post-install fix: black screen / no keyboard or touchpad

> Date: 2026-08-05  
> Affects: AIOS installations on real hardware with AMD GPU (active amdgpu/DRM).  
> Code fix: `aios-agent`, commit `5996ae2`.

## Symptom

After installing AIOS to disk on a laptop with AMD GPU:

- The system boots, the boot logo is visible, but afterwards the screen stays **black**.
- Or it boots without **keyboard or touchpad**.
- On virtual machines (VMSVGA graphics controller) the issue **does not reproduce**, because `/dev/dri` does not exist.

## Root cause (three chained bugs)

### 1. System D-Bus does not start

- `dbus.service` was a symlink to `dbus-broker.service`.
- The `dbus-broker` package/binary **was not installed**.
- Without a system bus, `systemd-logind` does not start.
- Without `systemd-logind`, the graphical session cannot start.

### 2. `systemd-gpt-auto-generator` breaks dbus-broker's mount namespace

- On **GPT disks with BIOS boot** (no real ESP partition), `systemd-gpt-auto-generator` creates the `efi.mount` and `efi.automount` units.
- Both fail to mount because there is no ESP.
- That broken mount breaks the mount namespace that `dbus-broker` needs due to its `ProtectSystem=full` sandbox.
- `dbus-broker` dies with status `226/NAMESPACE`.

**Manual fix on already installed systems:**

```bash
ln -sf /dev/null /etc/systemd/system/efi.mount
ln -sf /dev/null /etc/systemd/system/efi.automount
systemctl daemon-reload
```

> **Future note:** AIOS must support real UEFI (vfat ESP + grub-efi) in future versions. In that scenario these units will be valid and must not be masked.

### 3. The `aios` user is not in the desktop groups

With `amdgpu` active:

- `/dev/dri/card0` is `root:video 660`.
- `/dev/input/event*` are `root:input 660`.

If `aios` does not belong to `video` or `input`, Xorg fails:

```text
open /dev/dri/card0: Permission denied
vesa: Refusing to run, Framebuffer or dri device present
no screens found
```

The `tty1` getty restarts every ~5 seconds, so the screen stays black.

If `aios` also does not belong to `input`, there is no keyboard or touchpad access.

## Fix implemented in the installer

The fix is in `aios-install` (repo `aios-agent`, commit `5996ae2`).

The `add_user_groups(target)` function was added, executed in the chroot of the installed system, after `harden_ssh()` in `main()`:

```python
desktop_groups = [
    "video", "audio", "input", "storage", "optical", "power", "kvm",
    "render", "log", "rfkill", "disk", "cdrom", "dialout", "lp"
]

def add_user_groups(target):
    for group in desktop_groups:
        subprocess.run(["chroot", target, "groupadd", "-f", group], check=False)
    groups_csv = ",".join(desktop_groups)
    subprocess.run(
        ["chroot", target, "usermod", "-aG", groups_csv, "aios"],
        check=True
    )
```

The installer generates the full group scheme on the target disk (Arch-style GIDs: `video=981`, `audio=993`, `input=988`, `disk=989`, `cdrom=992`, `kvm=986`, `render=984`, `lp=985`, `tty=5`, etc.).

### ⚠️ Important: do not add these groups to the squashfs/base ISO

These groups must not be created in the squashfs or the base ISO. Doing so creates GID collisions. For example, if `power=986` is defined in the squashfs, it collides with `kvm=986` that the installer later creates on the disk.

**The correct fix is to apply it only from the installer:** `groupadd -f` + `usermod -aG`.

## Verification after installing

1. Check that `aios` belongs to all the groups:

```bash
groups aios
```

Expected output (order may vary):

```text
aios : aios wheel video audio input storage optical power kvm render log rfkill disk cdrom dialout lp
```

2. Check that `/dev/dri/card0` is accessible:

```bash
ls -l /dev/dri/card0
getfacl /dev/dri/card0   # if available
su - aios -c "test -r /dev/dri/card0 && echo OK"
```

3. Check that input devices are readable:

```bash
ls -l /dev/input/event*
su - aios -c "test -r /dev/input/event0 && echo OK"
```

4. If the problem persists, check the real Xorg log:

```bash
cat /home/aios/.local/share/xorg/Xorg.0.log
```

> **Note:** `/var/log/Xorg.0.log` may belong to an earlier boot or a root session. The log for user `aios` after `startx` is at `/home/aios/.local/share/xorg/Xorg.0.log`.

5. If `getty@tty1` restarts every ~5 seconds, the X session is dying immediately. Check `startx.log` in `/home/aios/`.

## Quick diagnosis

| Symptom | Likely cause |
|---|---|
| Black screen after the logo, getty restarting | Xorg cannot open `/dev/dri/card0` due to missing `video` group. |
| No keyboard/touchpad | Missing `input` group. |
| `dbus-broker` dies with `226/NAMESPACE` | Broken `efi.mount` / `efi.automount` units on GPT+BIOS. |
| `systemd-logind` inactive | No system D-Bus (`dbus-broker` not installed or not starting). |

## Future UEFI note

This document describes the current state for BIOS-on-GPT installations without ESP. When AIOS implements real UEFI support with a vfat ESP partition and `grub-efi`, the `efi.mount` and `efi.automount` units will no longer be problematic and the installer must be adapted not to mask them.
