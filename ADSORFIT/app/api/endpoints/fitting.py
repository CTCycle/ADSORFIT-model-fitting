from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Body, HTTPException, status
from pydantic import ValidationError

from Pharmagent.app.utils.serializer import DataSerializer
from Pharmagent.app.utils.services.clinical import (
    DrugToxicityEssay,
    HepatotoxicityPatternAnalyzer,
)
from Pharmagent.app.utils.services.translation import TranslationService
from Pharmagent.app.utils.services.parser import (
    BloodTestParser,
    DiseasesParser,
    DrugsParser,
    PatientCase,
)
from Pharmagent.app.api.schemas.clinical import (
    PatientData,
)
from Pharmagent.app.constants import TASKS_PATH, TRANSLATION_CONFIDENCE_THRESHOLD
from Pharmagent.app.logger import logger

serializer = DataSerializer()
translation_service = TranslationService()
drugs_parser = DrugsParser()
diseases_parser = DiseasesParser()
pattern_analyzer = HepatotoxicityPatternAnalyzer()
MAX_TRANSLATION_ATTEMPTS = 5

router = APIRouter(tags=["agent"])


# [ENPOINTS]
###############################################################################
async def process_single_patient(payload: PatientData, translate_to_eng: bool = False) -> dict[str, Any]:
    logger.info(
        "Starting Drug-Induced Liver Injury (DILI) analysis for patient: %s",
        payload.name,
    )

    translation_stats: dict[str, Any] | None = None
    updated_payload = payload.model_copy()
    if translate_to_eng:
        logger.info("Translating text to English")
        translation_stats, updated_payload = await translation_service.translate_payload(
            payload,
            certainty_threshold=TRANSLATION_CONFIDENCE_THRESHOLD,
            max_attempts=MAX_TRANSLATION_ATTEMPTS,
        )

    start_time = time.perf_counter()
    drug_data = drugs_parser.parse_drug_list(updated_payload.drugs or "")
    elapsed = time.perf_counter() - start_time
    logger.info("Drugs extraction required %.4f seconds", elapsed)
    logger.info("Detected %s drugs", len(drug_data.entries))

    pattern_score = pattern_analyzer.analyze(updated_payload)
    logger.info(
        "Patient hepatotoxicity pattern classified as %s (R=%.3f)",
        pattern_score.classification,
        pattern_score.r_score if pattern_score.r_score is not None else float("nan"),
    )

    start_time = time.perf_counter()
    toxicity_runner = DrugToxicityEssay(drug_data)
    drug_assessment = await toxicity_runner.run_analysis()
    elapsed = time.perf_counter() - start_time
    logger.info("Drugs toxicity essay required %.4f seconds", elapsed)

    start_time = time.perf_counter()
    diseases = await diseases_parser.extract_diseases(updated_payload.anamnesis or "")
    elapsed = time.perf_counter() - start_time
    logger.info("Disease extraction required %.4f seconds", elapsed)
    logger.info("Detected %s diseases for this patient", len(diseases["diseases"]))
    logger.info(
        "Subset of hepatic diseases includes %s entries",
        len(diseases["hepatic_diseases"]),
    )

    patient_info: dict[str, Any] = {
        "name": payload.name or "Unknown",
        "anamnesis": payload.anamnesis,
        "alt": payload.alt,
        "alt_max": payload.alt_max,
        "alp": payload.alp,
        "alp_max": payload.alp_max,
        "additional_tests": None,
        "drugs": drug_data.model_dump(),
        "symptoms": ", ".join(payload.symptoms),
        "diseases": diseases,
        "hepatotoxicity_pattern": pattern_score.model_dump(),
        "drug_toxicity_assessment": drug_assessment.model_dump(),
    }

    if payload.exams:
        patient_info["additional_tests"] = payload.exams

    if translation_stats:
        patient_info["translation"] = translation_stats

    serializer.save_patients_info(patient_info)
    return patient_info

# -----------------------------------------------------------------------------
@router.post("/agent", response_model=None, status_code=status.HTTP_202_ACCEPTED)
async def start_single_clinical_agent(
    name: str | None = Body(default=None),
    anamnesis: str | None = Body(default=None),
    drugs: str | None = Body(default=None),
    exams: str | None = Body(default=None),
    alt: str | None = Body(default=None),
    alt_max: str | None = Body(default=None),
    alp: str | None = Body(default=None),
    alp_max: str | None = Body(default=None),
    symptoms: list[str] | None = Body(default=None),
    translate_to_eng: bool = Body(default=False)
) -> dict[str, Any]:
    try:
        payload = PatientData(
            name=name,
            anamnesis=anamnesis,
            drugs=drugs,
            exams=exams,
            alt=alt,
            alt_max=alt_max,
            alp=alp,
            alp_max=alp_max,
            symptoms=symptoms or [],
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.errors()
        ) from exc

    single_result = await process_single_patient(payload, translate_to_eng)
    return {"status": "success", "processed": 1, "patients": [single_result]}


# -----------------------------------------------------------------------------
@router.post("/batch-agent", response_model=None, status_code=status.HTTP_202_ACCEPTED)
async def start_batch_clinical_agent() -> dict[str, Any]:

    patient_case = PatientCase()
    lab_parser = BloodTestParser()

    txt_files = [path for path in Path(TASKS_PATH).glob("*.txt") if path.is_file()]
    if not txt_files:
        logger.info(
            "No .txt files found in default path. Add new files and rerun the batch agent."
        )
        return {"status": "success", "processed": 0, "patients": []}

    results: list[dict[str, Any]] = []
    for path in txt_files:
        try:
            text = path.read_text(encoding="utf-8")
        except Exception as exc:
            logger.error(f"Failed reading {path}: {exc}")
            continue

        cleaned_text = patient_case.clean_patient_info(text)
        sections = patient_case.split_text_by_tags(cleaned_text, path.stem)

        anamnesis_section = sections.get("anamnesis")
        drugs_section = sections.get("drugs")
        exams_section = sections.get("additional_tests")

        hepatic_markers = lab_parser.parse_hepatic_markers(sections.get("blood_tests"))

        try:
            patient_payload = PatientData(
                name=path.stem,
                anamnesis=anamnesis_section,
                drugs=drugs_section,
                exams=exams_section,
                alt=hepatic_markers["alt"],
                alt_max=hepatic_markers["alt_max"],
                alp=hepatic_markers["alp"],
                alp_max=hepatic_markers["alp_max"],
                symptoms=[],
            )
        except ValidationError as exc:
            logger.error(f"Invalid data for patient {path.stem}: {exc}")
            continue

        case = await process_single_patient(patient_payload)
        results.append(case)

    return {"status": "success", "processed": len(results), "patients": results}
