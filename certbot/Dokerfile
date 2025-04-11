FROM certbot/certbot:latest

# Можно кастомизировать при необходимости
# ENV DOMAIN_EMAIL=${DOMAIN_EMAIL:-"admin@example.com"} \
#     DOMAIN_URL=${DOMAIN_URL:-"example.com"}

WORKDIR /certbot
COPY generate-certificate.sh .

RUN chmod +x generate-certificate.sh

CMD ["./generate-certificate.sh"]