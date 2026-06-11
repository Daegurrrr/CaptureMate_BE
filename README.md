# CaptureMate_BE
CaptureMate BE 레포입니다. AI 기반 스크린샷 분석 및 행동 추천 서비스의 서버 및 API 프로젝트입니다.

## 🧱 기술 스택

| 구분 | 기술 |
|------|------|
| 언어 | Python 3.11 |
| 프레임워크 | FastAPI |
| 데이터베이스 | PostgreSQL (AWS RDS) |
| 서버 | AWS EC2 |
| AI | Gemini API |

## 🖥️ 지원 환경
- Python 3.11+
- PostgreSQL 14+


## 🚀 실행 방법
1. 저장소를 clone 합니다.
```bash
git clone https://github.com/Daegurrrr/CaptureMate_BE
```

2. 의존성을 설치합니다.
```bash
pip install -r requirements.txt
```

3. `.env.example`을 복사하여 `.env` 파일을 생성하고 값을 입력합니다.
```bash
cp .env.example .env
```

4. 서버를 실행합니다.
```bash
uvicorn app.main:app --reload
```

## 📁 프로젝트 구조
```
CaptureMate_BE/
├── app/
│   ├── main.py
│   ├── ai/                    # OCR 및 분류 모델
│   │   ├── classifier_model.py
│   │   ├── classifier_v1.py
│   │   └── ocr.py
│   ├── api/                   # API 엔드포인트 라우터
│   │   ├── auth.py
│   │   ├── classify_model.py
│   │   ├── place.py
│   │   └── screenshot.py
│   ├── core/                  # DB 연결, 환경 변수, JWT 등 공통 인프라
│   │   ├── config.py
│   │   ├── database.py
│   │   └── security.py
│   ├── models/                # DB 테이블 정의
│   │   ├── analysis_result.py
│   │   ├── memo.py
│   │   ├── place.py
│   │   ├── schedule.py
│   │   ├── screenshot.py
│   │   ├── shopping.py
│   │   └── user.py
│   ├── schemas/               # 로그인 요청/응답 데이터 형식 정의
│   │   └── user.py
│   └── services/              # 비즈니스 로직 (외부 API 연동)
│       ├── auth_service.py
│       ├── gemini_service.py
│       ├── kakao_service.py
│       └── naver_service.py
├── .github/workflows/         # GitHub Actions CI/CD
├── requirements.txt
└── .env
```

## ⚙️ 아키텍처
프로젝트는 계층형 아키텍처로 구성되어 있습니다.

```
iOS (SwiftUI)
    │
    ▼
FastAPI Server
    ├── API      : 클라이언트 요청 처리 (auth, screenshot, classify)
    ├── AI       : OCR 텍스트 추출 + 카테고리 분류 + AI요약
    ├── Services : 외부 API 연동 (카카오맵, 네이버 쇼핑, Gemini)
    ├── Models   : DB 테이블 정의
    └── DB : PostgreSQL (AWS RDS)
```

- **API**: 클라이언트 요청을 받아 적절한 서비스로 전달
- **AI**: OCR 텍스트 추출 및 카테고리 분류 처리
- **Services**: 카카오맵/네이버 쇼핑/Gemini 등 외부 API 연동
- **Models**: 카테고리별 분석 결과를 DB에 저장 (장소 / 일정 / 쇼핑 / 메모 / 기타)
