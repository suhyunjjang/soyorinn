/**
 * 진행 중인 주문 (오픈 오더) 테이블
 */

import type { OpenOrder } from "../hooks/useAccount";

interface Props { orders: OpenOrder[] }

const fmt = (n: number, d = 2) => n.toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d });

const fmtTime = (sec: number) => {
  const d = new Date(sec * 1000);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getMonth() + 1}/${d.getDate()} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
};

export default function OrdersTable({ orders }: Props) {
  if (orders.length === 0) {
    return <div style={{ color: "#666", fontSize: "13px", padding: "12px 0" }}>진행 중인 주문 없음</div>;
  }

  return (
    <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13px" }}>
      <thead>
        <tr style={{ color: "#666", textAlign: "right", borderBottom: "1px solid #2a2e39" }}>
          <th style={th("left")}>심볼</th>
          <th style={th("left")}>방향</th>
          <th style={th("left")}>유형</th>
          <th style={th()}>수량</th>
          <th style={th()}>가격</th>
          <th style={th()}>스톱가</th>
          <th style={th("left")}>시간</th>
        </tr>
      </thead>
      <tbody>
        {orders.map((o) => {
          const sideColor = o.side === "BUY" ? "#26a69a" : "#ef5350";
          return (
            <tr key={o.order_id} style={{ borderBottom: "1px solid #1e2330" }}>
              <td style={td("left")}>{o.symbol}</td>
              <td style={{ ...td("left"), color: sideColor, fontWeight: 600 }}>{o.side}</td>
              <td style={td("left")}>{o.type}</td>
              <td style={td()}>{fmt(o.quantity, 4)}</td>
              <td style={td()}>{o.price > 0 ? fmt(o.price) : "-"}</td>
              <td style={td()}>{o.stop_price > 0 ? fmt(o.stop_price) : "-"}</td>
              <td style={{ ...td("left"), color: "#888" }}>{fmtTime(o.time)}</td>
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
