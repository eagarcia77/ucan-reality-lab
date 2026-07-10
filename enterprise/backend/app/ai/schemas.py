from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field, model_validator


class SelfCheckItem(BaseModel):
    question: str = Field(min_length=5)
    options: list[str] = Field(min_length=2, max_length=6)
    correct_index: int = Field(ge=0)
    feedback: str = Field(min_length=5)

    @model_validator(mode="after")
    def validate_index(self):
        if self.correct_index >= len(self.options):
            raise ValueError("correct_index está fuera del rango de opciones")
        return self


class ActivityDraft(BaseModel):
    title: str = Field(min_length=5, max_length=180)
    activity_type: Literal[
        "actividad", "laboratorio", "estudio_de_caso", "foro", "proyecto", "quiz"
    ] = "actividad"
    academic_level: str = "universitario"
    estimated_minutes: int = Field(default=30, ge=5, le=600)
    bloom_level: str
    objective: str = Field(min_length=10)
    competencies: list[str] = Field(min_length=1, max_length=10)
    context: str = Field(min_length=20)
    instructions: list[str] = Field(min_length=3, max_length=10)
    concepts: list[str] = Field(min_length=1, max_length=20)
    prompt: str = Field(min_length=10)
    expected_evidence: list[str] = Field(min_length=1, max_length=10)
    self_check: list[SelfCheckItem] = Field(default_factory=list, max_length=5)


class RubricLevel(BaseModel):
    label: str
    description: str
    score_ratio: float = Field(ge=0, le=1)


class RubricCriterion(BaseModel):
    criterion: str
    weight: int = Field(gt=0, le=100)
    levels: list[RubricLevel] = Field(min_length=3, max_length=5)


class MultimodalAnalysis(BaseModel):
    provider: str
    model: str
    status: Literal["external_ai", "local_fallback", "error"]
    detected_topic: str
    factual_summary: str = Field(min_length=20)
    alt_text: str = Field(min_length=5, max_length=220)
    extracted_concepts: list[str] = Field(min_length=1, max_length=25)
    detected_text: str = ""
    activity: ActivityDraft
    rubric: list[RubricCriterion] = Field(min_length=2, max_length=10)
    warnings: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def rubric_totals_100(self):
        total = sum(item.weight for item in self.rubric)
        if total != 100:
            raise ValueError(f"La rúbrica debe sumar 100 puntos; suma {total}")
        return self


class EditInstruction(BaseModel):
    instruction: str = Field(min_length=3, max_length=1000)
    current: MultimodalAnalysis
