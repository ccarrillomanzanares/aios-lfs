#!/usr/bin/env python3
"""AIOS i3bar status script — pure stdlib, Python 3.11+ compatible."""

import json
import os
import shutil
import socket
import subprocess
import sys
import time

# Colores por tema (aios-theme aplica el tema: wargames/amber/white/cyan)
THEMES = {
    "wargames": ("#00ff66", "#66ffa8"),
    "amber":    ("#ffb000", "#885500"),
    "white":    ("#ffffff", "#888888"),
    "cyan":     ("#00cccc", "#006666"),
}
COLOR_TEXT = "#00ff66"
COLOR_SEP = "#66ffa8"
SEPARATOR = {"full_text": " | ", "color": COLOR_SEP}
VERSION_LINE = {"version": 1, "click_events": False}

def _load_theme():
    """Lee theme: del config.yaml y aplica los colores (igual que aios-xterm)."""
    global COLOR_TEXT, COLOR_SEP, SEPARATOR
    try:
        with open(AIOS_CONFIG) as f:
            for line in f:
                if line.startswith("theme:"):
                    t = line.split(":", 1)[1].strip().strip("\"'")
                    if t in THEMES:
                        COLOR_TEXT, COLOR_SEP = THEMES[t]
                        SEPARATOR = {"full_text": " | ", "color": COLOR_SEP}
                    break
    except Exception:
        pass

WIFI_IFACE = "wlo1"
ETH_IFACE = "enp3s0"
AIOS_CONFIG = "/home/aios/.aios/config.yaml"
AIOS_SESSION_DIR = "/usr/local/bin/aios-agent/data"


def _item(text, color=None):
    return {"full_text": str(text), "color": color if color is not None else COLOR_TEXT}


def _read_first_line(path):
    try:
        with open(path, "r") as f:
            return f.readline().strip()
    except Exception:
        return None


def _iface_operstate(iface):
    return _read_first_line(f"/sys/class/net/{iface}/operstate") == "up"


def _iface_carrier(iface):
    try:
        path = f"/sys/class/net/{iface}/carrier"
        if not os.path.exists(path):
            return False
        return _read_first_line(path) == "1"
    except Exception:
        return False


def _iface_up(iface):
    try:
        return _iface_operstate(iface) and _iface_carrier(iface)
    except Exception:
        return False


def _iface_ip(iface):
    # 1) getifaddrs (falla en el python del LFS — devuelve None aunque haya IP)
    try:
        for entry in socket.getifaddrs():
            if entry.interface == iface and entry.family == socket.AF_INET:
                return entry.address[0]
    except Exception:
        pass
    # 2) ip -br addr (iproute2, funciona en el LFS)
    try:
        result = subprocess.run(
            ["ip", "-br", "addr", "show", iface],
            capture_output=True, text=True, timeout=2,
        )
        for line in result.stdout.splitlines():
            parts = line.split()
            for p in parts:
                if "/" in p and ":" not in p:
                    return p.split("/")[0]
    except Exception:
        pass
    return None


def _get_ssid_iw(iface):
    """SSID vía `iw dev <iface> link` (wpa_supplicant runs WITHOUT ctrl_interface on AIOS)."""
    try:
        result = subprocess.run(
            ["iw", "dev", iface, "link"],
            capture_output=True, text=True, timeout=2,
        )
        for line in result.stdout.splitlines():
            line = line.strip()
            if line.startswith("SSID:"):
                ssid = line.split(":", 1)[1].strip()
                return ssid or None
    except Exception:
        pass
    return None


def _get_ssid(iface):
    ssid = _get_ssid_iw(iface)
    if ssid is None:
        ssid = _get_ssid_wpa_cli(iface)  # fallback: requiere ctrl_interface configurado
    if ssid is None:
        ssid = _get_ssid_iwgetid(iface)  # fallback 2
    return ssid


