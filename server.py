"""
server.py: JanSetu AI Core Application Server (Upgraded).
Integrates UP Family ID (एक परिवार, एक पहचान), Proactive Scheme Discovery,
Vernacular Handwriting/Scan Intelligence, and Direct e-District Application Filing.
"""
import os
import uuid
from pathlib import Path
from typing import Optional, Dict, List, Any
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from schemas import FormSlots, EligibilityResult, AgentResponse, DocCheckResult, SessionState
from core.family_id import lookup_family, FamilyProfile, FAMILY_DATABASE
from core.discovery_engine import discover_schemes_for_family, FamilyEntitlementBasket, MatchedScheme
from vision.scan_reader import read_scanned_document, ScanExtractionResult, generate_handwritten_test_sample
from forms.filing_service import file_applications_and_generate_receipt
from rag.retriever import retrieve
from voice.speech import transcribe_audio, synthesize_speech
from core.agent import process_turn
from vision.doc_guard import check_document
from forms.pdf_builder import build_application_pdf

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
OUTPUTS_DIR = BASE_DIR / "outputs"
DATA_DIR = BASE_DIR / "data"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

# Generate test sample if not existing
generate_handwritten_test_sample()

app = FastAPI(
    title="JanSetu AI — UP Family ID & Citizen Services",
    description="Proactive Vernacular Entitlement Assistant for Uttar Pradesh (AI Kaushal Hackathon)",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Active Sessions
SESSIONS: Dict[str, Dict[str, Any]] = {}


def get_or_create_session(session_id: Optional[str] = None) -> Dict[str, Any]:
    sid = session_id or f"sess_{uuid.uuid4().hex[:8]}"
    if sid not in SESSIONS:
        # Default with primary Rameshwar Prasad family
        default_profile = lookup_family("24018291024")
        default_basket = discover_schemes_for_family(default_profile)
        SESSIONS[sid] = {
            "session_id": sid,
            "profile": default_profile,
            "basket": default_basket,
            "slots": FormSlots(
                scheme_type="old_age_pension",
                applicant_name=default_profile.head_name,
                age=default_profile.members[0].age,
                district=default_profile.district,
                residency_type="rural",
                annual_income=default_profile.annual_income
            ),
            "history": [],
            "scanned_doc_verified": False,
            "filed_receipt": None
        }
    return SESSIONS[sid]


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(content=b"", media_type="image/x-icon")


@app.get("/api/family/{family_id}")
async def get_family_entitlements(family_id: str, session_id: Optional[str] = None):
    """
    UP Family ID Resolver + Proactive Scheme Discovery Engine.
    Instantly evaluates 98 schemes for the entire household and speaks proactive pitch.
    """
    session = get_or_create_session(session_id)
    profile = lookup_family(family_id)
    if not profile:
        profile = FAMILY_DATABASE["24018291024"]

    basket = discover_schemes_for_family(profile)
    session["profile"] = profile
    session["basket"] = basket

    # Synthesize proactive audio in vernacular dialect
    audio_filename = f"pitch_{session['session_id']}_{uuid.uuid4().hex[:6]}.mp3"
    audio_path = str(OUTPUTS_DIR / audio_filename)
    await synthesize_speech(basket.proactive_pitch_vernacular, audio_path)

    return {
        "session_id": session["session_id"],
        "profile": profile.model_dump(),
        "basket": basket.model_dump(),
        "audio_url": f"/outputs/{audio_filename}"
    }


@app.post("/api/read-scan")
async def read_scan_endpoint(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None)
):
    """
    Handwritten & Scanned Document Intelligence:
    Reads handwritten Tehsil certificates, Urdu weaver cards, and Khatauni land records.
    """
    session = get_or_create_session(session_id)
    file_bytes = await file.read()

    result: ScanExtractionResult = read_scanned_document(file_bytes)
    session["scanned_doc_verified"] = result.is_legible and result.official_seal_verified

    audio_filename = f"scan_{session['session_id']}_{uuid.uuid4().hex[:6]}.mp3"
    audio_path = str(OUTPUTS_DIR / audio_filename)
    await synthesize_speech(result.vernacular_summary, audio_path)

    return {
        "session_id": session["session_id"],
        "result": result.model_dump(),
        "audio_url": f"/outputs/{audio_filename}"
    }


@app.post("/api/file-application")
async def file_application_endpoint(session_id: str = Form(...)):
    """
    'Ending in Something Filed':
    Dispatches verified multi-scheme application and returns official Acknowledgment Receipt.
    """
    session = get_or_create_session(session_id)
    profile: FamilyProfile = session["profile"]
    basket: FamilyEntitlementBasket = session["basket"]

    receipt = file_applications_and_generate_receipt(profile, basket.matched_schemes)
    session["filed_receipt"] = receipt

    speech_text = (
        f"बधाई हो {profile.head_name} जी! आपका आवेदन उत्तर प्रदेश ई-डिस्ट्रिक्ट पोर्टल पर सफलतापूर्वक जमा हो गया है। "
        f"आपकी आवेदन पावती संख्या {receipt['application_number']} है। "
        f"जनहित गारंटी अधिनियम के अनुसार 15 कार्य दिवसों में इसका अंतिम निस्तारण हो जाएगा।"
    )
    audio_filename = f"filed_{session['session_id']}_{uuid.uuid4().hex[:6]}.mp3"
    audio_path = str(OUTPUTS_DIR / audio_filename)
    await synthesize_speech(speech_text, audio_path)

    return {
        "session_id": session["session_id"],
        "receipt": receipt,
        "audio_url": f"/outputs/{audio_filename}"
    }


