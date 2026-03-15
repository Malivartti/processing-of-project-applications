FROM postgres:16-alpine

RUN apk add --no-cache dcron

COPY backup.sh /backup.sh
RUN chmod +x /backup.sh

# Schedule daily backup at 3:00 AM
RUN echo "0 3 * * * PGPASSWORD=\$POSTGRES_PASSWORD /backup.sh >> /var/log/backup.log 2>&1" \
    > /etc/crontabs/root

RUN mkdir -p /backups /var/log

CMD ["crond", "-f", "-l", "2"]
