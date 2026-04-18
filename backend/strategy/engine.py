"""
전략 엔진

책임:
- 봇 ON 시: 마진모드/레버리지 설정 + 캔들 리스너 등록
- 봇 OFF 시: 리스너 해제 (보유 포지션/TP는 거래소에 그대로 두어 익절 처리)
- 봉 마감 콜백:
  1) 봉당 1회 보장
  2) 포지션 청산 감지 → state 리셋
  3) 일일 진입 / 피라미딩 한도 체크
  4) 전략 호출 → ENTRY/ADD 신호
  5) 시장가 매수 → 평균진입가 조회 → 기존 TP 취소 → 새 TP 발주
  6) state 영속화
"""

import asyncio
import logging

from exchange import account
from exchange.stream import binance_stream
from strategy import config, state, registry
from strategy.base import Candle, Signal
import strategy.strategies  # noqa: F401  - 전략 자동 등록 트리거

logger = logging.getLogger(__name__)


class StrategyEngine:
    def __init__(self):
        self._lock = asyncio.Lock()      # 신호 처리 동시 실행 방지
        self._listening_key: tuple[str, str] | None = None

    # ----------------------------------------------------------------- public

    async def start(self):
        """봇 ON. 마진모드/레버리지 설정 후 캔들 리스너 등록."""
        async with self._lock:
            st = state.load()
            if st["bot_running"]:
                return st

            cfg = config.load()
            common = cfg["common"]
            symbol = common["symbol"]
            interval = common["interval"]
            leverage = int(common["leverage"])

            # 거래소 사전 설정
            try:
                account.set_margin_mode(symbol, "ISOLATED")
                account.set_leverage(symbol, leverage)
            except Exception as e:
                logger.error(f"[봇 시작 실패 - 거래소 설정] {e}")
                raise

            await binance_stream.add_listener(symbol, interval, self._on_candle)
            self._listening_key = (symbol, interval)

            st["bot_running"] = True
            state.save(st)
            logger.info(f"[봇 ON] {symbol}/{interval} | lev={leverage}")
            return st

    async def stop(self):
        """봇 OFF. 리스너만 해제 (포지션/TP는 유지)."""
        async with self._lock:
            st = state.load()
            if not st["bot_running"]:
                return st

            if self._listening_key:
                sym, itv = self._listening_key
                await binance_stream.remove_listener(sym, itv, self._on_candle)
                self._listening_key = None

            st["bot_running"] = False
            state.save(st)
            logger.info("[봇 OFF]")
            return st

    async def restore_if_running(self):
        """서버 재시작 시 봇 상태가 ON이면 리스너 자동 재등록"""
        st = state.load()
        if st.get("bot_running"):
            logger.info("[봇 상태 복구] ON으로 시작")
            try:
                await self.start()
            except Exception as e:
                logger.error(f"[봇 복구 실패] {e} — 상태를 OFF로 되돌림")
                st["bot_running"] = False
                state.save(st)

    # --------------------------------------------------------------- internal

    async def _on_candle(self, message: dict):
        """캔들 메시지 콜백 (확정봉만 처리)"""
        candle_data = message.get("candle", {})
        if not candle_data.get("is_closed"):
            return

        async with self._lock:
            try:
                await self._handle_closed_candle(message)
            except Exception as e:
                logger.error(f"[엔진 처리 오류] {e}", exc_info=True)

    async def _handle_closed_candle(self, message: dict):
        st = state.load()
        if not st["bot_running"]:
            return

        cfg = config.load()
        common = cfg["common"]
        symbol = common["symbol"]
        interval = common["interval"]

        # 메시지 심볼/인터벌이 활성과 다르면 무시 (전환 직후 잔여 콜백 방지)
        if message.get("symbol") != symbol or message.get("interval") != interval:
            return

        cd = message["candle"]
        candle_time = cd["time"]

        # 봉당 1회 보장
        if st.get("last_processed_candle_time") == candle_time:
            return

        candle = Candle(
            time=candle_time,
            open=cd["open"],
            high=cd["high"],
            low=cd["low"],
            close=cd["close"],
            volume=cd["volume"],
            rsi=message.get("rsi"),
        )

        # 현재 포지션 / 외부 청산 감지
        position = account.get_position(symbol)
        if position is None and st.get("last_entry_price") is not None:
            # TP가 체결됐거나 수동 청산됨 → 진입 상태 리셋
            logger.info("[포지션 청산 감지] 상태 리셋")
            state.reset_position_state(st)

        # 전략에 신호 요청
        active_name = cfg["active_strategy"]
        strat_cls = registry.get(active_name)
        params = cfg["strategies"].get(active_name, {})
        signal = strat_cls().on_candle_closed(candle, position, params, st)

        # 봉 처리 시간 갱신 (신호 유무와 무관)
        st["last_processed_candle_time"] = candle_time

        if signal is None:
            state.save(st)
            return

        # 안전장치: 일일 진입 한도
        if state.daily_entry_count_today(st) >= int(common["max_daily_entries"]):
            logger.info(f"[한도] 일일 최대 진입 횟수 초과 — 신호 스킵")
            state.save(st)
            return

        # 안전장치: 피라미딩 한도 (ADD일 때)
        if signal.type == "ADD":
            if st.get("pyramid_count", 0) >= int(common["max_pyramid_count"]):
                logger.info("[한도] 피라미딩 최대 횟수 초과 — 신호 스킵")
                state.save(st)
                return

        await self._execute_signal(signal, candle, common, params, st, position)
        state.save(st)

    async def _execute_signal(
        self,
        signal: Signal,
        candle: Candle,
        common: dict,
        params: dict,
        st: dict,
        prev_position: dict | None,
    ):
        symbol = common["symbol"]
        leverage = int(common["leverage"])
        capital_pct = float(common["capital_pct"])
        tp_roi_pct = float(params["tp_roi_pct"])

        # 포지션 사이즈 계산 (마진 = 총잔고 × capital_pct/100)
        balance = account.get_balance()
        margin = balance["balance"] * (capital_pct / 100.0)
        notional = margin * leverage
        price = candle.close
        qty = notional / price

        if qty <= 0:
            logger.error(f"[신호 실패] 계산된 수량이 0: balance={balance['balance']}")
            return

        logger.info(
            f"[신호 {signal.type}] rsi={signal.context['rsi']} price={price} "
            f"margin={margin:.4f} qty={qty:.6f}"
        )

        # 시장가 매수
        try:
            account.market_buy(symbol, qty)
        except Exception as e:
            logger.error(f"[시장가 매수 실패] {e}")
            return

        # 평균진입가 재조회 (체결 직후)
        # 바이낸스가 잠깐 반영 지연될 수 있어 짧게 재시도
        new_position = None
        for _ in range(5):
            new_position = account.get_position(symbol)
            if new_position is not None:
                break
            await asyncio.sleep(0.3)
        if new_position is None:
            logger.error("[신호 실패] 매수 후 포지션 조회 실패")
            return

        avg_entry = new_position["entry_price"]

        # 기존 TP 취소
        if st.get("tp_order_id"):
            account.cancel_order(symbol, st["tp_order_id"])
            st["tp_order_id"] = None

        # 새 TP 가격 = avg × (1 + roi/lev/100)
        tp_price = avg_entry * (1.0 + (tp_roi_pct / leverage / 100.0))
        try:
            tp = account.place_take_profit_long(
                symbol, new_position["quantity"], tp_price
            )
            st["tp_order_id"] = tp.get("orderId")
        except Exception as e:
            logger.error(f"[TP 주문 실패] {e} — 포지션은 보유 중, 수동 확인 필요")

        # state 업데이트
        st["last_entry_rsi"] = signal.context["rsi"]
        st["last_entry_price"] = price
        if signal.type == "ENTRY":
            st["pyramid_count"] = 0
        else:
            st["pyramid_count"] = st.get("pyramid_count", 0) + 1
        state.bump_daily_entry(st)


engine = StrategyEngine()
