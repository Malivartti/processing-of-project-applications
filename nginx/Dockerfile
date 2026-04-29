FROM nginx:alpine

COPY nginx.conf /etc/nginx/nginx.conf
COPY ssl/server.crt /etc/nginx/ssl/server.crt
COPY ssl/server.key /etc/nginx/ssl/server.key

EXPOSE 80 443
