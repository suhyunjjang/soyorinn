/**
 * 보유 포지션 테이블
 */

import type { Position } from "../hooks/useAccount";

interface Props { positions: Position[] }

const fmt = (n: number, d = 2) => n.toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d });

export default function PositionsTable({ positions }: Props) {
  if (positions.length === 0) {
    return <div style={{ color: "#666", fontSize: "13px", padding: "12px 0" }}>보유 포지션 없음</div>;
  }

  return (
    <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13px" }}>
      <thead>
        <tr style={{ color: "#666", textAlign: "right", borderBottom: "1px solid #2a2e39" }}>
          <th style={th("left")}>심볼</th>
          <th style={th("left")}>방향</th>
          <th style={th()}>수량</th>
          <th style={th()}>진입가</th>
          <th style={th()}>현재가</th>
          <th style={th()}>미실현 손익</th>
          <th style={th()}>레버리지</th>
          <th style={th()}>청산가</th>
        </tr>
      </thead>
      <tbody>
        {positions.map((p) => {
          const pnlColor = p.unrealized_pnl >= 0 ? "#26a69a" : "#ef5350";
          const sideColor = p.side === "LONG" ? "#26a69a" : "#ef5350";
          return (
            <tr key={p.symbol} style={{ borderBottom: "1px solid #1e2330" }}>
              <td style={td("left")}>{p.symbol}</td>
              <td style={{ ...td("left"), color: sideColor, fontWeight: 600 }}>{p.side}</td>
              <td style={td()}>{fmt(p.quantity, 4)}</td>
              <td style={td()}>{fmt(p.entry_price)}</td>
              <td style={td()}>{fmt(p.mark_price)}</td>
              <td style={{ ...td(), color: pnlColor, fontWeight: 600 }}>
                {p.unrealized_pnl >= 0 ? "+" : ""}{fmt(p.unrealized_pnl)}
              </td>
              <td style={td()}>{p.leverage}x</td>
              <td style={td()}>{fmt(p.liquidation_price)}</td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

const th = (align: "left" | "right" = "right"): React.CSSProperties => ({
  padding: "8px 12px", fontWeight: 500, textAlign: align,
});
const td = (align: "left" | "right" = "right"): React.CSSProperties => ({
  padding: "10px 12px", textAlign: align,
});
