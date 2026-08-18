# CaptureMate_BE

CaptureMate 백엔드 API 서버 레포입니다.

CaptureMate는 사용자가 저장한 캡쳐 이미지를 분석해 카테고리를 분류하고, 카테고리별 상세 정보를 추출하여 장소 보기, 상품 보기, 캘린더 저장 등 추천 액션에 필요한 데이터를 제공합니다.

백엔드는 별도의 사용자 계정이나 서버 DB를 사용하지 않으며, 캡쳐 및 분석 결과는 iOS 앱의 SwiftData에 저장됩니다.

## 🧱 기술 스택

| 구분                   | 기술                            |
| -------------------- | ----------------------------- |
| Language             | Python 3.11                   |
| Framework            | FastAPI                       |
| OCR                  | PaddleOCR                     |
| Text Classification  | RoBERTa                       |
| Image Classification | CLIP                          |
| Field Extraction     | Gemini API                    |
| Place Search         | Kakao Local API / Google Maps |
| Shopping Search      | Naver Shopping                |
| Model Hosting        | Hugging Face Hub              |

## 🖥️ 지원 환경

* Python 3.11+

## 🔄 주요 플로우

```text
iOS Client
    │
    ▼
POST /classify
    ├─ Capture Image
    ├─ PaddleOCR
    │    └─ OCR Text
    ├─ RoBERTa Text Classifier
    ├─ CLIP Image Classifier
    └─ Multimodal Fusion
         └─ Final Category + Confidence
    │
    ▼
POST /gemini
    ├─ OCR Text
    ├─ Category
    ├─ Gemini Field Extraction
    └─ External Service Integration
         ├─ place    → Kakao Map / Google Maps
         ├─ shopping → Naver Shopping
         ├─ schedule → Calendar data
         └─ memo     → Extracted memo data
    │
    ▼
iOS Client
    └─ SwiftData 저장 및 추천 액션 제공
```

`unknown` 카테고리는 추천 액션을 연결하지 않는 캡쳐이므로 Gemini 기반 상세 분석을 수행하지 않습니다.

## 🧠 Multimodal Classification

`/classify` API에서는 하나의 이미지에 대해 OCR과 이미지 분류를 함께 수행합니다.

```text
Image
  ├─ PaddleOCR → OCR Text → RoBERTa Text Classifier
  └─ Original Image → CLIP Image Classifier
                         │
                         ▼
                  Multimodal Fusion
                         │
                         ▼
                  Final Category
```

최종 분류 점수는 AI 레포와 동일한 fusion 비율을 사용합니다.

```text
Text weight  = 0.75
Image weight = 0.25
```

```text
final_score = text_score * 0.75 + image_score * 0.25
```

사용하는 모델은 Hugging Face Hub에서 다운로드합니다.

| Model       | Hugging Face Repo                                 |
| ----------- | ------------------------------------------------- |
| Text model  | `hur03/capturemate-category-classifier-v1-5class` |
| Image model | `hur03/capturemate-image-classifier-v1-5class`    |

## 🏷️ Categories

| Label      | Description           |
| ---------- | --------------------- |
| `schedule` | 일정, 예약, 티켓, 캘린더 관련 캡쳐 |
| `shopping` | 쇼핑, 상품, 결제, 주문 관련 캡쳐  |
| `place`    | 장소, 지도, 매장, 위치 관련 캡쳐  |
| `memo`     | 메모, 글, 저장용 텍스트 캡쳐     |
| `unknown`  | 추천 액션을 연결하지 않는 기타 캡쳐  |

## 🔌 API

### POST `/classify`

캡쳐 이미지를 전달받아 OCR 및 멀티모달 카테고리 분류를 수행합니다.

```text
Image
→ PaddleOCR
→ Text Classification
→ Image Classification
→ Fusion
→ Category
```

주요 반환 데이터:

```json
{
  "local_identifier": "string",
  "ocr_text": "string",
  "category": "shopping",
  "confidence": 0.9231
}
```

### POST `/gemini`

`/classify`에서 반환된 OCR 텍스트와 카테고리를 기반으로 카테고리별 상세 정보를 추출합니다.

```text
OCR Text + Category
→ Gemini
→ Category-specific Field Extraction
→ External Service Integration
```

