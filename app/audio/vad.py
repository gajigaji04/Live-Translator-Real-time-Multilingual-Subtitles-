import numpy as np


class SpeechSegmenter:
    def __init__(
        self,
        sample_rate: int = 16000,
        threshold: float = 0.01,
        min_speech_ms: int = 250,
        min_silence_ms: int = 400,
    ):
        self.sample_rate = sample_rate
        self.threshold = threshold

        self.min_speech_samples = int(
            sample_rate * min_speech_ms / 1000
        )

        self.min_silence_samples = int(
            sample_rate * min_silence_ms / 1000
        )

        self.buffer: list[np.ndarray] = []

        self.is_speaking = False
        self.silence_samples = 0

    def process(
        self,
        audio: np.ndarray,
    ) -> np.ndarray | None:

        # RMS 기반 음성 감지
        rms = np.sqrt(
            np.mean(
                np.square(audio)
            )
        )

        is_voice = rms >= self.threshold

        # -------------------------
        # 음성
        # -------------------------

        if is_voice:

            if not self.is_speaking:
                print("[VAD] Speech started")

            self.is_speaking = True
            self.silence_samples = 0

            self.buffer.append(audio)

            return None

        # -------------------------
        # 무음
        # -------------------------

        if not self.is_speaking:
            return None

        # 음성 중이었다면
        # 무음도 일단 버퍼에 포함
        self.buffer.append(audio)

        self.silence_samples += len(audio)

        # 충분히 오래 침묵했으면
        # 하나의 발화가 끝났다고 판단
        if self.silence_samples >= self.min_silence_samples:

            segment = np.concatenate(
                self.buffer
            )

            self.buffer.clear()

            self.is_speaking = False
            self.silence_samples = 0

            # 너무 짧은 소리는 무시
            if len(segment) < self.min_speech_samples:

                print(
                    "[VAD] Speech too short"
                )

                return None

            duration = (
                len(segment)
                / self.sample_rate
            )

            print(
                f"[VAD] Speech ended "
                f"({duration:.2f}s)"
            )

            return segment

        return None