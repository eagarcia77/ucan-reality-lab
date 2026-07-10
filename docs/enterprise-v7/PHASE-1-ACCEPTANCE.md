# Fase 1 — Criterios de aceptación

La Fase 1 se considerará completada cuando se cumpla lo siguiente:

## Ejecución

- El entorno completo inicia con un solo comando de Docker Compose.
- Frontend, API, PostgreSQL, Redis y MinIO reportan estado saludable.
- GitHub Codespaces abre el proyecto sin configuración manual adicional.

## Usuarios y seguridad

- Un usuario puede registrarse e iniciar sesión.
- Existen roles de administrador, profesor y revisor.
- Las contraseñas se almacenan mediante hash seguro.
- Las rutas privadas requieren autenticación.

## Proyectos

- El profesor puede crear, editar, duplicar, archivar y restaurar un proyecto.
- Cada cambio importante genera una versión recuperable.
- Los archivos se guardan fuera de la base de datos en almacenamiento compatible con S3.

## Editor

- Se pueden editar título, objetivo, instrucciones, preguntas y rúbrica.
- El profesor dispone de vista previa del estudiante.
- El sistema valida que la rúbrica totalice 100 puntos.

## Calidad técnica

- API documentada mediante OpenAPI.
- Migraciones de base de datos reproducibles.
- Pruebas unitarias y de integración para funciones críticas.
- GitHub Actions ejecuta lint, pruebas y construcción Docker.
- No existen secretos o claves en el repositorio.

## Accesibilidad

- Navegación esencial mediante teclado.
- Etiquetas asociadas a campos de formulario.
- Contraste y estructura semántica compatibles con WCAG 2.2 AA.
- La vista del estudiante ofrece alternativa textual para recursos visuales.
