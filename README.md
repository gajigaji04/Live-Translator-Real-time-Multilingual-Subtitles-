# Live Translator

실시간 음성 인식(STT)과 다국어 번역을 결합한 **실시간 음성 번역 시스템**입니다.

마이크에서 입력되는 음성을 감지하고, `faster-whisper`를 이용해 텍스트로 변환한 뒤 DeepL 또는 OpenAI를 통해 여러 언어로 번역합니다.

번역 결과는 WebSocket으로 전송할 수 있으며, OBS 등의 방송 프로그램에서 사용할 수 있도록 텍스트 파일로도 저장합니다.

---

## ✨ Features

- 🎙️ 실시간 마이크 음성 입력
- 🔊 VAD(Voice Activity Detection)를 이용한 음성 구간 감지
- 📝 faster-whisper 기반 음성 인식
- 🌐 입력 언어 자동 감지
- 🌍 다국어 동시 번역
- ⚡ 비동기 STT Worker 구조
- 🔄 DeepL / OpenAI 번역 API 선택 가능
- 📡 WebSocket을 통한 실시간 자막 전송
- 📄 `stream_caption.txt`를 통한 OBS 자막 출력
- 🖥️ OBS Browser Source와 연동 가능한 구조
- 🔐 API Key를 `.env`로 관리

---

# 🌍 지원 언어

현재 기본적으로 다음 4개 언어를 지원합니다.

| 언어   | 언어 코드 | 입력 | 번역 대상 |
| ------ | --------- | ---: | --------: |
| 한국어 | `KO`      |   ✅ |        ✅ |
| 일본어 | `JA`      |   ✅ |        ✅ |
| 영어   | `EN`      |   ✅ |        ✅ |
| 중국어 | `ZH`      |   ✅ |        ✅ |

> `ZH`는 중국어(Chinese)의 언어 코드입니다.
>
> `CN`은 중국(China)을 나타내는 국가 코드이므로 번역 언어 설정에는 `ZH`를 사용합니다.

### 입력 언어

입력 언어는 Whisper가 자동으로 감지합니다.

예:

```text
한국어 음성
↓
Whisper
↓
KO
```

또는:

```text
Japanese speech
↓
Whisper
↓
JA
```

별도로 입력 언어를 지정하지 않아도 됩니다.

### 번역 언어

번역 대상 언어는 `.env`의 `TARGET_LANGUAGES`에서 설정합니다.

```env
TARGET_LANGUAGES=JA,EN,ZH
```

이렇게 설정하면 하나의 음성을:

```text
한국어
 ├─ 일본어
 ├─ 영어
 └─ 중국어
```

로 동시에 번역합니다.

---

# 🏗️ Architecture

전체적인 처리 흐름은 다음과 같습니다.

```text
                    🎙️ Microphone
                          │
                          ▼
                 MicrophoneStream
                          │
                          ▼
                     Audio Queue
                          │
                          ▼
                     STT Worker
                          │
                    ┌─────┴─────┐
                    │           │
                   VAD       Whisper
                    │           │
                    └─────┬─────┘
                          │
                          ▼
                     Result Queue
                          │
                          ▼
                  Result Processor
                          │
                          ▼
                 ┌─────────────────┐
                 │   Translation   │
                 │                 │
                 │ DeepL / OpenAI  │
                 └────────┬────────┘
                          │
             ┌────────────┼────────────┐
             ▼            ▼            ▼
            JA           EN           ZH
             │            │            │
             └────────────┼────────────┘
                          │
                ┌─────────┴─────────┐
                ▼                   ▼
           WebSocket           Text File
                │                   │
                ▼                   ▼
              OBS            stream_caption.txt
```

---

# 📁 Project Structure

```text
live-translator/
│
├─ app/
│  │
│  ├─ audio/
│  │  ├─ microphone.py
│  │  └─ vad.py
│  │
│  ├─ stt/
│  │  ├─ whisper.py
│  │  └─ worker.py
│  │
│  ├─ translation/
│  │  └─ translator.py
│  │
│  ├─ server/
│  │  └─ websocket.py
│  │
│  ├─ output/
│  │  └─ text_file.py
│  │
│  ├─ config.py
│  └─ main.py
│
├─ web/
│  └─ index.html
│
├─ .env
├─ .env.example
├─ requirements.txt
└─ README.md
```

