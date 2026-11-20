import React, { useEffect, useRef, useState } from 'react';
import { createChart, ColorType } from 'lightweight-charts';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  TrendingUp, 
  RefreshCw, 
  Shield, 
  Target, 
  Eye, 
  EyeOff, 
  Compass,
  ArrowUpRight,
  ArrowDownRight,
  Crosshair
} from 'lucide-react';
import { sound } from '../utils/audio';

export default function ChartViewport({ matrix }) {
  const chartContainerRef = useRef(null);
  const chartRef = useRef(null);
  const seriesRef = useRef(null);
  const priceLinesRef = useRef([]);

  const [activeAsset, setActiveAsset] = useState('gold');
  const [activeInterval, setActiveInterval] = useState('15m');
  const [currentPrice, setCurrentPrice] = useState(2748.50);
  const [priceChange, setPriceChange] = useState({ diff: 0, pct: 0 });
  const [setupPlan, setSetupPlan] = useState(null);
  const [showSetupHud, setShowSetupHud] = useState(true);
  const [isLoading, setIsLoading] = useState(false);

  // Fetch chart candle data (up to 350 historical candles for deep scroll)
  const fetchCandles = async () => {
    try {
      setIsLoading(true);
      const endpoint = activeAsset === 'gold' 
        ? `/api/gold/chart?interval=${activeInterval}&limit=350`
        : `/api/dxy/chart?interval=${activeInterval}&limit=350`;
      
      const res = await fetch(endpoint);
      if (!res.ok) return;
      const data = await res.json();
      
      const candles = data.candles || [];
      if (candles.length > 0 && seriesRef.current) {
        // Format for lightweight-charts
        const formatted = candles.map(c => ({
          time: Number(c.time),
          open: Number(c.open),
          high: Number(c.high),
          low: Number(c.low),
          close: Number(c.close)
        })).sort((a, b) => a.time - b.time);

        // Remove duplicate timestamps if any
        const unique = [];
        const seen = new Set();
        for (const item of formatted) {
          if (!seen.has(item.time)) {
            seen.add(item.time);
            unique.push(item);
          }
        }

        seriesRef.current.setData(unique);
        const last = unique[unique.length - 1];
        if (last) {
          setCurrentPrice(last.close);
          const first = unique[0];
          const diff = last.close - first.open;
          const pct = first.open ? (diff / first.open) * 100 : 0;
          setPriceChange({ diff, pct });
        }
      }

      // Update institutional setup plan & draw levels on chart
      if (activeAsset === 'gold' && data.setup_plan && seriesRef.current) {
        const plan = data.setup_plan;
        setSetupPlan(plan);

        // Clear existing price lines
        priceLinesRef.current.forEach(line => {
          try {
            seriesRef.current.removePriceLine(line);
          } catch (e) {}
        });
        priceLinesRef.current = [];

        const newLines = [];

        // 1. Draw Planned Entry Line (Blue Solid)
        if (plan.planned_entry) {
          try {
            const entryLine = seriesRef.current.createPriceLine({
              price: Number(plan.planned_entry),
              color: '#3b82f6',
              lineWidth: 2,
              lineStyle: 0, // Solid
              axisLabelVisible: true,
              title: `🎯 ENTRY [${plan.side || 'BUY'}]: $${plan.planned_entry.toFixed(2)}`,
            });
            newLines.push(entryLine);
          } catch (e) {}
        }

        // 2. Draw Planned Stop Loss Line (Red Dashed)
        if (plan.planned_sl) {
          try {
            const slLine = seriesRef.current.createPriceLine({
              price: Number(plan.planned_sl),
              color: '#f43f5e',
              lineWidth: 2,
              lineStyle: 2, // Dashed
              axisLabelVisible: true,
              title: `🛡️ STOP LOSS (SL): $${plan.planned_sl.toFixed(2)}`,
            });
            newLines.push(slLine);
          } catch (e) {}
        }

        // 3. Draw Planned Take Profit Line (Green Dashed)
        if (plan.planned_tp) {
          try {
            const tpLine = seriesRef.current.createPriceLine({
              price: Number(plan.planned_tp),
              color: '#10b981',
              lineWidth: 2,
              lineStyle: 2, // Dashed
              axisLabelVisible: true,
              title: `🏆 TAKE PROFIT (TP): $${plan.planned_tp.toFixed(2)}`,
            });
            newLines.push(tpLine);
          } catch (e) {}
        }

        // 4. Draw Asian Range High (BSL / Orange Dotted)
        if (plan.asian_range && plan.asian_range.high > 0) {
          try {
            const aHighLine = seriesRef.current.createPriceLine({
              price: Number(plan.asian_range.high),
              color: '#f59e0b',
              lineWidth: 1,
              lineStyle: 3, // Dotted
              axisLabelVisible: true,
              title: `ASIAN HIGH (BSL): $${plan.asian_range.high.toFixed(2)}`,
            });
            newLines.push(aHighLine);
          } catch (e) {}
        }

        // 5. Draw Asian Range Low (SSL / Orange Dotted)
        if (plan.asian_range && plan.asian_range.low > 0) {
          try {
            const aLowLine = seriesRef.current.createPriceLine({
              price: Number(plan.asian_range.low),
              color: '#f59e0b',
              lineWidth: 1,
              lineStyle: 3, // Dotted
              axisLabelVisible: true,
              title: `ASIAN LOW (SSL): $${plan.asian_range.low.toFixed(2)}`,
            });
            newLines.push(aLowLine);
          } catch (e) {}
        }

        priceLinesRef.current = newLines;
      }
    } catch (err) {
      console.error("Failed to fetch candles:", err);
    } finally {
      setIsLoading(false);
    }
  };

  // Initialize TradingView Lightweight Chart
  useEffect(() => {
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: '#090a0f' },
        textColor: '#64748b',
        fontFamily: "'JetBrains Mono', monospace",
        fontSize: 11,
      },
      grid: {
        vertLines: { color: 'rgba(255, 255, 255, 0.03)' },
        horzLines: { color: 'rgba(255, 255, 255, 0.03)' },
      },
      crosshair: {
        vertLine: {
          color: 'rgba(59, 130, 246, 0.5)',
          width: 1,
          style: 3,
        },
        horzLine: {
          color: 'rgba(59, 130, 246, 0.5)',
          width: 1,
          style: 3,
        },
      },
      rightPriceScale: {
        borderColor: 'rgba(255, 255, 255, 0.08)',
        scaleMargins: { top: 0.18, bottom: 0.18 },
      },
      timeScale: {
        borderColor: 'rgba(255, 255, 255, 0.08)',
        timeVisible: true,
        secondsVisible: false,
        shiftVisibleRangeOnNewBar: true,
      },
      handleScroll: true,
      handleScale: true,
    });

    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#10b981',
      downColor: '#f43f5e',
      borderUpColor: '#10b981',
      borderDownColor: '#f43f5e',
      wickUpColor: '#10b981',
      wickDownColor: '#f43f5e',
    });

    chartRef.current = chart;
    seriesRef.current = candlestickSeries;

    // Resize observer
    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({
          width: chartContainerRef.current.clientWidth,
          height: chartContainerRef.current.clientHeight,
        });
      }
    };

    window.addEventListener('resize', handleResize);
    handleResize();

    fetchCandles();

    const intervalId = setInterval(fetchCandles, 4000);

    return () => {
      window.removeEventListener('resize', handleResize);
      clearInterval(intervalId);
      chart.remove();
    };
  }, [activeAsset, activeInterval]);

  return (
    <div className="relative flex-1 flex flex-col h-full bg-[#08090d] select-none overflow-hidden">
      {/* Top Chart Toolbar */}
      <div className="h-11 border-b border-white/[0.06] bg-[#0c0e14]/50 backdrop-blur-md px-4 flex items-center justify-between z-10">
        {/* Symbol & Timeframes */}
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-1.5">
            <button
              onClick={() => {
                sound.playTick();
                setActiveAsset('gold');
              }}
              className={`px-2.5 py-1 rounded text-xs font-semibold tracking-wide transition-all ${
                activeAsset === 'gold'
                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              XAUUSD (Gold)
            </button>
            <button
              onClick={() => {
                sound.playTick();
                setActiveAsset('dxy');
              }}
              className={`px-2.5 py-1 rounded text-xs font-semibold tracking-wide transition-all ${
                activeAsset === 'dxy'
                  ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              DXY (US Dollar)
            </button>
          </div>

          <div className="h-4 w-[1px] bg-white/10" />

          {/* Timeframe Buttons */}
          <div className="flex items-center space-x-1 bg-white/[0.03] p-0.5 rounded border border-white/[0.06]">
            {['1m', '5m', '15m', '1h'].map(tf => (
              <button
                key={tf}
                onClick={() => {
                  sound.playTick();
                  setActiveInterval(tf);
                }}
                className={`px-2 py-0.5 rounded text-[11px] font-mono transition-all ${
                  activeInterval === tf
                    ? 'bg-white/10 text-white font-medium shadow-sm'
                    : 'text-slate-500 hover:text-slate-300'
                }`}
              >
                {tf}
              </button>
            ))}
          </div>

          {/* Toggle Setup HUD visibility */}
          {activeAsset === 'gold' && setupPlan && (
            <button
              onClick={() => {
                sound.playTick();
                setShowSetupHud(!showSetupHud);
              }}
              className="flex items-center space-x-1 text-xs text-slate-400 hover:text-slate-200 px-2 py-1 rounded bg-white/[0.02] border border-white/[0.05]"
              title={showSetupHud ? "Hide Setup HUD" : "Show Setup HUD"}
            >
              {showSetupHud ? <Eye className="w-3.5 h-3.5 text-blue-400" /> : <EyeOff className="w-3.5 h-3.5" />}
              <span className="hidden md:inline text-[11px]">Setup HUD</span>
            </button>
          )}
        </div>

        {/* Live HUD Price & Metrics */}
        <div className="flex items-center space-x-4">
          <div className="flex items-baseline space-x-2">
            <span className="text-base font-bold font-mono text-white tracking-tight">
              ${currentPrice.toFixed(2)}
            </span>
            <span className={`text-xs font-mono font-medium ${priceChange.diff >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
              {priceChange.diff >= 0 ? '+' : ''}{priceChange.diff.toFixed(2)} ({priceChange.pct >= 0 ? '+' : ''}{priceChange.pct.toFixed(2)}%)
            </span>
          </div>

          <button
            onClick={() => {
              sound.playTick();
              fetchCandles();
            }}
            disabled={isLoading}
            className="p-1 rounded text-slate-400 hover:text-slate-200 hover:bg-white/[0.05] transition-colors"
            title="Refresh candles (350 bars)"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin text-blue-400' : ''}`} />
          </button>
        </div>
      </div>

      {/* Floating Planned Setup Card Overlay (Top-Right of Chart) */}
      <AnimatePresence>
        {activeAsset === 'gold' && setupPlan && showSetupHud && (
          <motion.div
            initial={{ opacity: 0, y: -10, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.98 }}
            transition={{ duration: 0.2 }}
            className="absolute top-14 right-4 z-20 max-w-sm w-full p-3.5 rounded-xl bg-[#0e111a]/90 backdrop-blur-xl border border-white/[0.1] shadow-2xl space-y-2.5 font-sans"
          >
            {/* Header: Title & Status */}
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-1.5">
                <Compass className="w-3.5 h-3.5 text-blue-400" />
                <span className="text-xs font-bold text-slate-200 tracking-wide">
                  Active Institutional Setup
                </span>
              </div>
              <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold flex items-center space-x-1 ${
                setupPlan.status === 'TRIGGERED'
                  ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                  : 'bg-amber-500/15 text-amber-400 border border-amber-500/30'
              }`}>
                <span className="w-1.5 h-1.5 rounded-full bg-current animate-pulse" />
                <span>{setupPlan.status.replace(/_/g, ' ')}</span>
              </span>
            </div>

            {/* Setup Name & Side */}
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="text-slate-400 font-medium truncate mr-2">
                {setupPlan.display_title || setupPlan.setup_name}
              </span>
              <span className={`font-bold px-1.5 py-0.5 rounded text-[10px] ${
                setupPlan.side === 'BUY'
                  ? 'bg-emerald-500/20 text-emerald-400'
                  : 'bg-rose-500/20 text-rose-400'
              }`}>
                {setupPlan.side === 'BUY' ? 'BUY (LONG)' : 'SELL (SHORT)'}
              </span>
            </div>

            {/* Exact Drawn Setup Levels */}
            <div className="grid grid-cols-3 gap-1.5 text-xs font-mono pt-1">
              {/* Entry */}
              <div className="p-1.5 rounded bg-blue-500/10 border border-blue-500/20">
                <span className="text-[10px] text-blue-300 block">🎯 Target Entry</span>
                <span className="font-bold text-blue-400">
                  ${setupPlan.planned_entry?.toFixed(2)}
                </span>
              </div>

              {/* SL */}
              <div className="p-1.5 rounded bg-rose-500/10 border border-rose-500/20">
                <span className="text-[10px] text-rose-300 block">🛡️ Stop Loss</span>
                <span className="font-bold text-rose-400">
                  ${setupPlan.planned_sl?.toFixed(2)}
                </span>
              </div>

              {/* TP */}
              <div className="p-1.5 rounded bg-emerald-500/10 border border-emerald-500/20">
                <span className="text-[10px] text-emerald-300 block">🏆 Take Profit</span>
                <span className="font-bold text-emerald-400">
                  ${setupPlan.planned_tp?.toFixed(2)}
                </span>
              </div>
            </div>

            {/* RRR & Asian Range Bounds */}
            <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 pt-0.5 border-t border-white/[0.04]">
              <div>Risk:Reward: <span className="font-bold text-slate-200">1:{setupPlan.rrr || 2.4}</span></div>
              {setupPlan.asian_range && (
                <div className="text-[10px]">
                  Asian: <span className="text-amber-400">${setupPlan.asian_range.low} - ${setupPlan.asian_range.high}</span>
                </div>
              )}
            </div>

            {/* Strategic Instruction / Narrative */}
            {setupPlan.instruction && (
              <p className="text-[11px] text-slate-400 leading-relaxed font-sans bg-white/[0.02] p-2 rounded border border-white/[0.03]">
                💡 <span className="italic">{setupPlan.instruction}</span>
              </p>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Candlestick Chart Canvas */}
      <div ref={chartContainerRef} className="w-full flex-1 relative" />

      {/* Watermark Branding */}
      <div className="absolute bottom-4 left-4 pointer-events-none text-[10px] font-mono text-white/[0.06] uppercase tracking-widest font-bold">
        INSTITUTIONAL LIQUIDITY ENGINE · SMART MONEY CONCEPTS · 350 BARS HISTORICAL DEPTH
      </div>
    </div>
  );
}
