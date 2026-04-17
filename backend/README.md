# 백엔드 실행 방법

## 최초 설정 (처음 한 번만)

```bash
cd backend

# 가상환경 생성
python3 -m venv venv

# 패키지 설치
source venv/bin/activate
pip install -r requirements.txt

# 환경변수 설정 (.env 파일 생성)
cp .env.example .env
# .env 파일 열어서 바이낸스 API 키 입력
```

## 서버 실행

```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload
```

서버 주소: http://localhost:8000

## API 목록

| 방식 | 경로 | 설명 |
|------|------|------|
| GET | `/symbols` | 지원 심볼/인터벌 목록 |
| WebSocket | `/ws/{symbol}` | 실시간 캔들 구독 |

**WebSocket 연결 예시**
- `ws://localhost:8000/ws/BTCUSDT`
- `ws://localhost:8000/ws/ETHUSDT`
- `ws://localhost:8000/ws/XRPUSDT`
- `ws://localhost:8000/ws/SOLUSDT`

**WebSocket 수신 데이터 형식**
```json
{
  "symbol": "BTCUSDT",
  "interval": "1m",
  "candle": {
    "time": 1700000000,
    "open": 50000.0,
    "high": 50100.0,
    "low": 49900.0,
    "close": 50050.0,
    "volume": 100.5,
    "is_closed": false
  }
}
```
