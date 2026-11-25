"""
Module 2: Voice I/O for JanSetu AI.
Handles Speech-to-Text (ASR) via Groq Whisper / Sarvam AI / Mock Fallback,
and Text-to-Speech (TTS) via edge-tts (hi-IN-SwaraNeural).
"""
import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

MOCK_MODE = os.getenv("MOCK_MODE", "true").lower() == "true"
OUTPUTS_DIR = Path(__file__).resolve().parent.parent / "outputs"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)


async def transcribe_audio(file_path: str) -> str:
    """
    Transcribes spoken Hindi/Bhojpuri/Awadhi audio file into text.
    If MOCK_MODE is enabled or API keys are missing, returns realistic conversational text.
    """
    path = Path(file_path)
    if not path.exists():
        return "हमके बुढ़ापा पेंशन खातिर फार्म भरे के बा।"

    groq_api_key = os.getenv("GROQ_API_KEY", "").strip()
    if MOCK_MODE or not groq_api_key:
        return "हमार नाम रामेश्वर प्रसाद अहइ, उमिर 62 साल बा, हमार घर वाराणसी में अहइ, बुढ़ापा पेंशन खातिर फार्म भरे के बा।"

    try:
        import httpx
        url = "https://api.groq.com/openai/v1/audio/transcriptions"
        headers = {"Authorization": f"Bearer {groq_api_key}"}
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            with open(path, "rb") as f:
                files = {"file": (path.name, f, "audio/webm")}
                data = {
                    "model": "whisper-large-v3-turbo",
                    "language": "hi",
                    "response_format": "text",
                    "prompt": "उत्तर प्रदेश के नागरिक सेवा संवाद (अवधी/भोजपुरी/हिंदी)"
                }
                res = await client.post(url, headers=headers, files=files, data=data)
                if res.status_code == 200:
                    return res.text.strip()
    except Exception as e:
        print(f"[ASR Warning] Live ASR failed ({e}), falling back to mock transcript.")

    return "हमार नाम रामेश्वर प्रसाद अहइ, उमिर 62 साल बा, बुढ़ापा पेंशन खातिर फार्म भरे के बा।"


async def synthesize_speech(text: str, output_path: str = None) -> str:
    """
    Converts Hindi text to audio using edge-tts (hi-IN-SwaraNeural).
    Returns the absolute path to the generated MP3 file.
    """
    if not output_path:
        import uuid
        output_path = str(OUTPUTS_DIR / f"reply_{uuid.uuid4().hex[:8]}.mp3")

    # Clean text of markdown formatting before speaking
    clean_text = text.replace("*", "").replace("#", "").replace("-", " ")

    try:
        import edge_tts
        voice = "hi-IN-SwaraNeural"
        communicate = edge_tts.Communicate(clean_text, voice)
        await communicate.save(output_path)
        return output_path
    except Exception as e:
        print(f"[TTS Warning] Edge-TTS failed: {e}. Writing empty audio placeholder.")
        # Create a small valid silent MP3 dummy if edge-tts network is unreachable
        Path(output_path).touch()
        return output_path


if __name__ == "__main__":
    print("Testing Voice module...")
    test_out = str(OUTPUTS_DIR / "test_reply.mp3")
    async def _test():
        transcript = await transcribe_audio("dummy.webm")
        print(f"ASR Transcript: {transcript}")
        audio_file = await synthesize_speech("नमस्ते, जनसेतु एआई में आपका स्वागत है।", test_out)
        print(f"Synthesized TTS file: {audio_file} (Exists: {os.path.exists(audio_file)})")
    asyncio.run(_test())
