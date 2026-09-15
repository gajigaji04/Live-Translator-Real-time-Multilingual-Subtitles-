import os
from dotenv import load_dotenv

load_dotenv()


def get_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default

    return value.lower() in ("true", "1", "yes", "y")


SAMPLE_RATE = int(os.getenv("SAMPLE_RATE", "16000"))
CHANNELS = int(os.getenv("CHANNELS", "1"))
CHUNK_MS = int(os.getenv("CHUNK_MS", "100"))

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")
WHISPER_COMPUTE_TYPE = os.getenv(
    "WHISPER_COMPUTE_TYPE",
    "int8"
)

WHISPER_LANGUAGE = os.getenv(
    "WHISPER_LANGUAGE",
    "auto"
)

VAD_THRESHOLD = float(
    os.getenv("VAD_THRESHOLD", "0.5")
)

MIN_SPEECH_MS = int(
    os.getenv("MIN_SPEECH_MS", "250")
)

MIN_SILENCE_MS = int(
    os.getenv("MIN_SILENCE_MS", "500")
)

TRANSLATION_PROVIDER = os.getenv(
    "TRANSLATION_PROVIDER",
    "deepl"
)

DEEPL_API_KEY = os.getenv(
    "DEEPL_API_KEY",
    ""
)

OPENAI_API_KEY = os.getenv(
    "OPENAI_API_KEY",
    ""
)

OPENAI_MODEL = os.getenv(
    "OPENAI_MODEL",
    "gpt-4o-mini"
)

TARGET_LANGUAGE = os.getenv(
    "TARGET_LANGUAGE",
    "JA"
)

WS_HOST = os.getenv(
    "WS_HOST",
    "localhost"
)

WS_PORT = int(
    os.getenv("WS_PORT", "8765")
)

CAPTION_FILE = os.getenv(
    "CAPTION_FILE",
    "stream_caption.txt"
)