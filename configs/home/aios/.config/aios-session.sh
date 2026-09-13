#!/bin/sh
# AIOS session: D-Bus + PipeWire (audio) + i3
# Lanzado por .xinitrc via dbus-run-session (metodo BLFS para LFS sin display manager)
# XDG_RUNTIME_DIR lo crea systemd-tmpfiles en cada arranque (/etc/tmpfiles.d/aios-runtime.conf)
#
# Audio: PipeWire belongs to systemd --user, NOT to this script. It used to be
# started here by hand ("pipewire & pipewire-pulse & wireplumber &" -- the BLFS
# method from when LFS had no pam_systemd). pam_systemd exists now, so systemd
# --user starts them as well: there were TWO owners, the second one failed to
# lock the socket ("unable to lock lockfile") and left a duplicated wireplumber
# fighting for the card (duplicate sinks). Measured 13 Sep 2026.
# Asking systemd to start them is idempotent and works on installs without the
# enable symlinks, so there is always exactly ONE owner: systemd.
export XDG_RUNTIME_DIR=/run/user/1000
# ONE owner: systemd --user. Idempotent (already-active services are a no-op).
if ! systemctl --user start pipewire pipewire-pulse wireplumber 2>/dev/null; then
    # No user session bus (a build without pam_systemd): old BLFS fallback.
    pipewire &
    pipewire-pulse &
    wireplumber &
fi
exec i3
