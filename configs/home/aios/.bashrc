# AIOS: erase char estandar para xterm/pty (los shells no-login no leen /etc/profile)
stty erase '^?' 2>/dev/null || true
