/**
 * 계정 정보 통합 패널
 * - 잔고 / 포지션 / 오픈 오더를 한 번에 표시
 * - useAccount 훅으로 5초마다 자동 갱신
 */

import type { Balance, Position, OpenOrder } from "../hooks/useAccount";
import BalancePanel from "./BalancePanel";
import PositionsTable from "./PositionsTable";
import OrdersTable from "./OrdersTable";

interface Props {
  balance: Balance | null;
  positions: Position[];
  orders: OpenOrder[];
}

export default function AccountPanel({ balance, positions, orders }: Props) {

  return (
    <div style={{ display: "grid", gap: "16px" }}>
      <Section title="지갑 잔고">
        <BalancePanel balance={balance} />
      </Section>
      <Section title={`보유 포지션 (${positions.length})`}>
        <PositionsTable positions={positions} />
      </Section>
      <Section title={`진행 중인 주문 (${orders.length})`}>
        <OrdersTable orders={orders} />
      </Section>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ background: "#131722", borderRadius: "8px", padding: "16px" }}>
      <div style={{ marginBottom: "12px", fontSize: "13px", color: "#888", fontWeight: 500 }}>{title}</div>
      {children}
    </div>
  );
}
