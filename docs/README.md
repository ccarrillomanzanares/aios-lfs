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

### Pendientes

- Soportar el modo ISO de Rufus (FAT32) en el script init del initrd live.
- Preparar el kernel #5 con controladores NVMe y UAS para ampliar la compatibilidad de hardware.

## 6 Ago 2026 — LLM local en portátil: SIGILL (estado actual)

**Síntoma**: `aios-llama.service` falla en bucle `status=4/ILL` (SIGILL core dump) en el HP (AMD A8-7410 — sin AVX2/FMA3/AVX-512). `launch_llama.py` usa `LLAMA_BIN=/usr/local/bin/llama-server` + `LD_LIBRARY_PATH=/usr/local/lib/llama` (build1 original, `GGML_NATIVE=ON` → AVX-512 → SIGILL garantizado).

**Descartado (verificado 6 Ago)**:
- **GGUF**: md5 idéntico VPS/portátil (`1f7c1dfa76fa25696c806e580f0964b7`), mismo tamaño exacto. El mismo modelo funciona en el VPS.
- **ISA de ggml**: build4 AVX1+F16C puro (`--fresh`, AVX2/FMA/AVX512=OFF) verificado con objdump en las 14 libs (0 `vpblendd|vpermd|vpbroadcast|vpsllvd|vpermq|vpmaskmov|vinserti128|vextracti128|vfmadd|zmm`) → SIGILL igual al cargar el modelo (`--version` sí funciona). El conteo "290" que despistó era falso positivo (`vpblendvb`=AVX1, `vpblendw`=SSE4.1).
- **Mezcla glibc**: core dump con cadena normal y con cadena LFS forzada (`/usr/lib/ld-linux-x86-64.so.2`).

**Pendiente**:
- Probar el build SSE-only del VPS (`~/llama.cpp/build/bin`: `GGML_AVX=OFF`, `GGML_AVX2=OFF`, 0 zmm) en el portátil — nunca probado; es el discriminador natural contra la teoría glibc/CPU Jaguar.
- Carlos probará en otro portátil (mañana).
- build4 está en `/tmp/llama4` del portátil, **NO instalado**; `/usr/local/lib/llama` sigue con build1 AVX-512.

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
- Pendiente: ISO final ~1.5 GB (sin modelo — el GGUF 4.7 GB se copia aparte), validar y probar el LLM (momento del SIGILL)

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
