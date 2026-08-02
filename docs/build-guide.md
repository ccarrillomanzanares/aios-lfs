# Guía de construcción: ISO AIOS LFS

## Requisitos

- VPS Linux (Ubuntu 24.04+) con ~20 GB libres
- ISO base LFS 13.0-systemd
- Paquetes: xorriso, grub-pc-bin, mtools
- Kernel linux-6.18.10
- Python 3.11+, git, cmake, make, gcc

## Compilación dentro del chroot (recomendado)

Siempre compilar dentro del chroot `/lfs-rw/`, no copiar binarios del host VPS.

### llama.cpp

```bash
# Montar entorno chroot
sudo mount --bind /dev /lfs-rw/dev
sudo mount --bind /proc /lfs-rw/proc
sudo mount --bind /sys /lfs-rw/sys

# Instalar cmake si no está
sudo chroot /lfs-rw sven install cmake

# Clonar y compilar
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

### Modelo Qwen3-8B

```bash
sudo mkdir -p /lfs-rw/usr/local/share/aios/models
sudo chroot /lfs-rw /bin/bash -lc "
  pip3 install huggingface-hub
  python3 -c \"from huggingface_hub import hf_hub_download; hf_hub_download(bartowski/Qwen_Qwen3-8B-GGUF, Qwen_Qwen3-8B-Q4_K_M.gguf, local_dir=/usr/local/share/aios/models/)\"
"
```

## Generación de la ISO

```bash
# 1. Preparar
sudo rm -rf /lfs-rw/tmp/*
sudo rm -f /tmp/iso/live/lfs.squashfs

# 2. Squashfs
sudo mksquashfs /lfs-rw /tmp/iso/live/lfs.squashfs -comp zstd -b 128K

# 3. ISO (soporte archivos >4 GB con -iso-level 3)
sudo xorriso -as mkisofs -iso-level 3 \
  -eltorito-boot boot/grub/i386-pc/eltorito.img \
  -no-emul-boot -boot-load-size 4 -boot-info-table \
  --grub2-boot-info -eltorito-catalog boot/grub/boot.cat \
  -volid "AIOS_LFS" \
  -o /home/ccmai/lfs-rw-sven.iso /tmp/iso
```

## Notas importantes

1. **Compilar en chroot**: no copiar binarios del host VPS. Las librerías del host y del chroot pueden diferir.
2. **iso-level 3**: necesario porque el modelo GGUF (4.7 GB) supera el límite de 4 GB del ISO 9660.
3. **Servicios deshabilitados**: aios-llama.service y sshd.service arrancan bajo demanda, no al boot.
4. **Backup**: mantener backup de /lfs-rw antes de cambios grandes.

## Fixes aplicados (jul 2026)

### chat.py
- Error wrapper robusto: maneja EOFError sin excepción anidada
- Permisos: `/usr/local/bin/aios-agent/` debe ser `aios:wheel` para que chat.py pueda escribir `data/`
- `data/` se crea previamente en el build

### Servicios
- `aios-llama.service`: deshabilitado en boot, lo activa setup.py al elegir local/híbrido
- `sshd.service`: deshabilitado, arranque manual
- `ssh-host-keys.service`: eliminado

### ISO
- Sin modelo incluido (1.4 GB). Modo cloud funciona directo.
- Modo local requiere descargar modelo desde HuggingFace.

## Configuración PAM y sudo (BLFS estándar)

Tras instalar Linux-PAM desde Sven, configurar los archivos PAM según BLFS:

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

## sudo NOPASSWD para ISO live

```bash
echo "%wheel ALL=(ALL:ALL) NOPASSWD: ALL" > /etc/sudoers.d/wheel-nopasswd
```

## nsswitch.conf (LFS 13.0-systemd estándar)

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
