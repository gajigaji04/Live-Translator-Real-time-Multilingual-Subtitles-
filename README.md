# Live Translator

마이크 입력을 실시간으로 음성 인식하고, DeepL 또는 OpenAI로 번역해 OBS 브라우저 소스와 `stream_caption.txt`에 동시에 내보내는 Python 3.10+ 파이프라인입니다.

## 폴더 구조

```text
live-translator/
|-- app/
|   |-- audio.py              # sounddevice 입력 콜백과 asyncio 큐
|   |-- config.py             # 환경 변수 및 언어 매핑
|   |-- events.py             # partial/final 자막 이벤트
|   |-- main.py               # 파이프라인 실행 진입점
|   |-- publisher.py          # WebSocket/텍스트 파일 출력
|   |-- stt.py                # 에너지 VAD + faster-whisper
|   |-- translator.py         # DeepL/OpenAI 비동기 번역
|   `-- websocket_server.py   # OBS 클라이언트용 WebSocket
|-- web/index.html            # OBS Browser Source 템플릿
|-- .env.example
|-- requirements.txt
`-- README.md
```

## 설치 및 실행

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python -m app.main
```

첫 실행 때 `faster-whisper` 모델이 다운로드됩니다. CPU에서는 `STT_MODEL=base` 또는 `small`, NVIDIA GPU에서는 `STT_DEVICE=cuda`와 적절한 `STT_COMPUTE_TYPE=float16`을 권장합니다.

## 환경 변수

`.env.example`을 `.env`로 복사한 뒤 다음을 설정합니다.

- `SOURCE_LANGUAGE=auto`: 자동 감지. `KR`, `EN`, `JP`, `CN`으로 고정할 수도 있습니다.
- `TARGET_LANGUAGE=EN`: `KR`, `EN`, `JP`, `CN` 중 하나.
- `TRANSLATION_PROVIDER=deepl` 또는 `openai`와 해당 API 키.
- `DEEPL_API_KEY` 또는 `OPENAI_API_KEY` 중 선택한 공급자의 키.
- `CAPTION_FILE`: OBS 텍스트 소스나 다른 프로그램이 읽을 파일 경로.

지원 언어 표기는 애플리케이션에서 `KR`, `EN`, `JP`, `CN`을 사용하고, API가 요구하는 `KO`, `JA`, `ZH` 표기는 내부에서 변환합니다.

## OBS 설정

1. OBS에서 `Browser` 소스를 추가합니다.
2. 로컬 파일로 `web/index.html`을 선택합니다.
3. 기본 WebSocket 주소는 `ws://127.0.0.1:8765`입니다. 다른 주소는 `web/index.html?ws=ws://호스트:포트`로 지정합니다.
4. 페이지는 투명 배경이며, `partial` 이벤트는 흐리게, `final` 이벤트는 선명하게 표시합니다.

WebSocket 이벤트 예시:

```json
{
  "text": "안녕하세요",
  "kind": "final",
  "source_language": "KR",
  "target_language": "EN",
  "translation": "Hello",
  "timestamp": 1720000000.0
}
```

## 지연 시간 및 VAD 튜닝

기본 지연은 오디오 블록(`AUDIO_BLOCK_MS`) + 부분 인식 주기(`PARTIAL_INTERVAL_MS`) + 모델 추론 시간의 합입니다.

- `AUDIO_BLOCK_MS=160~320`: 160은 반응성이 좋고 CPU 호출이 많습니다. 320은 안정적인 기본값입니다.
- `PARTIAL_INTERVAL_MS=500~800`: 500은 더 자주 갱신하고, 700은 비용과 반응성의 균형입니다.
- `SILENCE_MS=500~800`: 짧게 하면 완결 자막이 빠르지만 문장이 끊길 수 있습니다.
- `VAD_THRESHOLD=0.008~0.025`: 마이크 RMS 기준입니다. 조용한 환경은 낮추고, 팬/키보드 소음이 있으면 높입니다.
- `MIN_SPEECH_MS=200~300`: 클릭이나 짧은 잡음을 발화로 인식하지 않게 합니다.
- `STT_MODEL`: 모델이 클수록 정확하지만 추론 지연이 늘어납니다. 먼저 `base`/`small`로 측정하세요.

실제 운영 순서는 `AUDIO_BLOCK_MS=320`, `PARTIAL_INTERVAL_MS=700`, `SILENCE_MS=650`에서 시작한 뒤, CPU 사용률과 자막 체감 지연을 함께 보며 한 변수씩 조정하는 것이 좋습니다. VAD는 빠른 에너지 게이트로 발화 구간을 만들고, faster-whisper의 `vad_filter`가 최종 오디오를 한 번 더 정리합니다.

## 출력 흐름

```text
Microphone -> asyncio queue -> energy VAD -> faster-whisper
		  -> partial/final CaptionEvent -> DeepL/OpenAI
		  -> WebSocket -> OBS HTML
		  -> stream_caption.txt
```

API 키가 비어 있으면 번역 요청을 보내지 않고 인식 텍스트를 그대로 출력하므로, 오디오와 STT 경로를 먼저 점검할 수 있습니다.
