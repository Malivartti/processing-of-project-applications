FROM postgres:16-alpine

RUN apk add --no-cache curl && \
    curl -fsSL https://github.com/aptible/supercronic/releases/latest/download/supercronic-linux-amd64 \
    -o /usr/local/bin/supercronic && \
    chmod +x /usr/local/bin/supercronic

COPY backup.sh /backup.sh
RUN chmod +x /backup.sh

RUN echo "0 3 * * * PGPASSWORD=\$POSTGRES_PASSWORD /backup.sh >> /var/log/backup.log 2>&1" \
    > /etc/crontab

RUN mkdir -p /backups /var/log

CMD ["supercronic", "/etc/crontab"]