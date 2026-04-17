# 바이낸스 선물 자동매매 프로그램

개인 사용 목적의 바이낸스 선물 자동매매 봇 + 모니터링 대시보드.

## 프로젝트 구조

```
soyorinn/
├── backend/        # Python 백엔드 (FastAPI)
└── frontend/       # React 프론트엔드 (대시보드)
```

## 기술 스택

### Backend (Python)
- `FastAPI` — REST API 서버 및 WebSocket
- `python-binance` 또는 `ccxt` — 바이낸스 API 연동
- `pandas`, `numpy` — 가격 데이터 처리
- `pandas-ta` — 기술적 지표 계산 (RSI, MACD, 볼린저밴드 등)
- `APScheduler` — 전략 주기 실행
- `SQLite` — 거래 내역 및 설정 저장
- `python-dotenv` — 환경변수 관리

### Frontend (React)
- `React` + `TypeScript`
- `lightweight-charts` — 캔들차트
- `recharts` — 수익/통계 그래프
- `axios` — 백엔드 API 호출

## 역할 분리 원칙

- **모든 계산은 백엔드에서만** 수행 (지표, 전략, 주문 등)
- **프론트엔드는 표시만** — 백엔드 API 결과를 받아 차트/현황 렌더링

## 코딩 규칙

- 주석은 **한국어**로 작성
- API 키 등 민감 정보는 반드시 `.env` 파일로 관리, 절대 코드에 하드코딩 금지
- 개인 사용 목적이므로 인증/권한 시스템 불필요
- 백엔드/프론트엔드 각각 독립적으로 실행 가능하게 유지

## 작업 방식

- **대화는 항상 한국어로** 진행
- **코드 변경 전** — 어떤 작업을 할지 먼저 설명하고 사용자 확인 후 진행
- **작업 시** — TodoWrite로 작업 항목을 표시하며 진행 상황 공유
- **코드 변경 후** — 어떤 파일을 어떻게 변경했는지 요약 안내

## 주요 기능 (예정)

- [ ] 바이낸스 선물 실시간 가격 수신 (WebSocket)
- [ ] 기술적 지표 계산 및 매매 전략 실행
- [ ] 자동 주문 (진입 / 청산 / 손절)
- [ ] 캔들차트 + 지표 시각화 (프론트)
- [ ] 포지션 현황 및 수익 모니터링 (프론트)
- [ ] 봇 ON/OFF 제어 (프론트)
- [ ] 거래 내역 기록 및 조회

## 환경변수 (.env)

```
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_api_secret
```

## 실행 방법 (추후 작성 예정)

```bash
# 백엔드
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# 프론트엔드
cd frontend
npm install
npm run dev
```
