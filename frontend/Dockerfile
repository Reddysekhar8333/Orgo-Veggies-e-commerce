FROM nginx:1.27-alpine

ENV FRONTEND_PORT=80 \
    NGINX_BACKEND_HOST=backend \
    NGINX_BACKEND_PORT=8000

RUN apk add --no-cache gettext

COPY index.html /usr/share/nginx/html/index.html
COPY static/ /usr/share/nginx/html/static/
COPY templates/ /usr/share/nginx/html/templates/
COPY js/ /usr/share/nginx/html/js/
COPY css/ /usr/share/nginx/html/css/
COPY nginx.conf /etc/nginx/templates/default.conf.template

EXPOSE ${FRONTEND_PORT}

CMD ["/bin/sh", "-c", "envsubst '$$FRONTEND_PORT $$NGINX_BACKEND_HOST $$NGINX_BACKEND_PORT' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'"]
