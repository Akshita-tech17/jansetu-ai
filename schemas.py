from __future__ import annotations
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


class FormSlots(BaseModel):
    """Extracted citizen slot information for Uttar Pradesh public schemes."""
    scheme_type: Optional[str] = Field(
        default=None,
        description="Identified scheme key: old_age_pension, income_cert, caste_cert, pm_kisan, jansunwai"
    )
    applicant_name: Optional[str] = Field(default=None, description="Citizen's full legal name")
    father_or_husband_name: Optional[str] = Field(default=None, description="Father or husband name")
    age: Optional[int] = Field(default=None, description="Age in completed years")
    district: Optional[str] = Field(default=None, description="Uttar Pradesh district (e.g., Lucknow, Varanasi, Gorakhpur)")
    residency_type: Optional[Literal["rural", "urban"]] = Field(
        default=None,
        description="Residency area: rural (ग्रामीण) or urban (शहरी)"
    )
    annual_income: Optional[float] = Field(default=None, description="Total annual family income in INR")
    grievance_summary: Optional[str] = Field(default=None, description="Brief summary for Jansunwai grievances")
    missing_fields: List[str] = Field(
        default_factory=list,
        description="List of required slot names that are still missing"
    )


class EligibilityResult(BaseModel):
    """Automated eligibility assessment based on grounded UP scheme rules."""
    is_eligible: Optional[bool] = Field(
        default=None,
        description="True if eligible, False if disqualified, None if incomplete data"
    )
    reasons: List[str] = Field(
        default_factory=list,
        description="Bullet reasons in clear Hindi explaining eligibility or disqualification"
    )
    citations: List[str] = Field(
        default_factory=list,
        description="Cited rule markdown source files and specific criteria matched"
    )


class AgentResponse(BaseModel):
    """Output contract for single-turn Vernacular LLM agent."""
    normalized_hindi: str = Field(
        ...,
        description="Awadhi/Bhojpuri/regional dialect input normalized into standard Hindi"
    )
    reply_hindi: str = Field(
        ...,
        description="Conversational, empathetic response in plain Hindi asking for 1-2 missing fields or confirming next steps"
    )
    slots: FormSlots = Field(..., description="Current accumulated form slots")
    eligibility: EligibilityResult = Field(..., description="Current eligibility evaluation")
    ready_for_docs: bool = Field(
        default=False,
        description="True if essential slots are filled and applicant is eligible to upload Aadhaar/Income certificate"
    )


class DocCheckResult(BaseModel):
    """Telemetry and outcome of Document Pre-Check Guard (Laplacian Blur + Name Matching)."""
    passed: bool = Field(..., description="True if document satisfies clarity and name consistency checks")
    is_blurry: bool = Field(..., description="True if blur_score is below the threshold")
    blur_score: float = Field(..., description="Laplacian variance score of the normalized image")
    extracted_name: Optional[str] = Field(default=None, description="Name extracted from document via OCR/Vision")
    name_match_score: Optional[float] = Field(default=None, description="Fuzzy match percentage (0-100) with applicant name")
    warning_hindi: str = Field(default="", description="Citizen-friendly Hindi instruction if document check fails")


class SessionState(BaseModel):
    """In-memory multi-turn conversational session container."""
    session_id: str
    history: List[Dict[str, str]] = Field(default_factory=list)
    slots: FormSlots = Field(default_factory=FormSlots)
    doc_verified: bool = False
    doc_result: Optional[DocCheckResult] = None
    created_at: Optional[str] = None


if __name__ == "__main__":
    # Smoke test Pydantic serialization
    sample_slots = FormSlots(
        scheme_type="old_age_pension",
        applicant_name="रामेश्वर प्रसाद",
        age=62,
        district="वाराणसी",
        residency_type="rural",
        annual_income=42000,
        missing_fields=["father_or_husband_name"]
    )
    res = AgentResponse(
        normalized_hindi="मुझे वृद्धावस्था पेंशन के लिए आवेदन करना है।",
        reply_hindi="नमस्ते रामेश्वर जी! आपकी उम्र 60 वर्ष से अधिक है और ग्रामीण आय सीमा (₹46,080) के अंतर्गत है। कृपया अपने पिता या पति का नाम बताएं।",
        slots=sample_slots,
        eligibility=EligibilityResult(
            is_eligible=True,
            reasons=["उम्र 60 वर्ष या उससे अधिक है", "ग्रामीण आय ₹46,080 वार्षिक सीमा के भीतर है"],
            citations=["old_age_pension.md - पात्रता मानदंड"]
        ),
        ready_for_docs=False
    )
    print("schemas.py verified successfully! Sample JSON:")
    print(res.model_dump_json(indent=2))
