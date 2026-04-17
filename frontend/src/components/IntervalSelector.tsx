/**
 * 인터벌 선택 버튼 컴포넌트
 */

const INTERVALS = [
  { value: "1m",  label: "1분" },
  { value: "5m",  label: "5분" },
  { value: "15m", label: "15분" },
  { value: "1h",  label: "1시간" },
  { value: "4h",  label: "4시간" },
  { value: "1d",  label: "1일" },
  { value: "1w",  label: "1주" },
  { value: "1M",  label: "1달" },
];

interface Props {
  selected: string;
  onChange: (interval: string) => void;
}

export default function IntervalSelector({ selected, onChange }: Props) {
  return (
    <div style={{ display: "flex", gap: "6px" }}>
      {INTERVALS.map(({ value, label }) => (
        <button
          key={value}
          onClick={() => onChange(value)}
          style={{
            padding: "4px 12px",
            borderRadius: "4px",
            border: "1px solid #333",
            background: selected === value ? "#3a3a5c" : "transparent",
            color: selected === value ? "#a0a8ff" : "#666",
            fontWeight: selected === value ? "bold" : "normal",
            cursor: "pointer",
            fontSize: "13px",
          }}
        >
          {label}
        </button>
      ))}
    </div>
  );
}
