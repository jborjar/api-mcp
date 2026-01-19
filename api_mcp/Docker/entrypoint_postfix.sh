#!/bin/bash
set -e

# Configuración base de Postfix
HOSTNAME=${POSTFIX_HOSTNAME:-mail.local}
DOMAIN=${POSTFIX_DOMAIN:-local}
NETWORKS=${POSTFIX_NETWORKS:-"172.16.0.0/12 192.168.0.0/16 10.0.0.0/8"}

# Configuración de relay (opcional)
RELAY_HOST=${POSTFIX_RELAY_HOST:-}
RELAY_PORT=${POSTFIX_RELAY_PORT:-587}
RELAY_USER=${POSTFIX_RELAY_USER:-}
RELAY_PASSWORD=${POSTFIX_RELAY_PASSWORD:-}

echo "Configurando Postfix..."
echo "  Hostname: $HOSTNAME"
echo "  Domain: $DOMAIN"
echo "  Networks: $NETWORKS"

# Configuración principal
postconf -e "myhostname = $HOSTNAME"
postconf -e "mydomain = $DOMAIN"
postconf -e "myorigin = \$mydomain"

# Reescribir remitente para correos locales (envelope y headers)
postconf -e "smtp_generic_maps = hash:/etc/postfix/generic"
postconf -e "smtp_header_checks = regexp:/etc/postfix/header_checks"
echo "root@postfix-api-mcp aviso@progex.grupoexpansion" > /etc/postfix/generic
echo "root aviso@progex.grupoexpansion" >> /etc/postfix/generic
echo "@postfix-api-mcp @progex.grupoexpansion" >> /etc/postfix/generic
postmap /etc/postfix/generic

# Reescribir header From (cualquier remitente local)
cat > /etc/postfix/header_checks << 'EOF'
/^From:.*root.*/ REPLACE From: aviso@progex.grupoexpansion
/^From:.*@progex\.local.*/ REPLACE From: aviso@progex.grupoexpansion
/^From:.*@postfix-api-mcp.*/ REPLACE From: aviso@progex.grupoexpansion
/^From:.*api-mcp.*/ REPLACE From: aviso@progex.grupoexpansion
EOF
postconf -e "inet_interfaces = all"
postconf -e "inet_protocols = ipv4"
postconf -e "mydestination = \$myhostname, localhost.\$mydomain, localhost"
postconf -e "mynetworks = 127.0.0.0/8 $NETWORKS"
postconf -e "smtpd_relay_restrictions = permit_mynetworks, reject_unauth_destination"

# Configuración de seguridad básica
postconf -e "smtpd_banner = \$myhostname ESMTP"
postconf -e "biff = no"
postconf -e "append_dot_mydomain = no"
postconf -e "readme_directory = no"

# Configuración de relay externo (si está configurado)
if [ -n "$RELAY_HOST" ]; then
    echo "Configurando relay externo: $RELAY_HOST:$RELAY_PORT"
    postconf -e "relayhost = [$RELAY_HOST]:$RELAY_PORT"

    if [ -n "$RELAY_USER" ] && [ -n "$RELAY_PASSWORD" ]; then
        echo "Configurando autenticación SASL para relay..."
        postconf -e "smtp_sasl_auth_enable = yes"
        postconf -e "smtp_sasl_password_maps = hash:/etc/postfix/sasl_passwd"
        postconf -e "smtp_sasl_security_options = noanonymous"
        postconf -e "smtp_tls_security_level = encrypt"
        postconf -e "smtp_tls_CAfile = /etc/ssl/certs/ca-certificates.crt"

        # Crear archivo de credenciales
        echo "[$RELAY_HOST]:$RELAY_PORT $RELAY_USER:$RELAY_PASSWORD" > /etc/postfix/sasl_passwd
        postmap /etc/postfix/sasl_passwd
        chmod 600 /etc/postfix/sasl_passwd /etc/postfix/sasl_passwd.db
    fi
else
    echo "Modo envío directo (sin relay)"
    postconf -e "relayhost ="
fi

# Forzar DNS externo para resolver dominios
echo "nameserver 8.8.8.8" > /etc/resolv.conf
echo "nameserver 8.8.4.4" >> /etc/resolv.conf

# Copiar resolv.conf al chroot de Postfix
cp /etc/resolv.conf /var/spool/postfix/etc/resolv.conf

# Crear directorios necesarios
mkdir -p /var/spool/postfix/pid
chown root:root /var/spool/postfix/pid

# Iniciar Postfix en primer plano
echo "Iniciando Postfix..."
postfix start-fg
