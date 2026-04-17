/**
 * 지갑 잔고 표시 (USDT)
 */

import type { Balance } from "../hooks/useAccount";

interface Props { balance: Balance | null }

const fmt = (n: number) => n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

export default function BalancePanel({ balance }: Props) {
  if (!balance) {
    return <div style={{ color: "#666", fontSize: "13px" }}>잔고 로딩 중...</div>;
  }

  const pnlColor = balance.unrealized_pnl >= 0 ? "#26a69a" : "#ef5350";

  return (
    <div style={{ display: "flex", gap: "32px", flexWrap: "wrap" }}>
      <Item label="총 잔고" value={`${fmt(balance.balance)} USDT`} />
      <Item label="주문 가능" value={`${fmt(balance.available)} USDT`} />
      <Item label="미실현 손익" value={`${balance.unrealized_pnl >= 0 ? "+" : ""}${fmt(balance.unrealized_pnl)} USDT`} color={pnlColor} />
    </div>
  );
}

function Item({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div>
      <div style={{ color: "#666", fontSize: "12px", marginBottom: "4px" }}>{label}</div>
      <div style={{ color: color ?? "#d1d4dc", fontSize: "18px", fontWeight: 600 }}>{value}</div>
    </div>
  );
}
