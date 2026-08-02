#!/usr/bin/env bash
# build-iso.sh - Complete AIOS ISO build flow on the VPS/build host.
# This script rebuilds the AIOS live ISO by extracting, patching, and
# repacking the squashfs image, then regenerating the bootable ISO.

set -euo pipefail

# Absolute paths used throughout the script
ISO_BACKUP="${HOME}/lfs-rw-sven.iso"
AIOS_DIR="${HOME}/aios"
SQUASHFS="${AIOS_DIR}/live/lfs.squashfs"
SRE_AGENT_DIR="${HOME}/sre-agent"
SQ_FINAL_DIR="/tmp/sq-final"
SQUASHFS_ROOT="${SQ_FINAL_DIR}/squashfs-root"
FINAL_ISO="${HOME}/aios.iso"

# Print helpers
info() { printf '\033[1;34m[INFO]\033[0m %s\n' "$*"; }
ok()   { printf '\033[1;32m[OK]\033[0m   %s\n' "$*"; }
warn() { printf '\033[1;33m[WARN]\033[0m %s\n' "$*" >&2; }
err()  { printf '\033[1;31m[ERR]\033[0m  %s\n' "$*" >&2; }

# Ensure required tools are available
check_prereqs() {
    info "Checking prerequisites..."
    for tool in unsquashfs mksquashfs grub-mkrescue mount umount; do
        if ! command -v "${tool}" >/dev/null 2>&1; then
            err "Required tool '${tool}' is not installed or not in PATH"
            exit 1
        fi
    done
    ok "All required tools found"
}

# Restore squashfs from backup ISO if current one looks corrupted
restore_squashfs_if_needed() {
    if [[ ! -f "${SQUASHFS}" ]]; then
        warn "Squashfs not found at ${SQUASHFS}; will restore from backup ISO"
    elif [[ "$(stat -c%s "${SQUASHFS}" 2>/dev/null || echo 0)" -lt 104857600 ]]; then
        warn "Squashfs is smaller than 100MB, likely corrupt; restoring from backup ISO"
    else
        ok "Squashfs looks healthy"
        return 0
    fi

    if [[ ! -f "${ISO_BACKUP}" ]]; then
        err "Backup ISO not found at ${ISO_BACKUP}; cannot restore squashfs"
        exit 1
    fi

    info "Restoring squashfs from backup ISO..."
    sudo mount -o loop,ro "${ISO_BACKUP}" /mnt/lfs
    sudo cp /mnt/lfs/live/lfs.squashfs "${SQUASHFS}"
    sudo umount /mnt/lfs
    ok "Squashfs restored"
}

# Extract the squashfs image to a working directory
extract_squashfs() {
    info "Extracting squashfs to ${SQ_FINAL_DIR}..."
    sudo rm -rf "${SQ_FINAL_DIR}"
    mkdir -p "${SQ_FINAL_DIR}"
    cd "${SQ_FINAL_DIR}"
    sudo unsquashfs "${SQUASHFS}"
    ok "Squashfs extracted"
}

# Deploy the AIOS agent files into the squashfs root
deploy_agent() {
    info "Deploying AIOS agent into squashfs root..."
    if [[ ! -d "${SRE_AGENT_DIR}" ]]; then
        err "SRE agent directory not found at ${SRE_AGENT_DIR}"
        exit 1
    fi

    sudo mkdir -p "${SQUASHFS_ROOT}/usr/local/bin/aios-agent"
    sudo cp "${SRE_AGENT_DIR}/setup.py" "${SQUASHFS_ROOT}/usr/local/bin/aios-agent/setup.py"
    sudo cp "${SRE_AGENT_DIR}/aios-install" "${SQUASHFS_ROOT}/usr/local/bin/aios-install"
    ok "Agent files deployed"
}

# Repack the squashfs root using zstd compression (xz is unsupported by the kernel)
repack_squashfs() {
    info "Repacking squashfs with zstd compression..."
    cd "${SQ_FINAL_DIR}"
    sudo rm -f "${SQUASHFS}"
    sudo mksquashfs "${SQUASHFS_ROOT}" "${SQUASHFS}" -comp zstd -b 256K -no-xattrs
    sudo chown "${USER}:${USER}" "${SQUASHFS}"

    info "Verifying compression method..."
    if unsquashfs -s "${SQUASHFS}" | grep -q Compression; then
        ok "Compression verified"
    else
        err "Failed to verify squashfs compression"
        exit 1
    fi
    ok "Squashfs repacked"
}

# Regenerate the bootable ISO from the AIOS directory
regenerate_iso() {
    info "Regenerating ISO at ${FINAL_ISO}..."
    sudo grub-mkrescue -o "${FINAL_ISO}" "${AIOS_DIR}"
    ok "ISO regenerated: ${FINAL_ISO}"
}

main() {
    info "Starting AIOS ISO build flow..."

    check_prereqs
    restore_squashfs_if_needed
    extract_squashfs
    deploy_agent
    repack_squashfs
    regenerate_iso

    ok "AIOS ISO build complete: ${FINAL_ISO}"
}

main "$@"
