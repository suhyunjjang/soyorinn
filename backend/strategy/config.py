"""
전략 설정 영속화 (JSON 파일)

구조:
{
  "active_strategy": "rsi_long",
  "common": {
    "symbol": "ETHUSDT",
    "interval": "15m",
    "capital_pct": 10,
    "leverage": 7,
    "max_daily_entries": 5,
    "max_pyramid_count": 5
  },
  "strategies": {
    "rsi_long": { "rsi_threshold": 30, "tp_roi_pct": 5 }
  }
}
"""

import json
import logging
from pathlib import Path
from threading import Lock

from strategy import registry

logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).parent.parent / "data" / "strategy_config.json"

DEFAULT_COMMON = {
    "symbol": "ETHUSDT",
    "interval": "15m",
    "capital_pct": 10.0,
    "leverage": 7,
    "max_pyramid_count": 5,
}

_lock = Lock()


def _default_config() -> dict:
    """등록된 전략 기본값으로 초기 config 생성"""
    return {
        "active_strategy": "rsi_long",
        "common": dict(DEFAULT_COMMON),
        "strategies": {
            name: dict(registry.get(name).default_params)
            for name in registry.names()
        },
    }


def load() -> dict:
    """파일에서 설정 로드, 없으면 기본값 생성 후 저장"""
    with _lock:
        if not CONFIG_PATH.exists():
            cfg = _default_config()
            _write(cfg)
            return cfg
        try:
            with CONFIG_PATH.open("r", encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception as e:
            logger.error(f"[설정 로드 실패] {e} — 기본값으로 재생성")
            cfg = _default_config()
            _write(cfg)
            return cfg

        # 새 전략이 추가되어 파일에 없을 수 있으므로 보강
        cfg.setdefault("active_strategy", "rsi_long")
        cfg.setdefault("common", dict(DEFAULT_COMMON))
        for k, v in DEFAULT_COMMON.items():
            cfg["common"].setdefault(k, v)
        cfg.setdefault("strategies", {})
        for name in registry.names():
            defaults = dict(registry.get(name).default_params)
            cfg["strategies"].setdefault(name, defaults)
            # 새 파라미터가 추가된 경우 보강 (기존 값은 유지)
            for k, v in defaults.items():
                cfg["strategies"][name].setdefault(k, v)
        return cfg


def save(cfg: dict) -> dict:
    """설정 저장 + 검증"""
    with _lock:
        # 활성 전략은 등록된 것만 허용
        if cfg.get("active_strategy") not in registry.names():
            raise ValueError(f"등록되지 않은 전략: {cfg.get('active_strategy')}")
        _write(cfg)
        return cfg


def _write(cfg: dict):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CONFIG_PATH.open("w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
