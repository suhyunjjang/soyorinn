"""
바이낸스 선물 계정 정보 조회 + 주문 모듈 (인증 필요)

- 지갑 잔고 (USDT)
- 보유 포지션
- 진행 중인 주문 (오픈 오더)
- 마진 모드 / 레버리지 설정
- 시장가 매수, TP 주문, 주문 취소
"""

import logging
import math
import os
from binance.client import Client
from binance.exceptions import BinanceAPIException
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
        # 바이낸스 V3 positionRisk는 leverage / liquidationPrice / markPrice가
        # 누락될 수 있어 안전 처리. 빈 문자열도 0으로 캐스팅.
        result.append({
            "symbol": p["symbol"],
            "side": "LONG" if amt > 0 else "SHORT",
            "quantity": abs(amt),
            "entry_price": float(p.get("entryPrice") or 0),
            "mark_price": float(p.get("markPrice") or 0),
            "unrealized_pnl": float(p.get("unRealizedProfit") or 0),
            "leverage": int(float(p.get("leverage") or 0)),
            "liquidation_price": float(p.get("liquidationPrice") or 0),
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


# ----------------------------------------------------------------------------
# 주문 / 설정 함수 (전략 엔진에서 사용)
# ----------------------------------------------------------------------------


# 심볼별 거래 규칙 캐시 (stepSize, tickSize, minQty)
_symbol_filters: dict[str, dict] = {}


def get_symbol_filters(symbol: str) -> dict:
    """
    심볼의 거래 규칙 조회 (stepSize, tickSize, minQty).
    한 번 조회 후 메모리 캐시.
    """
    symbol = symbol.upper()
    if symbol in _symbol_filters:
        return _symbol_filters[symbol]

    client = get_client()
    info = client.futures_exchange_info()
    target = next((s for s in info["symbols"] if s["symbol"] == symbol), None)
    if not target:
        raise RuntimeError(f"심볼 정보를 찾을 수 없음: {symbol}")

    lot = next(f for f in target["filters"] if f["filterType"] == "LOT_SIZE")
    price = next(f for f in target["filters"] if f["filterType"] == "PRICE_FILTER")

    _symbol_filters[symbol] = {
        "step_size": float(lot["stepSize"]),
        "min_qty": float(lot["minQty"]),
        "tick_size": float(price["tickSize"]),
        "quantity_precision": int(target["quantityPrecision"]),
        "price_precision": int(target["pricePrecision"]),
    }
    return _symbol_filters[symbol]


def _quantize_down(value: float, step: float, precision: int) -> float:
    """value를 step 단위로 내림 + 부동소수 오차 방지"""
    q = math.floor(value / step) * step
    return round(q, precision)


def get_mark_price(symbol: str) -> float:
    """심볼의 현재 마크 가격 조회"""
    client = get_client()
    data = client.futures_mark_price(symbol=symbol.upper())
    return float(data["markPrice"])


def get_position(symbol: str) -> dict | None:
    """단일 심볼의 보유 포지션 조회 (없으면 None)"""
    symbol = symbol.upper()
    for p in get_positions():
        if p["symbol"] == symbol:
            return p
    return None


def set_margin_mode(symbol: str, mode: str = "ISOLATED"):
    """
    마진 모드 설정 (ISOLATED / CROSSED).
    이미 같은 모드면 -4046 에러가 나지만 무시한다.
    """
    client = get_client()
    try:
        client.futures_change_margin_type(symbol=symbol.upper(), marginType=mode)
        logger.info(f"[마진 모드] {symbol} → {mode}")
    except BinanceAPIException as e:
        if e.code == -4046:  # No need to change margin type
            return
        raise


def set_leverage(symbol: str, leverage: int):
    """레버리지 설정"""
    client = get_client()
    client.futures_change_leverage(symbol=symbol.upper(), leverage=int(leverage))
    logger.info(f"[레버리지] {symbol} → {leverage}배")


def market_buy(symbol: str, quantity: float) -> dict:
    """
    시장가 매수 (LONG 진입).

    Returns: 바이낸스 응답 dict
    """
    client = get_client()
    filters = get_symbol_filters(symbol)
    qty = _quantize_down(quantity, filters["step_size"], filters["quantity_precision"])
    if qty < filters["min_qty"]:
        raise ValueError(
            f"수량 {qty}이 minQty {filters['min_qty']}보다 작음 (자본/레버리지 부족)"
        )

    logger.info(f"[시장가 매수] {symbol} qty={qty}")
    return client.futures_create_order(
        symbol=symbol.upper(),
        side="BUY",
        type="MARKET",
        quantity=qty,
    )


def place_take_profit_long(symbol: str, quantity: float, stop_price: float) -> dict:
    """
    LONG 포지션용 TAKE_PROFIT_MARKET 주문 (reduceOnly).
    가격이 stop_price에 닿으면 시장가로 청산.
    """
    client = get_client()
    filters = get_symbol_filters(symbol)
    qty = _quantize_down(quantity, filters["step_size"], filters["quantity_precision"])
    sp = _quantize_down(stop_price, filters["tick_size"], filters["price_precision"])

    logger.info(f"[TP 주문] {symbol} qty={qty} stop={sp}")
    # reduceOnly는 일부 환경에서 boolean이 거부되어 lowercase 문자열로 전송
    return client.futures_create_order(
        symbol=symbol.upper(),
        side="SELL",
        type="TAKE_PROFIT_MARKET",
        quantity=qty,
        stopPrice=sp,
        reduceOnly="true",
        workingType="MARK_PRICE",
    )


def cancel_order(symbol: str, order_id: int) -> dict | None:
    """
    주문 취소. 이미 체결/취소된 주문이면 (-2011) None 반환.
    """
    client = get_client()
    try:
        return client.futures_cancel_order(symbol=symbol.upper(), orderId=order_id)
    except BinanceAPIException as e:
        if e.code == -2011:  # Unknown order / already gone
            logger.info(f"[취소 무시] {symbol} order_id={order_id} 이미 없음")
            return None
        raise
