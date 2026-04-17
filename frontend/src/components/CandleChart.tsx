/**
 * 실시간 캔들차트 컴포넌트 (lightweight-charts v5)
 *
 * 패널 구성 (고정 크기):
 *   Pane 0 (400px) - 캔들스틱
 *   Pane 1 (100px) - 거래량 (Volume)
 *   Pane 2 (120px) - RSI (14)
 */

import { useEffect, useRef, useCallback, useState } from "react";
import {
  createChart,
  CandlestickSeries,
  HistogramSeries,
  LineSeries,
  LineStyle,
} from "lightweight-charts";
import type {
  IChartApi,
  ISeriesApi,
  CandlestickData,
  HistogramData,
  SingleValueData,
  Time,
} from "lightweight-charts";
import { useWebSocket } from "../hooks/useWebSocket";
import type { WsUpdate } from "../hooks/useWebSocket";

const API_BASE = "http://localhost:8000";

const PANE_HEIGHTS = { candle: 400, volume: 100, rsi: 120 };
const TOTAL_HEIGHT = PANE_HEIGHTS.candle + PANE_HEIGHTS.volume + PANE_HEIGHTS.rsi;

// 심볼/인터벌 전환 시에도 사용자가 조절한 패널 높이 유지
const savedHeights = { candle: PANE_HEIGHTS.candle, volume: PANE_HEIGHTS.volume, rsi: PANE_HEIGHTS.rsi };

interface KlineRow {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  rsi: number | null;
}

interface Props {
  symbol: string;
  interval: string;
}

export default function CandleChart({ symbol, interval }: Props) {
  const chartDivRef     = useRef<HTMLDivElement>(null);
  const chartRef        = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<"Histogram"> | null>(null);
  const rsiSeriesRef    = useRef<ISeriesApi<"Line"> | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!chartDivRef.current) return;

    if (chartRef.current) {
      // 재초기화 전 현재 패널 높이 저장
      const panes = chartRef.current.panes();
      if (panes[0]) savedHeights.candle = panes[0].getHeight();
      if (panes[1]) savedHeights.volume = panes[1].getHeight();
      if (panes[2]) savedHeights.rsi    = panes[2].getHeight();
      chartRef.current.remove();
      chartRef.current = null;
    }

    const chart = createChart(chartDivRef.current, {
      width:  chartDivRef.current.clientWidth,
      height: TOTAL_HEIGHT,
      layout: {
        background: { color: "#131722" },
        textColor: "#d1d4dc",
      },
      grid: {
        vertLines: { color: "#1e2330" },
        horzLines: { color: "#1e2330" },
      },
      rightPriceScale: { borderColor: "#2a2e39" },
      timeScale: {
        borderColor: "#2a2e39",
        timeVisible: true,
        secondsVisible: false,
      },
    });

    // Pane 0: 캔들스틱
    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: "#26a69a", downColor: "#ef5350",
      borderUpColor: "#26a69a", borderDownColor: "#ef5350",
      wickUpColor: "#26a69a", wickDownColor: "#ef5350",
    }, 0);

    // Pane 1: 거래량
    const volumeSeries = chart.addSeries(HistogramSeries, {
      priceFormat: { type: "volume" },
      priceScaleId: "volume",
    }, 1);
    volumeSeries.priceScale().applyOptions({ scaleMargins: { top: 0.1, bottom: 0 } });

    // Pane 2: RSI
    const rsiSeries = chart.addSeries(LineSeries, {
      color: "#7b61ff",
      lineWidth: 1,
      priceScaleId: "rsi",
    }, 2);
    rsiSeries.priceScale().applyOptions({ scaleMargins: { top: 0.1, bottom: 0.1 } });
    rsiSeries.createPriceLine({ price: 70, color: "#ef5350", lineWidth: 1, lineStyle: LineStyle.Dashed, axisLabelVisible: true,  title: "" });
    rsiSeries.createPriceLine({ price: 30, color: "#26a69a", lineWidth: 1, lineStyle: LineStyle.Dashed, axisLabelVisible: true,  title: "" });
    rsiSeries.createPriceLine({ price: 50, color: "#555",    lineWidth: 1, lineStyle: LineStyle.Dotted,  axisLabelVisible: false, title: "" });

    // 차트 렌더링 완료 후 저장된 패널 높이 복원
    setTimeout(() => {
      const panes = chart.panes();
      panes[0]?.setHeight(savedHeights.candle);
      panes[1]?.setHeight(savedHeights.volume);
      panes[2]?.setHeight(savedHeights.rsi);
    }, 0);

    chartRef.current        = chart;
    candleSeriesRef.current = candleSeries;
    volumeSeriesRef.current = volumeSeries;
    rsiSeriesRef.current    = rsiSeries;

    const handleResize = () => {
      if (chartDivRef.current) {
        chart.applyOptions({ width: chartDivRef.current.clientWidth });
      }
    };
    window.addEventListener("resize", handleResize);

    // 과거 데이터 로드
    let cancelled = false;
    setLoading(true);

    fetch(`${API_BASE}/klines/${symbol}?interval=${interval}&limit=500`)
      .then((r) => r.json())
      .then((data: KlineRow[]) => {
        if (cancelled || !candleSeriesRef.current) return;

        const candles: CandlestickData<Time>[] = [];
        const volumes: HistogramData<Time>[]   = [];
        const rsiPts:  SingleValueData<Time>[] = [];

        data.forEach((c) => {
          candles.push({ time: c.time as Time, open: c.open, high: c.high, low: c.low, close: c.close });
          volumes.push({ time: c.time as Time, value: c.volume, color: c.close >= c.open ? "#26a69a60" : "#ef535060" });
          if (c.rsi !== null) rsiPts.push({ time: c.time as Time, value: c.rsi });
        });

        candleSeriesRef.current!.setData(candles);
        volumeSeriesRef.current!.setData(volumes);
        rsiSeriesRef.current!.setData(rsiPts);
        chart.timeScale().scrollToRealTime();
        setLoading(false);
      })
      .catch((e) => {
        console.error("[과거 데이터 로드 실패]", e);
        setLoading(false);
      });

    return () => {
      cancelled = true;
      window.removeEventListener("resize", handleResize);
      chart.remove();
      chartRef.current = null;
    };
  }, [symbol, interval]);

  const handleUpdate = useCallback(({ candle, rsi }: WsUpdate) => {
    if (!candleSeriesRef.current) return;
    candleSeriesRef.current.update({ time: candle.time as Time, open: candle.open, high: candle.high, low: candle.low, close: candle.close });
    volumeSeriesRef.current?.update({ time: candle.time as Time, value: candle.volume, color: candle.close >= candle.open ? "#26a69a60" : "#ef535060" });
    if (rsi !== null) rsiSeriesRef.current?.update({ time: candle.time as Time, value: rsi });
  }, []);

  useWebSocket(symbol, interval, handleUpdate);

  return (
    <div style={{ position: "relative", width: "100%" }}>
      {loading && (
        <div style={{
          position: "absolute", inset: 0, zIndex: 10,
          display: "flex", alignItems: "center", justifyContent: "center",
          background: "#131722", color: "#666", fontSize: "14px", borderRadius: "8px",
          height: TOTAL_HEIGHT,
        }}>
          데이터 로딩 중...
        </div>
      )}
      <div ref={chartDivRef} style={{ width: "100%", borderRadius: "8px", overflow: "hidden" }} />
    </div>
  );
}
