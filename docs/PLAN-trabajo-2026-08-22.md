# Plan de trabajo AIOS — 22 Ago 2026

Verificado contra el estado real del árbol (`~/aios-work/squashfs-root`) y del repo `sre-agent` el 22 Ago 2026.

## Cerrado (sin trabajo)
- **glibc dual**: RESUELTA. El árbol tiene glibc **2.44 única** en `/usr/lib`, y `/lib64/{libc.so.6,ld-linux-x86-64.so.2}` son symlinks internos hacia `/usr/lib`. `ldd` en chroot = 2.44. Sin rastro de Ubuntu.

## Descartado / pendiente (no se toca por ahora)
- Bloque 0 (PipeWire, microcódigo, wireless-regdb, binds i3): olvidado por ahora.
- Firefox/YouTube: Carlos lo prueba y reporta.
- Daemon/watchdog (1.5), backup restic (1.6), `aios-update` (2.1), persistencia live (2.3), CI (3.1), tests (3.2): no.

## Hitos

### Hito 1 — Eliminar el modo híbrido
- Ya no está en `setup.py`; quedan restos en `agent.py` (líneas 117, 122, 173, 339), `chat.py` (docstring + flag `--mode hybrid` + ramas 376-395-465), `scripts/launch_llama.py`, docs (`README.md`, `CHANGELOG.md`, `docs/ejecutivo.md`).
- Quitar las ramas `hybrid` y simplificar los condicionales a `local`/`cloud`; actualizar docs.
- **Verificación**: `grep -ri hybrid` = 0 en `*.py`; `py_compile` de todo; flujos local y cloud intactos.

### Hito 2 — Tool `web_extract`
- Lee una URL y devuelve texto plano (manpages, issues, doc de paquetes). Reutilizar el scrape de Firecrawl si está disponible; si no, `lynx -dump` o `urllib` + conversión.
- **Verificación**: `web_extract` sobre una URL real devuelve contenido legible.

### Hito 3 — Memoria de usuario persistente
- `~/.aios/user_memory.json` + carga al iniciar + tools `remember`/`recall` para preferencias estables ("usa sven", "puerto 8083", "responde en español").
- Se inyecta en el system prompt, separada de la memoria procedural (que sigue igual).
- **Verificación**: el agente recuerda una preferencia entre reinicios.

### Hito 4 — Skills versionados
- Directorio `~/.aios/skills/*.md` + tools `list_skills`/`load_skill`.
- El agente puede cargar una skill a demanda en vez de depender solo del JSON procedural.
- **Verificación**: una skill de ejemplo se lista y se carga correctamente.

### Hito 5 — Visión cloud `describe_screen`
- `screenshot()` (ya existe) + subir el PNG al endpoint cloud (extendiendo `cloud_reasoning`, que ya está) para que un VLM **describa** la imagen — no solo OCR.
- Solo activa en modo cloud; OCR/screenshot/xdotool locales se quedan igual.
- **Verificación**: `describe_screen` en cloud devuelve una descripción semántica de una captura.

### Hito 5.5 — Revisar a fondo el squashfs (limpieza segura)
- Recorrer el árbol `~/aios-work/squashfs-root` buscando cosas que se puedan limpiar con seguridad: restos del build (vboxadd, `.cache`, backups internos, firmware duplicado, docs/PDFs de prueba, paquetes no usados, artefactos de sesiones de debug), sin tocar nada de lo que dependa el arranque o el agente.
- Antes de borrar nada: inventario + propuesta de borrado con justificación, y confirmación explícita de Carlos.

### Hito 6 — UEFI (con mucho cuidado)
- Hito separado, al final. Primero investigar cómo está empaquetada la ISO hoy (`grub-mkrescue` sin EFI), luego plan EFI **con rollback** y prueba aislada antes de tocar la ISO estable. Nada hasta verlo juntos.

## Nota (futuro, no ahora)
- Teclas que fallan: brillo, forward/reverse/play-pause, Impr Pant → `bindsym` i3 faltantes (`XF86MonBrightnessUp/Down`, `XF86AudioNext/Prev/Play`, `Print`). El volumen ya funciona (esos binds sí existen). No entra en este plan salvo orden expresa.

## Orden
1 → 2 → 3 → 4 → 5 (código de agente, bajo riesgo, en una tanda); 5.5 y 6 aparte.
