FROM nginx:1.28-alpine
COPY frontend/dist /usr/share/nginx/html
COPY infra/nginx.direct.conf /etc/nginx/conf.d/default.conf
