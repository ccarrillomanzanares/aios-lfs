# AIOS LFS

ISO live de Linux From Scratch con agente AIOS.

- docs/: documentacion
- configs/: configuracion del sistema (grub, i3, locale, issue, drop-ins)
- scripts/: scripts de build y despliegue

## Generacion de la ISO

```bash
sudo grub-mkrescue -o ~/aios.iso ~/aios
```

### ISO con modelo LLM incluido (>4 GiB)

Si el squashfs supera 4 GiB (p.ej. con el modelo local Qwen3-8B Q4_K_M de 4.7 GB en
`/usr/local/share/aios/models/`), `grub-mkrescue` falla con "Grafting failed" por el
limite de 4 GiB/archivo del ISO9660 level 2. Es OBLIGATORIO usar `-iso-level 3`:

```bash
sudo grub-mkrescue -iso-level 3 -o ~/aios.iso ~/aios
```

- `-iso-level 3` va DIRECTO como opcion de grub-mkrescue (no `-- -iso-level 3`, que
  lo pasaria a xorriso 1.5.6 y fallaria con "Not a known command").
- Verificar tras generar: `ls -lh ~/aios.iso` debe mostrar ~5.5 GB, no el tamano
  anterior (914M). Un `| tail -1` en el pipeline enmascara el fallo de xorriso.

### Componentes del LLM local

| Componente | Ruta |
|---|---|
| Modelo | `/usr/local/share/aios/models/Qwen_Qwen3-8B-Q4_K_M.gguf` |
| llama-server | `/usr/local/bin/llama-server` |
| Librerias llama.cpp | `/usr/local/lib/llama/` |
| Servicio | `aios-llama.service` (lanza llama-server en modo local, puerto 8083, `--jinja`) |

Con el modelo en la ISO, el modo local del agente funciona sin internet ni API
(ideal para el portatil de 8 GB RAM: context 8K, threads auto).

## Problemas conocidos

### Pantalla negra o sin teclado tras instalar en hardware real

Si tras instalar AIOS a disco en un portátil con GPU AMD el sistema arranca con pantalla negra o sin teclado/touchpad, consulta [docs/instalacion/grupos-escritorio-pantalla-negra.md](docs/instalacion/grupos-escritorio-pantalla-negra.md). El fix ya está integrado en el instalador (`aios-agent`, commit `5996ae2`) y documenta los tres bugs encadenados que lo provocaban.
