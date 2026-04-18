"""
전략 추상 인터페이스

모든 전략은 Strategy를 상속하고 다음을 정의한다.
- name / display_name / default_params / param_schema
- on_candle_closed(candle, position, state) -> Signal | None
"""

from dataclasses import dataclass
from typing import Literal


SignalType = Literal["ENTRY", "ADD"]


@dataclass
class Signal:
    """전략이 봉 마감 시 반환하는 매매 신호"""
    type: SignalType
    # 신호 발생 시점의 RSI 등 컨텍스트 (state 기록용)
    context: dict


@dataclass
class Candle:
    """확정된 봉 데이터 + 지표"""
    time: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    rsi: float | None


class Strategy:
    """전략 베이스 클래스"""

    name: str = ""                # 식별자 (영문, 소문자, 변경 금지)
    display_name: str = ""        # UI 표시명
    default_params: dict = {}     # 전략별 파라미터 기본값
    # UI 자동 생성용 스키마: { 키: { "label": str, "type": "number"|"int", "min": ..., "max": ..., "step": ... } }
    param_schema: dict = {}

    def on_candle_closed(
        self,
        candle: Candle,
        position: dict | None,
        params: dict,
        state: dict,
    ) -> Signal | None:
        """
        봉 마감 시 호출. 매매 신호를 반환하거나 None.

        Args:
            candle: 방금 마감된 봉
            position: 현재 보유 포지션 (없으면 None)
            params: 이 전략의 파라미터 (병합된 최종값)
            state: 봇 상태 (last_entry_rsi, last_entry_price 등)
        """
        raise NotImplementedError