---

# 🔎 각 파일의 역할

## `app/main.py`

프로그램의 전체 실행 흐름을 관리합니다.

주요 역할:

```text
Microphone
↓
Audio Queue
↓
STT Worker
↓
Result Queue
↓
Translation
↓
WebSocket / TXT
```

각 작업을 `asyncio` Task로 분리하여 음성을 받는 동안 Whisper 처리가 전체 마이크 입력을 막지 않도록 구성되어 있습니다.

---

## `app/audio/microphone.py`

마이크에서 오디오 데이터를 가져옵니다.

기본 설정:

```env
SAMPLE_RATE=16000
CHANNELS=1
CHUNK_MS=100
```

100ms 단위의 오디오 Chunk를 생성하여 Queue로 전달합니다.

마이크 입력과 음성 인식 작업을 분리하기 때문에 Whisper가 처리 중이어도 새로운 음성 데이터를 계속 받을 수 있습니다.

---

## `app/audio/vad.py`

Voice Activity Detection을 담당합니다.

현재는 RMS 기반의 간단한 VAD를 사용합니다.

```text
음성 시작
↓
오디오 누적
↓
침묵 감지
↓
음성 구간 완성
↓
Whisper로 전달
```

너무 짧은 음성이나 일정 시간 이상의 침묵은 하나의 음성 문장으로 처리하지 않습니다.

> 향후 Silero VAD 등의 보다 정교한 VAD로 교체할 수 있도록 분리되어 있습니다.

---

## `app/stt/whisper.py`

`faster-whisper`를 이용하여 음성을 텍스트로 변환합니다.

현재 기본 설정:

```env
WHISPER_MODEL=small
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8
WHISPER_LANGUAGE=auto
```

`WHISPER_LANGUAGE=auto`로 설정하면 Whisper가 입력 언어를 자동으로 감지합니다.

예:

```text
한국어 → ko
일본어 → ja
영어 → en
중국어 → zh
```

---

## `app/stt/worker.py`

음성 인식 작업을 담당하는 Worker입니다.

중요한 이유는 **마이크 입력과 Whisper 처리를 분리하기 위해서**입니다.

기존처럼 하나의 루프에서:

```text
음성 입력
↓
Whisper
↓
번역
↓
다시 음성 입력
```

방식으로 처리하면 Whisper나 번역 API가 처리되는 동안 마이크 입력이 밀릴 수 있습니다.

현재는:

```text
Microphone
     ↓
Audio Queue
     ↓
STT Worker
     ↓
Result Queue
```

구조로 분리되어 있습니다.

---

# 🌐 Translation

## `app/translation/translator.py`

번역 API를 담당합니다.

현재 지원:

- DeepL
- OpenAI

`.env`에서 선택합니다.

```env
TRANSLATION_PROVIDER=deepl
```

또는:

```env
TRANSLATION_PROVIDER=openai
```

---

# 🔤 다국어 번역 방식

예를 들어:

```env
TARGET_LANGUAGES=JA,EN,ZH
```

이고 한국어가 입력되면:

```text
Input

안녕하세요
KO
```

↓

```text
JA → こんにちは
EN → Hello
ZH → 大家好
```

처럼 여러 번역을 동시에 수행합니다.

같은 언어로 번역할 필요가 없는 경우에는 API를 호출하지 않고 원문을 사용합니다.

예:

```text
입력: 일본어
대상: JA
```

이면:

```text
JA → 원문 유지
```

합니다.

---

# ⚡ 병렬 번역

여러 언어를 번역할 때 각 번역 요청을 순차적으로 기다리지 않고 `asyncio.gather()`를 사용하여 동시에 요청합니다.

```text
             STT
              │
              ▼
       "안녕하세요"
              │
      ┌───────┼───────┐
      ▼       ▼       ▼
     JA      EN      ZH
      │       │       │
      ▼       ▼       ▼
   DeepL    DeepL    DeepL
```

