FROM curl AS downloader
WORKDIR /app
RUN curl -LO  \
  https://github.com/FortuneN/kete/releases/download/2026.08.27.08.03/kete.jar 

  
FROM quay.io/keycloak/keycloak:26.4
COPY --from=downloader /app/kete.jar /opt/keycloak/providers/
RUN /opt/keycloak/bin/kc.sh build