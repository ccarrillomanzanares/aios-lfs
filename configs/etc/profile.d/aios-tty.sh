# AIOS: fijar el erase char del tty al estandar moderno (0x7f = DEL).
# Sin esto, el backspace no borra en prompts canonicos (sudo, login, getpass)
# y muestra "^H"/"^?" + letras acumuladas (bug reportado 26 Ago 2026).
stty erase '^?' 2>/dev/null || true
