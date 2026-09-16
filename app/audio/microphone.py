import asyncio
import numpy as np
import sounddevice as sd

from app.config import (
    SAMPLE_RATE,
    CHANNELS,
    CHUNK_MS,
)


class MicrophoneStream:

    def __init__(self):

        self.queue = asyncio.Queue(
            maxsize=20
        )

        self.chunk_size = int(
            SAMPLE_RATE * CHUNK_MS / 1000
        )

        self.loop = asyncio.get_running_loop()

    def callback(
        self,
        indata,
        frames,
        time,
        status,
    ):

        if status:
            print("[Audio]", status)

        audio = (
            indata[:, 0]
            .copy()
            .astype(np.float32)
        )

        self.loop.call_soon_threadsafe(
            self._put_audio,
            audio,
        )

    def _put_audio(
        self,
        audio: np.ndarray,
    ):

        try:
            self.queue.put_nowait(
                audio
            )

        except asyncio.QueueFull:

            print(
                "[Audio] Queue full - "
                "dropping chunk"
            )

    async def read(self):

        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="float32",
            blocksize=self.chunk_size,
            callback=self.callback,
        ):

            print(
                "🎙️ Microphone started"
            )

            while True:

                chunk = (
                    await self.queue.get()
                )

                yield np.asarray(
                    chunk,
                    dtype=np.float32,
                )