def _get_ssid_wpa_cli(iface):
    try:
        result = subprocess.run(
            ["wpa_cli", "-i", iface, "status"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode != 0:
            return None
        for line in result.stdout.splitlines():
            if line.startswith("ssid="):
                return line.split("=", 1)[1].strip()
    except Exception:
        pass
    return None


def _get_ssid_iwgetid(iface):
    try:
        if shutil.which("iwgetid"):
            result = subprocess.run(
                ["iwgetid", "-r", iface],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if result.returncode == 0:
                ssid = result.stdout.strip()
                if ssid:
                    return ssid
    except Exception:
        pass
    return None


def _get_signal_pct(iface):
    """% de cobertura wifi desde 'signal: -XX dBm' de `iw dev <iface> link` (0-100)."""
    try:
        r = subprocess.run(["iw", "dev", iface, "link"],
                           capture_output=True, text=True, timeout=2)
        for line in r.stdout.splitlines():
            if "signal:" in line:
                dbm = float(line.split("signal:")[1].split()[0])
                return int(max(0, min(100, 2 * (dbm + 100))))
    except Exception:
        pass
    return None


def get_network_blocks():
    """Return a list of i3bar items for active WiFi and/or Ethernet."""
    try:
        blocks = []
        if _iface_up(WIFI_IFACE):
            ssid = _get_ssid(WIFI_IFACE)
            ip = _iface_ip(WIFI_IFACE)
            sig = _get_signal_pct(WIFI_IFACE)
            parts = ["WiFi"]
            if ssid:
                parts.append(ssid)
            if ip:
                parts.append(ip)
            if sig is not None:
                parts.append(f"{sig}%")
            if len(parts) > 1:
                blocks.append(_item(" ".join(parts)))
        if _iface_up(ETH_IFACE):
            ip = _iface_ip(ETH_IFACE)
            if ip:
                blocks.append(_item(f"ETH {ip}"))
        return blocks
    except Exception:
        return []


# Context limits per provider (fixed table, mirror of setup.py)
PROVIDER_CONTEXT_LIMITS = {
    "DeepSeek": 1048576,
    "OpenAI": 128000,
    "Anthropic": 200000,
    "Google Gemini": 1048576,
    "Kimi / Moonshot": 128000,
    "Ollama Cloud": 128000,
    "OpenRouter": 128000,
}
DEFAULT_CLOUD_LIMIT = 128000


def _ram_gb():
    """RAM total en GB (redondeado) desde /proc/meminfo."""
    try:
        with open("/proc/meminfo", "r") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    kb = int(line.split()[1])
                    return max(1, kb // (1024 * 1024))
    except Exception:
        pass
    return 8


def _auto_context_local(ram_gb):
    """Auto-select context por RAM (espejo de setup.py auto_context)."""
    if ram_gb <= 8:
        return 8192
    elif ram_gb <= 16:
        return 32768
    else:
        return 65536


def _read_config():
    """Lee mode y provider del config.yaml (parser naive, sin yaml)."""
    mode, provider = None, None
    try:
        with open(AIOS_CONFIG, "r") as f:
            for line in f:
                stripped = line.strip()
                if stripped.startswith("mode:"):
                    mode = stripped.split(":", 1)[1].split("#")[0].strip()
                elif stripped.startswith("provider:"):
                    provider = stripped.split(":", 1)[1].split("#")[0].strip()
    except Exception:
        pass
    return mode, provider


def get_llm_context():
    """Estima el % de contexto usado: cloud → tabla fija por proveedor; local → auto_context por RAM."""
    try:
        if not os.path.isfile(AIOS_CONFIG):
            return _item("CTX --")

        mode, provider = _read_config()

        if mode == "cloud":
            # Fixed limit per provider (do not read context_limit from config)
            limit = PROVIDER_CONTEXT_LIMITS.get(provider, DEFAULT_CLOUD_LIMIT)
        elif mode == "local":
            # Auto-context by machine RAM (mirror of setup.py auto_context)
            limit = _auto_context_local(_ram_gb())
        else:
            return _item("CTX --")

        session_path = os.path.join(AIOS_SESSION_DIR, f"session_{mode}.json")
        if not os.path.isfile(session_path):
            return _item("CTX --")

        with open(session_path, "r") as f:
            messages = json.load(f)

        tokens = 0
        for msg in messages:
            try:
                content = msg.get("content") if isinstance(msg, dict) else None
                if isinstance(content, str):
                    tokens += len(content) // 4
            except Exception:
                pass

        pct = min(tokens * 100 // limit, 100)

        if pct > 95:
            color = "#ff0000"
        elif pct > 80:
            color = "#ff8800"
        else:
            color = COLOR_TEXT

        return _item(f"CTX {pct}%", color=color)
    except Exception:
        return _item("CTX --")


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
    dias = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    meses = ["ene", "feb", "mar", "abr", "may", "jun",
             "jul", "ago", "sep", "oct", "nov", "dic"]
    return f"{dias[t.tm_wday]} {t.tm_mday:02d} {meses[t.tm_mon - 1]} {t.tm_hour:02d}:{t.tm_min:02d}"


# Estado para medir uso de red entre muestras (el loop llama build_blocks cada 2s)
_net_last = {}


def _net_rate_bps(iface):
    """Tasa RX/TX actual en bits/s (diferencia entre dos lecturas de rx_bytes/tx_bytes)."""
    global _net_last
    try:
        rx = int(open(f"/sys/class/net/{iface}/statistics/rx_bytes").read().strip())
        tx = int(open(f"/sys/class/net/{iface}/statistics/tx_bytes").read().strip())
        now = time.time()
        prev = _net_last.get(iface)
        _net_last[iface] = (now, rx, tx)
        if not prev:
            return None  # first sample: no data yet
        dt = now - prev[0]
        if dt <= 0:
            return None
        rx_bps = (rx - prev[1]) * 8 / dt
        tx_bps = (tx - prev[2]) * 8 / dt
        return rx_bps, tx_bps
    except Exception:
        return None


def _iface_capacity_bps(iface):
    """Capacidad de la interfaz: ethernet /sys/.../speed (Mbps) o wifi tx bitrate de iw."""
    try:
        speed = open(f"/sys/class/net/{iface}/speed").read().strip()
        if speed.isdigit() and int(speed) > 0:
            return int(speed) * 1_000_000
    except Exception:
        pass
    try:
        r = subprocess.run(["iw", "dev", iface, "link"],
                           capture_output=True, text=True, timeout=2)
        for line in r.stdout.splitlines():
            if "tx bitrate:" in line:
                mbit = float(line.split("tx bitrate:")[1].split()[0])
                return int(mbit * 1_000_000)
    except Exception:
        pass
    return None


def get_net_usage_block():
    """% de uso de red sobre la capacidad de la interfaz activa (o KB/s si no hay capacidad).
    Sin trafico: muestra el link de la interfaz (p.ej. NET 100M)."""
    try:
        for iface in (WIFI_IFACE, ETH_IFACE):
            if not _iface_up(iface):
                continue
            rate = _net_rate_bps(iface)
            cap = _iface_capacity_bps(iface)
            if rate:
                rx_bps, tx_bps = rate
                total_bps = rx_bps + tx_bps
                if cap:
                    pct = min(total_bps * 100 / cap, 100)
                    if pct < 1:
                        return _item(f"NET {int(cap/1_000_000)}M")
                    color = "#ff0000" if pct > 95 else ("#ff8800" if pct > 80 else COLOR_TEXT)
                    return _item(f"NET {pct:.0f}%", color=color)
                return _item(f"NET {total_bps/1024:.0f}KB/s")
            if cap:
                return _item(f"NET {int(cap/1_000_000)}M")
        return None
    except Exception:
        return None


def get_agent_busy_block():
    """⏳ if the agent is working (marker /tmp/aios-agent.busy created by agent.py)."""
    try:
        if os.path.isfile("/tmp/aios-agent.busy"):
            return _item("⏳", color=COLOR_TEXT)
    except Exception:
        pass
    return None


def get_volume_block():
    """VOL % del sink por defecto via pactl (PipeWire). Fallback amixer si no hay pactl."""
    try:
        env = dict(os.environ)
        env.setdefault("XDG_RUNTIME_DIR", "/run/user/1000")
        r = subprocess.run(["pactl", "get-sink-volume", "@DEFAULT_SINK@"],
                           capture_output=True, text=True, timeout=5, env=env)
        if r.returncode != 0:
            return None
        # "Volume: front-left: 29490 /  45% / -20.81 dB, ..." -> 45
        import re
        m = re.search(r"(\d+)%", r.stdout)
        if not m:
            return None
        pct = int(m.group(1))
        # estado mute
        muted = False
        rm = subprocess.run(["pactl", "get-sink-mute", "@DEFAULT_SINK@"],
                            capture_output=True, text=True, timeout=5, env=env)
        if rm.returncode == 0 and "yes" in rm.stdout.lower():
            muted = True
        if muted:
            return _item(f"VOL {pct}% 🔇", color="#ff8800")
        if pct > 95:
            color = "#ff0000"
        elif pct > 80:
            color = "#ff8800"
        else:
            color = COLOR_TEXT
        return _item(f"VOL {pct}%", color=color)
    except Exception:
        return None


def get_voice_block():
    """VOX/MIC status (green = active, dim = off) from data/voice_state.json."""
    try:
        with open(os.path.join(AIOS_SESSION_DIR, "voice_state.json")) as f:
            st = json.load(f)
    except Exception:
        st = {}
    vox = st.get("tts") not in (None, "off")
    mic = st.get("stt") not in (None, "off")
    s = ("VOX" if vox else "vox") + " " + ("MIC" if mic else "mic")
    return _item(s, color=COLOR_TEXT if (vox or mic) else "#555555")


def build_blocks():
    items = []
    busy = get_agent_busy_block()
    if busy is not None:
        items.append(busy)
    items.extend([
        _item("Help:F1"),
        _item(get_cpu_load()),
        _item(get_memory()),
        _item(get_disk()),
    ])
    items.extend(get_network_blocks())
    net_usage = get_net_usage_block()
    if net_usage is not None:
        items.append(net_usage)
    vol = get_volume_block()
    if vol is not None:
        items.append(vol)
    items.append(get_voice_block())
    items.append(get_llm_context())
    items.append(_item(get_datetime()))

    # Place separators only between present blocks.
    blocks = []
    for i, it in enumerate(items):
        blocks.append(it)
        if i < len(items) - 1:
            blocks.append(SEPARATOR)
    return blocks


def main():
    _load_theme()
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
