# UCAN Reality Lab v6.0 — Edición final para GitHub

Plataforma educativa para analizar imágenes y documentos, generar actividades y rúbricas, integrar un modelo 3D de Sketchfab seleccionado por el profesor y exportar un paquete **SCORM 1.2** para Blackboard Ultra. El SCORM incluye el recurso original, autoevaluación, rúbrica y un área donde el estudiante redacta y guarda su respuesta.

## Ejecutar solamente desde GitHub Codespaces

Esta es la opción recomendada porque no requiere instalar Python ni Docker en la computadora.

1. Cree un repositorio nuevo en GitHub.
2. Suba **todo el contenido de esta carpeta** al repositorio.
3. En el repositorio, seleccione **Code → Codespaces → Create codespace on main**.
4. Espere a que Codespaces termine la configuración.
5. El puerto `8151` se abrirá automáticamente. Si no abre, entre a la pestaña **Ports** y seleccione **Open in Browser** junto al puerto `8151`.

El programa se inicia automáticamente mediante `.devcontainer/start-codespace.sh`.

### Configurar IA real en Codespaces

El programa funciona sin API, pero utiliza un generador local limitado. Para análisis real de imágenes/documentos, añada estos secretos en **GitHub → Settings → Codespaces → Secrets** y autorícelos para el repositorio:

```text
AI_BASE_URL=https://api.openai.com/v1
AI_API_KEY=su_clave
AI_MODEL=modelo_multimodal_compatible
SKETCHFAB_API_TOKEN=token_opcional
```

Después reconstruya el Codespace: `Ctrl+Shift+P` → **Codespaces: Rebuild Container**.

> No coloque claves privadas dentro de `.env` antes de subir el proyecto a GitHub.

## Flujo del profesor

1. Subir una imagen o documento.
2. Describir la actividad deseada.
3. Generar y editar la actividad y la rúbrica.
4. Examinar las tres sugerencias de modelos 3D.
5. Escoger un modelo individual en Sketchfab.
6. Copiar su código **Embed/Incrustar** y pegarlo en el programa.
7. Validar el visor 3D.
8. Crear, previsualizar y descargar el paquete SCORM.
9. Cargar el ZIP SCORM en Blackboard Ultra sin descomprimirlo.

## Mejoras de esta edición

- GitHub Codespaces configurado para iniciar automáticamente.
- GitHub Actions para probar Python, construir Docker y verificar `/api/health`.
- Publicación opcional de la imagen en GitHub Container Registry mediante una etiqueta `v*`.
- Persistencia de proyectos, archivos y paquetes SCORM.
- Validación de `imsmanifest.xml` y llamadas SCORM esenciales.
- Modelo 3D mediante embed seguro de Sketchfab proporcionado por el profesor.
- Recurso original incluido dentro del SCORM.
- Respuesta del estudiante guardada en `cmi.suspend_data`, `cmi.comments` y almacenamiento local de respaldo.
- Rúbrica editable de 100 puntos, autoevaluación y vista previa.
- Contenedor ejecutado con usuario sin privilegios y comprobación de salud.

## Ejecutar localmente con Docker

```bash
docker compose up --build -d
```

Abra `http://localhost:8151`.

Para cambiar el puerto externo:

```bash
UCAN_PORT=8165 docker compose up --build -d
```

En Windows también puede crear un archivo `.env` con:

```text
UCAN_PORT=8165
```

## Verificación

```text
http://localhost:8151/api/health
```

Pruebas:

```bash
pytest -q
```

## Estructura principal

```text
.devcontainer/          Inicio automático en GitHub Codespaces
.github/workflows/      Pruebas y publicación en GHCR
app/main.py             API, análisis, Sketchfab y generador SCORM
app/static/index.html   Interfaz del profesor
app/data/               Datos persistentes, ignorados por Git
Dockerfile              Imagen de producción
docker-compose.yml      Ejecución local
requirements.txt        Dependencias
```

## Limitación importante

GitHub Pages no puede ejecutar este proyecto porque Pages solo sirve contenido estático y UCAN Reality Lab necesita un backend Python. Para ejecutarlo únicamente dentro de GitHub, utilice **GitHub Codespaces**. Para una instalación pública permanente, publique la imagen de GHCR en un servicio compatible con contenedores.
