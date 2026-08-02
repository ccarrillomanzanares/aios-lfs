#!/usr/bin/env bash
# update-agent.sh - Update the AIOS agent on an installed AIOS system.
# Run this script inside the installed AIOS environment.

set -euo pipefail

# Destination paths on the installed system
AGENT_DIR="/usr/local/bin/aios-agent"
INSTALL_BIN="/usr/local/bin/aios-install"
AGENT_BIN="/usr/local/bin/aios"
AGENT_REPO_URL="https://github.com/ccarrillomanzanares/aios-agent.git"

# Print helpers
info() { printf '\033[1;34m[INFO]\033[0m %s\n' "$*"; }
ok()   { printf '\033[1;32m[OK]\033[0m   %s\n' "$*"; }
warn() { printf '\033[1;33m[WARN]\033[0m %s\n' "$*" >&2; }
err()  { printf '\033[1;31m[ERR]\033[0m  %s\n' "$*" >&2; }

# Ensure git is available
require_git() {
    if ! command -v git >/dev/null 2>&1; then
        err "git is not installed; install it first"
        exit 1
    fi
}

# Obtain or update the agent repository
update_repo() {
    if [[ ! -d "${AGENT_DIR}" ]]; then
        info "Agent directory missing; cloning ${AGENT_REPO_URL} into ${AGENT_DIR}..."
        sudo mkdir -p "${AGENT_DIR}"
        sudo git clone "${AGENT_REPO_URL}" "${AGENT_DIR}"
    else
        info "Updating agent repository at ${AGENT_DIR}..."
        cd "${AGENT_DIR}"
        sudo git pull
    fi
    ok "Agent repository ready"
}

# Install/update the agent entry-point scripts
copy_agent_files() {
    info "Copying agent executables to system paths..."
    sudo cp "${AGENT_DIR}/setup.py" "${AGENT_DIR}/"
    sudo cp "${AGENT_DIR}/aios-install" "${INSTALL_BIN}"
    sudo cp "${AGENT_DIR}/chat.py" "${AGENT_BIN}"
    sudo chmod +x "${INSTALL_BIN}" "${AGENT_BIN}"
    ok "Agent executables installed"
}

# Restart systemd services if they are present and active
restart_services() {
    if command -v systemctl >/dev/null 2>&1; then
        info "Restarting AIOS agent services if present..."
        for service in aios-agent aios; do
            if systemctl list-unit-files "${service}.service" >/dev/null 2>&1; then
                sudo systemctl restart "${service}.service" && ok "Restarted ${service}.service"
            else
                warn "${service}.service not found; skipping"
            fi
        done
    else
        warn "systemctl not available; skipping service restart"
    fi
}

main() {
    info "Starting AIOS agent update..."

    require_git
    update_repo
    copy_agent_files
    restart_services

    ok "AIOS agent update complete"
}

main "$@"
