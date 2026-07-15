FROM nginx:1.27-alpine
COPY *.html /usr/share/nginx/html/
COPY *.js /usr/share/nginx/html/
COPY *.css /usr/share/nginx/html/
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD wget -qO- http://localhost/healthz >/dev/null || exit 1