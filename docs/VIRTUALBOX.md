# VirtualBox Guide for Testing AIOS

How to set up a virtual machine to test AIOS (ISO 1.4, live + installation).
Verified with the first external user (Arnold, 25 Aug 2026).

## Create the VM

| Parameter | Value | Note |
|---|---|---|
| Type | **Linux** | — |
| Version | **Oracle Linux (64-bit)** | If a Linux type is not selected, VirtualBox won't detect the system |
| RAM | **8192 MB (8 GB)** minimum | With 2 GB the local LLM and desktop run very slowly (the agent responds, but takes time) |
| CPU | 2+ cores | |
| Disk | **20 GB minimum** | The installed system + LLM model (4.7 GB) need space |
| Network | **NAT** (default) | Verified: the VM gets 10.0.2.15/24 and works |

## Boot the ISO

1. In the VM: *Storage → IDE Controller → Add optical disk* → select `aios-1.4.iso` (6.7 GB).
2. Start the VM. The AIOS menu appears in the terminal (green).

## During boot/use

- The **main menu** has 3 options: `1) Test AIOS live` · `2) Install AIOS` · `0) Exit to shell`.
- After choosing **Install**, the installer shows steps `[1/7] … [7/7]` with progress.
- **Installation takes ~30 minutes** (copying the 4.7 GB LLM model). Do not interrupt.
- Keyboard help: **F1 or Win+F1**.
- French/AZERTY keyboard is configured from the chat: *"change the keyboard to french"*.

## Notes / known issues

- **Firefox may take >30 s to open** on a VM with little RAM (2 GB) → the agent reports timeout.
  This is not a system failure: with 8 GB RAM it opens normally (verified on real hardware).
- The agent's **web_search** requires configuration (API key/backend);
  without it the agent warns about a connection problem. This is not a VM network failure.
- If installation is **cancelled** (invalid disk or confirmation rejected), the installer
  returns to the menu — no need to reboot the VM.
- Only tested on **non-multiboot** machines (see installer disclaimer).

## Links

- ISO: `https://ccmai.org/aios/releases/aios-1.4.iso`
- Project website: `https://ccmai.org/aios/`
- Repos: `github.com/ccarrillomanzanares/aios-lfs` · `github.com/ccarrillomanzanares/aios-agent`
