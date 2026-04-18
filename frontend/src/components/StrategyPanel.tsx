/**
 * 전략 설정 + 봇 ON/OFF 패널
 *
 * - 전략 드롭다운 (param_schema 기반 입력 자동 렌더)
 * - 공통 설정: 심볼 / 인터벌 / 자본% / 레버리지 / 일일·피라미딩 한도
 * - 봇 ON 상태에서는 모든 입력 잠금 (서버에서도 거부)
 * - 마지막 진입 정보 / 일일 진입 카운트 표시
 */

import { useEffect, useMemo, useState } from "react";
import {
  useStrategy,
  type StrategySettings,
} from "../hooks/useStrategy";

const SYMBOLS = ["BTCUSDT", "ETHUSDT", "XRPUSDT", "SOLUSDT"];
const INTERVALS = ["1m", "5m", "15m", "1h", "4h", "1d"];

export default function StrategyPanel() {
  const { list, settings, state, loading, error, updateSettings, toggle } = useStrategy();

  // 편집용 로컬 사본
  const [draft, setDraft] = useState<StrategySettings | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveMsg, setSaveMsg] = useState<string | null>(null);

  useEffect(() => {
    if (settings) setDraft(structuredClone(settings));
  }, [settings]);

  const botRunning = state?.bot_running ?? false;
  const disabled = botRunning || saving;

  const activeMeta = useMemo(
    () => list.find((s) => s.name === draft?.active_strategy),
    [list, draft?.active_strategy],
  );

  const dirty = useMemo(() => {
    if (!draft || !settings) return false;
    return JSON.stringify(draft) !== JSON.stringify(settings);
  }, [draft, settings]);

  if (loading) return <div style={{ color: "#888" }}>전략 정보 로딩 중...</div>;
  if (!draft || !settings) return <div style={{ color: "#888" }}>전략 정보 없음</div>;

  const onSave = async () => {
    setSaving(true);
    setSaveMsg(null);
    try {
      await updateSettings(draft);
      setSaveMsg("저장됨");
      setTimeout(() => setSaveMsg(null), 1500);
    } catch (e) {
      setSaveMsg(`저장 실패: ${(e as Error).message}`);
    } finally {
      setSaving(false);
    }
  };

  const onToggle = async () => {
    try {
      await toggle();
    } catch {
      // error는 hook의 error로 표시됨
    }
  };

  // common 필드 핸들러
  const setCommon = <K extends keyof StrategySettings["common"]>(
    key: K,
    value: StrategySettings["common"][K],
  ) => {
    setDraft({ ...draft, common: { ...draft.common, [key]: value } });
  };

  // 활성 전략 파라미터 핸들러
  const setParam = (key: string, value: number) => {
    const name = draft.active_strategy;
    setDraft({
      ...draft,
      strategies: {
        ...draft.strategies,
        [name]: { ...draft.strategies[name], [key]: value },
      },
    });
  };

  return (
    <div style={{ display: "grid", gap: "16px" }}>
      {/* 봇 상태 + 토글 */}
      <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
        <Badge running={botRunning} />
        <button
          onClick={onToggle}
          style={{
            padding: "8px 20px",
            borderRadius: "6px",
            border: "none",
            background: botRunning ? "#d9534f" : "#5cb85c",
            color: "#fff",
            fontWeight: "bold",
            cursor: "pointer",
            fontSize: "14px",
          }}
        >
          {botRunning ? "봇 OFF" : "봇 ON"}
        </button>
        {error && <span style={{ color: "#d9534f", fontSize: "12px" }}>{error}</span>}
      </div>

      {/* 활성 전략 선택 */}
      <Field label="활성 전략">
        <select
          disabled={disabled}
          value={draft.active_strategy}
          onChange={(e) => setDraft({ ...draft, active_strategy: e.target.value })}
          style={selectStyle}
        >
          {list.map((s) => (
            <option key={s.name} value={s.name}>{s.display_name}</option>
          ))}
        </select>
      </Field>

      {/* 공통 설정 */}
      <SubSection title="공통 설정">
        <Field label="심볼">
          <select
            disabled={disabled}
            value={draft.common.symbol}
            onChange={(e) => setCommon("symbol", e.target.value)}
            style={selectStyle}
          >
            {SYMBOLS.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </Field>
        <Field label="봉 인터벌">
          <select
            disabled={disabled}
            value={draft.common.interval}
            onChange={(e) => setCommon("interval", e.target.value)}
            style={selectStyle}
          >
            {INTERVALS.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </Field>
        <Field label="자본 비율 % (마진)">
          <NumInput
            disabled={disabled}
            value={draft.common.capital_pct}
            min={0.1} max={100} step={0.1}
            onChange={(v) => setCommon("capital_pct", v)}
          />
        </Field>
        <Field label="레버리지">
          <NumInput
            disabled={disabled}
            value={draft.common.leverage}
            min={1} max={125} step={1}
            onChange={(v) => setCommon("leverage", Math.round(v))}
          />
        </Field>
        <Field label="일일 최대 진입">
          <NumInput
            disabled={disabled}
            value={draft.common.max_daily_entries}
            min={1} max={100} step={1}
            onChange={(v) => setCommon("max_daily_entries", Math.round(v))}
          />
        </Field>
        <Field label="피라미딩 최대 횟수">
          <NumInput
            disabled={disabled}
            value={draft.common.max_pyramid_count}
            min={0} max={50} step={1}
            onChange={(v) => setCommon("max_pyramid_count", Math.round(v))}
          />
        </Field>
      </SubSection>

      {/* 활성 전략 파라미터 (스키마 기반 자동 렌더) */}
      {activeMeta && (
        <SubSection title={`전략 파라미터 — ${activeMeta.display_name}`}>
          {Object.entries(activeMeta.param_schema).map(([key, schema]) => (
            <Field key={key} label={schema.label}>
              <NumInput
                disabled={disabled}
                value={draft.strategies[draft.active_strategy]?.[key] ?? 0}
                min={schema.min}
                max={schema.max}
                step={schema.step}
                onChange={(v) => setParam(key, v)}
              />
            </Field>
          ))}
        </SubSection>
      )}

      {/* 저장 */}
      <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
        <button
          onClick={onSave}
          disabled={disabled || !dirty}
          style={{
            padding: "8px 20px",
            borderRadius: "6px",
            border: "none",
            background: !dirty || disabled ? "#333" : "#f0b90b",
            color: !dirty || disabled ? "#666" : "#000",
            fontWeight: "bold",
            cursor: !dirty || disabled ? "not-allowed" : "pointer",
            fontSize: "14px",
          }}
        >
          설정 저장
        </button>
        {saveMsg && <span style={{ color: "#aaa", fontSize: "12px" }}>{saveMsg}</span>}
        {botRunning && (
          <span style={{ color: "#888", fontSize: "12px" }}>
            * 봇 ON 상태에서는 변경 불가 — OFF 후 변경하세요
          </span>
        )}
      </div>

      {/* 런타임 상태 */}
      <SubSection title="현재 상태">
        <Stat label="마지막 진입 RSI" value={state?.last_entry_rsi ?? "-"} />
        <Stat label="마지막 진입 가격" value={state?.last_entry_price ?? "-"} />
        <Stat label="피라미딩 카운트" value={state?.pyramid_count ?? 0} />
        <Stat label="오늘 진입 횟수" value={state?.daily_entry_count ?? 0} />
        <Stat label="활성 TP 주문 ID" value={state?.tp_order_id ?? "-"} />
      </SubSection>
    </div>
  );
}

// ----------------------------------------------------------------------------

function Badge({ running }: { running: boolean }) {
  return (
    <span style={{
      padding: "4px 10px",
      borderRadius: "12px",
      background: running ? "#1f5e3a" : "#5e1f1f",
      color: running ? "#a8e6b8" : "#e6a8a8",
      fontSize: "12px",
      fontWeight: "bold",
    }}>
      봇 {running ? "ON" : "OFF"}
    </span>
  );
}

function SubSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{
      border: "1px solid #2a2e3a",
      borderRadius: "6px",
      padding: "12px",
    }}>
      <div style={{ fontSize: "12px", color: "#888", marginBottom: "10px" }}>{title}</div>
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
        gap: "10px",
      }}>
        {children}
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label style={{ display: "flex", flexDirection: "column", gap: "4px", fontSize: "12px", color: "#aaa" }}>
      <span>{label}</span>
      {children}
    </label>
  );
}

function Stat({ label, value }: { label: string; value: string | number | null }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
      <span style={{ fontSize: "11px", color: "#888" }}>{label}</span>
      <span style={{ fontSize: "13px", color: "#d1d4dc" }}>{value ?? "-"}</span>
    </div>
  );
}

function NumInput({
  value, onChange, disabled, min, max, step,
}: {
  value: number;
  onChange: (v: number) => void;
  disabled?: boolean;
  min?: number;
  max?: number;
  step?: number;
}) {
  return (
    <input
      type="number"
      value={value}
      disabled={disabled}
      min={min}
      max={max}
      step={step}
      onChange={(e) => {
        const n = parseFloat(e.target.value);
        if (!Number.isNaN(n)) onChange(n);
      }}
      style={inputStyle}
    />
  );
}

const inputStyle: React.CSSProperties = {
  background: "#0f1117",
  border: "1px solid #333",
  borderRadius: "4px",
  padding: "6px 8px",
  color: "#d1d4dc",
  fontSize: "13px",
};

const selectStyle: React.CSSProperties = {
  ...inputStyle,
  cursor: "pointer",
};
