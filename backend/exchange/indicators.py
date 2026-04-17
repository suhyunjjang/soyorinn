"""
기술적 지표 계산 모듈

모든 계산은 백엔드에서만 수행.
"""


def calculate_rsi(closes: list[float], period: int = 14) -> float | None:
    """
    RSI (Relative Strength Index) 계산 - Wilder's Smoothing 방식

    Args:
        closes: 종가 리스트 (시간 오름차순)
        period: RSI 기간 (기본 14)

    Returns:
        RSI 값 (0~100), 데이터 부족 시 None
    """
    if len(closes) < period + 1:
        return None

    gains = []
    losses = []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i - 1]
        gains.append(max(diff, 0.0))
        losses.append(max(-diff, 0.0))

    # 초기 평균 (단순 평균)
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    # Wilder's Smoothing (지수 평활)
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)


def calculate_rsi_series(closes: list[float], period: int = 14) -> list[float | None]:
    """
    종가 리스트 전체에 대해 RSI 시리즈 계산 (과거 데이터 API용)

    Returns:
        closes와 같은 길이의 RSI 값 리스트 (초기 period개는 None)
    """
    results: list[float | None] = [None] * len(closes)

    if len(closes) < period + 1:
        return results

    gains = []
    losses = []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i - 1]
        gains.append(max(diff, 0.0))
        losses.append(max(-diff, 0.0))

    # 초기 평균
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    def rsi_from_avg(ag: float, al: float) -> float:
        if al == 0:
            return 100.0
        return round(100 - (100 / (1 + ag / al)), 2)

    results[period] = rsi_from_avg(avg_gain, avg_loss)

    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        results[i + 1] = rsi_from_avg(avg_gain, avg_loss)

    return results
