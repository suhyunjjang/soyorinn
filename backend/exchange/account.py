"""
바이낸스 선물 계정 정보 조회 모듈 (인증 필요)

- 지갑 잔고 (USDT)
- 보유 포지션
- 진행 중인 주문 (오픈 오더)
"""

import logging
import os
from binance.client import Client
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")

if not API_KEY or not API_SECRET:
    logger.warning("[계정] BINANCE_API_KEY/SECRET 누락 — 인증 엔드포인트 사용 불가")

# python-binance Client (선물은 futures_* 메서드 사용)
_client: Client | None = None


def get_client() -> Client:
    """Client 싱글턴 반환 (지연 초기화)"""
    global _client
    if _client is None:
        if not API_KEY or not API_SECRET:
            raise RuntimeError("BINANCE_API_KEY/SECRET이 설정되지 않았습니다 (.env 확인)")
        _client = Client(API_KEY, API_SECRET)
    return _client


def get_balance() -> dict:
    """
    선물 지갑 잔고 조회 (USDT 기준)

    응답:
    {
        "asset": "USDT",
        "balance": 1000.0,         # 총 잔고
        "available": 800.0,        # 주문 가능 금액
        "unrealized_pnl": 12.5     # 미실현 손익
    }
    """
    client = get_client()
    # futures_account_balance: 자산별 잔고 리스트
    balances = client.futures_account_balance()
    usdt = next((b for b in balances if b["asset"] == "USDT"), None)

    if not usdt:
        return {"asset": "USDT", "balance": 0.0, "available": 0.0, "unrealized_pnl": 0.0}

    return {
        "asset": "USDT",
        "balance": float(usdt["balance"]),
        "available": float(usdt["availableBalance"]),
        "unrealized_pnl": float(usdt["crossUnPnl"]),
    }


def get_positions() -> list[dict]:
    """
    현재 보유 중인 포지션 조회 (수량이 0이 아닌 것만)

    응답: [
        {
            "symbol": "BTCUSDT",
            "side": "LONG" | "SHORT",
            "quantity": 0.5,
            "entry_price": 50000.0,
            "mark_price": 50500.0,
            "unrealized_pnl": 250.0,
            "leverage": 10,
            "liquidation_price": 45000.0
        }, ...
    ]
    """
    client = get_client()
    positions = client.futures_position_information()

    result = []
    for p in positions:
        amt = float(p["positionAmt"])
        if amt == 0:
            continue
        result.append({
            "symbol": p["symbol"],
            "side": "LONG" if amt > 0 else "SHORT",
            "quantity": abs(amt),
            "entry_price": float(p["entryPrice"]),
            "mark_price": float(p["markPrice"]),
            "unrealized_pnl": float(p["unRealizedProfit"]),
            "leverage": int(p["leverage"]),
            "liquidation_price": float(p["liquidationPrice"]),
        })
    return result


def get_open_orders() -> list[dict]:
    """
    진행 중인 주문 조회 (체결되지 않은 모든 오픈 오더)

    응답: [
        {
            "order_id": 123456,
            "symbol": "BTCUSDT",
            "side": "BUY" | "SELL",
            "type": "LIMIT" | "STOP_MARKET" | ...,
            "quantity": 0.5,
            "price": 50000.0,           # LIMIT 가격 (없으면 0)
            "stop_price": 49000.0,      # STOP 가격 (없으면 0)
            "status": "NEW",
            "time": 1700000000          # 초 단위
        }, ...
    ]
    """
    client = get_client()
    orders = client.futures_get_open_orders()

    return [
        {
            "order_id": o["orderId"],
            "symbol": o["symbol"],
            "side": o["side"],
            "type": o["type"],
            "quantity": float(o["origQty"]),
            "price": float(o["price"]),
            "stop_price": float(o["stopPrice"]),
            "status": o["status"],
            "time": o["time"] // 1000,
        }
        for o in orders
    ]
