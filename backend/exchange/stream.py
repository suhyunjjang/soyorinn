"""
바이낸스 선물 WebSocket 스트림 관리 모듈

- (심볼, 인터벌) 조합별로 독립적인 Binance WS 연결 유지
- 구독자가 생기면 스트림 시작, 없어지면 자동 종료
- RSI 계산을 위해 종가 버퍼 유지 (과거 100개 캔들로 초기화)
"""

import asyncio
import json
import logging
import httpx
import websockets
from fastapi import WebSocket
from config import SYMBOLS, BINANCE_WS_BASE
from exchange.indicators import calculate_rsi

logger = logging.getLogger(__name__)

StreamKey = tuple[str, str]  # (symbol, interval)

BINANCE_REST = "https://fapi.binance.com"
RSI_PERIOD = 14
BUFFER_SIZE = 200   # 유지할 최대 종가 개수


class BinanceStreamManager:
    """(심볼, 인터벌) 단위로 바이낸스 실시간 스트림 관리"""

    def __init__(self):
        self._subscribers: dict[StreamKey, set[WebSocket]] = {}
        self._tasks: dict[StreamKey, asyncio.Task] = {}
        # RSI 계산용 확정 종가 버퍼
        self._close_buffers: dict[StreamKey, list[float]] = {}

    async def subscribe(self, symbol: str, interval: str, websocket: WebSocket):
        key: StreamKey = (symbol.upper(), interval)

        if key not in self._subscribers:
            self._subscribers[key] = set()
        self._subscribers[key].add(websocket)

        # 스트림이 없으면 버퍼 초기화 후 시작
        if key not in self._tasks or self._tasks[key].done():
            await self._seed_buffer(key)
            self._tasks[key] = asyncio.create_task(self._run(key))
            logger.info(f"[스트림 시작] {key}")

        logger.info(f"[구독 등록] {key} | 구독자: {len(self._subscribers[key])}")

    async def unsubscribe(self, symbol: str, interval: str, websocket: WebSocket):
        key: StreamKey = (symbol.upper(), interval)

        if key in self._subscribers:
            self._subscribers[key].discard(websocket)
            logger.info(f"[구독 해제] {key} | 구독자: {len(self._subscribers[key])}")

            if not self._subscribers[key]:
                if key in self._tasks and not self._tasks[key].done():
                    self._tasks[key].cancel()
                    logger.info(f"[스트림 종료] {key}")
                del self._subscribers[key]
                self._tasks.pop(key, None)
                self._close_buffers.pop(key, None)

    async def _seed_buffer(self, key: StreamKey):
        """RSI 계산 정확도를 위해 과거 종가 데이터로 버퍼 초기화"""
        symbol, interval = key
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{BINANCE_REST}/fapi/v1/klines",
                    params={"symbol": symbol, "interval": interval, "limit": 100},
                    timeout=10,
                )
                data = resp.json()
                # 마지막 캔들은 미확정이므로 제외
                self._close_buffers[key] = [float(row[4]) for row in data[:-1]]
                logger.info(f"[버퍼 초기화] {key} | {len(self._close_buffers[key])}개 종가 로드")
        except Exception as e:
            logger.error(f"[버퍼 초기화 실패] {key}: {e}")
            self._close_buffers[key] = []

    async def _run(self, key: StreamKey):
        """바이낸스 단일 심볼 스트림 연결 루프"""
        symbol, interval = key
        url = f"{BINANCE_WS_BASE}/ws/{symbol.lower()}@kline_{interval}"

        while True:
            try:
                logger.info(f"[바이낸스] 연결 시도: {url}")
                async with websockets.connect(url, ping_interval=20, ping_timeout=10) as ws:
                    logger.info(f"[바이낸스] 연결 성공: {key}")
                    async for raw in ws:
                        await self._handle(key, raw)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[바이낸스] 오류 {key}: {e} | 5초 후 재연결")
                await asyncio.sleep(5)

    async def _handle(self, key: StreamKey, raw: str):
        """캔들 데이터 파싱 + RSI 계산 후 구독자에게 브로드캐스트"""
        try:
            data = json.loads(raw)
            kline = data.get("k")
            if not kline:
                return

            symbol, interval = key
            close = float(kline["c"])
            is_closed = kline["x"]

            buf = self._close_buffers.get(key, [])

            # 캔들 확정 시 버퍼에 추가
            if is_closed:
                buf.append(close)
                if len(buf) > BUFFER_SIZE:
                    buf = buf[-BUFFER_SIZE:]
                self._close_buffers[key] = buf

            # RSI: 버퍼(확정 종가) + 현재 종가로 계산
            rsi_closes = buf + [close] if buf else [close]
            rsi = calculate_rsi(rsi_closes, RSI_PERIOD)

            message = {
                "symbol": symbol,
                "interval": interval,
                "candle": {
                    "time": kline["t"] // 1000,
                    "open": float(kline["o"]),
                    "high": float(kline["h"]),
                    "low": float(kline["l"]),
                    "close": close,
                    "volume": float(kline["v"]),
                    "is_closed": is_closed,
                },
                "rsi": rsi,
            }

            await self._broadcast(key, message)

        except Exception as e:
            logger.error(f"[파싱 오류] {key}: {e}")

    async def _broadcast(self, key: StreamKey, data: dict):
        """구독자 전체에게 전송, 끊어진 연결 자동 제거"""
        subscribers = self._subscribers.get(key, set()).copy()
        disconnected = set()

        for ws in subscribers:
            try:
                await ws.send_json(data)
            except Exception:
                disconnected.add(ws)

        for ws in disconnected:
            self._subscribers[key].discard(ws)


binance_stream = BinanceStreamManager()
