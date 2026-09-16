import asyncio
import numpy as np

from app.audio.vad import SpeechSegmenter
from app.stt.whisper import WhisperSTT


class STTWorker:

    def __init__(
        self,
        audio_queue: asyncio.Queue,
        result_queue: asyncio.Queue,
    ):
        self.audio_queue = audio_queue
        self.result_queue = result_queue

        self.segmenter = SpeechSegmenter(
            sample_rate=16000,
            threshold=0.01,
            min_speech_ms=250,
            min_silence_ms=400,
        )

        self.stt = WhisperSTT()

    async def run(self):

        print(
            "[STT Worker] Started"
        )

        while True:

            chunk = await self.audio_queue.get()

            try:

                segment = (
                    self.segmenter.process(
                        chunk
                    )
                )

                if segment is None:
                    continue

                print(
                    "[STT Worker] "
                    "Transcribing..."
                )

                result = await asyncio.to_thread(
                    self.stt.transcribe,
                    segment,
                )

                text = result["text"]

                if not text:
                    continue

                await self.result_queue.put(
                    result
                )

            finally:

                self.audio_queue.task_done()