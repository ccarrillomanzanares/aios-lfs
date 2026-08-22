# AIOS LFS v11

ISO live de **Linux From Scratch 13.0-systemd** con el agente **AIOS** (wargame/CTF). Diseñada para arrancar en modo silencioso desde CD/USB, ofrecer una sesión gráfica mínima (i3 + xterm) y permitir instalar el sistema a disco duro conservando el mismo look de boot.

- **Versión**: v11 (agosto 2026)
- **Kernel**: 6.18.10-lfs #5 (kernel de distro: wifi, DRM, NVMe, ALSA)
- **Base**: LFS 13.0-systemd
- **Init**: systemd
- **Entorno gráfico**: X11 + i3 + xterm
- **Licencia**: MIT

---

## Descripción

AIOS LFS es una distribución live minimalista construida desde cero siguiendo el libro LFS 13.0-systemd. El objetivo es tener un entorno autocontenido, ligero y con estética wargame/CTF para ejecutar el agente AIOS.

La v10 corrige todos los problemas detectados durante el verano de 2026: colgados del menú de setup por DNS sin timeout, bucles de Plymouth que bloqueaban el login, mojibake de cajas Unicode en xterm, y la diferencia visual entre arranque live e instalado.

---

## Características

- Sistema live con OverlayFS totalmente escribible en RAM.
- Arranque silencioso: fondo negro, sin mensajes de kernel/systemd, banner AIOS mostrado desde initrd.
- Kernel compilado con gcc del host VPS 15.2.0, verificado en `/proc/version`.
- Menú del setup centrado en pantalla (`print_box` con padding horizontal y vertical).
- Validación de API key en hilo con timeout de 12 s (corrige bloqueo por resolución DNS).
- Flujo `setup.py` → `aios` automático en la misma ventana xterm.
- Instalador a disco con opción de cambio de passwords de root y aios.
- **Kernel de distro (#5)**: drivers wifi (iwlwifi, rtlwifi/rtl8723be, rtw88/89, ath9k/10k/11k, brcmfmac), DRM (i915/amdgpu/nouveau), NVMe, UAS, I2C_HID_ACPI, ethernet (r8169/e1000e/igb) y ALSA HDA + USB, con firmware linux-firmware integrado.
- **Opción 5 WIFI SETUP** en el setup: escaneo de redes, wpa_supplicant, verificación de internet (urllib) y persistencia al arranque vía systemd-networkd (DHCP en wl*).
- **Sistema operativo completo en hardware real** (HP Notebook AMD + Realtek): wifi con IP al arranque, touchpad, audio y resolución nativa (verificado 4 Ago 2026).
- Firefox incluido para obtener la API key del proveedor elegido.
- Cliente AIOS minimalista wargame con estilo Matrix en TTY/terminal.
- `nokaslr` eliminado en live e instalador por seguridad.
- Plymouth descartado definitivamente.

---

## Requisitos

| Entorno | Requisitos |
|---|---|
| VirtualBox recomendado | 2 vCPU, 4 GB RAM, 20 GB disco para instalar, controlador gráfico VBoxVGA o VMSVGA |
| Hardware real | x86_64, BIOS/UEFI con soporte para arranque desde USB/CD |
| Sin red | Funciona el modo **LOCAL** de AIOS si se descarga un modelo GGUF previamente |
| Con red | Permite usar AIOS en modo cloud sin descargar el LLM |

---

## Usuarios por defecto

| Usuario | Password | Notas |
|---|---|---|
| `root` | `root` | Administrador del sistema |
| `aios` | `aios` | Usuario para ejecutar el agente |

> Tras instalar a disco, `aios-install v1.1.1` permite cambiar ambas passwords. Si el usuario elige no cambiarlas, el resumen final muestra `Login: aios/aios or root/root`; si se cambian, se omite el aviso por seguridad.

---

## Instalación a disco

1. Arrancar la ISO live.
2. Iniciar sesión como `aios`/`aios` o `root`/`root`.
3. Ejecutar `setup.py` y elegir **`4) INSTALL TO DISK`** (o lanzar directamente `/usr/local/bin/aios-install`).
4. Seguir las instrucciones del instalador.
5. Al finalizar, `aios-install` pregunta:

   ```text
   ¿Cambiar la password de root? [s/N]:
   ¿Cambiar la password de aios? [s/N]:
   ```

   Se usa `getpass` y se valida un mínimo de 8 caracteres. El cambio se aplica vía `chpasswd` dentro del chroot del disco recién instalado (stdin).

6. Confirmar reinicio (`reboot`).

El sistema instalado arranca exactamente igual que el live: fondo negro sin mensajes, banner AIOS y login en `tty1`.

---

## Componentes

| Componente | Ruta en live | Ruta tras instalar a disco |
|---|---|---|
| Kernel | `/boot/vmlinuz-6.18.10-lfs` (también en squashfs `boot/vmlinuz-6.18.10-lfs`) | `/boot/vmlinuz` |
| Initrd | `/boot/initrd.img` (también en squashfs `boot/initrd.img`) | `/boot/initrd.img` |
| Sistema raíz | `live/lfs.squashfs` + OverlayFS en RAM | Partición real con ext4 |
| Repositorio agente | `/usr/local/bin/aios-agent/` | `/usr/local/bin/aios-agent/` |
| Cliente AIOS | `/usr/local/bin/aios` | `/usr/local/bin/aios` |
| Instalador | `/usr/local/bin/aios-install` | no aplica |
| Wrapper setup | `/usr/local/bin/setup.py` o `setup.py` en PATH | no aplica |
| Config AIOS | `~/.aios/config.yaml` y `~/.aios/.env` | `~/.aios/config.yaml` y `~/.aios/.env` |
| Servidor llama.cpp | `/usr/local/bin/llama-server` | `/usr/local/bin/llama-server` |

### Novedad v10: kernel e initrd dentro del squashfs

El squashfs ahora incluye:

```text
boot/vmlinuz-6.18.10-lfs
boot/initrd.img
```

Esto permite que el instalador los copie al disco sin necesidad de extraerlos de la ISO en tiempo de instalación.

---

## Secuencia de arranque

1. GRUB carga `/boot/vmlinuz` + `/boot/initrd.img`.
2. El kernel inicia con `quiet loglevel=3 systemd.show_status=false vt.global_cursor_default=0`.
3. El initrd:
   - Monta `proc`, `sysfs`, `devtmpfs`, `tmpfs`.
   - Limpia la pantalla inmediatamente (`clear` + ocultar cursor).
   - Muestra el banner AIOS.
   - Localiza la ISO live, monta el squashfs, crea el overlay (`lowerdir` + `upperdir` + `workdir`) y ejecuta `switch_root` hacia `/sbin/init`.
4. systemd arranca en `multi-user.target`.
5. `agetty` abre `tty1`.
6. Al hacer login en `tty1`, se ejecuta el script de sesión (`scripts/aios-session`), que:
   - Lanza `setup.py` si no existe `~/.aios/config.yaml`.
   - Tras la configuración, inicia X11 (`startx`) → i3 → xterm con el agente.

---

## Silent boot y banner AIOS

### GRUB live

```text
set default=0
set timeout=0
menuentry "AIOS LFS v10" {
    linux /boot/vmlinuz quiet loglevel=3 systemd.show_status=false vt.global_cursor_default=0
    initrd /boot/initrd.img
}
```

> No se usa `nokaslr` en ningún sitio.

### Initrd

El initrd realiza `clear` + `ocultar cursor` antes de buscar el medio live:

```sh
/bin/busybox printf "\033[2J\033[H" > /dev/tty0
/bin/busybox printf "\033[?25l" > /dev/tty0
```

Luego imprime el banner AIOS (texto ASCII/Unicode) y monta el sistema raíz.

### Instalado a disco

El instalador genera un nuevo initrd (`build_disk_initrd`) que:

- Conserva las mismas rutinas de clear + cursor + banner.
- Reemplaza el bucle de búsqueda de ISO por un `mount` directo de la partición raíz real.
- Finaliza con `switch_root /sbin/init`.

La configuración de GRUB del disco usa `timeout=0` y los mismos parámetros silenciosos del live, apuntando `root=` a la partición real.

---

## Servicios systemd

```text
/usr/lib/systemd/system/
├── aios-llama.service    # llama-server (disabled at boot)
├── aios-agent.service    # chat.py interactivo (disabled, lo lanza i3)
└── getty@tty1.service    # login en tty1
```

- `aios-llama.service` se habilita/arranca solo cuando setup.py selecciona modo `local` o `hybrid`.
- `sshd` está deshabilitado por defecto en la ISO.
- No hay servicio de Plymouth.

---

## SSH

`sshd` no arranca por defecto. Para activarlo manualmente en live:

```bash
/etc/rc.d/init.d/sshd start
```

Las host keys se regeneran automáticamente al primer uso. El servicio está controlado por el script SysV tradicional de LFS, no por systemd.

---

## Firefox

Firefox ESR se incluye en `/opt/firefox/`, con enlace en `/usr/local/bin/firefox`. Se usa para que el usuario pueda obtener la API key de su proveedor (OpenAI, Anthropic, DeepSeek, etc.) sin depender de otro equipo. Las dependencias GTK3 necesarias se instalan manualmente desde `archive.archlinux.org` cuando los mirrors actuales fallan por checksums corruptos.

Para lanzarlo desde i3:

```text
exec --no-startup-id /usr/local/bin/firefox about:blank
```

---

## Configuración de librerías ldconfig

Tras instalar paquetes extra (Firefox, GTK3, llama.cpp, etc.), ejecutar:

```bash
ldconfig
```

Además, crear o actualizar `/etc/ld.so.conf.d/` según sea necesario:

```text
/usr/local/lib
/usr/local/lib/llama
/opt/firefox
```

---

## Generación de la ISO

Resumen de pasos en el host de build:

```bash
# 1. Preparar directorio ISO
mkdir -p /tmp/iso/{boot/grub,live}

# 2. Copiar kernel e initrd
sudo cp ~/aios/boot/vmlinuz /tmp/iso/boot/vmlinuz
sudo cp ~/aios/boot/initrd.img /tmp/iso/boot/initrd.img

# 3. GRUB
sudo tee /tmp/iso/boot/grub/grub.cfg << 'GRUBEOF'
set default=0
set timeout=0
menuentry "AIOS LFS v10" {
    linux /boot/vmlinuz quiet loglevel=3 systemd.show_status=false vt.global_cursor_default=0
    initrd /boot/initrd.img
}
GRUBEOF

# 4. Squashfs (incluye kernel e initrd copiados dentro)
sudo mksquashfs /lfs-rw /tmp/iso/live/lfs.squashfs -comp zstd -b 128K -noappend

# 5. ISO
sudo grub-mkrescue -o aios-lfs-v10.iso /tmp/iso
```

**Si la ISO supera 4 GB**, añadir `-iso-level 3`.

---

## Fix de GRUB en instalación a disco

El instalador `aios-install` genera automáticamente `grub.cfg` para el disco con:

```text
set default=0
set timeout=0
menuentry "AIOS LFS v10" {
    linux /boot/vmlinuz root=/dev/sda2 quiet loglevel=3 systemd.show_status=false vt.global_cursor_default=0
    initrd /boot/initrd.img
}
```

- `root=` apunta a la partición real seleccionada durante la instalación.
- No se usa `nokaslr`.
- El initrd del disco es una variante del live generada por `build_disk_initrd`.

---

## Repositorio del agente

El agente AIOS se despliega en `/usr/local/bin/aios-agent/` dentro del squashfs. Sus partes principales son:

| Archivo | Función |
|---|---|
| `setup.py` | Wizard de configuración del proveedor/modelo |
| `chat.py` | Cliente interactivo con manejo robusto de EOF/errores |
| `agent.py` | Bucle de function calling |
| `scripts/aios-session` | Arranque de sesión gráfica en la ISO |
| `scripts/aios-install` | Instalador a disco v1.1.1 |

### Cambios v10 en setup.py

- `validate_api_key` se ejecuta en un hilo daemon con `join(timeout=12)`; dentro del hilo, `urlopen(..., timeout=5)` limita la espera por la API. Esto corrige el bloqueo por `getaddrinfo` sin límite (Ctrl+C tampoco respondía por `SA_RESTART`).
- La API key se guarda en `~/.aios/.env` (no en `config.yaml`).
- Al final del script se usa `os._exit(0)` para evitar que hilos residuales mantengan el proceso abierto.
- Menú LOCAL actualizado:
  - Modelo por defecto: `Qwen3-8B-Instruct`.
  - Texto: `1) LOCAL (no internet) / Simple tasks`.
  - Se eliminó la frase `Works 100% offline`.
- Los menús se pintan centrados usando `os.get_terminal_size()` con padding horizontal y vertical.

### Flujo setup → agente v10

Tras completar la configuración, setup.py ejecuta `aios` automáticamente en la misma ventana:

```bash
xterm -fa 'Adwaita Mono' -fs 11 -bg black -fg green -cr green \
  -e "cd /usr/local/bin/aios-agent && python3 setup.py && [ -f \$HOME/.aios/config.yaml ] && aios || exec bash"
```

- No se usa `-hold`: evita que parezca que el menú se cuelga tras terminar.
- Si el setup se cancela, se abre un shell bash interactivo.

### xterm en i3 v10

```text
xterm -fa 'Adwaita Mono' -fs 11 -bg black -fg green -cr green ...
```

La fuente `Adwaita Mono` contiene los glifos de línea doble (`╔═╗`) que antes se mostraban como mojibake.

---

## Kernel #4

Configuración real del kernel 6.18.10-lfs #4:

```text
CONFIG_X86_VERBOSE_BOOTUP=n
CONFIG_OVERLAY_FS=y
CONFIG_FB_VESA=y
```

Sin:

```text
# CONFIG_DRM_VMWGFX is not set
# CONFIG_DRM_VBOXVIDEO is not set
# CONFIG_DRM_FBDEV_EMULATION is not set
```

- Compilado con gcc del host VPS 15.2.0 (verificado en `/proc/version` de la VM).
- `make olddefconfig` y compilación normal; NO se usa `LD=/mnt/sq/usr/bin/ld` (el ld LFS necesita `libbfd` que no está disponible fuera del chroot).

---

## Locale

El sistema live/instalado usa:

```text
LANG=C.UTF-8
LC_ALL=C.UTF-8
```

en `/etc/locale.conf`. `es_ES.UTF-8` no está generado en el sistema base; si se define sin generarlo, glibc cae a `C` y xterm interpreta los caracteres de caja en Latin-1, produciendo mojibake (``). La solución adoptada es fijar `C.UTF-8`, que está disponible y soporta Unicode correctamente.

Si se desea español completo, generar el locale antes de fijarlo:

```bash
localedef -i es_ES -f UTF-8 es_ES.UTF-8
```

---

## Plymouth descartado definitivamente

Se probó Plymouth con múltiples configuraciones (VBoxVGA+vesafb, VMSVGA+vmwgfx, gfxpayload). En todos los casos el resultado fue pantalla negra o logo no visible. La causa raíz en v10 es definitiva:

- El kernel #4 no incluye `vmwgfx`, `vboxvideo` ni `fbdev-emulation`.
- VirtualBox con VMSVGA no ofrece VBE clásico.
- `vesafb` no puede crear `/dev/fb0` ni `/dev/dri`.
- `plymouthd` no encuentra renderer, espera el timeout de systemd, y al morir retiene el VT bloqueando el login.

**Alternativa adoptada**: banner ASCII/Unicode mostrado directamente desde el initrd, con fondo negro y cursor oculto.

---

## Fix v11 - panic en arranque desde disco (2 Ago 2026)

### Síntoma

Después de instalar AIOS LFS a disco duro, el sistema mostraba un **kernel panic** al arrancar:

```
Attempted to kill init! exit code=0x7f00
```

(`0x7f00` = 127). Ocurría tras el logo AIOS, antes de llegar al login.

### Causa raíz

El panic venía de tres fallos acumulados en `build_disk_initrd`, la función de `aios-install` que transforma el initrd live para arranque desde disco:

1. **Escape octal `\1` → SOH en el init generado.** El patrón `sed` usado con `tail` estaba escrito en Python con un solo backslash: `'s/.*root=\([^ ]*\).*/\1/p'`. Python interpreta `\1` como el carácter de control SOH (`0x01`), que se escribía literalmente en el script `init` generado. Al ejecutarse, `sed` devolvía un dispositivo root inexistente, y `mount -t ext4` fallaba.
2. **Fallback a `/bin/sh` inexistente.** Cuando el `mount` fallaba, el initrd ejecutaba `exec /bin/sh`, pero el initrd transformado no incluye `/bin/sh`: solo contiene `init` y `bin/busybox`, sin symlinks de applets. El `exec` devolvía 127, el init moría y el kernel lanzaba el panic.
3. **Sin espera al dispositivo root.** El dispositivo de root podía no estar listo en el momento en que el init intentaba montarlo, haciendo el fallo intermitente.

### Solución (aios-install v1.1.2)

- Se corrigió el patrón `sed`/`tail` con **doble backslash** (`\\(` y `\\1`) para que el `init` generado contenga `\(` y `\1` correctos, y `sed` extraiga el dispositivo root real.
- Se añadió un **bucle de espera de hasta 30 segundos** hasta que aparezca el dispositivo root en `/dev`.
- Se cambió el fallback a **`exec /bin/busybox sh`**, que sí está disponible en el initrd.
- Se usa **`exec /bin/busybox switch_root /root /sbin/init`** para pasar el control al sistema instalado.
- Se incluyó **`/bin/busybox` estático (2.1 MB, extraído del initrd)** en el squashfs del sistema live, porque `build_disk_initrd` lo necesita y el sistema live no lo tenía.

### Verificación

Reinstalando AIOS LFS a disco, el arranque desde disco funciona correctamente: aparece el logo AIOS y el sistema llega al prompt de login.

> **Nota:** todavía se muestra el mensaje de GRUB `'Welcome to GRUB!'`. Queda pendiente pulirlo en el futuro usando `timeout_style=hidden` y `quiet_boot=1`.

## Hito v12 - AIOS en hardware físico (2 Ago 2026)

### Síntoma

Al arrancar la ISO de AIOS LFS desde USB en un portátil real, el sistema se detenía con un kernel panic porque el init del initrd live no encontraba el dispositivo de arranque.

### Causas

- El script init no esperaba a que el kernel enumerara los dispositivos de bloque, por lo que el medio USB aún no existía cuando se buscaba el sistema live.
- La lista de dispositivos candidatos era demasiado corta y no incluía controladores modernos como NVMe ni MMC.
- Cuando se usaba Rufus en modo ISO, la partición USB se formateaba como FAT32, mientras que el init buscaba un sistema de archivos iso9660, provocando fallo silencioso.

### Solución

- Se añadió un bucle de espera de hasta 30 segundos en el init del initrd live, comprobando `[ -b <dispositivo> ]` y saliendo con `break 2` al encontrarlo.
- Se amplió la lista de dispositivos de búsqueda: `sdc`, `sdd`, discos `hd*`, `nvme*` y `mmcblk*`.
- Se sustituyó el kernel panic por un mensaje legible: `AIOS: boot media not found`, seguido de una shell de emergencia busybox para diagnóstico.
- Se documentó que, mientras tanto, la ISO debe grabarse con Rufus en modo DD para que el init encuentre un volumen iso9660.

### Verificación

- ISO escrita en USB con Rufus en modo DD.
- Arranque live USB correcto en portátil físico con SSD SATA.
- Instalación de AIOS LFS al disco SSD completada.
- Reinicio y arranque desde disco con banner AIOS y prompt de login funcionando.

### Pendientes (histórico — resueltos con el kernel #7)
- ~~Soportar el modo ISO de Rufus (FAT32)~~ → resuelto: Rufus en modo DD es el método documentado
- ~~Preparar el kernel #5 con controladores NVMe y UAS~~ → resuelto con el kernel #7 (config Ubuntu 6.18.10, ver 7 Ago)

## 6 Ago 2026 — LLM local en portátil: SIGILL (RESUELTO el 8 Ago)

**Síntoma histórico**: `aios-llama.service` fallaba en bucle `status=4/ILL` (SIGILL core dump) en el HP AMD A8-7410 (sin AVX2/FMA3/AVX-512). Causas descartadas en su momento: GGUF corrupto, ISA de ggml (builds AVX1+F16C), mezcla glibc.

**Resolución (8 Ago)**: el SIGILL se resolvió con la alineación de glibc (única 2.44 de sven, `/lib64` → `/usr/lib`) + el paquete sven `llama-cpp` (b10221, x86-64-baseline). Verificado: el LLM carga y genera **~1.2 tok/s** en el A8. Detalle de la investigación completa en la skill `aios-iso-build`.

## 6 Ago 2026 — Agente AIOS en VPS con Qwen local (funciona)

- Server local: `nohup env LD_LIBRARY_PATH=~/llama.cpp/build/bin ~/llama.cpp/build/bin/llama-server -m /home/ccmai/models/Qwen_Qwen3-8B-Q4_K_M.gguf -c 65536 -t 14 --host 127.0.0.1 --port 8083` + `~/.aios/config.yaml` con `mode: local` → `cd ~/sre-agent && python3 chat.py`.
- El "cuelgue" del chat.py era el **historial de sesión**: `~/sre-agent/data/session_local.json` (20 KB → prompt ~6.2K tokens → ~2 min de prompt processing a ~52 tok/s). `rm session_local.json` → respuestas en 30-60 s.
- El build del VPS es **SSE-only** (cache: `GGML_AVX=OFF`) → 17 tok/s gen / 31-57 tok/s prompt es el piso SSE; con `GGML_NATIVE=ON` en el EPYC ~2x (pendiente decisión; solo para el build local, nunca para distribuir).
- El `import yaml` lento fue transitorio (contención CPU con la carga del modelo).

## 7 Ago 2026 — Saneamiento: kernel #7 (config Ubuntu 6.18.10) + módulos 157 MB + fixes

**Kernel #7 — config de Ubuntu para el MISMO kernel (6.18.10)** (idea de Carlos: en vez de la lista manual de =m, usar la config que Ubuntu usa para ese kernel — el mainline build `v6.18.10` de kernel.ubuntu.com; la config va DENTRO del .deb `linux-headers-*`). Trae TODOS los drivers de distro (rtlwifi/rtl8723be, i915, amdgpu SI/CIK, HP_WMI, iwlwifi, snd-hda...) ya incluidos. Ajustes: `OVERLAY_FS=y`, `SQUASHFS=y` (live), `LOCALVERSION=""`, `SYSTEM_TRUSTED_KEYS=""` (la config referencia `debian/canonical-certs.pem` — no existe en el tree), BTF off, y **drivers de arranque =y** (ISO9660, SATA_AHCI, NVME, USB_STORAGE, XHCI/EHCI/OHCI — el initrd AIOS no carga módulos). Deps build host: libdwarf-dev + libdw-dev + symlinks dwarf.h (gendwarfksyms).

**Validado: arranca en VM y en AMBOS portátiles** (el viejo A8-7410 y el nuevo HP).

**Tamaño módulos: 8.1 GB → 157 MB** (mejor que Ubuntu: 172 MB), mecanismo oficial del kernel:
1. `MODULE_COMPRESS_ZSTD=y` → compresión en `modules_install` (8.1 → 2.2 GB; requiere rebuild limpio para regenerar auto.conf)
2. `INSTALL_MOD_STRIP=1` → quita el debug DWARF5 de la config mainline (2.2 GB → 157 MB) — el mismo módulo rtl8723be: 6.29 MB → 82.5 KB

**Fixes del saneamiento**:
- glibc 2.44 única y alineada (`/lib64` → `/usr/lib`, cero Ubuntu) + protegida en sven
- LLM: paquete `llama-cpp` de sven (b10221, baseline, GLIBC 2.34) — scripts adaptados (`/usr/bin/llama-server`, sin LD_LIBRARY_PATH); builds manuales eliminados (sin fallback)
- Setup restaurado (una config.yaml de prueba en el árbol hacía saltar el wizard); aios-install v1.1.3 (grupos, passwords, silent boot disco); grub sin nokaslr
- Pendiente histórico: ISO final ~1.5 GB (sin modelo — el GGUF 4.7 GB se copia aparte) — superado: el firmware completo (416 MB) sube la ISO a ~1.5-1.8 GB; el modelo LLM va aparte.

## 8 Ago 2026 — Hardware validado (ISO #7 + LLM)

| Portátil | Modelo | CPU | RAM | Resultado |
|---|---|---|---|---|
| Viejo (instalado) | HP con **AMD A8-7410** | AMD A8-7410 @ 2.2 GHz, 4C (Jaguar, sin AVX2) | 8 GB (6.7 GiB visibles — iGPU comparte) | ✅ Arranca + LLM carga y genera **~1.2 tok/s** (límite DDR3L single-channel); **SIGILL resuelto** |
| Nuevo (probado desde USB, sin instalar) | **HP Laptop 15s-fq1xxx** | **Intel Core i5-1035G1** @ 1.0 GHz (boost 3.6), 4C/8T (Ice Lake, AVX2/AVX-512) | **8 GB** | ✅ Arranca y funciona; carga del modelo desde USB **7-8 min**; genera ~velocidad de tecleo (usable) |

**Notas (8 Ago)**:
- El cuello de botella de los 7-8 min es la **carga del modelo desde el USB** (4.7 GB a ~10-15 MB/s). Desde el SSD NVMe (SK hynix BC511 512 GB) será ~100x más rápida (segundos).
- El i5-1035G1 (AVX-512) aprovecha las variantes CPU del paquete ggml mucho más que el Jaguar (AVX1) — el rendimiento en el HP nuevo será muy superior al 1.2 tok/s del viejo.
- Observación de Carlos: "contesta aproximadamente a la velocidad de una persona promedio tecleando" (el viejo).

## 19-21 Ago 2026 — Arranque colgado, GPU/firmware completo, vbox condicionado, tema completo, instalador

### Arranque colgado en el logo (resuelto)
- **Síntoma**: tras instalar a disco, el sistema se quedaba en el logo (~2 min) y luego arrancaba. **Causa raíz**: instalación a medias por el bug de `harden_sudo` (`glob` devuelve strings → `is_file()` fallaba → el instalador abortaba ANTES de `persist_wifi`) → disco sin wifi → `systemd-networkd-wait-online` bloqueaba el boot.
- **Fixes (en árbol e ISO)**:
  - `systemd-networkd-wait-online` **deshabilitado** en el árbol → el arranque nunca depende de la red
  - `options rtl8723be ips=0 fwlps=0` en `/etc/modprobe.d/rtl8723be.conf` → sin soft lockups del wifi
  - Instalador corregido: revert del autologin/harden_sudo + fix `Path.glob` + **aborts con `sys.exit(1)`** (antes exit 0 → el setup decía "installation complete" sin haber instalado) + **menú que re-pregunta ante entradas inválidas** (setup.py y aios-install)
- Arranque verificado: **6.3 s** a multi-user, escritorio arriba, wifi conectado (persistencia OK).

### GPU: firmware radeon MULLINS (resuelto — causa raíz de la "barra verde"/scrot congelado)
- El árbol tenía una copia **parcial** de firmware (solo amdgpu, 534 MB, del 3 Ago) → el radeon de la APU A8 (MULLINS) no tenía sus `.bin` → `Fatal error during GPU init` → sin `/dev/dri` → X sin driver nativo → render por vesa congelado (scrot devolvía siempre la misma imagen; la "barra verde" era un frame viejo, no la barra real).
- **Fix (vía oficial)**: `sven install linux-firmware` (paquete completo de Arch, `.zst` — el kernel 6.18.10 tiene `CONFIG_FW_LOADER_COMPRESS=y`) → `/usr/lib/firmware` 416 MB con TODO (radeon, amdgpu, iwlwifi, brcm, atheros…) + `regulatory.db` preservado. El `/lib/firmware` viejo (534 MB) se movió a backup (`~/aios-work/backups/backup-firmware-lib-20260821/`) → **~530 MB menos de ISO**.
- **Regla del build**: el firmware se instala SIEMPRE con el paquete sven `linux-firmware` completo (nunca copias parciales manuales).
- Verificado en caliente: `radeon` inicializado (`/dev/dri/card0` + `renderD128`), render fresco, barra correcta.
- **Microcódigo CPU**: `amd-ucode` + `intel-ucode` (paquetes sven) en el árbol — parches de CPU para cualquier equipo.

### vboxadd: condicionado a VirtualBox (no es basura, es adaptativo)
- Las units `vboxadd.service`, `vboxadd-service.service`, `vboxservice.service` llevan un drop-in con **`ConditionVirtualization=oracle`** → en hardware físico no se activan (arranque limpio, sin degraded); en VirtualBox real se levantan con los módulos del kernel de distro (`vboxguest.ko.zst` de 6.18.10 — los de las Guest Additions 7.2.6, incompatibles, se movieron a backup).

### Tema de color completo (ver sección "Temas de color" más abajo)
- `aios-theme` central + `status.py` lee el tema + i3 con `colors.conf` incluido — los 4 temas cambian TODO al momento (verificado en el portátil).

### Push a GitHub (lección aprendida)
- El token del VPS estaba caducado → los pushes de los últimos commits "parecían" funcionar por el `| tail -1` que **enmascara el error** (mismo pitfall que con xorriso). Fix: token nuevo en `~/.git-credentials` del VPS, remotos sin usuario en la URL (`https://github.com/...`), helper store en ambos repos. **Regla: nunca terminar un push con `| tail -1` sin verificar el resultado.**

## 21 Ago 2026 (tarde) — Web v1.4, estadísticas por correo, frases de Wargames, ISO 1.4

### Publicación y web (ccmai.org)
- **ISO v1.4 publicada** en `/var/www/ccmai.org/releases/aios-1.4.iso` (1.9 GB, 21 Ago 20:36) — la 1.3 queda en el servidor sin enlazar (decisión de Carlos).
- **Backup de la web** en `~/aios-work/backups/web-ccmai-20260821/` (patrón de siempre).
- **Rediseño completo estilo wargames/AIOS**: fondo negro, verde Matrix (`#00ff00`/`#006400`), tipografía mono, hexágono **SVG** (borde grueso 8 + círculo relleno — sustituye al ASCII de semitonos, sin pixelación), "Greetings, Professor Falken" con **typewriter + beep 850 Hz/35 ms** (Web Audio API, 8 frases rotativas cada ~6 s, toggle 🔊/🔇 abajo a la derecha — el navegador exige primer clic para el audio), cursor bloque sólido parpadeante, scanlines CRT sutiles (desktop), favicon SVG con hexágono+círculo, meta description + Open Graph (imagen `assets/hex.svg`).
- **Estructura final**: hexágono → AIOS → "Artificial Intelligence Operating System" → frase rotativa → misión (2 frases + "Made with a nostalgic nod to WarGames (1983)") → descarga (sin aios-install, con mención físico/VirtualBox) → enlaces GitHub (corregidos a `ccarrillomanzanares`; **sre-agent fuera**) → footer (badge v1.4 · x86-64 + disclaimer "Proof of concept — beta stage · use at your own risk").
- **Web versionada en el repo**: `aios-lfs/web/` (index.html + releases/index.html + assets/hex.svg) — antes solo vivía en el servidor.

### Estadísticas de acceso (ccmai.org)
- **Script `~/scripts/ccmai-stats-mail.py`**: informe diario (peticiones, IPs únicas, estados, top rutas, descargas ISO con bytes/completas, escaneos sospechosos) en **HTML responsive** (KPIs, barras, media query móvil) + alternativa texto plano; envía por **SMTP Zoho** (`smtp.zoho.eu:587`, app password en `~/info.txt` — ruta absoluta porque el cron corre como root).
- **Cron diario root**: `30 7 * * *` (07:30) → correo a `ccarrillo@ccmai.org`.
- Dato relevante: ~86% del tráfico son 404 de escaneos automáticos (`/.env`, `/.git/config`, `.aws/credentials`); la ISO se descarga en parciales (ninguna completa en 15 días); detrás de Cloudflare (IPs del edge, no reales — `CF-Connecting-IP` pendiente si se quiere).

### Frases de Wargames rotativas (web + AIOS)
- 8 frases míticas: "Greetings, Professor Falken", "Shall we play a game?", "Would you prefer a nice game of chess?", "A strange game. The only winning move is not to play.", "How about Global Thermonuclear War?", "What's the difference?", "To win the game.", "You are a hard man to reach."
- **AIOS**: `setup.py` (wg con typewriter+beep) y `chat.py` (`_greet`) eligen frase aleatoria en cada arranque — commit `dba187e`. **La ISO v1.4 publicada NO lleva esto** (se regenera después).
- **Web**: JS typewriter + beep por carácter.

### Incidente 522 intermitente (móvil de Carlos)
- Síntoma: 522 de Cloudflare + error de certificado SOLO desde el móvil (wifi, sin wifi y datos); portátil OK.
- Diagnóstico: origen sano (localhost 200 en 0.0008 s, workers OK, firewall abierto, DNS global apunta a Cloudflare en router/8.8.8.8/1.1.1.1); certificados válidos (CF: Let's Encrypt hasta Nov 2026; VPS: self-signed). Los 522 no llegan al Apache (no hay línea en el access log del momento).
- Conclusión: **problema del móvil** (caché DNS / DNS privado / hora / VPN con inspección TLS) o ruta intermitente edge-CF→VPS. Pendiente: verificar en el móvil (otros https, DNS privado, hora, reinicio) — no es del servidor.

## 21-22 Ago 2026 (madrugada) — Cuatro bugs encadenados tras el firmware y sus fixes (ISO final 07:38)

### 1. ISO rota: kernel vanilla busca SOLO /lib/firmware
- **Síntoma** (portátil 2014, live): la wifi "se encuentra" pero no levanta ni escanea; dmesg: `Direct firmware load for rtlwifi/rtl8723befw.bin failed with error -2` (ENOENT) — también radeon, regulatory.db, bluetooth.
- **Causa**: al mover el `/lib/firmware` viejo (534 MB) a backup, el árbol quedó con el firmware solo en `/usr/lib/firmware` (paquete sven). El kernel de distro (vanilla 6.18.10 + config Ubuntu, **sin el parche de código de Ubuntu que añade /usr/lib/firmware**) busca SOLO en `/lib/firmware`. Error de proceso: asumir la ruta sin verificarla + publicar la ISO sin arrancarla.
- **Fix (en el árbol)**: `sudo ln -s ../usr/lib/firmware $R/lib/firmware` — symlink, sin duplicación (mismo inodo); `sven install` sigue instalando en /usr/lib. Verificado con `stat -c %i` y `unsquashfs -ll`.
- **Lección**: el puente /lib/firmware → /usr/lib/firmware es OBLIGATORIO en el árbol (regla añadida a la skill aios-distro-kernel).

### 2. Tema parcial tras instalar: colors.conf root:root
- **Síntoma**: el tema elegido se aplica en xterm y status.py pero NO en el borde i3 / rectángulo de workspace (quedan verde wargames).
- **Causa**: `colors.conf` se subió al árbol con `sudo cp` (después del chown de la fase 2.2) → `root:root` → `aios-theme` (corre como aios) no podía escribirlo → PermissionError; y el script **no comprobaba el error** (decía "Theme applied" con exit 0, y el setup lo tragaba con capture_output).
- **Fix**: `chown -R 1000:1000` en `.config/i3/` del árbol + `set -e` en aios-theme (ahora falla ruidoso). Comprobación del tema: `head -4 /home/aios/.config/i3/colors.conf` debe tener `(white)`/`(amber)`… en la primera línea.

### 3. Escritorio muerto: carrera udev-trigger vs udevd (intermitente)
- **Síntoma**: arranca el logo, autologin, X "se levanta" y nada más. Xorg.0.log: `(EE) open /dev/dri/card0: No such file or directory` + `Fatal server error`.
- **Causa**: el kernel inicializa radeon bien (firmware OK), pero **/dev/dri/card0 lo crea udev** al procesar el uevent. El unit `systemd-udev-trigger.service` (systemd upstream) solo tiene `After=` de los **sockets** de udevd, no del **daemon** → en arranques lentos (HDD 2014) el trigger ejecuta `udevadm trigger` antes de que udevd escuche → los uevents se pierden → sin /dev/dri → X muere. **Carrera intermitente** (las ISOs anteriores la ganaron por casualidad).
- **Diagnóstico en caliente**: `udevadm trigger --subsystem-match=drm` crea card0 al momento (prueba de la causa); journal muestra `Finished systemd-udev-trigger.service` ANTES de `Started systemd-udevd.service`.
- **Fix (en el árbol)**: drop-in `/etc/systemd/system/systemd-udev-trigger.service.d/order.conf` con `[Unit]\nAfter=systemd-udevd.service`.

### 4. Xterm no aparece: -sr no existe en el xterm del build
- **Síntoma**: tras añadir scroll, el live arranca el escritorio pero la xterm del menú no se muestra.
- **Causa**: `xterm: bad command line option "-sr"` — la opción CLI de scrollbar-derecha no existe en el xterm del build LFS.
- **Fix**: la derecha se configura por **recurso X**: `-xrm "*rightScrollBar: true"` (probado, exit 0). Wrapper final: `xterm -fa "Adwaita Mono" -fs 11 ... -sb -sl 2000 -xrm "*rightScrollBar: true"`.

### ISO final de la ronda
- `~/aios.iso` → `releases/aios-1.4.iso` (22 Ago 07:38, 1.9 GB): lleva los 4 fixes + firmware accesible + tema + frases Wargames + microcódigo + vbox adaptativo + instalador corregido.
- Verificación post-build sistemática en esta ronda: `unsquashfs -cat/-ll` del squashfs (symlink, drop-in, aios-xterm, permisos colors.conf) antes de publicar.

## 22 Ago 2026 (mañana) — Ronda final: login endurecido, audio, imagemagick, early microcode — ⚠️ PROBLEMA ABIERTO en el arranque

### Hecho y verificado (en el árbol, repo y portátil donde aplica)
- **Login en disco endurecido (punto 4 del plan)**: `harden_login` en `aios-install` — retira `/etc/sudoers.d/wheel-nopasswd` y el autologin de `getty@tty1` (por archivo, sin globs — lección 19 Ago), tras `set_passwords`, con verificación `visudo -c`. **Probado en el portátil 2014 (disco)**: sudo pide contraseña ("a password is required") + getty pide login. El live mantiene autologin+NOPASSWD (decisión Carlos). Backups de la prueba: `/root/backup-login-20260822/` en el disco. Contraseñas temporales pendientes de cambiar por Carlos.
- **Audio / beep**: `/etc/asound.conf` → `pcm.!default { type plug; slave.pcm "plughw:1,0" }` + `ctl card 1` (sin esto aplay iba al HDMI — el beep se perdía; "Host is down" con `defaults.pcm.card` simple, la vía plug+plughw funciona). Probado en el live: beep audible.
- **Volumen persistente**: `/etc/alsa/asound.state` (Master 64%, card "Generic" ALC3227) + **alsa-restore activado** (el unit era static sin `[Install]` → symlink en `multi-user.target.wants` — sin esto el restore nunca corría).
- **Imagemagick**: `sven install imagemagick` (magick v7) en el árbol.
- **.bak fuera del árbol**: 11 archivos → `~/aios-work/backups/bak-arbol-20260822/` (incluido `vmlinuz-6.18.10-lfs.bak-k6`).
- Repos: `aios-agent` `c438861` (early microcode instalador) · `aios-lfs` `1d66b62` (asound.state + alsa-restore).

### ⚠️ PROBLEMA ABIERTO — la ISO definitiva (08:41) no arranca en el 2014
- **Cambio sospechoso (único de arranque)**: early microcode en el initrd — cpio newc (18 MB, `kernel/x86/microcode/AuthenticAMD.bin` + `GenuineIntel.bin`) concatenado DELANTE del initrd gzip (1.1 MB) → initrd total 19 MB (`070701` al inicio, método estándar de Arch). Justificación: el kernel 6.18.10 tiene `CONFIG_MICROCODE=y` pero **`LATE_LOADING` desactivado** → el initrd es la única vía para el microcódigo.
- **Síntoma en el 2014**: GRUB arranca, el kernel corre, el init del live se ejecuta pero: `mounting /dev/loop0 on /squashfs failed` → "AIOS: boot media not found" → sh sin tty. El init SÍ encontró el medio (montó la ISO) pero el mount loop del squashfs falla.
- **Verificado sano**: la ISO está íntegra (md5 del lfs.squashfs idéntico dentro/fuera `63e2e4aa`, superbloque válido, initrd con 070701, grub.cfg correcto). La grabación del USB NO se ha verificado por hash (pendiente: `dd if=/dev/sdb bs=4M | md5sum` → debe dar `b42dddb8`).
- **QEMU en el VPS (sin KVM)**: intento 1 (cdrom) se queda en SeaBIOS; intento 2 (media=disk, MBR grub) arranca "GRUB" pero no completa el boot en 7 min (TCG lento — no concluyente).
- **Plan de aislamiento pendiente (próxima sesión)**:
  1. Verificar la grabación del USB (hash `b42dddb8`) — 3 min, descarta/confirma el USB.
  2. **ISO de control sin early microcode** (initrd original 1.1 MB, todo lo demás igual): si arranca → el initrd es el culpable (buscar vía correcta: p.ej. microcódigo dentro del initrd gzip, o early solo en el disco); si falla igual → squashfs/USB.
  3. El microcódigo early en `build_disk_initrd` (instalador) también está pendiente de validar con la ISO nueva.
- **Rollback disponible**: `~/aios-work/backups/initrd-originales/initrd.img-antes-early-20260822` (1.1 MB, el initrd bueno de las ISOs anteriores).

## Changelog

### v10 — agosto 2026

- **setup.py**: validación de API key en hilo con timeout de 12 s (corrige bloqueo por DNS sin límite y Ctrl+C sin respuesta por SA_RESTART).
- **setup.py**: API key guardada en `~/.aios/.env` en lugar de `config.yaml`.
- **setup.py**: `os._exit(0)` al final para terminar sin esperar hilos residuales.
- **setup.py**: menú LOCAL actualizado a `Qwen3-8B-Instruct` y texto `1) LOCAL (no internet) / Simple tasks`; eliminado `Works 100% offline`.
- **setup.py** y **aios-install**: menús centrados en pantalla usando `os.get_terminal_size()` con padding horizontal y vertical.
- **Flujo setup → agente**: al completar el setup se ejecuta `aios` automáticamente en la misma ventana xterm sin `-hold`, usando `&& [ -f $HOME/.aios/config.yaml ] && aios || exec bash`.
- **aios-install v1.1.1**: al finalizar pregunta si cambiar las passwords de root y aios, con validación de 8 caracteres vía `getpass` y `chpasswd` por stdin dentro del chroot del disco.
- **Silent boot en disco**: el sistema instalado arranca igual que el live (fondo negro + banner AIOS). Nuevo initrd generado por `build_disk_initrd` que monta la partición real y hace `switch_root`.
- **Squashfs**: ahora incluye `boot/vmlinuz-6.18.10-lfs` y `boot/initrd.img` para facilitar la instalación a disco.
- **Seguridad**: eliminado `nokaslr` del live y del instalador a disco.
- **Kernel #4 real**: compilado con gcc 15.2.0 del host VPS; config con `CONFIG_X86_VERBOSE_BOOTUP=n`, `CONFIG_OVERLAY_FS=y`, `CONFIG_FB_VESA=y`; sin `VMWGFX`/`VBOXVIDEO`/`FBDEV_EMULATION`.
- **Locale**: `/etc/locale.conf` fijado a `LANG=C.UTF-8` para evitar mojibake de caracteres de caja.
- **xterm**: fuente `Adwaita Mono` a 11 pt, sin `-hold`.
- **Plymouth**: descartado definitivamente por falta de framebuffer en la VM con el kernel #4.

### v9 y anteriores

- Base LFS 13.0-systemd con OverlayFS rw.
- Integración de Sven para paquetes Arch.
- Instalación de OpenSSH, X11, i3, xterm.
- Cliente AIOS wargame con estilo Matrix.
- Instalador a disco inicial (`aios-install`).
- Intentos previos de Plymouth y logo de kernel.

---

## Licencia

MIT — ver el archivo `LICENSE` del repositorio.

## Menú Wargames y agente — cambios v12 (Ago 2026)

### Menú de arranque (setup.py)
- Saludo **"Greetings, Professor Falken"** con efecto teletipo: tic de 850 Hz / 35 ms por carácter (PCM sintetizado vía `aplay` persistente por stdin — sin archivos de audio)
- El saludo sale **SIEMPRE**: en el arranque del setup y **al iniciar el chat** (aios-agent) cada vez
- **Beep fiable desde el primer carácter**: buffer/period ALSA mínimos (512 frames ~11.6 ms) + **warm-up de 0.2 s de silencio** al abrir aplay (fuerza a ALSA a abrir el dispositivo antes del primer tic — si no, los primeros tics se acumulan en el pipe y suenan tarde)
- **`/sound`** en el chat: activa/desactiva el tic (`SOUND_ON` es atributo de clase `Agent`)
- El saludo va **seguido directamente del menú** (sin limpiar pantalla): `Greetings, Professor Falken` → `You have just booted Artificial Intelligence Operating System.`
- **Sin cajas** (`print_box` eliminado de todos los menús; `aios-install` idem — solo queda la definición inerte)
- **Menú inicial insistente**: una opción inválida repite la pregunta (`Invalid option. Please choose 1 or 2.`) — nunca cae a live
- **Backspace fiable**: `readline` con `^H` y `DEL` mapeados a `backward-delete-char` (setup.py y chat.py — cubre los dos códigos que envían los terminales)

### Check de internet honesto
- **Cascada de 6 destinos TCP**: 1.1.1.1:443, 1.0.0.1:443, 8.8.8.8:53, google.com:443, google.es:443, archlinux.org:443 — IPs sin DNS + dominios reales con DNS (una red que filtra IPs — como la de Carlos — no da falso negativo)
- **OpenDNS** (208.67.222.222 / 208.67.220.220) en todo el sistema: live e instalado, eth + wifi (`.network` con `[DHCP] UseDNS=no` + `_ensure_dns` del wizard wifi + `persist_wifi` del instalador)

### Temas de color (completado el 21 Ago 2026)
- **4 temas**: `wargames` (verde oscuro `#006400`, por defecto), `amber` (`#ffb000`), `white` (`#ffffff`), `cyan` (`#00cccc`)
- **`aios-theme <tema>`** (script central en `/usr/local/bin`): escribe `theme:` en `~/.aios/config.yaml`, genera `~/.config/i3/colors.conf` (colores `client.*` + barra) y **aplica al momento** (reinicia la barra `status.py` + `i3-msg reload`) — una sola vía para TODO
- **Wrapper `/usr/local/bin/aios-xterm`**: lee `theme:` de `config.yaml` y lanza xterm con los colores — usado por el menú, el chat y `$mod+Return`
- **`status.py`** (barra i3): lee `theme:` del `config.yaml` y emite los colores del tema (las alertas rojas/naranjas se mantienen — semántica)
- **i3 config**: los colores viven en `include /home/aios/.config/i3/colors.conf` (generado por aios-theme)
- Selección: **setup** (al configurar pregunta el tema y lo aplica), **`/theme`** en el chat (**aplica al momento**, sin reiniciar), o `aios-theme <tema>` manual
- El instalador acepta **`--theme`** (el disco conserva el tema elegido)

### Proveedor "Other"
- Opción **8) Other** en el menú de proveedores: nombre + endpoint URL (chat completions) + modelo + **API key validada contra ese endpoint** (`GET <base>/models`)
- La config guarda `cloud.base_url` y el chat lo usa (endpoint custom en vez de `CLOUD_ENDPOINTS`)

### Contexto del agente (agent.py)
- **Prompt según modo**: `cloud` = identidad completa (qué es AIOS, LFS + sven, capacidades: comandos/archivos/procesos, búsqueda web, visión OCR/screenshots/xdotool, paquetes sven, red, servicios, LLM local en 8083); `local` = muy resumido (1 línea de identidad + capacidades esenciales) — el límite de contexto es el del proveedor elegido
- Regla de idioma: **"Always respond in the same language the user writes in"** — el LLM responde en el idioma del usuario
- Todo el texto de interfaz en **inglés** (modelos, mensajes, docstrings); el prompt del agente en inglés

### Instalación a disco (aios-install) — login y sudo
- ⚠️ **REVERTIDO el 19 Ago 2026**: el disco instalado **conserva el autologin y el NOPASSWD del live** (disco = live). El intento de endurecer (disable_autologin + harden_sudo) se revirtió porque introdujo un bug (`harden_sudo` con `glob` → `is_file()` fallaba) que **abortaba el instalador a mitad** → disco sin wifi persistido → `systemd-networkd-wait-online` bloqueaba el arranque (logo colgado ~2 min). El instalador corregido (21 Ago) ya no toca autologin ni sudoers.
- El instalador es **ÚNICO**: `/usr/local/bin/aios-install` (versionado en el repo `sre-agent`; el de `scripts/` era un duplicado obsoleto — eliminado)

### Nota de requisitos LOCAL
- En el menú (live e instalar):
```
  1) LOCAL - the built-in Qwen3-8B model (no internet needed)
     Requires: CPU at least like an Intel i5-1035G1 (4 cores / 8 threads,
     1.0 GHz base / 3.6 GHz boost, 6 MB cache), 8 GB RAM.
     Note: runs slow, about human typing speed.
```

### Initrd (banner)
- El banner volvió al **original** (arte de semitonos ▒▓░ — sin cambios): los experimentos de arte sólido (█) y del fix del scroll (cursor a línea 33) se descartaron — no quedaron en el initrd
