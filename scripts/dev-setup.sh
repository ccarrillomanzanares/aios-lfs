#!/usr/bin/env bash
# dev-setup.sh - Prepare an installed AIOS system as a development environment.
# Run this script inside the installed AIOS environment.

set -euo pipefail

# Configuration
GIT_USER_NAME="${GIT_USER_NAME:-AIOS Developer}"
GIT_USER_EMAIL="${GIT_USER_EMAIL:-dev@aios.local}"
DEV_DIR="${HOME}/dev"
AGENT_REPO="https://github.com/ccarrillomanzanares/aios-agent.git"
LFS_REPO="https://github.com/ccarrillomanzanares/aios-lfs.git"

# Print helpers
info() { printf '\033[1;34m[INFO]\033[0m %s\n' "$*"; }
ok()   { printf '\033[1;32m[OK]\033[0m   %s\n' "$*"; }
warn() { printf '\033[1;33m[WARN]\033[0m %s\n' "$*" >&2; }
err()  { printf '\033[1;31m[ERR]\033[0m  %s\n' "$*" >&2; }

# Install git if it is missing; try the sven helper when available
install_git_if_missing() {
    if command -v git >/dev/null 2>&1; then
        ok "git is already installed"
        return 0
    fi

    info "git not found; attempting to install..."
    if command -v sven >/dev/null 2>&1; then
        sudo sven install git
    elif command -v apt >/dev/null 2>&1; then
        sudo apt update && sudo apt install -y git
    elif command -v pacman >/dev/null 2>&1; then
        sudo pacman -Sy --noconfirm git
    else
        err "No supported package manager found; install git manually"
        exit 1
    fi

    if ! command -v git >/dev/null 2>&1; then
        err "git installation failed"
        exit 1
    fi
    ok "git installed successfully"
}

# Configure git user name and email
configure_git() {
    info "Configuring git identity..."
    git config --global user.name "${GIT_USER_NAME}"
    git config --global user.email "${GIT_USER_EMAIL}"
    ok "Git identity configured as ${GIT_USER_NAME} <${GIT_USER_EMAIL}>"
}

# Generate SSH keys if none exist
generate_ssh_keys() {
    if [[ -f "${HOME}/.ssh/id_ed25519" ]] || [[ -f "${HOME}/.ssh/id_rsa" ]]; then
        ok "SSH key already exists"
        return 0
    fi

    info "Generating a new SSH key pair..."
    mkdir -p "${HOME}/.ssh"
    ssh-keygen -t ed25519 -C "${GIT_USER_EMAIL}" -f "${HOME}/.ssh/id_ed25519" -N ""
    ok "SSH key generated at ${HOME}/.ssh/id_ed25519"
}

# Clone the main AIOS repositories into the development directory
clone_repos() {
    info "Preparing development directory ${DEV_DIR}..."
    mkdir -p "${DEV_DIR}"

    for repo in "${AGENT_REPO}" "${LFS_REPO}"; do
        local name
        name="$(basename "${repo}" .git)"
        local dest="${DEV_DIR}/${name}"

        if [[ -d "${dest}/.git" ]]; then
            warn "Repository ${name} already cloned at ${dest}; pulling latest changes"
            cd "${dest}"
            git pull
        else
            info "Cloning ${repo} into ${dest}..."
            rm -rf "${dest}"
            git clone "${repo}" "${dest}"
        fi
        ok "Repository ${name} ready at ${dest}"
    done
}

main() {
    info "Starting AIOS development environment setup..."

    install_git_if_missing
    configure_git
    generate_ssh_keys
    clone_repos

    ok "Development environment setup complete"
    info "Next steps:"
    info "  1. Add the following SSH public key to your GitHub account:"
    info "     ${HOME}/.ssh/id_ed25519.pub"
    info "  2. Use the repositories under ${DEV_DIR} for development"
}

main "$@"
