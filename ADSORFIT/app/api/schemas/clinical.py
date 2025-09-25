from __future__ import annotations

import re
from typing import Literal, Any

from pydantic import BaseModel, Field, field_validator, model_validator


Comparator = Literal["<=", "<", ">=", ">"]


###############################################################################
class PatientData(BaseModel):
    """
    Input schema for submitting structured clinical data.
    - Accepts manual clinical sections captured in the GUI.
    - Normalizes whitespace and keeps compat with legacy single-text payloads.
    """

    name: str | None = Field(
        None,
        min_length=1,
        max_length=200,
        description="Name of the patient (optional).",
        examples=["Marco Rossi"],
    )
    anamnesis: str | None = Field(
        None,
        max_length=20000,
        description="Patient anamnesis notes.",
    )
    drugs: str | None = Field(
        None,
        max_length=20000,
        description="Medication list and dosage notes.",
    )
    exams: str | None = Field(
        None,
        max_length=20000,
        description="Blood and instrumental exam notes.",
    )
    alt: str | None = Field(
        None,
        description="ALT laboratory value.",
        examples=["189", "189 U/L"],
    )
    alt_max: str | None = Field(
        None,
        description="Reference maximum for ALT.",
        examples=["47", "47 U/L"],
    )
    alp: str | None = Field(
        None,
        description="ALP laboratory value.",
        examples=["140", "140 U/L"],
    )
    alp_max: str | None = Field(
        None,
        description="Reference maximum for ALP.",
        examples=["150", "150 U/L"],
    )
    symptoms: list[str] = Field(
        default_factory=list, description="Additional boolean options from the UI."
    )

    @field_validator("name", mode="before")
    @classmethod
    def _strip_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = str(value).strip()
        return stripped or None

    @field_validator(
        "anamnesis", "drugs", "exams", "alt", "alt_max", "alp", "alp_max", mode="before"
    )
    @classmethod
    def _strip_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = str(value).strip()
        return stripped or None

    @model_validator(mode="after")
    def _require_sections(self) -> "PatientData":
        if any((self.anamnesis, self.drugs, self.exams)):
            return self
        raise ValueError("Provide at least one clinical section before submitting.")

    @staticmethod
    def _coerce_marker(value: str | None) -> tuple[float | None, str | None]:
        if value is None:
            return None, None
        stripped = str(value).strip()
        if not stripped:
            return None, None
        normalized = stripped.replace(",", ".")
        try:
            return float(normalized), None
        except ValueError:
            return None, stripped

    def manual_hepatic_markers(self) -> dict[str, Any]:
        markers: dict[str, Any] = {}
        alt_value, alt_text = self._coerce_marker(self.alt)
        alt_cutoff, alt_cutoff_text = self._coerce_marker(self.alt_max)
        if any((alt_value is not None, alt_text, alt_cutoff, alt_cutoff_text)):
            entry: dict[str, Any] = {
                "value": alt_value,
                "value_text": alt_text,
                "unit": None,
                "date": None,
            }
            if alt_cutoff is not None or alt_cutoff_text is not None:
                entry["cutoff"] = alt_cutoff
                entry["cutoff_text"] = alt_cutoff_text
            markers["ALAT"] = entry
        alp_value, alp_text = self._coerce_marker(self.alp)
        alp_cutoff, alp_cutoff_text = self._coerce_marker(self.alp_max)
        if any((alp_value is not None, alp_text, alp_cutoff, alp_cutoff_text)):
            entry = {
                "value": alp_value,
                "value_text": alp_text,
                "unit": None,
                "date": None,
            }
            if alp_cutoff is not None or alp_cutoff_text is not None:
                entry["cutoff"] = alp_cutoff
                entry["cutoff_text"] = alp_cutoff_text
            markers["ALP"] = entry
        return markers

    
    def compose_structured_text(self) -> str | None:
        sections: list[str] = []
        if self.anamnesis:
            sections.append(f"# ANAMNESIS\n{self.anamnesis}")
        blood_lines: list[str] = []
        if self.alt or self.alt_max:
            alt_tokens: list[str] = []
            if self.alt:
                alt_tokens.append(str(self.alt))
            if self.alt_max:
                alt_tokens.append(f"(max {self.alt_max})")
            blood_lines.append(f"ALAT: {' '.join(alt_tokens).strip()}")
        if self.alp or self.alp_max:
            alp_tokens: list[str] = []
            if self.alp:
                alp_tokens.append(str(self.alp))
            if self.alp_max:
                alp_tokens.append(f"(max {self.alp_max})")
            blood_lines.append(f"ALP: {' '.join(alp_tokens).strip()}")
        blood_body = "\n".join(line for line in blood_lines if line)
        if blood_body or self.exams:
            parts = [part for part in (blood_body, self.exams) if part]
            sections.append(f"# BLOOD TESTS\n{'\n'.join(parts)}")
        if self.exams:
            sections.append(f"# ADDITIONAL TESTS\n{self.exams}")
        if self.drugs:
            sections.append(f"# DRUGS\n{self.drugs}")
        if not sections:
            return None
        return "\n\n".join(section.strip() for section in sections if section.strip())


###############################################################################
class PatientOutputReport(BaseModel):
    report: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Multiline text output with the final report.",
        examples=["This is a sample note."],
    )

    @field_validator("report", mode="before")
    @classmethod
    def _strip_report(cls, v: str) -> str:
        if v is None:
            return v
        return str(v).strip()


