from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

router = APIRouter(prefix="/api/ai", tags=["AI Authoring"])

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini").strip()


class ImageActivityRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    image_url: str = Field(min_length=10, max_length=8_000_000)
    project_title: str = Field(default="Actividad educativa", max_length=160)
    course: str = Field(default="", max_length=120)
    academic_level: str = Field(default="Subgraduado", max_length=60)
    teacher_goal: str = Field(default="", max_length=2000)
    language: str = Field(default="es-PR", max_length=20)


class RubricCriterion(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    points: int
    levels: str


class ImageActivityResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    image_summary: str
    detected_concepts: list[str]
    activity_title: str
    bloom_level: str
    objectives: str
    instructions: str
    main_question: str
    expected_answer: str
    quiz: list[str]
    model_search_terms: list[str]
    model_accessibility_description: str
    rubric: list[RubricCriterion]
    source: str


def _fallback(payload: ImageActivityRequest) -> ImageActivityResponse:
    topic = payload.teacher_goal.strip() or payload.project_title.strip() or "la imagen presentada"
    return ImageActivityResponse(
        image_summary="La imagen fue incorporada correctamente. La actividad se generó localmente; configure OPENAI_API_KEY para análisis visual detallado.",
        detected_concepts=[topic, "observación", "análisis visual", "aplicación"],
        activity_title=f"Análisis visual aplicado: {topic[:90]}",
        bloom_level="Analizar",
        objectives=(f"1. Identificar los elementos principales relacionados con {topic}.\n"
                    "2. Explicar las relaciones observables entre los componentes.\n"
                    "3. Aplicar conceptos del curso mediante evidencia visual.\n"
                    "4. Comunicar conclusiones claras y fundamentadas."),
        instructions="Observe cuidadosamente el recurso, identifique sus elementos principales, documente evidencia visible y relacione sus observaciones con el contenido del curso. Responda la pregunta central y revise la rúbrica antes de entregar.",
        main_question=f"¿Qué elementos principales se observan y cómo se relacionan con {topic}? Sustente su explicación con evidencia de la imagen.",
        expected_answer="La respuesta debe identificar elementos verificables, explicar relaciones, aplicar conceptos del curso y presentar una conclusión organizada.",
        quiz=[
            "Identifique tres elementos visibles y explique la importancia de cada uno.",
            "¿Qué relación existe entre los componentes observados?",
            "¿Cómo aplicaría este análisis a una situación auténtica?",
        ],
        model_search_terms=[topic, f"{topic} 3D model", f"{topic} GLB"],
        model_accessibility_description=f"Modelo tridimensional complementario relacionado con {topic}.",
        rubric=[
            RubricCriterion(name="Identificación y dominio del contenido", points=25, levels="Excelente, competente, en desarrollo e insuficiente"),
            RubricCriterion(name="Análisis y uso de evidencia visual", points=30, levels="Excelente, competente, en desarrollo e insuficiente"),
            RubricCriterion(name="Aplicación y pensamiento crítico", points=25, levels="Excelente, competente, en desarrollo e insuficiente"),
            RubricCriterion(name="Organización y comunicación", points=20, levels="Excelente, competente, en desarrollo e insuficiente"),
        ],
        source="guided-fallback",
    )


def _extract_output_text(response: dict[str, Any]) -> str:
    if isinstance(response.get("output_text"), str):
        return response["output_text"]
    for item in response.get("output", []):
        for content in item.get("content", []):
            if isinstance(content.get("text"), str):
                return content["text"]
    raise ValueError("The AI response did not include text output")


def _strict_schema() -> dict[str, Any]:
    schema = ImageActivityResponse.model_json_schema()
    schema["additionalProperties"] = False
    for definition in schema.get("$defs", {}).values():
        if definition.get("type") == "object":
            definition["additionalProperties"] = False
    return schema


def _analyze_with_ai(payload: ImageActivityRequest) -> ImageActivityResponse:
    prompt = f"""
Actúa como diseñador instruccional universitario experto en educación en línea, Blackboard Ultra,
accesibilidad y evaluación auténtica. Analiza la imagen y crea una actividad completa en español de
Puerto Rico. No inventes detalles que no sean visibles; distingue observación de inferencia.

Proyecto: {payload.project_title}
Curso: {payload.course or 'No especificado'}
Nivel: {payload.academic_level}
Propósito del profesor: {payload.teacher_goal or 'Diseñar una actividad educativa a partir de la imagen'}

La rúbrica debe sumar exactamente 100 puntos. Incluye tres términos de búsqueda específicos para localizar
modelos 3D educativos eficientes en formato GLB/glTF o en Sketchfab. En source escribe "multimodal-ai".
Devuelve únicamente JSON válido que cumpla exactamente el esquema.
""".strip()
    body = {
        "model": OPENAI_MODEL,
        "input": [{"role": "user", "content": [
            {"type": "input_text", "text": prompt},
            {"type": "input_image", "image_url": payload.image_url},
        ]}],
        "text": {"format": {"type": "json_schema", "name": "ucan_image_activity", "schema": _strict_schema(), "strict": True}},
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as result:
            raw = json.loads(result.read().decode("utf-8"))
        parsed = json.loads(_extract_output_text(raw))
        parsed["source"] = "multimodal-ai"
        return ImageActivityResponse.model_validate(parsed)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:800]
        raise HTTPException(status_code=502, detail=f"El servicio de IA rechazó la solicitud: {detail}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise HTTPException(status_code=503, detail="El servicio de IA no está disponible temporalmente") from exc
    except (json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="La IA respondió en un formato que no se pudo validar") from exc


@router.post("/design-from-image", response_model=ImageActivityResponse)
def design_from_image(payload: ImageActivityRequest) -> ImageActivityResponse:
    if not payload.image_url.startswith(("https://", "data:image/")):
        raise HTTPException(status_code=422, detail="Use una URL HTTPS o suba una imagen válida")
    if not OPENAI_API_KEY:
        return _fallback(payload)
    return _analyze_with_ai(payload)
