# Apache Hardening and Configuration — ccmai.org

Procedure and status of the Apache configuration on the VPS (31.220.80.78),
applied on **24 Aug 2026** (security audit). Reference document:
if Apache is changed, update this file.

## Current status

- Apache2 (Debian/Ubuntu), sites: `ccmai.org.conf` (http) + `ccmai.org-ssl.conf` (https).
- Public traffic through Cloudflare; TLS Let's Encrypt (TLS 1.3).
- `headers` module ENABLED (required for the `Header` directives).
- DocumentRoot: `/var/www/ccmai.org` (parent site; the AIOS product lives at `/aios/`).

## 1. Hide Apache version

File: `/etc/apache2/conf-enabled/security.conf`

```apache
ServerTokens Prod
ServerSignature Off
```

Apply:

```bash
sudo sed -i "s/^ServerTokens.*/ServerTokens Prod/; s/^ServerSignature.*/ServerSignature Off/" /etc/apache2/conf-enabled/security.conf
sudo systemctl reload apache2
```

Verify (locally — Cloudflare hides the Server header externally):

```bash
curl -sI http://127.0.0.1/ | grep -i "^server"
# Expected: Server: Apache   (no version number)
```

## 2. Security headers (HSTS + X-Content-Type-Options)

1. Enable the module (first time only):

```bash
sudo a2enmod headers && sudo apachectl -t && sudo systemctl reload apache2
```

2. In `/etc/apache2/sites-enabled/ccmai.org-ssl.conf`, right after `ServerName`:

```apache
    # Security (24 Aug 2026): HSTS + X-Content-Type-Options
    Header always set Strict-Transport-Security "max-age=31536000"
    Header always set X-Content-Type-Options "nosniff"
```

3. Reload and verify:

```bash
sudo apachectl -t && sudo systemctl reload apache2
curl -sI https://ccmai.org/aios/ | grep -iE "strict-transport|x-content-type"
# Expected: Strict-Transport-Security: max-age=31536000
#           X-Content-Type-Options: nosniff
```

To add more headers (X-Frame-Options, CSP...), use the same directive in the same vhost.

## 3. The ccmai.org vhosts

- `ServerName ccmai.org`, `ServerAlias www.ccmai.org`, DocumentRoot `/var/www/ccmai.org`.
- Redirects from the parent site to the product:

```apache
RedirectMatch 301 ^/$ /aios/
RedirectMatch 301 ^/releases(/.*)?$ /aios/releases$1
```

- Backup of the SSL vhost: `~/aios-work/backups/ccmai-ssl-20260824.bak`.
- ⚠️ Pitfall: if you add a `Header` directive without the `headers` module enabled, Apache
  fails with `AH00526: Invalid command 'Header'` → run `sudo a2enmod headers` first.

## 4. fail2ban (add-on: SSH brute force)

- Installed and activated on 24 Aug 2026. Config: `/etc/fail2ban/jail.local`

```ini
[DEFAULT]
bantime = 10m
findtime = 10m
maxretry = 5
ignoreip = 127.0.0.1/8 ::1

[sshd]
enabled = true
```

- Unban an IP (e.g. your own dynamic IP):

```bash
sudo fail2ban-client set sshd unbanip <ip>
```

- Status: `sudo fail2ban-client status sshd`

## 5. Development pages (`/aios-dev/`)

- **REMOVED from the server** since 24 Aug (moved to `~/aios-work/backups/aios-dev-20260824/`).
  Returns 404. Still versioned in the repo: `aios-lfs/web/aios-dev/`.
- To serve it again when needed: restore the directory to
  `/var/www/ccmai.org/aios-dev/` (or add an `Alias` in the vhost) and reload Apache.

## 6. Verification checklist

```bash
sudo apachectl -t                                   # Syntax OK
curl -sI http://127.0.0.1/ | grep -i "^server"      # Server: Apache (no version)
curl -sI https://ccmai.org/aios/ | grep -iE "strict-transport|x-content-type"   # both
curl -s -o /dev/null -w "%{http_code}\n" https://ccmai.org/aios-dev/            # 404
curl -s -o /dev/null -w "%{http_code}\n" https://ccmai.org/aios/releases/aios-1.4.iso  # 200
curl -s -o /dev/null -w "%{http_code}\n" https://ccmai.org/                     # 301 -> /aios/
```

## 7. Firewall

- `ufw`/`iptables` **not configured** (decision on 24 Aug: we use the Contabo provider
  firewall). Do not enable ufw without reviewing the full flow (SSH 22,
  HTTP 80, HTTPS 443).

## History

- **24 Aug 2026**: audit — ServerTokens Prod, ServerSignature Off, headers
  module, HSTS + X-Content-Type-Options, fail2ban active, /aios-dev/ removed from
  the server, Firecrawl bound to 127.0.0.1 + stopped (see master README).
