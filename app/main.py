import asyncio
import numpy as np

from app.audio.microphone import (
    MicrophoneStream
)

from app.stt.whisper import (
    WhisperSTT
)

from app.translation.translator import (
    Translator
)

from app.server.websocket import (
    CaptionServer
)

from app.output.text_file import (
    TextFileOutput
)

from app.config import (
    TARGET_LANGUAGE,
    WS_HOST,
    WS_PORT,
    CAPTION_FILE,
)


async def main():

    print("=" * 50)

    print(
        "Realtime Speech Translator"
    )

    print("=" * 50)

    stt = WhisperSTT()

    translator = Translator(
        TARGET_LANGUAGE
    )

    microphone = MicrophoneStream()

    output = TextFileOutput(
        CAPTION_FILE
    )

    server = CaptionServer(
        WS_HOST,
        WS_PORT
    )

    await server.start()

    audio_buffer = []

    buffer_seconds = 2.0

    sample_rate = 16000

    max_samples = int(
        buffer_seconds * sample_rate
    )

    print(
        f"Target language: "
        f"{TARGET_LANGUAGE}"
    )

    print("Listening...")

    async for chunk in microphone.read():

        audio_buffer.append(chunk)

        current_samples = sum(
            len(x)
            for x in audio_buffer
        )

        if current_samples < max_samples:
            continue

        audio = np.concatenate(
            audio_buffer
        )

        audio_buffer.clear()

        # ---------------------
        # STT
        # ---------------------

        result = await asyncio.to_thread(
            stt.transcribe,
            audio
        )

        text = result["text"]

        if not text:
            continue

        source_language = (
            result["language"]
        )

        print(
            f"[{source_language}] "
            f"{text}"
        )

        # ---------------------
        # Translation
        # ---------------------

        translated = (
            await translator.translate(
                text,
                source_language
            )
        )

        print(
            f"[{TARGET_LANGUAGE}] "
            f"{translated}"
        )

        # ---------------------
        # WebSocket
        # ---------------------

        await server.broadcast(
            {
                "type": "final",
                "source_language":
                    source_language,
                "source_text": text,
                "target_language":
                    TARGET_LANGUAGE,
                "text": translated,
            }
        )

        # ---------------------
        # TXT
        # ---------------------

        await output.write(
            translated
        )


if __name__ == "__main__":

    try:

        asyncio.run(main())

    except KeyboardInterrupt:

        print(
            "\nStopped."
        )