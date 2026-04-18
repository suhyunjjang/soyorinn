/**
 * 전략 설정 / 상태 / 토글 훅
 *
 * 백엔드:
 *   GET  /strategy/list      - 전략 목록 + param_schema
 *   GET  /strategy/settings  - 현재 설정
 *   PUT  /strategy/settings  - 설정 저장
 *   POST /strategy/toggle    - 봇 ON/OFF
 *   GET  /strategy/state     - 봇 상태 (5초 폴링)
 */

import { useCallback, useEffect, useState } from "react";

const API_BASE = "http://localhost:8000";
const STATE_REFRESH_MS = 5000;

export interface ParamSchemaField {
  label: string;
  type: "number" | "int";
  min?: number;
  max?: number;
  step?: number;
}

export interface StrategyMeta {
  name: string;
  display_name: string;
  default_params: Record<string, number>;
  param_schema: Record<string, ParamSchemaField>;
}

export interface StrategySettings {
  active_strategy: string;
  common: {
    symbol: string;
    interval: string;
    capital_pct: number;
    leverage: number;
    max_daily_entries: number;
    max_pyramid_count: number;
  };
  strategies: Record<string, Record<string, number>>;
}

export interface StrategyState {
  bot_running: boolean;
  last_entry_rsi: number | null;
  last_entry_price: number | null;
  pyramid_count: number;
  tp_order_id: number | null;
  daily_entry_date: string | null;
  daily_entry_count: number;
  last_processed_candle_time: number | null;
}

export function useStrategy() {
  const [list, setList] = useState<StrategyMeta[]>([]);
  const [settings, setSettings] = useState<StrategySettings | null>(null);
  const [state, setState] = useState<StrategyState | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 초기 로드
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [l, s, st] = await Promise.all([
          fetch(`${API_BASE}/strategy/list`).then((r) => r.json()),
          fetch(`${API_BASE}/strategy/settings`).then((r) => r.json()),
          fetch(`${API_BASE}/strategy/state`).then((r) => r.json()),
        ]);
        if (cancelled) return;
        setList(l);
        setSettings(s);
        setState(st);
      } catch (e) {
        if (!cancelled) setError(String(e));
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  // 상태 폴링
  useEffect(() => {
    let cancelled = false;
    const tick = async () => {
      try {
        const st = await fetch(`${API_BASE}/strategy/state`).then((r) => r.json());
        if (!cancelled) setState(st);
      } catch {
        // ignore
      }
    };
    const id = setInterval(tick, STATE_REFRESH_MS);
    return () => { cancelled = true; clearInterval(id); };
  }, []);

  const updateSettings = useCallback(async (next: StrategySettings) => {
    setError(null);
    const r = await fetch(`${API_BASE}/strategy/settings`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(next),
    });
    if (!r.ok) {
      const detail = await r.json().catch(() => ({ detail: r.statusText }));
      const msg = detail.detail || r.statusText;
      setError(msg);
      throw new Error(msg);
    }
    const saved = await r.json();
    setSettings(saved);
    return saved as StrategySettings;
  }, []);

  const toggle = useCallback(async () => {
    setError(null);
    const r = await fetch(`${API_BASE}/strategy/toggle`, { method: "POST" });
    if (!r.ok) {
      const detail = await r.json().catch(() => ({ detail: r.statusText }));
      const msg = detail.detail || r.statusText;
      setError(msg);
      throw new Error(msg);
    }
    const st = await r.json();
    setState(st);
    return st as StrategyState;
  }, []);

  return { list, settings, state, loading, error, updateSettings, toggle };
}
