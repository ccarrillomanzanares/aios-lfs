# Fix post-instalación: pantalla negra / sin teclado ni touchpad

> Fecha: 2026-08-05  
> Afecta a: instalaciones de AIOS en hardware real con GPU AMD (amdgpu/DRM activo).  
> Fix de código: `aios-agent`, commit `5996ae2`.

## Síntoma

Tras instalar AIOS a disco en un portátil con GPU AMD:

- El sistema arranca, se ve el logo de boot, pero después queda **pantalla negra**.
- O bien arranca sin **teclado ni touchpad**.
- En máquinas virtuales (controladora gráfica VMSVGA) el problema **no se reproduce**, porque no existe `/dev/dri`.

## Causa raíz (tres bugs encadenados)

### 1. D-Bus del sistema no arranca

- `dbus.service` era un symlink a `dbus-broker.service`.
- El paquete/binario `dbus-broker` **no estaba instalado**.
- Sin bus de sistema, `systemd-logind` no arranca.
- Sin `systemd-logind`, la sesión gráfica no puede iniciar.

### 2. `systemd-gpt-auto-generator` rompe el mount namespace de dbus-broker

- En discos **GPT con arranque BIOS** (sin partición ESP real), `systemd-gpt-auto-generator` crea las units `efi.mount` y `efi.automount`.
- Ambas fallan al montar porque no hay ESP.
- Ese mount roto rompe el mount namespace que `dbus-broker` necesita por su sandbox `ProtectSystem=full`.
- `dbus-broker` muere con el estado `226/NAMESPACE`.

**Fix manual en sistemas ya instalados:**

```bash
ln -sf /dev/null /etc/systemd/system/efi.mount
ln -sf /dev/null /etc/systemd/system/efi.automount
systemctl daemon-reload
```

> **Nota de futuro:** AIOS debe soportar UEFI real (ESP vfat + grub-efi) en versiones futuras. En ese escenario estas units serán válidas y no deberán enmascararse.

### 3. El usuario `aios` no está en los grupos de escritorio

Con `amdgpu` activo:

- `/dev/dri/card0` es `root:video 660`.
- `/dev/input/event*` son `root:input 660`.

Si `aios` no pertenece a `video` ni `input`, Xorg falla:

```text
open /dev/dri/card0: Permission denied
vesa: Refusing to run, Framebuffer or dri device present
no screens found
```

El getty de `tty1` reinicia cada ~5 segundos, por lo que la pantalla queda negra.

Si `aios` tampoco pertenece a `input`, no hay acceso a teclado ni touchpad.

## Fix implementado en el instalador

La corrección está en `aios-install` (repo `aios-agent`, commit `5996ae2`).

Se añadió la función `add_user_groups(target)`, ejecutada en el chroot del sistema instalado, tras `harden_ssh()` en `main()`:

```python
desktop_groups = [
    "video", "audio", "input", "storage", "optical", "power", "kvm",
    "render", "log", "rfkill", "disk", "cdrom", "dialout", "lp"
]

def add_user_groups(target):
    for group in desktop_groups:
        subprocess.run(["chroot", target, "groupadd", "-f", group], check=False)
    groups_csv = ",".join(desktop_groups)
    subprocess.run(
        ["chroot", target, "usermod", "-aG", groups_csv, "aios"],
        check=True
    )
```

El instalador genera el esquema completo de grupos en el disco destino (GIDs estilo Arch: `video=981`, `audio=993`, `input=988`, `disk=989`, `cdrom=992`, `kvm=986`, `render=984`, `lp=985`, `tty=5`, etc.).

### ⚠️ Importante: no añadir los grupos al squashfs/ISO base

No hay que crear estos grupos en el squashfs o en la ISO base. Hacerlo crea colisiones de GID. Por ejemplo, si en el squashfs se define `power=986`, choca con `kvm=986` que el instalador crea después en el disco.

**El fix correcto es aplicarlo solo desde el instalador:** `groupadd -f` + `usermod -aG`.

## Verificación tras instalar

1. Comprobar que `aios` pertenece a todos los grupos:

```bash
groups aios
```

Salida esperada (orden puede variar):

```text
aios : aios wheel video audio input storage optical power kvm render log rfkill disk cdrom dialout lp
```

2. Comprobar que `/dev/dri/card0` es accesible:

```bash
ls -l /dev/dri/card0
getfacl /dev/dri/card0   # si está disponible
su - aios -c "test -r /dev/dri/card0 && echo OK"
```

3. Comprobar que los dispositivos de entrada son legibles:

```bash
ls -l /dev/input/event*
su - aios -c "test -r /dev/input/event0 && echo OK"
```

4. Si el problema persiste, revisar el log real de Xorg:

```bash
cat /home/aios/.local/share/xorg/Xorg.0.log
```

> **Nota:** `/var/log/Xorg.0.log` puede pertenecer a un boot anterior o a una sesión de root. El log del usuario `aios` tras `startx` está en `/home/aios/.local/share/xorg/Xorg.0.log`.

5. Si `getty@tty1` se reinicia cada ~5 segundos, significa que la sesión X muere al instante. Revisar `startx.log` en `/home/aios/`.

## Diagnóstico rápido

| Síntoma | Causa probable |
|---|---|
| Pantalla negra tras el logo, getty reiniciándose | Xorg no puede abrir `/dev/dri/card0` por falta de grupo `video`. |
| Sin teclado/touchpad | Falta grupo `input`. |
| `dbus-broker` muere con `226/NAMESPACE` | Unidades `efi.mount` / `efi.automount` rotas en GPT+BIOS. |
| `systemd-logind` inactivo | No hay D-Bus del sistema (`dbus-broker` no instalado o no arranca). |

## Nota UEFI futuro

Este documento describe el estado actual para instalaciones BIOS sobre GPT sin ESP. Cuando AIOS implemente soporte UEFI real con partición ESP vfat y `grub-efi`, las units `efi.mount` y `efi.automount` dejarán de ser problemáticas y el instalador deberá adaptarse para no enmascararlas.
