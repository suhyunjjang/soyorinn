"""
전략 구현체 패키지

각 전략 모듈이 import 시 registry에 등록된다.
새 전략 추가 시 아래에 import만 한 줄 더하면 된다.
"""

from . import rsi_long  # noqa: F401
