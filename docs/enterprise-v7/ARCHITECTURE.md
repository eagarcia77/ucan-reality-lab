# UCAN Reality Lab Enterprise v7.0 — Arquitectura

## Propósito

Transformar el prototipo v6.0 en una plataforma institucional modular para analizar recursos educativos, generar actividades y rúbricas con IA, integrar modelos 3D y exportar contenidos compatibles con Blackboard Ultra.

## Principios

- Separación estricta entre interfaz, API, procesamiento, datos y exportación.
- IA configurable; nunca se almacenan claves en el repositorio.
- Revisión docente obligatoria antes de publicar o exportar.
- Accesibilidad WCAG 2.2 AA desde el diseño.
- Trazabilidad de cambios, versiones y auditoría.
- Exportaciones verificadas mediante pruebas automáticas.

## Componentes

### Frontend

- Next.js + React + TypeScript.
- Editor visual para actividad y rúbrica.
- Vista del profesor y vista previa del estudiante.
- Visor 3D mediante iframe validado de Sketchfab y soporte futuro para GLB.

### Backend

- FastAPI con API versionada bajo `/api/v1`.
- Validación con Pydantic.
- Servicios desacoplados para análisis, rúbricas, modelos 3D, calidad y exportación.

### Datos

- PostgreSQL para usuarios, proyectos, actividades, rúbricas, versiones y auditoría.
- MinIO/S3 para archivos originales, miniaturas y paquetes exportados.
- Redis para cola de tareas y caché.

### Procesamiento

- Celery para análisis de documentos, generación de actividades y construcción de paquetes.
- Estados de tarea: pendiente, procesando, completada y error.

### IA

- Proveedor multimodal configurable mediante variables de entorno.
- Respuesta estructurada y validada contra esquemas.
- Modo local claramente identificado como limitado.
- Registro del proveedor, modelo, fecha y versión del prompt, sin guardar secretos.

### Modelos 3D

- Búsqueda mediante proveedores autorizados y APIs configuradas.
- Presentación de tres candidatos con autor, licencia, miniatura, visor y puntuación.
- Selección final y validación del embed por el profesor.

### Exportación

- Primera prioridad: SCORM 1.2.
- Fases posteriores: SCORM 2004, Common Cartridge, H5P y xAPI.
- Validación de manifiesto, archivos requeridos, rutas, seguimiento y accesibilidad.

## Servicios previstos

```text
frontend      Next.js
backend       FastAPI
worker        Celery
postgres      PostgreSQL
redis         Redis
minio         almacenamiento S3 compatible
nginx         proxy inverso para producción
```

## Seguridad

- Autenticación JWT con rotación de tokens.
- OAuth futuro con Microsoft y Google.
- Roles: administrador, diseñador instruccional, profesor y revisor.
- Límites de tamaño y tipos de archivo.
- Sanitización de HTML y validación estricta de embeds.
- Auditoría de operaciones importantes.

## Migración desde v6.0

La rama `main` continuará funcionando mientras se construye v7.0. La nueva arquitectura se desarrollará en fases y se integrará solo cuando cada módulo cumpla sus criterios de aceptación.
