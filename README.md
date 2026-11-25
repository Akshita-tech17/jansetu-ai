# JanSetu AI — Vernacular Citizen Services Assistant

**Event:** AI Kaushal Hackathon (IIIT Lucknow)  
**Track:** Citizen Services / Vernacular AI Assistant for Uttar Pradesh  

JanSetu AI is a voice-first, dialect-aware citizen service assistant engineered specifically for Uttar Pradesh. It normalizes regional dialects (Awadhi, Bhojpuri, and colloquial Hindi), evaluates citizen eligibility against official grounded scheme guidelines with zero hallucination, inspects citizen identity documents before submission (blur and name mismatch guards), and generates official UP e-District pre-filled draft PDFs.

---

## 🚀 Quick Start (One Command)

### Option 1: Double Click `run.bat`
Or in your terminal:
```bash
cd jansetu-ai
run.bat
```

### Option 2: Run via Python CLI
```bash
cd jansetu-ai
python -m uvicorn server:app --host 127.0.0.1 --port 8000 --reload
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser.

---

## 🏛️ Core Architecture & Implemented Modules

| Module | File | Capability |
| :--- | :--- | :--- |
| **Module 0** | `schemas.py` | Strict Pydantic I/O contracts (`FormSlots`, `EligibilityResult`, `DocCheckResult`, etc.) |
| **Module 1** | `rag/retriever.py` | Grounded hybrid RAG retriever over 5 UP scheme guidelines (`data/schemes/`) |
| **Module 2** | `voice/speech.py` | Vernacular ASR (Whisper) + TTS (`edge-tts` & Web Speech API fallback) |
| **Module 3** | `core/agent.py` | Single-turn agent for dialect normalization + eligibility check + slot-filling |
| **Module 4** | `vision/doc_guard.py` | Resolution-normalized OpenCV Laplacian blur check + RapidFuzz name mismatch guard |
| **Module 5** | `forms/pdf_builder.py` | ReportLab generator producing bilingual UP e-District application draft PDFs |
| **Module 6** | `server.py` + `static/` | FastAPI server + Split-Screen WhatsApp Chat & Live AI Inspector Telemetry UI |

---

## 🎬 1-Click Hackathon Live Demo Presets

The interface features an **AI Inspector Panel** on the right with instant 1-click test buttons for evaluators:
1. **👴 पेंशन आवेदन (Voice):** Simulates spoken Awadhi elder pension query, normalizes text, extracts slots, and retrieves eligibility limits.
2. **📷 धुंधला आधार (Blurry Test):** Tests the OpenCV Laplacian blur guard, computes variance (`< 90.0`), and flags blurry images with vernacular audio warning.
3. **✅ साफ आधार (Verified):** Validates a sharp Aadhaar image, confirms 100% name match, and unlocks form completion.
4. **📄 PDF प्रारूप:** Generates and downloads the official pre-filled UP e-District draft PDF.
