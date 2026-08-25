# Guía de VirtualBox para probar AIOS

Cómo montar una máquina virtual para probar AIOS (ISO 1.4, live + instalación).
Verificado con el primer usuario externo (Arnold, 25 Ago 2026).

## Crear la VM

| Parámetro | Valor | Nota |
|---|---|---|
| Tipo | **Linux** | — |
| Versión | **Oracle Linux (64-bit)** | Si no se elige un tipo Linux, VirtualBox no detecta el sistema |
| RAM | **8192 MB (8 GB)** mínimo | Con 2 GB el LLM local y el escritorio van muy lentos (el agente responde, pero tarda) |
| CPU | 2+ núcleos | |
| Disco | **20 GB mínimo** | El sistema instalado + el modelo LLM (4,7 GB) necesitan espacio |
| Red | **NAT** (por defecto) | Verificado: la VM recibe 10.0.2.15/24 y funciona |

## Arrancar la ISO

1. En la VM: *Almacenamiento → Controladora IDE → Añadir disco óptico* → seleccionar `aios-1.4.iso` (6,7 GB).
2. Arrancar la VM. El menú de AIOS aparece en la terminal (verde).

## Durante el arranque/uso

- El **menú principal** tiene 3 opciones: `1) Test AIOS live` · `2) Install AIOS` · `0) Exit to shell`.
- Tras elegir **Instalar**, el instalador muestra pasos `[1/7] … [7/7]` con progreso.
- **La instalación tarda ~30 minutos** (copia del modelo LLM de 4,7 GB). No interrumpir.
- Ayuda de teclado: **F1 o Win+F1**.
- El teclado francés/azerty se configura desde el chat: *"cambia el teclado a francés"*.

## Notas / problemas conocidos

- **Firefox puede tardar >30 s en abrir** en VM con poca RAM (2 GB) → el agente reporta timeout.
  No es un fallo del sistema: con 8 GB de RAM abre con normalidad (verificado en hardware real).
- El **web_search del agente** (búsqueda web) requiere configuración (API key/backend);
  sin ella el agente avisa de problema de conexión. No es un fallo de red de la VM.
- Si la instalación se **cancela** (disco inválido o confirmación rechazada), el instalador
  vuelve al menú — no hay que reiniciar la VM.
- Solo se ha probado en máquinas **sin multi-boot** (ver disclaimer del instalador).

## Enlaces

- ISO: `https://ccmai.org/aios/releases/aios-1.4.iso`
- Web del proyecto: `https://ccmai.org/aios/`
- Repos: `github.com/ccarrillomanzanares/aios-lfs` · `github.com/ccarrillomanzanares/aios-agent`
