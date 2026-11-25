# JanSetu AI — Team Build Plan & Progress Tracker

**Event:** AI Kaushal Hackathon (IIIT Lucknow)  
**Use Case:** Vernacular Citizen Services Assistant (Uttar Pradesh)  
**Team Size:** 3 Members  
**Submission Deadline:** November 27, 2026  
**Deliverable:** Working Local PoC + 60–90s Demo Video + Pitch Deck (packed in a `.zip` under 20MB)

---

## 1. Architecture & Tech Stack

* **Package Manager / Runtime:** Python 3.11+ / uv
* **Backend:** FastAPI + Uvicorn
* **Frontend:** Vanilla HTML, CSS, and JavaScript (Split-Screen WhatsApp + AI Inspector)
* **Voice (ASR + TTS):**
  * **ASR:** Groq (`whisper-large-v3-turbo`) or Sarvam AI (`saaras:v4`) with Mock Mode
  * **TTS:** `edge-tts` (`hi-IN-SwaraNeural`) with browser Web Speech API / MP3 fallback
* **Grounded RAG:** Hybrid FAISS + BM25 with Reciprocal Rank Fusion (RRF) over 5 curated UP scheme Markdown files
* **Agentic Core:** Single structured JSON LLM call (dialect normalization + eligibility check + multi-turn slot-filling)
* **Document Pre-Check Guard:** OpenCV Laplacian blur check + Vision/OCR extraction + RapidFuzz name-mismatch guard
* **PDF Generator:** ReportLab with Devanagari font support

---

## 2. Repository Structure

```text
jansetu-ai/
├── PLAN.md                 # Architecture + live team checklist
├── .gitignore              # Ignore .env, .venv/, __pycache__/, outputs/
├── .env                    # Local API keys + MOCK_MODE toggle (never commit)
├── .env.example            # Shared template for environment variables
├── pyproject.toml          # Project configuration
├── schemas.py              # Module 0: Shared Pydantic I/O contracts
├── data/
│   ├── schemes/            # 5 clean UP scheme Markdown files [Track A]
│   │   ├── old_age_pension.md
│   │   ├── income_cert.md
│   │   ├── caste_cert.md
│   │   ├── pm_kisan.md
│   │   └── jansunwai.md
│   ├── fonts/              # NotoSansDevanagari-Regular.ttf [Track B]
│   └── test_samples/       # 1 clear + 1 blurry dummy doc + test audio [Track B]
├── rag/
│   ├── __init__.py
│   └── retriever.py        # Module 1: Hybrid FAISS + BM25 search [Track A]
├── voice/
│   ├── __init__.py
│   └── speech.py           # Module 2: ASR + Edge-TTS wrapper [Track B]
├── core/
│   ├── __init__.py
│   └── agent.py            # Module 3: Dialect normalizer + eligibility + slot-filler [Track A]
├── vision/
│   ├── __init__.py
│   └── doc_guard.py        # Module 4: OpenCV blur check + OCR mismatch guard [Track B]
├── forms/
│   ├── __init__.py
│   └── pdf_builder.py      # Module 5: FormSlots -> Pre-filled UP Draft PDF [Track B]
├── outputs/                # Generated TTS audio & pre-filled PDFs (gitignored)
├── server.py               # Module 6a: FastAPI app (3 endpoints + static mount) [Track C]
└── static/                 # Module 6b: Split-screen WhatsApp Chat + AI Inspector [Track C]
    ├── index.html
    ├── style.css
    └── app.js
```
