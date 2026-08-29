# Build Guide: AIOS LFS ISO

## Requirements

- Linux VPS (Ubuntu 24.04+) with ~20 GB free
- Base ISO LFS 13.0-systemd
- Packages: xorriso, grub-pc-bin, mtools
- Kernel linux-6.18.10
- Python 3.11+, git, cmake, make, gcc

## Compilation inside the chroot (recommended)

Always compile inside the chroot `/lfs-rw/`, never copy binaries from the host VPS.

### llama.cpp

```bash
# Mount chroot environment
sudo mount --bind /dev /lfs-rw/dev
sudo mount --bind /proc /lfs-rw/proc
sudo mount --bind /sys /lfs-rw/sys

# Install cmake if missing
sudo chroot /lfs-rw sven install cmake

# Clone and compile
sudo chroot /lfs-rw /bin/bash -lc "
  git clone https://github.com/ggml-org/llama.cpp /home/aios/llama.cpp
  cd /home/aios/llama.cpp
  mkdir build && cd build
  cmake .. -DLLAMA_CUDA=OFF -DLLAMA_METAL=OFF
  make -j\$(nproc) llama-server
  cp build/bin/llama-server /usr/local/bin/
  cp build/bin/lib*.so* /usr/local/lib/llama/
  echo /usr/local/lib/llama > /etc/ld.so.conf.d/llama.conf
  ldconfig
"
```

### AIOS Agent

```bash
sudo chroot /lfs-rw git clone https://github.com/ccarrillomanzanares/aios-agent /usr/local/bin/aios-agent
```

### Qwen3-8B Model

```bash
sudo mkdir -p /lfs-rw/usr/local/share/aios/models
sudo chroot /lfs-rw /bin/bash -lc "
  pip3 install huggingface-hub
  python3 -c \"from huggingface_hub import hf_hub_download; hf_hub_download(bartowski/Qwen_Qwen3-8B-GGUF, Qwen_Qwen3-8B-Q4_K_M.gguf, local_dir=/usr/local/share/aios/models/)\"
"
```

## ISO Generation

```bash
# 1. Prepare
sudo rm -rf /lfs-rw/tmp/*
sudo rm -f /tmp/iso/live/lfs.squashfs

# 2. Squashfs
sudo mksquashfs /lfs-rw /tmp/iso/live/lfs.squashfs -comp zstd -b 128K

# 3. ISO (support for files >4 GB with -iso-level 3)
sudo xorriso -as mkisofs -iso-level 3 \
  -eltorito-boot boot/grub/i386-pc/eltorito.img \
  -no-emul-boot -boot-load-size 4 -boot-info-table \
  --grub2-boot-info -eltorito-catalog boot/grub/boot.cat \
  -volid "AIOS_LFS" \
  -o /home/ccmai/lfs-rw-sven.iso /tmp/iso
```

## Important notes

1. **Compile in chroot**: do not copy binaries from the host VPS. Host and chroot libraries may differ.
2. **iso-level 3**: required because the GGUF model (4.7 GB) exceeds the 4 GB ISO 9660 limit.
3. **Disabled services**: aios-llama.service and sshd.service start on demand, not at boot.
4. **Backup**: keep a backup of /lfs-rw before big changes.

## Fixes applied (Jul 2026)

### chat.py
- Robust error wrapper: handles EOFError without a nested exception
- Permissions: `/usr/local/bin/aios-agent/` must be `aios:wheel` so chat.py can write `data/`
- `data/` is created beforehand during build

### Services
- `aios-llama.service`: disabled at boot, setup.py enables it when local/hybrid is chosen
- `sshd.service`: disabled, manual start
- `ssh-host-keys.service`: removed

### ISO
- No model included (1.4 GB). Cloud mode works out of the box.
- Local mode requires downloading the model from HuggingFace.

## PAM and sudo configuration (standard BLFS)

After installing Linux-PAM from Sven, configure the PAM files according to BLFS:

```bash
# /etc/pam.d/system-auth
echo "auth required pam_unix.so" > /etc/pam.d/system-auth

# /etc/pam.d/system-account
echo "account required pam_unix.so" > /etc/pam.d/system-account

# /etc/pam.d/system-session
echo "session required pam_unix.so" > /etc/pam.d/system-session

# /etc/pam.d/system-password
echo "password required pam_unix.so yescrypt shadow try_first_pass" > /etc/pam.d/system-password

# /etc/pam.d/sudo
cat > /etc/pam.d/sudo << "EOF"
auth      include     system-auth
account   include     system-account
session   required    pam_env.so
session   include     system-session
EOF
```

## sudo NOPASSWD for live ISO

```bash
echo "%wheel ALL=(ALL:ALL) NOPASSWD: ALL" > /etc/sudoers.d/wheel-nopasswd
```

## nsswitch.conf (standard LFS 13.0-systemd)

```bash
cat > /etc/nsswitch.conf << "EOF"
# Begin /etc/nsswitch.conf
passwd: files systemd
group: files systemd
shadow: files systemd
hosts: mymachines resolve [!UNAVAIL=return] files myhostname dns
networks: files
protocols: files
services: files
ethers: files
rpc: files
# End /etc/nsswitch.conf
EOF
```