카테고리별 처리:

| Category   | Processing                                         |
| ---------- | -------------------------------------------------- |
| `place`    | 장소 정보 추출 후 Kakao Map 검색, 필요 시 Google Maps fallback |
| `shopping` | 상품 정보 추출 후 Naver Shopping 검색                       |
| `schedule` | 일정명, 날짜, 시간 등 캘린더 저장용 정보 추출                        |
| `memo`     | 메모에 필요한 주요 정보 추출                                   |
| `unknown`  | Gemini 분석 미수행                                      |

## 🔗 External Service Integration

### Place

Gemini가 추출한 장소명을 기준으로 **Kakao Local API를 우선 사용**합니다.

```text
Place Name
→ Kakao Local API
→ 검색 성공: Kakao Map 정보 반환
→ 검색 실패 / 해외 장소: Google Maps 검색 URL 반환
```

### Shopping

Gemini가 추출한 상품명을 기준으로 네이버 쇼핑 검색 URL을 생성합니다.

```text
Product Name
→ Naver Shopping
→ Shopping Search URL
```

### Schedule

Gemini가 일정명, 날짜, 시작 시간, 종료 시간 등 구조화된 데이터를 반환하며, iOS 앱에서 EventKit을 이용해 캘린더에 저장합니다.

## 🚀 실행 방법

1. 저장소를 clone 합니다.

```bash
git clone https://github.com/Daegurrrr/CaptureMate_BE
cd CaptureMate_BE
```

2. 의존성을 설치합니다.

```bash
pip install -r requirements.txt
```

3. `.env.example`을 복사하여 `.env` 파일을 생성합니다.

```bash
cp .env.example .env
```

4. 필요한 환경 변수를 입력합니다.

5. 서버를 실행합니다.

```bash
uvicorn app.main:app --reload
```

기본 서버 주소:

```text
http://localhost:8000
```

FastAPI Swagger:

```text
http://localhost:8000/docs
```

## 🔐 Environment Variables

주요 환경 변수는 `.env`에서 관리합니다.

```text
GEMINI_API_KEY=
KAKAO_REST_API_KEY=
```

Hugging Face 모델은 기본적으로 지정된 모델 ID를 사용해 자동으로 다운로드합니다.

```text
CAPTUREMATE_TEXT_MODEL_ID=hur03/capturemate-category-classifier-v1-5class
CAPTUREMATE_IMAGE_MODEL_ID=hur03/capturemate-image-classifier-v1-5class
```

## 📁 프로젝트 구조

```text
CaptureMate_BE/
├── app/
│   ├── main.py
│   │
│   ├── ai/
│   │   ├── classifier.py
│   │   ├── image_classifier.py
│   │   └── ocr.py
│   │
│   ├── api/
│   │   ├── classify.py
│   │   └── gemini.py
│   │
│   ├── core/
│   │   └── config.py
│   │
│   └── services/
│       ├── gemini_service.py
│       ├── kakao_service.py
│       └── naver_service.py
│
├── requirements.txt
├── .env.example
└── README.md
```

## 🗂️ Data Storage

백엔드는 분석 결과를 별도의 서버 DB에 저장하지 않습니다.

```text
Backend
→ 분석 결과 반환

iOS Client
→ SwiftData에 로컬 저장
```

따라서 백엔드는 사용자 계정이나 캡쳐 데이터를 관리하는 서버가 아니라, **AI 추론 및 외부 서비스 연동을 담당하는 stateless API 서버**로 동작합니다.

## 📝 Notes

* 원본 캡쳐 이미지는 서버 DB에 저장하지 않습니다.
* 이미지는 OCR 및 이미지 분류를 위해 요청 처리 중에만 사용됩니다.
* 추론 시 입력 이미지는 Hugging Face로 전송되지 않습니다.
* `unknown` 카테고리는 Gemini 상세 분석 및 추천 액션 생성 대상에서 제외합니다.
* AI 모델과 fusion 방식은 `CaptureMate_AI` 레포와 동일하게 유지합니다.
* 모델 ID, label 순서 또는 fusion 비율을 변경한 경우 AI 레포와 백엔드 코드를 함께 확인해야 합니다.