이를 통해 다국어 번역 결과가 가능한 한 비슷한 시점에 완성되도록 합니다.

---

# 📡 WebSocket

## `app/server/websocket.py`

실시간 자막 데이터를 WebSocket으로 전송합니다.

기본 주소:

```text
ws://localhost:8765
```

클라이언트가 연결되면 번역 결과를 JSON 형태로 전송합니다.

예:

```json
{
  "type": "caption",
  "status": "final",
  "source_language": "ko",
  "source_text": "안녕하세요",
  "translations": {
    "JA": "こんにちは",
    "EN": "Hello",
    "ZH": "大家好"
  }
}
```

WebSocket을 이용하기 때문에 향후 다음과 같은 클라이언트를 연결할 수 있습니다.

```text
실시간 웹 자막
OBS Browser Source
별도 데스크톱 UI
방송용 자막 프로그램
```

---

# 📄 Text Output

## `app/output/text_file.py`

번역 결과를 텍스트 파일에 저장합니다.

기본 파일:

```text
stream_caption.txt
```

현재 OBS에서 사용하기 쉽도록 기본적으로 일본어(`JA`)를 우선 출력합니다.

우선순위:

```text
JA
↓
EN
↓
ZH
↓
원문
```

따라서 현재 설정에서 일본어 번역이 존재하면:

```text
stream_caption.txt
```

에는 일본어 자막이 기록됩니다.

---

# 🎥 OBS 사용

OBS에서 텍스트 파일을 이용한 자막을 사용할 수 있습니다.

프로그램을 실행하면:

```text
stream_caption.txt
```

파일이 생성/갱신됩니다.

OBS에서:

```text
Sources
→ Text
→ Read from file
```

형태로 해당 파일을 지정하면 번역 결과를 방송 화면에 표시할 수 있습니다.

> OBS 버전이나 운영체제 설정에 따라 메뉴 이름이 조금 다를 수 있습니다.

---

# ⚙️ Configuration

## `.env`

프로젝트 루트에 `.env` 파일을 생성합니다.

예:

```env
SAMPLE_RATE=16000
CHANNELS=1
CHUNK_MS=100

WHISPER_MODEL=small
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8
WHISPER_LANGUAGE=auto

VAD_THRESHOLD=0.01
MIN_SPEECH_MS=250
MIN_SILENCE_MS=400

TRANSLATION_PROVIDER=deepl

DEEPL_API_KEY=
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini

TARGET_LANGUAGES=JA,EN,ZH

WS_HOST=localhost
WS_PORT=8765

CAPTION_FILE=stream_caption.txt
```

---

# 🔐 API Key 설정

### DeepL 사용

```env
TRANSLATION_PROVIDER=deepl
DEEPL_API_KEY=YOUR_API_KEY
```

### OpenAI 사용

```env
TRANSLATION_PROVIDER=openai
OPENAI_API_KEY=YOUR_API_KEY
OPENAI_MODEL=gpt-4o-mini
```

API Key는 절대 Git에 커밋하지 않습니다.

`.gitignore`에 다음이 포함되어 있는지 확인합니다.

```gitignore
.env
```

공개 저장소에는 실제 API Key를 작성하지 않습니다.

---

# 🌎 번역 언어 설정 방법

## 일본어 + 영어 + 중국어

```env
TARGET_LANGUAGES=JA,EN,ZH
```

## 영어만

```env
TARGET_LANGUAGES=EN
```

## 일본어 + 영어

```env
TARGET_LANGUAGES=JA,EN
```

## 모든 지원 언어

```env
TARGET_LANGUAGES=KO,JA,EN,ZH
```

단, 입력 언어와 동일한 언어는 번역 API를 호출하지 않고 원문을 사용합니다.

---

# ▶️ Installation

## 1. Repository Clone

```bash
git clone <repository-url>
cd live-translator
```

---

## 2. Virtual Environment

Windows:

```powershell
python -m venv .venv
```

활성화:

```powershell
.venv\Scripts\Activate.ps1
```

---

## 3. Dependencies

