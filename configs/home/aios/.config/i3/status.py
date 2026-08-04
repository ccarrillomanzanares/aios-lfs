#!/usr/bin/env python3
"""AIOS i3bar status script — pure stdlib, Python 3.11+ compatible."""

import json
import os
import shutil
import socket
import sys
import time

# i3bar Matrix color scheme
COLOR_TEXT = "#00ff00"
COLOR_SEP = "#005500"
SEPARATOR = {"full_text": " | ", "color": COLOR_SEP}
VERSION_LINE = {"version": 1, "click_events": False}


def _item(text):
    return {"full_text": str(text), "color": COLOR_TEXT}


def get_cpu_load():
    try:
        with open("/proc/loadavg", "r") as f:
            load1 = float(f.read().split()[0])
        return f"CPU {load1:.2f}"
    except Exception:
        return "--"


def get_memory():
    try:
        total_kb = avail_kb = free_kb = None
        with open("/proc/meminfo", "r") as f:
            for line in f:
                parts = line.split()
                if not parts:
                    continue
                key = parts[0]
                if key == "MemTotal:":
                    total_kb = int(parts[1])
                elif key == "MemAvailable:":
                    avail_kb = int(parts[1])
                elif key == "MemFree:" and free_kb is None:
                    free_kb = int(parts[1])
        if total_kb is None:
            return "--"
        used_kb = total_kb - (avail_kb if avail_kb is not None else free_kb)
        total_gb = total_kb * 1024 / 1e9
        used_gb = used_kb * 1024 / 1e9
        return f"MEM {used_gb:.1f}/{total_gb:.1f}GB"
    except Exception:
        return "--"


def get_disk():
    try:
        total, used, free = shutil.disk_usage("/")
        return f"DISK {used/1e9:.1f}/{free/1e9:.1f}GB"
    except Exception:
        return "--"


def _default_iface():
    """Return the interface owning the default route, or None."""
    try:
        with open("/proc/net/route", "r") as f:
            header = f.readline().split()
            iface_idx = header.index("Iface")
            dest_idx = header.index("Destination")
            flags_idx = header.index("Flags")
            for line in f:
                parts = line.split()
                if len(parts) < max(iface_idx, dest_idx, flags_idx) + 1:
                    continue
                if parts[dest_idx] == "00000000" and (int(parts[flags_idx], 16) & 0x0003) == 0x0003:
                    return parts[iface_idx]
    except Exception:
        pass
    return None


def _iface_ip(iface):
    try:
        for entry in socket.getifaddrs():
            if entry.interface == iface and entry.family == socket.AF_INET:
                return entry.address[0]
    except Exception:
        pass
    return None


def get_network():
    try:
        iface = _default_iface()
        ip = _iface_ip(iface)
        if ip is None:
            # Fallback: first non-loopback IPv4 address
            for entry in socket.getifaddrs():
                if entry.family == socket.AF_INET and entry.interface != "lo":
                    ip = entry.address[0]
                    break
        return f"NET {ip}" if ip else "--"
    except Exception:
        return "--"


def get_datetime():
    try:
        import locale
        # Try Spanish locales first; fall through to UTC+2 manual below.
        for loc in ("es_ES.UTF-8", "es_ES.utf8", "es_ES", "spanish"):
            try:
                locale.setlocale(locale.LC_TIME, loc)
                return time.strftime("%a %d %b %H:%M")
            except Exception:
                continue
    except Exception:
        pass

    # Fallback: UTC+2 with Spanish weekday/month abbreviations.
    t = time.gmtime(time.time() + 2 * 3600)
    dias = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]
    meses = ["ene", "feb", "mar", "abr", "may", "jun",
             "jul", "ago", "sep", "oct", "nov", "dic"]
    return f"{dias[t.tm_wday]} {t.tm_mday:02d} {meses[t.tm_mon - 1]} {t.tm_hour:02d}:{t.tm_min:02d}"


def build_blocks():
    return [
        _item("AIOS"),
        SEPARATOR,
        _item(get_cpu_load()),
        SEPARATOR,
        _item(get_memory()),
        SEPARATOR,
        _item(get_disk()),
        SEPARATOR,
        _item(get_network()),
        SEPARATOR,
        _item(get_datetime()),
    ]


def main():
    print(json.dumps(VERSION_LINE))
    print("[")
    sys.stdout.flush()

    first = True
    while True:
        blocks = build_blocks()
        line = json.dumps(blocks)
        if not first:
            line = "," + line
        first = False
        print(line)
        sys.stdout.flush()
        time.sleep(2)


if __name__ == "__main__":
    main()
