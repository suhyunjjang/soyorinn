"""
전략 레지스트리

각 전략 모듈이 import 시 register()로 자기 자신을 등록한다.
"""

from strategy.base import Strategy

_REGISTRY: dict[str, type[Strategy]] = {}


def register(cls: type[Strategy]) -> type[Strategy]:
    """전략 클래스 등록 (데코레이터 또는 직접 호출)"""
    if not cls.name:
        raise ValueError(f"전략 {cls.__name__}에 name이 없습니다")
    if cls.name in _REGISTRY:
        raise ValueError(f"전략 이름 중복: {cls.name}")
    _REGISTRY[cls.name] = cls
    return cls


def get(name: str) -> type[Strategy]:
    if name not in _REGISTRY:
        raise KeyError(f"등록되지 않은 전략: {name}")
    return _REGISTRY[name]


def list_all() -> list[dict]:
    """프론트로 보낼 전략 메타 정보 목록"""
    return [
        {
            "name": cls.name,
            "display_name": cls.display_name,
            "default_params": cls.default_params,
            "param_schema": cls.param_schema,
        }
        for cls in _REGISTRY.values()
    ]


def names() -> list[str]:
    return list(_REGISTRY.keys())
