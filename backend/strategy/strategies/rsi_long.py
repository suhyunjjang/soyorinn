"""
RSI 롱 전략

진입 조건 (봉 마감 시):
- 보유 포지션 없음 + RSI <= rsi_threshold                                  → ENTRY
- 보유 중 + RSI <= 마지막 진입 RSI
         + 가격 <= 마지막 진입가 × (1 - pyramid_drop_pct/100)              → ADD (피라미딩)

청산은 거래소의 TAKE_PROFIT_MARKET reduceOnly 주문이 자동 처리.
손절 없음.
"""

from strategy.base import Strategy, Signal, Candle
from strategy.registry import register


@register
class RsiLongStrategy(Strategy):
    name = "rsi_long"
    display_name = "RSI 롱"

    default_params = {
        "rsi_threshold": 30,
        "tp_roi_pct": 5.0,
        "pyramid_drop_pct": 2.0,
    }

    param_schema = {
        "rsi_threshold": {
            "label": "RSI 진입 임계값",
            "type": "number",
            "min": 1,
            "max": 50,
            "step": 1,
        },
        "tp_roi_pct": {
            "label": "익절 마진 ROI %",
            "type": "number",
            "min": 0.1,
            "max": 100,
            "step": 0.1,
        },
        "pyramid_drop_pct": {
            "label": "물타기 추가 진입 하락 %",
            "type": "number",
            "min": 0.1,
            "max": 10,
            "step": 0.1,
        },
    }

    def on_candle_closed(
        self,
        candle: Candle,
        position: dict | None,
        params: dict,
        state: dict,
    ) -> Signal | None:
        rsi = candle.rsi
        if rsi is None:
            return None

        threshold = float(params["rsi_threshold"])

        # 신규 진입: 포지션 없고 RSI가 임계값 이하
        if position is None:
            if rsi <= threshold:
                return Signal(type="ENTRY", context={"rsi": rsi, "price": candle.close})
            return None

        # 피라미딩: 마지막 진입 RSI 이하 + 가격이 일정 % 추가 하락
        last_rsi = state.get("last_entry_rsi")
        last_price = state.get("last_entry_price")
        if last_rsi is None or last_price is None:
            # 봇 외부에서 포지션이 들어온 경우 — 추가 진입은 보류
            return None

        drop_pct = float(params.get("pyramid_drop_pct", 2.0))
        add_threshold_price = last_price * (1.0 - drop_pct / 100.0)

        if rsi <= last_rsi and candle.close <= add_threshold_price:
            return Signal(type="ADD", context={"rsi": rsi, "price": candle.close})
        return None
