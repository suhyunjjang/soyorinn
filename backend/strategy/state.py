"""
봇 런타임 상태 영속화 (JSON 파일)

- 봇 ON/OFF
- 마지막 진입 정보 (RSI, 가격, 피라미딩 카운트)
- TP 주문 ID
- 일일 진입 카운트 (자정 UTC 기준)
- 마지막 처리한 봉 시간 (봉당 1회 보장)
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

logger = logging.getLogger(__name__)

STATE_PATH = Path(__file__).parent.parent / "data" / "strategy_state.json"

_DEFAULT_STATE = {
    "bot_running": False,
    "last_entry_rsi": None,
    "last_entry_price": None,
    "pyramid_count": 0,
    "tp_order_id": None,
    "daily_entry_date": None,   # "YYYY-MM-DD" (UTC)
    "daily_entry_count": 0,
    "last_processed_candle_time": None,  # 마지막으로 처리한 봉의 open time (sec)
}

_lock = Lock()


def load() -> dict:
    with _lock:
        if not STATE_PATH.exists():
            _write(_DEFAULT_STATE)
            return dict(_DEFAULT_STATE)
        try:
            with STATE_PATH.open("r", encoding="utf-8") as f:
                state = json.load(f)
        except Exception as e:
            logger.error(f"[상태 로드 실패] {e} — 기본값 재생성")
            _write(_DEFAULT_STATE)
            return dict(_DEFAULT_STATE)
        # 누락 키 보강
        for k, v in _DEFAULT_STATE.items():
            state.setdefault(k, v)
        return state


def save(state: dict) -> dict:
    with _lock:
        _write(state)
        return state


def reset_position_state(state: dict) -> dict:
    """포지션 청산 시 호출 (last_entry_*, pyramid_count, tp_order_id 초기화)"""
    state["last_entry_rsi"] = None
    state["last_entry_price"] = None
    state["pyramid_count"] = 0
    state["tp_order_id"] = None
    return state


def bump_daily_entry(state: dict) -> dict:
    """일일 진입 카운터 +1 (날짜가 바뀌면 리셋)"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if state.get("daily_entry_date") != today:
        state["daily_entry_date"] = today
        state["daily_entry_count"] = 0
    state["daily_entry_count"] += 1
    return state


def daily_entry_count_today(state: dict) -> int:
    """오늘(UTC) 진입 횟수"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if state.get("daily_entry_date") != today:
        return 0
    return state.get("daily_entry_count", 0)


def _write(state: dict):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with STATE_PATH.open("w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
