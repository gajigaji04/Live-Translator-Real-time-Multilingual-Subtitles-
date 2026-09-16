import asyncio

from app.audio.microphone import (
    MicrophoneStream,
)

from app.audio.vad import (
    SpeechSegmenter,
)

from app.stt.whisper import (
    WhisperSTT,
)

from app.translation.translator import (
    Translator,
)

from app.server.websocket import (
    CaptionServer,
)

from app.output.text_file import (
    TextFileOutput,
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

    # ---------------------
    # STT
    # ---------------------

    stt = WhisperSTT()

    # ---------------------
    # Translation
    # ---------------------

    translator = Translator(
        TARGET_LANGUAGE
    )

    # ---------------------
    # Microphone
    # ---------------------

    microphone = MicrophoneStream()

    # ---------------------
    # VAD
    # ---------------------

    segmenter = SpeechSegmenter(
        sample_rate=16000,
        threshold=0.01,
        min_speech_ms=250,
        min_silence_ms=400,
    )

    # ---------------------
    # Output
    # ---------------------

    output = TextFileOutput(
        CAPTION_FILE
    )

    # ---------------------
    # WebSocket
    # ---------------------

    server = CaptionServer(
        WS_HOST,
        WS_PORT,
    )

    await server.start()

    print(
        f"Target language: "
        f"{TARGET_LANGUAGE}"
    )

    print("Listening...")

    # ---------------------
    # Audio Pipeline
    # ---------------------

    async for chunk in microphone.read():

        segment = segmenter.process(
            chunk
        )

        if segment is None:
            continue

        # ---------------------
        # STT
        # ---------------------

        result = await asyncio.to_thread(
            stt.transcribe,
            segment,
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
                source_language,
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