# Securización y configuración de Apache — ccmai.org

Procedimiento y estado de la configuración de Apache del VPS (31.220.80.78),
aplicado el **24 Ago 2026** (auditoría de seguridad). Documento de referencia:
si se toca Apache, actualizar este archivo.

## Estado actual

- Apache2 (Debian/Ubuntu), sitios: `ccmai.org.conf` (http) + `ccmai.org-ssl.conf` (https).
- Tráfico público por Cloudflare; TLS Let's Encrypt (TLS 1.3).
- Módulo `headers` HABILITADO (necesario para las directivas `Header`).
- DocumentRoot: `/var/www/ccmai.org` (matriz; el producto AIOS vive en `/aios/`).

## 1. Ocultar la versión de Apache

Archivo: `/etc/apache2/conf-enabled/security.conf`

```apache
ServerTokens Prod
ServerSignature Off
```

Aplicar:

```bash
sudo sed -i "s/^ServerTokens.*/ServerTokens Prod/; s/^ServerSignature.*/ServerSignature Off/" /etc/apache2/conf-enabled/security.conf
sudo systemctl reload apache2
```

Verificar (local — Cloudflare oculta el Server en el exterior):

```bash
curl -sI http://127.0.0.1/ | grep -i "^server"
# Esperado: Server: Apache   (sin número de versión)
```

## 2. Headers de seguridad (HSTS + X-Content-Type-Options)

1. Habilitar el módulo (solo la primera vez):

```bash
sudo a2enmod headers && sudo apachectl -t && sudo systemctl reload apache2
```

2. En `/etc/apache2/sites-enabled/ccmai.org-ssl.conf`, justo tras `ServerName`:

```apache
    # Seguridad (24 Ago 2026): HSTS + X-Content-Type-Options
    Header always set Strict-Transport-Security "max-age=31536000"
    Header always set X-Content-Type-Options "nosniff"
```

3. Recargar y verificar:

```bash
sudo apachectl -t && sudo systemctl reload apache2
curl -sI https://ccmai.org/aios/ | grep -iE "strict-transport|x-content-type"
# Esperado: Strict-Transport-Security: max-age=31536000
#           X-Content-Type-Options: nosniff
```

Para añadir más headers (X-Frame-Options, CSP...), misma directiva en el mismo vhost.

## 3. Los vhosts de ccmai.org

- `ServerName ccmai.org`, `ServerAlias www.ccmai.org`, DocumentRoot `/var/www/ccmai.org`.
- Redirects de la matriz al producto:

```apache
RedirectMatch 301 ^/$ /aios/
RedirectMatch 301 ^/releases(/.*)?$ /aios/releases$1
```

- Backup del vhost SSL: `~/aios-work/backups/ccmai-ssl-20260824.bak`.
- ⚠️ Pitfall: si se añade una directiva `Header` sin el módulo `headers` activo, Apache
  falla con `AH00526: Invalid command 'Header'` → `sudo a2enmod headers` primero.

## 4. fail2ban (complemento: fuerza bruta SSH)

- Instalado y activo el 24 Ago 2026. Config: `/etc/fail2ban/jail.local`

```ini
[DEFAULT]
bantime = 10m
findtime = 10m
maxretry = 5
ignoreip = 127.0.0.1/8 ::1

[sshd]
enabled = true
```

- Desbanear una IP (p. ej. la propia con IP dinámica):

```bash
sudo fail2ban-client set sshd unbanip <ip>
```

- Estado: `sudo fail2ban-client status sshd`

## 5. Páginas de desarrollo (`/aios-dev/`)

- **FUERA del servidor** desde el 24 Ago (movido a `~/aios-work/backups/aios-dev-20260824/`).
  Da 404. Sigue versionada en el repo: `aios-lfs/web/aios-dev/`.
- Para volver a servirla cuando se necesite: restaurar el directorio en
  `/var/www/ccmai.org/aios-dev/` (o añadir un `Alias` en el vhost) y recargar Apache.

## 6. Checklist de verificación

```bash
sudo apachectl -t                                   # Syntax OK
curl -sI http://127.0.0.1/ | grep -i "^server"      # Server: Apache (sin versión)
curl -sI https://ccmai.org/aios/ | grep -iE "strict-transport|x-content-type"   # ambos
curl -s -o /dev/null -w "%{http_code}\n" https://ccmai.org/aios-dev/            # 404
curl -s -o /dev/null -w "%{http_code}\n" https://ccmai.org/aios/releases/aios-1.4.iso  # 200
curl -s -o /dev/null -w "%{http_code}\n" https://ccmai.org/                     # 301 -> /aios/
```

## 7. Firewall

- `ufw`/`iptables` **no configurados** (decisión 24 Ago: se usa el firewall del
  proveedor Contabo). No habilitar ufw sin revisar el flujo completo (SSH 22,
  HTTP 80, HTTPS 443).

## Historial

- **24 Ago 2026**: auditoría — ServerTokens Prod, ServerSignature Off, módulo
  headers, HSTS + X-Content-Type-Options, fail2ban activo, /aios-dev/ fuera del
  servidor, Firecrawl bind 127.0.0.1 + parado (ver README maestro).
