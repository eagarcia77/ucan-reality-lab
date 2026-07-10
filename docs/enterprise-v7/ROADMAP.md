# Hoja de ruta — UCAN Reality Lab Enterprise v7.0

## Fase 1 — Base institucional

- [ ] Crear monorepo con `frontend`, `backend` y paquetes compartidos.
- [ ] Configurar PostgreSQL, Redis y MinIO en Docker Compose.
- [ ] Implementar autenticación y roles.
- [ ] Crear gestión de proyectos y versiones.
- [ ] Añadir editor visual inicial.
- [ ] Añadir pruebas, linting y CI.

**Resultado:** plataforma estable donde el profesor crea, guarda, abre y versiona proyectos.

## Fase 2 — IA multimodal

- [ ] Analizar imágenes, PDF, DOCX y PPTX.
- [ ] Extraer tema, conceptos, texto alternativo y competencias.
- [ ] Generar actividad y rúbrica estructuradas.
- [ ] Añadir asistente de edición por instrucciones.
- [ ] Mostrar proveedor y estado real de la IA.

**Resultado:** generación basada en el contenido real, con revisión docente.

## Fase 3 — Biblioteca 3D

- [ ] Integrar API de Sketchfab cuando exista token.
- [ ] Diseñar conectores para proveedores adicionales.
- [ ] Mostrar tres candidatos reales con licencia y vista previa.
- [ ] Validar embed y guardar atribución.
- [ ] Añadir alternativa textual accesible.

**Resultado:** selección confiable de modelos 3D existentes.

## Fase 4 — Actividades, rúbricas y exportación

- [ ] Tipos de actividad configurables.
- [ ] Rúbricas analíticas y holísticas editables.
- [ ] SCORM 1.2 con respuesta, progreso, puntuación y recuperación.
- [ ] Validación automatizada del paquete.
- [ ] Vista previa del estudiante.
- [ ] Preparar SCORM 2004, H5P y Common Cartridge.

**Resultado:** paquetes reutilizables y verificables para Blackboard Ultra.

## Fase 5 — Calidad y operación institucional

- [ ] Informe de alineación, accesibilidad, ortografía y calidad.
- [ ] Panel administrativo y auditoría.
- [ ] Analítica de creación y uso.
- [ ] Marketplace institucional de plantillas y actividades.
- [ ] Manuales de profesor, administrador y despliegue.
- [ ] Despliegue permanente con copias de seguridad.

**Resultado:** plataforma institucional operable y mantenible.

## Regla de entrega

Cada fase debe incluir código funcional, pruebas, documentación, criterios de aceptación y una demostración verificable antes de integrarse en `main`.