```powershell
pip install -r requirements.txt
```

---

## 4. Environment Variables

`.env.example`을 참고하여 `.env`를 생성합니다.

```text
.env.example
    ↓
.env
```

그리고 사용할 번역 API Key를 설정합니다.

---

# ▶️ Run

가상환경이 활성화된 상태에서:

```powershell
python -m app.main
```

정상적으로 실행되면 다음과 비슷한 로그가 출력됩니다.

```text
==================================================
Realtime Speech Translator
==================================================
Target languages: JA, EN, ZH
Loading Whisper model: small
WebSocket server: ws://localhost:8765
Listening...
[Audio Producer] Started
🎙️ Microphone started
[STT Worker] Started
[Result Processor] Started
```

이후 마이크에 말을 하면:

```text
[VAD] Speech started
[VAD] Speech ended (1.00s)
[STT Worker] Transcribing...

[ko] 안녕하세요

[JA] こんにちは
[EN] Hello
[ZH] 大家好
```

형태로 출력됩니다.

---

# 🧪 Example

한국어:

```text
안녕하세요.
```

Whisper:

```text
language = ko
text = 안녕하세요
```

Translation:

```text
JA → こんにちは
EN → Hello
ZH → 大家好
```

WebSocket:

```json
{
  "type": "caption",
  "status": "final",
  "source_language": "ko",
  "source_text": "안녕하세요",
  "translations": {
    "JA": "こんにちは",
    "EN": "Hello",
    "ZH": "大家好"
  }
}
```

---

# 🧠 처리 로직

전체 처리 과정은 다음과 같습니다.

### 1. Microphone

마이크에서 100ms 단위의 오디오 Chunk를 받습니다.

```text
Microphone
↓
100ms Audio Chunk
```

### 2. Audio Queue

마이크와 STT 작업 사이에 Queue를 둡니다.

```text
Microphone
↓
Audio Queue
```

이렇게 하면 Whisper가 실행되는 동안에도 마이크 입력을 계속 받을 수 있습니다.

### 3. VAD

음성이 시작되고 끝나는 시점을 감지합니다.

```text
Silence
↓
Speech Start
↓
Speech
↓
Silence
↓
Speech End
```

### 4. Whisper

음성 구간을 Whisper에 전달합니다.

```text
Audio Segment
↓
faster-whisper
↓
Text + Language
```

예:

```json
{
  "text": "안녕하세요",
  "language": "ko"
}
```

### 5. Translation

감지된 언어와 설정된 대상 언어를 기준으로 번역합니다.

```text
KO
├── JA
├── EN
└── ZH
```

### 6. Output

결과를 두 곳으로 전달합니다.

```text
Translation
   │
   ├── WebSocket
   │
   └── stream_caption.txt
```

---

# ⚠️ 현재의 한계

현재 버전은 실시간 번역 시스템의 프로토타입입니다.

### 1. STT 정확도

Whisper의 음성 인식 결과에 따라 번역 결과도 영향을 받습니다.

예:

```text
실제 발화
"그래도 이렇게 작동하네"

STT
"그래도 이렇게 작동"
```

이 경우 번역 API는 잘못 인식된 텍스트를 기준으로 번역하기 때문에 결과가 부자연스러울 수 있습니다.

즉:

```text
STT 오류
↓
번역 입력 오류
↓
번역 결과도 부정확할 가능성
```

이 있습니다.

---

### 2. 현재 VAD

현재는 RMS 기반의 간단한 VAD를 사용합니다.

따라서 다음과 같은 상황에서 정확도가 떨어질 수 있습니다.

- 주변 소음
- 작은 목소리
- 갑작스러운 음량 변화
- 단어 사이의 긴 pause
- 음악이나 게임 소리

향후 Silero VAD 등의 음성 특화 모델을 적용할 수 있습니다.

---

### 3. 완전한 Streaming STT는 아님

현재 구조는:

```text
음성 시작
↓
음성 구간 수집
↓
침묵 감지
↓
Whisper
↓
번역
```

방식입니다.

