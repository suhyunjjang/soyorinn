/**
 * 다음 봉 시작까지 남은 시간 카운트다운 훅
 * - 바이낸스는 UTC 경계로 봉을 정렬 (1d=00:00 UTC, 1w=월요일 00:00 UTC, 1M=1일 00:00 UTC)
 * - 1초마다 갱신
 */

import { useEffect, useState } from "react";

const FIXED_INTERVAL_SEC: Record<string, number> = {
  "1m": 60,
  "5m": 300,
  "15m": 900,
  "1h": 3600,
  "4h": 14400,
  "1d": 86400,
};

function getNextCandleSec(interval: string): number {
  const nowSec = Math.floor(Date.now() / 1000);
  const fixed = FIXED_INTERVAL_SEC[interval];
  if (fixed) return Math.floor(nowSec / fixed) * fixed + fixed;

  const d = new Date();
  if (interval === "1w") {
    // 다음 월요일 00:00 UTC
    const dow = d.getUTCDay(); // 0=일, 1=월, ..., 6=토
    const daysUntilMon = ((8 - dow) % 7) || 7;
    return Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate() + daysUntilMon) / 1000;
  }
  if (interval === "1M") {
    // 다음 달 1일 00:00 UTC
    return Date.UTC(d.getUTCFullYear(), d.getUTCMonth() + 1, 1) / 1000;
  }
  return nowSec;
}

function format(remainSec: number): string {
  if (remainSec < 0) remainSec = 0;
  const d = Math.floor(remainSec / 86400);
  const h = Math.floor((remainSec % 86400) / 3600);
  const m = Math.floor((remainSec % 3600) / 60);
  const s = remainSec % 60;
  const pad = (n: number) => String(n).padStart(2, "0");

  if (d > 0) return `${d}일 ${pad(h)}:${pad(m)}:${pad(s)}`;
  if (h > 0) return `${pad(h)}:${pad(m)}:${pad(s)}`;
  return `${pad(m)}:${pad(s)}`;
}

export function useCandleCountdown(interval: string): string {
  const [text, setText] = useState(() => format(getNextCandleSec(interval) - Math.floor(Date.now() / 1000)));

  useEffect(() => {
    const tick = () => {
      const remain = getNextCandleSec(interval) - Math.floor(Date.now() / 1000);
      setText(format(remain));
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [interval]);

  return text;
}
