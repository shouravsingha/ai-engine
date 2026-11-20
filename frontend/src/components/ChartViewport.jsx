import React, { useEffect, useRef, useState } from 'react';
import { createChart, ColorType } from 'lightweight-charts';
import { motion } from 'framer-motion';
import { TrendingUp, RefreshCw, BarChart2, Shield } from 'lucide-react';
import { sound } from '../utils/audio';

export default function ChartViewport({ matrix }) {
  const chartContainerRef = useRef(null);
  const chartRef = useRef(null);
  const seriesRef = useRef(null);
  const [activeAsset, setActiveAsset] = useState('gold');
  const [activeInterval, setActiveInterval] = useState('15m');
  const [currentPrice, setCurrentPrice] = useState(2748.50);
  const [priceChange, setPriceChange] = useState({ diff: 0, pct: 0 });
  const [asianRange, setAsianRange] = useState({ high: 0, low: 0 });
  const [isLoading, setIsLoading] = useState(false);

  // Fetch chart candle data
  const fetchCandles = async () => {
    try {
      setIsLoading(true);
      const endpoint = activeAsset === 'gold' 
        ? `/api/gold/chart?interval=${activeInterval}&limit=90`
        : `/api/dxy/chart?interval=${activeInterval}&limit=90`;
      
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

      if (data.setup_plan && data.setup_plan.asian_range) {
        setAsianRange(data.setup_plan.asian_range);
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
        scaleMargins: { top: 0.15, bottom: 0.15 },
      },
      timeScale: {
        borderColor: 'rgba(255, 255, 255, 0.08)',
        timeVisible: true,
        secondsVisible: false,
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

    const intervalId = setInterval(fetchCandles, 5000);

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
        </div>

        {/* Live HUD Price & Metrics */}
        <div className="flex items-center space-x-4">
          {asianRange.high > 0 && (
            <div className="hidden lg:flex items-center space-x-1.5 text-[11px] font-mono text-slate-400">
              <Shield className="w-3 h-3 text-amber-400" />
              <span>Asian Range:</span>
              <span className="text-slate-200">${asianRange.low.toFixed(1)} - ${asianRange.high.toFixed(1)}</span>
            </div>
          )}

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
            title="Refresh candles"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin text-blue-400' : ''}`} />
          </button>
        </div>
      </div>

      {/* Candlestick Chart Canvas */}
      <div ref={chartContainerRef} className="w-full flex-1 relative" />

      {/* Watermark Branding */}
      <div className="absolute bottom-4 left-4 pointer-events-none text-[10px] font-mono text-white/[0.06] uppercase tracking-widest font-bold">
        INSTITUTIONAL LIQUIDITY ENGINE · SMART MONEY CONCEPTS · ZERO NOISE
      </div>
    </div>
  );
}