따라서 문장을 말하는 도중에 글자가 계속 업데이트되는 완전한 실시간 Partial Caption 방식은 아직 구현하지 않았습니다.

현재는 **발화가 끝난 뒤 Final Caption을 생성하는 방식**입니다.

---

# 🚧 향후 개발 계획

## Phase 1 — Core

- [x] Microphone input
- [x] Audio Queue
- [x] VAD
- [x] faster-whisper STT
- [x] Automatic language detection
- [x] DeepL translation
- [x] OpenAI translation
- [x] Multiple target languages
- [x] Async STT Worker
- [x] WebSocket server
- [x] Text file output

## Phase 2 — Real-time

- [ ] Partial STT
- [ ] Partial Caption
- [ ] Streaming translation
- [ ] Better VAD
- [ ] Translation result caching
- [ ] Persistent HTTP/WebSocket session
- [ ] Latency measurement

## Phase 3 — OBS

- [ ] OBS Browser Source UI
- [ ] Caption animation
- [ ] Language selection
- [ ] Caption styling
- [ ] Multiple language layout
- [ ] Automatic subtitle positioning

## Phase 4 — Production

- [ ] Error recovery
- [ ] API timeout/retry
- [ ] Logging system
- [ ] Performance monitoring
- [ ] CPU/GPU optimization
- [ ] Docker support
- [ ] Configuration UI

---

# 🛠️ Troubleshooting

## `DEEPL_API_KEY is not configured`

`.env`에 DeepL API Key가 설정되어 있는지 확인합니다.

```env
DEEPL_API_KEY=YOUR_API_KEY
```

그리고:

```env
TRANSLATION_PROVIDER=deepl
```

인지 확인합니다.

---

## `WebSocket server` 포트가 이미 사용 중

다른 프로그램이 `8765` 포트를 사용하고 있을 수 있습니다.

`.env`에서 변경할 수 있습니다.

```env
WS_PORT=8766
```

---

## Whisper가 너무 느림

현재 기본 모델은:

```env
WHISPER_MODEL=small
```

입니다.

CPU 환경에서 속도가 느리다면 더 작은 모델을 사용할 수 있습니다.

```env
WHISPER_MODEL=base
```

또는:

```env
WHISPER_MODEL=tiny
```

단, 모델 크기를 줄이면 일반적으로 음성 인식 정확도와 속도 사이의 trade-off가 발생합니다.

---

## 번역 결과가 이상함

먼저 Whisper의 STT 결과를 확인합니다.

```text
[ko] 실제로 인식된 문장
```

STT가 잘못 인식했다면 번역 API가 정확하게 번역하기 어렵습니다.

따라서:

```text
음성
↓
STT 결과 확인
↓
STT가 정확한가?
↓
번역 결과 확인
```

순서로 문제를 확인하는 것이 좋습니다.

---

# 🔒 Security

다음 정보는 절대 Git에 커밋하지 않습니다.

```text
.env
API Key
Secret
Token
Password
```

특히:

```env
DEEPL_API_KEY=
OPENAI_API_KEY=
```

에는 실제 API Key가 들어가기 때문에 공개 저장소에 업로드하지 않습니다.

---

# 📌 Developer Notes

이 프로젝트에서 가장 중요한 설계 포인트는 **음성 입력과 무거운 처리 작업을 분리하는 것**입니다.

잘못된 구조:

```text
Microphone
↓
Whisper
↓
Translation
↓
Microphone
```

이 구조에서는 Whisper와 번역 API가 느려질 경우 음성 입력이 밀릴 수 있습니다.

현재 구조:

```text
Microphone
↓
Audio Queue
↓
STT Worker
↓
Result Queue
↓
Translation
```

이 구조에서는 각 단계가 Queue를 통해 분리됩니다.

따라서 향후 다음 기능을 추가하기 쉽습니다.

```text
Partial STT
Streaming Translation
Multiple WebSocket Clients
OBS Browser Source
Translation Cache
GPU Worker
```

---

# 📄 License

프로젝트의 라이선스 정책에 따라 작성합니다.

예:

```text
MIT License
```

또는 별도의 라이선스 파일을 추가할 수 있습니다.
