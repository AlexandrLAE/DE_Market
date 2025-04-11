#!/bin/bash
set -e  # Прерывать выполнение при ошибках

# Пути и переменные
CERT_DIR="/etc/letsencrypt/live/certfolder"
TEMP_DIR="/tmp/certbot"

echo "### Starting certificate generation process ###"

# Очистка старых сертификатов (с проверкой существования)
if [ -d "$CERT_DIR" ]; then
    echo "Removing old certificates in $CERT_DIR"
    rm -rf "$CERT_DIR"
fi

# Создаем временную директорию
mkdir -p "$TEMP_DIR"

echo "Requesting new certificate for domain: $DOMAIN_URL"

# Запрос сертификата с обработкой ошибок
if ! certbot certonly \
    --standalone \
    --email "$DOMAIN_EMAIL" \
    -d "$DOMAIN_URL" \
    --cert-name "certfolder" \
    --key-type "rsa" \
    --agree-tos \
    --non-interactive \
    --config-dir "$TEMP_DIR" \
    --work-dir "$TEMP_DIR" \
    --logs-dir "$TEMP_DIR"; then
    
    echo "### ERROR: Certificate generation failed! ###"
    exit 1
fi

# Проверка полученных сертификатов
if [ -d "$CERT_DIR" ]; then
    echo "### Certificate successfully generated! ###"
    echo "Certificate location: $CERT_DIR"
    ls -la "$CERT_DIR"
else
    echo "### ERROR: Certificate files not found! ###"
    exit 1
fi

# Очистка временных файлов
rm -rf "$TEMP_DIR"

echo "### Process completed successfully ###"
