#!/bin/bash

# чистим папку, где могут находиться старые сертификаты
rm -rf /etc/letsencrypt/live/certfolder*

# выдаем себе сертификат (обратите внимание на переменные среды)
certbot certonly --standalone --email $DOMAIN_EMAIL -d $DOMAIN_URL --cert-name=certfolder --key-type rsa --agree-tos

