import asyncio

from app.audio.microphone import MicrophoneStream
from app.config import (
    TARGET_LANGUAGES,
    WS_HOST,
    WS_PORT,
    CAPTION_FILE,
)
from app.output.text_file import TextFileOutput
from app.server.websocket import CaptionServer
from app.stt.worker import STTWorker
from app.translation.translator import Translator


# =========================
# Audio Producer
# =========================

async def feed_audio(
    microphone: MicrophoneStream,
    audio_queue: asyncio.Queue,
):
    """
    Microphone에서 들어오는 오디오를
    STT Worker용 Queue로 전달한다.

    Microphone과 STT 처리를 분리해서
    Whisper가 실행되는 동안에도
    마이크 입력을 계속 받을 수 있게 한다.
    """

    print("[Audio Producer] Started")

    async for chunk in microphone.read():

        try:
            audio_queue.put_nowait(
                chunk
            )

        except asyncio.QueueFull:

            print(
                "[Audio Producer] "
                "STT queue full - "
                "dropping chunk"
            )


# =========================
# Translation / Output
# =========================

async def process_results(
    result_queue: asyncio.Queue,
    translator: Translator,
    server: CaptionServer,
    output: TextFileOutput,
):
    """
    STT 결과를 받아서

    STT
      ↓
    Translation
      ↓
    WebSocket
      ↓
    TXT

    순서로 처리한다.
    """

    print("[Result Processor] Started")

    while True:

        result = await result_queue.get()

        try:

            text = result.get(
                "text",
                "",
            )

            source_language = result.get(
                "language",
                "",
            )

            if not text:
                continue

            print(
                f"[{source_language}] "
                f"{text}"
            )

            translations = {}

            # =========================
            # Translate
            # =========================

            translation_tasks = []

            target_languages = []

            for target_language in TARGET_LANGUAGES:

                # 같은 언어면 번역할 필요 없음
                if (
                    target_language.lower()
                    == source_language.lower()
                ):
                    translations[
                        target_language
                    ] = text

                    continue

                target_languages.append(
                    target_language
                )

                translation_tasks.append(
                    translator.translate(
                        text,
                        source_language,
                        target_language,
                    )
                )

            # 여러 언어를 동시에 번역
            if translation_tasks:

                translated_results = (
                    await asyncio.gather(
                        *translation_tasks,
                        return_exceptions=True,
                    )
                )

                for (
                    target_language,
                    translated,
                ) in zip(
                    target_languages,
                    translated_results,
                ):

                    if isinstance(
                        translated,
                        Exception,
                    ):

                        print(
                            f"[Translation Error] "
                            f"{target_language}: "
                            f"{translated}"
                        )

                        translations[
                            target_language
                        ] = ""

                        continue

                    translations[
                        target_language
                    ] = translated

                    print(
                        f"[{target_language}] "
                        f"{translated}"
                    )

            # =========================
            # WebSocket
            # =========================

            await server.broadcast(
                {
                    "type": "caption",
                    "status": "final",
                    "source_language":
                        source_language,
                    "source_text": text,
                    "translations":
                        translations,
                }
            )

            # =========================
            # TXT Output
            # =========================

            # OBS에서 사용할 기본 언어
            # 현재는 일본어를 우선 사용한다.

            output_text = ""

            if "JA" in translations:
                output_text = translations["JA"]

            elif "EN" in translations:
                output_text = translations["EN"]

            elif "ZH" in translations:
                output_text = translations["ZH"]

            else:
                output_text = text

            if output_text:
                await output.write(
                    output_text
                )

        except Exception as error:

            print(
                "[Result Processor Error]",
                error,
            )

        finally:

            result_queue.task_done()


# =========================
# Main
# =========================

async def main():

    print("=" * 50)
    print("Realtime Speech Translator")
    print("=" * 50)

    print(
        "Target languages:",
        ", ".join(TARGET_LANGUAGES),
    )

    # =========================
    # Components
    # =========================

    microphone = MicrophoneStream()

    # Microphone과 STT Worker 사이의 Queue
    audio_queue = asyncio.Queue(
        maxsize=100
    )

    # STT 결과 Queue
    result_queue = asyncio.Queue(
        maxsize=20
    )

    stt_worker = STTWorker(
        audio_queue=audio_queue,
        result_queue=result_queue,
    )

    translator = Translator()

    server = CaptionServer(
        WS_HOST,
        WS_PORT,
    )

    output = TextFileOutput(
        CAPTION_FILE
    )

    # =========================
    # WebSocket
    # =========================

    await server.start()

    # =========================
    # Tasks
    # =========================

    audio_task = asyncio.create_task(
        feed_audio(
            microphone,
            audio_queue,
        )
    )

    stt_task = asyncio.create_task(
        stt_worker.run()
    )

    result_task = asyncio.create_task(
        process_results(
            result_queue,
            translator,
            server,
            output,
        )
    )

    print("Listening...")

    try:

        await asyncio.gather(
            audio_task,
            stt_task,
            result_task,
        )

    except KeyboardInterrupt:

        print(
            "\nStopping..."
        )

    finally:

        for task in (
            audio_task,
            stt_task,
            result_task,
        ):

            task.cancel()

        await asyncio.gather(
            audio_task,
            stt_task,
            result_task,
            return_exceptions=True,
        )


# =========================
# Entry Point
# =========================

if __name__ == "__main__":

    asyncio.run(
        main()
    )