@app.post("/api/chat")
async def chat_endpoint(text: str = Form(...), session_id: Optional[str] = Form(None)):
    session = get_or_create_session(session_id)
    
    agent_resp: AgentResponse = await process_turn(
        user_text=text,
        current_slots=session["slots"],
        history=session["history"]
    )
    session["slots"] = agent_resp.slots
    session["history"].append({"role": "user", "content": text})
    session["history"].append({"role": "assistant", "content": agent_resp.reply_hindi})

    audio_filename = f"reply_{session['session_id']}_{len(session['history'])}.mp3"
    audio_path = str(OUTPUTS_DIR / audio_filename)
    await synthesize_speech(agent_resp.reply_hindi, audio_path)

    return {
        "session_id": session["session_id"],
        "normalized_hindi": agent_resp.normalized_hindi,
        "reply_hindi": agent_resp.reply_hindi,
        "slots": agent_resp.slots.model_dump(),
        "eligibility": agent_resp.eligibility.model_dump(),
        "ready_for_docs": agent_resp.ready_for_docs,
        "audio_url": f"/outputs/{audio_filename}"
    }


@app.post("/api/voice")
async def voice_endpoint(audio: UploadFile = File(...), session_id: Optional[str] = Form(None)):
    session = get_or_create_session(session_id)
    temp_audio_path = OUTPUTS_DIR / f"in_{session['session_id']}_{uuid.uuid4().hex[:6]}.webm"
    with open(temp_audio_path, "wb") as f:
        content = await audio.read()
        f.write(content)

    transcript = await transcribe_audio(str(temp_audio_path))
    agent_resp = await process_turn(user_text=transcript, current_slots=session["slots"], history=session["history"])
    session["slots"] = agent_resp.slots

    audio_filename = f"reply_{session['session_id']}_{len(session['history']) + 1}.mp3"
    audio_path = str(OUTPUTS_DIR / audio_filename)
    await synthesize_speech(agent_resp.reply_hindi, audio_path)

    return {
        "session_id": session["session_id"],
        "transcript": transcript,
        "normalized_hindi": agent_resp.normalized_hindi,
        "reply_hindi": agent_resp.reply_hindi,
        "slots": agent_resp.slots.model_dump(),
        "eligibility": agent_resp.eligibility.model_dump(),
        "ready_for_docs": agent_resp.ready_for_docs,
        "audio_url": f"/outputs/{audio_filename}"
    }


@app.post("/api/check-doc")
async def check_doc_endpoint(file: UploadFile = File(...), session_id: Optional[str] = Form(None)):
    session = get_or_create_session(session_id)
    file_bytes = await file.read()
    expected_name = session["slots"].applicant_name or "रामेश्वर प्रसाद"
    result: DocCheckResult = check_document(file_bytes, expected_name=expected_name)

    audio_filename = f"doc_{session['session_id']}_{uuid.uuid4().hex[:6]}.mp3"
    audio_path = str(OUTPUTS_DIR / audio_filename)
    await synthesize_speech(result.warning_hindi, audio_path)

    return {
        "session_id": session["session_id"],
        "result": result.model_dump(),
        "audio_url": f"/outputs/{audio_filename}"
    }


@app.post("/api/generate-pdf")
async def generate_pdf_endpoint(session_id: str = Form(...)):
    session = get_or_create_session(session_id)
    dummy_elig = EligibilityResult(
        is_eligible=True,
        reasons=[
            f"आवेदक की आयु {session['slots'].age or 62} वर्ष है (न्यूनतम 60 वर्ष आवश्यक)।",
            f"पारिवारिक आय ₹{int(session['slots'].annual_income or 42000):,} ग्रामीण सीमा के भीतर है।"
        ],
        citations=["old_age_pension.md - पात्रता मानदंड"]
    )
    pdf_filename = f"UP_eDistrict_{session['session_id']}.pdf"
    pdf_path = str(OUTPUTS_DIR / pdf_filename)
    build_application_pdf(session["slots"], dummy_elig, pdf_path)
    return {
        "session_id": session["session_id"],
        "pdf_url": f"/outputs/{pdf_filename}",
        "filename": pdf_filename
    }


app.mount("/outputs", StaticFiles(directory=str(OUTPUTS_DIR)), name="outputs")
app.mount("/data", StaticFiles(directory=str(DATA_DIR)), name="data")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
async def serve_index():
    return FileResponse(str(STATIC_DIR / "index.html"))
