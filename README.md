# AIOS LFS

ISO live de Linux From Scratch con agente AIOS.

- docs/: documentacion
- configs/: configuracion del sistema (grub, i3, locale, issue, drop-ins)
- scripts/: scripts de build y despliegue

## Problemas conocidos

### Pantalla negra o sin teclado tras instalar en hardware real

Si tras instalar AIOS a disco en un portátil con GPU AMD el sistema arranca con pantalla negra o sin teclado/touchpad, consulta [docs/instalacion/grupos-escritorio-pantalla-negra.md](docs/instalacion/grupos-escritorio-pantalla-negra.md). El fix ya está integrado en el instalador (`aios-agent`, commit `5996ae2`) y documenta los tres bugs encadenados que lo provocaban.
