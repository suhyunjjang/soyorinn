/**
 * 계정 정보 폴링 훅
 * - 잔고 / 포지션 / 오픈 오더를 5초마다 갱신
 * - 백엔드 인증 엔드포인트 호출
 */

import { useEffect, useState } from "react";

const API_BASE = "http://localhost:8000";
const REFRESH_MS = 5000;

export interface Balance {
  asset: string;
  balance: number;
  available: number;
  unrealized_pnl: number;
}

export interface Position {
  symbol: string;
  side: "LONG" | "SHORT";
  quantity: number;
  entry_price: number;
  mark_price: number;
  unrealized_pnl: number;
  leverage: number;
  liquidation_price: number;
}

export interface OpenOrder {
  order_id: number;
  symbol: string;
  side: "BUY" | "SELL";
  type: string;
  quantity: number;
  price: number;
  stop_price: number;
  status: string;
  time: number;
}

interface ApiError { error: string }

async function fetchJson<T>(path: string): Promise<T | null> {
  try {
    const r = await fetch(`${API_BASE}${path}`);
    const data = await r.json();
    if ((data as ApiError).error) {
      console.error(`[${path}]`, (data as ApiError).error);
      return null;
    }
    return data as T;
  } catch (e) {
    console.error(`[${path}]`, e);
    return null;
  }
}

export function useAccount() {
  const [balance, setBalance] = useState<Balance | null>(null);
  const [positions, setPositions] = useState<Position[]>([]);
  const [orders, setOrders] = useState<OpenOrder[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    const refresh = async () => {
      const [b, p, o] = await Promise.all([
        fetchJson<Balance>("/account/balance"),
        fetchJson<Position[]>("/account/positions"),
        fetchJson<OpenOrder[]>("/account/orders"),
      ]);
      if (cancelled) return;
      if (b) setBalance(b);
      if (p) setPositions(p);
      if (o) setOrders(o);
      setLoading(false);
    };

    refresh();
    const id = setInterval(refresh, REFRESH_MS);
    return () => { cancelled = true; clearInterval(id); };
  }, []);

  return { balance, positions, orders, loading };
}
