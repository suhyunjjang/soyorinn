/**
 * 메인 앱 컴포넌트
 * - 심볼 + 인터벌 선택
 * - 실시간 캔들차트
 */

import { useState } from "react";
import SymbolSelector from "./components/SymbolSelector";
import IntervalSelector from "./components/IntervalSelector";
import CandleChart from "./components/CandleChart";
import AccountPanel from "./components/AccountPanel";
import StrategyPanel from "./components/StrategyPanel";
import { useCandleCountdown } from "./hooks/useCandleCountdown";

export default function App() {
  const [symbol, setSymbol] = useState("ETHUSDT");
  const [interval, setInterval] = useState("5m");
  const countdown = useCandleCountdown(interval);

  return (
    <div style={{
      minHeight: "100vh",
      background: "#0f1117",
      color: "#d1d4dc",
      fontFamily: "sans-serif",
      padding: "24px",
    }}>
      {/* 헤더 */}
      <h1 style={{ margin: "0 0 20px 0", fontSize: "20px", color: "#f0b90b" }}>
        자동매매 대시보드
      </h1>

      {/* 심볼 + 인터벌 선택 */}
      <div style={{ display: "flex", alignItems: "center", gap: "16px", marginBottom: "16px", flexWrap: "wrap" }}>
        <SymbolSelector selected={symbol} onChange={setSymbol} />
        <div style={{ width: "1px", height: "24px", background: "#333" }} />
        <IntervalSelector selected={interval} onChange={setInterval} />
      </div>

      {/* 캔들차트 */}
      <div style={{ background: "#131722", borderRadius: "8px", padding: "12px", marginBottom: "16px" }}>
        <div style={{ marginBottom: "8px", fontSize: "13px", color: "#666" }}>
          {symbol} · {interval} · 실시간 · 다음 봉까지 <span style={{ color: "#d1d4dc" }}>{countdown}</span>
        </div>
        <CandleChart symbol={symbol} interval={interval} />
      </div>

      {/* 전략 설정 / 봇 ON·OFF */}
      <div style={{ background: "#131722", borderRadius: "8px", padding: "16px", marginBottom: "16px" }}>
        <div style={{ marginBottom: "12px", fontSize: "13px", color: "#888", fontWeight: 500 }}>전략</div>
        <StrategyPanel />
      </div>

      {/* 계정 정보 (잔고 / 포지션 / 오더) */}
      <AccountPanel />
    </div>
  );
}
