/**
 * 심볼 선택 버튼 컴포넌트
 * - BTC / ETH / XRP / SOL 선택
 */

const SYMBOLS = ["BTCUSDT", "ETHUSDT", "XRPUSDT", "SOLUSDT"];

// 화면에 표시할 짧은 이름
const LABELS: Record<string, string> = {
  BTCUSDT: "BTC",
  ETHUSDT: "ETH",
  XRPUSDT: "XRP",
  SOLUSDT: "SOL",
};

interface Props {
  selected: string;
  onChange: (symbol: string) => void;
}

export default function SymbolSelector({ selected, onChange }: Props) {
  return (
    <div style={{ display: "flex", gap: "8px" }}>
      {SYMBOLS.map((sym) => (
        <button
          key={sym}
          onClick={() => onChange(sym)}
          style={{
            padding: "6px 18px",
            borderRadius: "6px",
            border: "1px solid #444",
            background: selected === sym ? "#f0b90b" : "#1e1e2e",
            color: selected === sym ? "#000" : "#ccc",
            fontWeight: selected === sym ? "bold" : "normal",
            cursor: "pointer",
            fontSize: "14px",
          }}
        >
          {LABELS[sym]}
        </button>
      ))}
    </div>
  );
}
