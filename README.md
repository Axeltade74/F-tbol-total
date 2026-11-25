# FÚTBOL TOTAL — app automática
Se actualiza sola cada 15 min: resultados (API-Football), noticias (Google News RSS) y fotos con licencia libre (Wikipedia/Commons, con crédito).
## Puesta en marcha (10 min, sin servidor propio)
1. Creá un repositorio en GitHub y subí todo este contenido.
2. Cuenta gratuita en https://www.api-football.com y copiá tu clave. En el repo: Settings → Secrets and variables → Actions → New secret: `API_FOOTBALL_KEY`.
3. Settings → Pages → Source: "Deploy from a branch" → rama `main`, carpeta `/docs`.
4. Pestaña Actions → "Actualizar FÚTBOL TOTAL" → Run workflow (la primera vez). Desde ahí corre sola.
Tu app queda en `https://TU-USUARIO.github.io/TU-REPO/`.
## Notas
- Plan gratuito de la API: 100 consultas/día; el cron usa 1 por ejecución (96/día).
- Las noticias muestran titular, fuente y enlace al medio original, sin copiar los artículos.
- Fotos: solo imágenes con licencia libre; si un jugador no tiene, se muestra con sus iniciales.
- Prueba local: `python fetch.py --demo` y abrir `docs/index.html` con un servidor (`python -m http.server -d docs`).
