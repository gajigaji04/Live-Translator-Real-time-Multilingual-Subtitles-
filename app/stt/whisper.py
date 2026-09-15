import numpy as np

from faster_whisper import WhisperModel

from app.config import (
    WHISPER_MODEL,
    WHISPER_DEVICE,
    WHISPER_COMPUTE_TYPE,
    WHISPER_LANGUAGE,
)


class WhisperSTT:

    def __init__(self):

        print(
            f"Loading Whisper model: "
            f"{WHISPER_MODEL}"
        )

        self.model = WhisperModel(
            WHISPER_MODEL,
            device=WHISPER_DEVICE,
            compute_type=WHISPER_COMPUTE_TYPE,
        )

    def transcribe(
        self,
        audio: np.ndarray
    ):

        language = None

        if WHISPER_LANGUAGE != "auto":
            language = WHISPER_LANGUAGE

        segments, info = self.model.transcribe(
            audio,
            language=language,

            beam_size=1,

            vad_filter=True,

            vad_parameters={
                "min_silence_duration_ms": 300,
                "speech_pad_ms": 100,
            },

            condition_on_previous_text=False,

            temperature=0.0,
        )

        text_parts = []

        for segment in segments:

            text = segment.text.strip()

            if text:
                text_parts.append(text)

        text = " ".join(text_parts)

        return {
            "text": text,
            "language": info.language,
            "language_probability": info.language_probability,
        }