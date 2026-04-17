/**
 * 백엔드 WebSocket 연결 훅
 * - 심볼 또는 인터벌이 바뀌면 기존 연결 끊고 새 연결
 * - 연결이 끊기면 3초 후 자동 재연결
 */

import { useEffect, useRef, useCallback } from "react";

const WS_BASE = "ws://localhost:8000/ws";

export interface Candle {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  is_closed: boolean;
}

interface WsMessage {
  symbol: string;
  interval: string;
  candle: Candle;
  rsi: number | null;
}

export interface WsUpdate {
  candle: Candle;
  rsi: number | null;
}

export function useWebSocket(
  symbol: string,
  interval: string,
  onUpdate: (update: WsUpdate) => void
) {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  // 현재 활성 (symbol, interval) 추적 - 재연결 루프 방지용
  const activeKey = useRef(`${symbol}/${interval}`);

  const connect = useCallback((sym: string, intv: string) => {
    const key = `${sym}/${intv}`;

    // 기존 연결 정리
    if (wsRef.current) {
      wsRef.current.onclose = null;
      wsRef.current.close();
      wsRef.current = null;
    }
    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current);
    }

    const ws = new WebSocket(`${WS_BASE}/${sym}/${intv}`);
    wsRef.current = ws;

    ws.onopen = () => console.log(`[WS] 연결: ${key}`);

    ws.onmessage = (event) => {
      const msg: WsMessage = JSON.parse(event.data);
      onUpdate({ candle: msg.candle, rsi: msg.rsi });
    };

    ws.onerror = (e) => console.error(`[WS] 오류:`, e);

    ws.onclose = () => {
      console.warn(`[WS] 종료: ${key} | 3초 후 재연결`);
      // 현재 활성 키와 같을 때만 재연결 (심볼/인터벌이 바뀐 경우 재연결 스킵)
      if (activeKey.current === key) {
        reconnectTimer.current = setTimeout(() => connect(sym, intv), 3000);
      }
    };
  }, [onUpdate]);

  useEffect(() => {
    activeKey.current = `${symbol}/${interval}`;
    connect(symbol, interval);

    return () => {
      if (wsRef.current) {
        wsRef.current.onclose = null;
        wsRef.current.close();
      }
      if (reconnectTimer.current) {
        clearTimeout(reconnectTimer.current);
      }
    };
  }, [symbol, interval, connect]);
}
