"""
FastAPI 메인 앱

엔드포인트:
  GET  /symbols                   - 지원 심볼/인터벌 목록
  GET  /klines/{symbol}?interval= - 과거 캔들 데이터 (Binance REST)
  WS   /ws/{symbol}/{interval}    - 실시간 캔들 구독
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import httpx
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import SYMBOLS, INTERVALS
from exchange.stream import binance_stream
from exchange.indicators import calculate_rsi_series
from exchange import account
from strategy import config as strategy_config, state as strategy_state, registry as strategy_registry
from strategy.engine import engine as strategy_engine

# 로그를 콘솔 + 파일 양쪽에 저장 (10MB × 5개 회전).
# uvicorn 접근 로그(200 OK 등)는 WARNING으로 올려 잡음 제거.
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

_log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_formatter = logging.Formatter(_log_format)

_file_handler = RotatingFileHandler(
    LOG_DIR / "bot.log", maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
)
_file_handler.setFormatter(_formatter)

_console_handler = logging.StreamHandler()
_console_handler.setFormatter(_formatter)

logging.basicConfig(level=logging.INFO, handlers=[_console_handler, _file_handler])
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# 바이낸스 선물 REST API 베이스 URL
BINANCE_REST = "https://fapi.binance.com"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("[앱 시작]")
    # 서버 재시작 시 봇 상태가 ON이면 자동 복구
    await strategy_engine.restore_if_running()
    yield
    logger.info("[앱 종료]")


app = FastAPI(title="자동매매 백엔드", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/symbols")
def get_symbols():
    """지원 심볼 및 인터벌 목록 반환"""
    return {"symbols": SYMBOLS, "intervals": INTERVALS}


@app.get("/klines/{symbol}")
async def get_klines(symbol: str, interval: str = "1h", limit: int = 500):
    """
    과거 캔들 데이터 반환 (바이낸스 REST API 프록시)

    예: GET /klines/BTCUSDT?interval=1h&limit=500
    """
    symbol = symbol.upper()

    if symbol not in SYMBOLS:
        return {"error": f"지원하지 않는 심볼: {symbol}"}
    if interval not in INTERVALS:
        return {"error": f"지원하지 않는 인터벌: {interval}"}

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BINANCE_REST}/fapi/v1/klines",
            params={"symbol": symbol, "interval": interval, "limit": limit},
            timeout=10,
        )
        raw = resp.json()

    # 바이낸스 응답: [openTime, open, high, low, close, volume, ...]
    closes = [float(row[4]) for row in raw]
    rsi_series = calculate_rsi_series(closes)

    candles = [
        {
            "time": row[0] // 1000,   # 밀리초 → 초
            "open": float(row[1]),
            "high": float(row[2]),
            "low": float(row[3]),
            "close": float(row[4]),
            "volume": float(row[5]),
            "rsi": rsi_series[i],
        }
        for i, row in enumerate(raw)
    ]

    return candles


@app.get("/account/balance")
def get_account_balance():
    """선물 지갑 잔고 (USDT)"""
    try:
        return account.get_balance()
    except Exception as e:
        logger.error(f"[잔고 조회 실패] {e}")
        return {"error": str(e)}


@app.get("/account/positions")
def get_account_positions():
    """현재 보유 중인 포지션"""
    try:
        return account.get_positions()
    except Exception as e:
        logger.error(f"[포지션 조회 실패] {e}")
        return {"error": str(e)}


@app.get("/account/orders")
def get_account_orders():
    """진행 중인 주문 (오픈 오더)"""
    try:
        return account.get_open_orders()
    except Exception as e:
        logger.error(f"[주문 조회 실패] {e}")
        return {"error": str(e)}


# ----------------------------------------------------------------------------
# 전략 관련 엔드포인트
# ----------------------------------------------------------------------------


class StrategySettingsBody(BaseModel):
    active_strategy: str
    common: dict
    strategies: dict


@app.get("/strategy/list")
def get_strategy_list():
    """등록된 전략 목록 + 각 전략의 파라미터 스키마"""
    return strategy_registry.list_all()


@app.get("/strategy/settings")
def get_strategy_settings():
    """현재 전략 설정"""
    return strategy_config.load()


@app.put("/strategy/settings")
def put_strategy_settings(body: StrategySettingsBody):
    """
    설정 업데이트.
    봇 ON 상태에서는 변경 불가 — 먼저 OFF 후 변경.
    """
    st = strategy_state.load()
    if st["bot_running"]:
        raise HTTPException(
            status_code=409,
            detail="봇이 켜진 상태에서는 설정을 변경할 수 없습니다. 먼저 봇을 끄세요.",
        )
    try:
        return strategy_config.save(body.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/strategy/toggle")
async def post_strategy_toggle():
    """봇 ON/OFF 토글"""
    st = strategy_state.load()
    try:
        if st["bot_running"]:
            new_state = await strategy_engine.stop()
        else:
            new_state = await strategy_engine.start()
        return new_state
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/strategy/state")
def get_strategy_state():
    """
    봇 런타임 상태.

    호출 시점에 보유 포지션이 사라졌으면 진입 정보(last_entry_*, pyramid_count, tp_order_id)
    를 즉시 초기화한다. 봉 마감 콜백을 기다리지 않고 UI에 깔끔한 상태가 바로 반영되도록.
    """
    st = strategy_state.load()
    if st.get("last_entry_price") is not None:
        cfg = strategy_config.load()
        symbol = cfg["common"]["symbol"]
        try:
            position = account.get_position(symbol)
        except Exception as e:
            logger.error(f"[state 검증 - 포지션 조회 실패] {e}")
            position = None  # 조회 실패 시 보수적으로 리셋 안 함
            return st
        if position is None:
            logger.info("[state 검증] 포지션 없음 → 진입 상태 즉시 리셋")
            strategy_state.reset_position_state(st)
            strategy_state.save(st)
    return st


@app.websocket("/ws/{symbol}/{interval}")
async def websocket_candle(websocket: WebSocket, symbol: str, interval: str):
    """
    실시간 캔들 구독 엔드포인트

    연결: ws://localhost:8000/ws/BTCUSDT/1h
    수신 형식:
    {
        "symbol": "BTCUSDT",
        "interval": "1h",
        "candle": {
            "time": 1700000000,
            "open": 50000.0, "high": 50100.0,
            "low": 49900.0,  "close": 50050.0,
            "volume": 100.5, "is_closed": false
        }
    }
    """
    symbol = symbol.upper()

    if symbol not in SYMBOLS:
        await websocket.close(code=4000, reason=f"지원하지 않는 심볼: {symbol}")
        return
    if interval not in INTERVALS:
        await websocket.close(code=4001, reason=f"지원하지 않는 인터벌: {interval}")
        return

    await websocket.accept()
    await binance_stream.subscribe(symbol, interval, websocket)
    logger.info(f"[WS 연결] {symbol}/{interval}")

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        logger.info(f"[WS 종료] {symbol}/{interval}")
    finally:
        await binance_stream.unsubscribe(symbol, interval, websocket)
