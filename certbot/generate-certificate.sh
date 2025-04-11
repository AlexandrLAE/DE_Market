#!/bin/bash

echo "Starting certificate generation..."

# Проверяем обязательные переменные
if [ -z "$DOMAIN_EMAIL" ] || [ -z "$DOMAIN_URL" ]; then
    echo "ERROR: DOMAIN_EMAIL and DOMAIN_URL must be set!"
    exit 1
fi

# Основная команда Certbot
echo "Requesting certificate for $DOMAIN_URL..."
certbot certonly \
    --standalone \
    --non-interactive \
    --agree-tos \
    --email "$DOMAIN_EMAIL" \
    -d "$DOMAIN_URL" \
    --cert-name "certfolder"

# Проверяем результат
if [ $? -eq 0 ]; then
    echo "Certificate successfully generated!"
    ls -la /etc/letsencrypt/live/certfolder/
else
    echo "Failed to generate certificate!"
    exit 1
fi

# docker compose run --rm certbot certonly --webroot --webroot-path /var/www/certbot/ --dry-run -d de-project.space