###############################################################################
class PatientDiseases(BaseModel):
    diseases: list[str] = Field(default_factory=list)
    hepatic_diseases: list[str] = Field(default_factory=list)

    @field_validator("diseases", "hepatic_diseases")
    def strip_and_nonempty(cls, v) -> list[str]:
        # Clean up each string, skip empty/None
        return [str(item).strip() for item in v if item and str(item).strip()]

    @field_validator("diseases", "hepatic_diseases")
    def must_be_unique(cls, v):
        if len(v) != len(set(map(str.lower, v))):
            raise ValueError("List must contain unique items (case-insensitive)")
        return v

    @model_validator(mode="after")
    def hepatic_subset_of_diseases(self):
        disease_set = set(s.strip().lower() for s in self.diseases)
        hepatic_set = set(s.strip().lower() for s in self.hepatic_diseases)
        missing = hepatic_set - disease_set
        if missing:
            raise ValueError(
                f"hepatic_diseases contains items not present in diseases: {sorted(missing)}"
            )

        return self


###############################################################################
class BloodTest(BaseModel):
    """A single blood test result extracted from text."""

    name: str = Field(
        ..., description="Test name exactly as found (minimally normalized)."
    )
    value: float | None = Field(
        None, description="Numeric value if applicable (dot-decimal)."
    )
    value_text: str | None = Field(
        None, description="Raw textual value when not numeric (e.g., '1:80')."
    )
    unit: str | None = Field(None, description="Unit as found, if present.")
    cutoff: float | None = Field(None, description="Cutoff/upper limit if provided.")
    cutoff_unit: str | None = Field(
        None, description="Cutoff unit if specified; often same as unit."
    )
    note: str | None = Field(
        None, description="Parenthetical note not related to cutoff."
    )
    context_date: str | None = Field(
        None,
        description="ISO YYYY-MM-DD if parsed, else original date string for this batch.",
    )

    @field_validator("name")
    @classmethod
    def _normalize_name(cls, v: str) -> str:
        v = re.sub(r"\s+", " ", v.strip())
        return v.rstrip(",:;.- ")


# -----------------------------------------------------------------------------
class PatientBloodTests(BaseModel):
    """Container for parsed blood test entries."""

    entries: list[BloodTest] = Field(default_factory=list)


###############################################################################
class DrugEntry(BaseModel):
    """A single drug prescription extracted from text."""

    name: str = Field(..., description="Drug name as found in the source text.")
    dosage: str | None = Field(None, description="Dosage or concentration details.")
    administration_mode: str | None = Field(
        None, description="Pharmaceutical form or administration mode (e.g., cpr, sir)."
    )
    daytime_administration: list[float] = Field(
        default_factory=list,
        description="Administration schedule across the day (four slots).",
    )
    suspension_status: bool | None = Field(
        None, description="True if the drug is suspended, False if explicitly active."
    )
    suspension_date: str | None = Field(
        None, description="Suspension date in the original format, if captured."
    )

    @field_validator("daytime_administration")
    @classmethod
    def _validate_schedule(cls, value: list[float]) -> list[float]:
        if value and len(value) != 4:
            raise ValueError("daytime_administration must contain exactly four values.")
        return value


# -----------------------------------------------------------------------------
class PatientDrugs(BaseModel):
    """Container for parsed drug entries."""

    entries: list[DrugEntry] = Field(default_factory=list)


###############################################################################
class LiverToxMatchInfo(BaseModel):
    nbk_id: str = Field(..., min_length=1, max_length=50)
    matched_name: str = Field(..., min_length=1, max_length=200)
    confidence: float = Field(..., ge=0.0, le=1.0)
    reason: str = Field(..., min_length=1, max_length=50)
    notes: list[str] = Field(default_factory=list)


###############################################################################
class HepatotoxicityPatternScore(BaseModel):
    alt_multiple: float | None = Field(
        None,
        description="ALT value divided by its upper reference limit.",
    )
    alp_multiple: float | None = Field(
        None,
        description="ALP value divided by its upper reference limit.",
    )
    r_score: float | None = Field(
        None,
        description="R ratio computed as (ALT multiple) / (ALP multiple).",
    )
    classification: Literal[
        "hepatocellular",
        "cholestatic",
        "mixed",
        "indeterminate",
    ] = Field(
        "indeterminate",
        description="DILI pattern classification derived from the R ratio.",
    )


###############################################################################
class DrugToxicityFindings(BaseModel):
    pattern: list[str] = Field(default_factory=list)
    adverse_reactions: list[str] = Field(default_factory=list)

    @field_validator("pattern", "adverse_reactions")
    @classmethod
    def _normalize_unique(cls, value: list[str]) -> list[str]:
        unique: dict[str, str] = {}
        for item in value:
            if not item:
                continue
            normalized = item.strip()
            if not normalized:
                continue
            key = normalized.lower()
            if key not in unique:
                unique[key] = normalized
        return list(unique.values())


###############################################################################
class DrugHepatotoxicityAnalysis(BaseModel):
    drug_name: str = Field(..., min_length=1, max_length=200)
    source_text: str | None = Field(
        None,
        description="Excerpt from LiverTox or related knowledge base used for the analysis.",
    )
    analysis: DrugToxicityFindings | None = Field(
        None, description="Structured LLM findings for the drug."
    )
    error: str | None = Field(
        None,
        description="Optional error message if the analysis could not be completed.",
    )
    livertox_match: LiverToxMatchInfo | None = Field(
        None,
        description="Metadata about the LiverTox monograph matched for this drug.",
    )

    @model_validator(mode="after")
    def _require_result_or_error(self) -> "DrugHepatotoxicityAnalysis":
        if self.analysis is None and not self.error:
            raise ValueError("Either analysis or error must be provided for each drug.")
        return self


###############################################################################
class PatientDrugToxicityBundle(BaseModel):
    entries: list[DrugHepatotoxicityAnalysis] = Field(default_factory=list)
