import React, { useState, useEffect } from 'react';
import HeaderNav from './components/HeaderNav';
import ChartViewport from './components/ChartViewport';
import PositionsBar from './components/PositionsBar';
import AgentDrawer from './components/AgentDrawer';
import DecisionDeskDrawer from './components/DecisionDeskDrawer';
import TelemetryDrawer from './components/TelemetryDrawer';
import { sound } from './utils/audio';

export default function App() {
  const [telemetry, setTelemetry] = useState(null);
  const [isAgentsOpen, setIsAgentsOpen] = useState(false);
  const [isDeskOpen, setIsDeskOpen] = useState(false);
  const [isTelemetryOpen, setIsTelemetryOpen] = useState(false);
  const [muted, setMuted] = useState(false);

  // Poll live telemetry from FastAPI backend
  const fetchTelemetry = async () => {
    try {
      const res = await fetch('/api/telemetry');
      if (res.ok) {
        const data = await res.json();
        setTelemetry(data);
      }
    } catch (err) {
      console.error("Telemetry fetch error:", err);
    }
  };

  useEffect(() => {
    fetchTelemetry();
    const interval = setInterval(fetchTelemetry, 2500);
    return () => clearInterval(interval);
  }, []);

  const handleToggleSupervisor = async () => {
    const isRunning = telemetry?.gen3?.is_running && !telemetry?.gen3?.is_paused;
    const endpoint = isRunning ? '/api/gen3/supervisor/pause' : '/api/gen3/supervisor/resume';
    try {
      await fetch(endpoint, { method: 'POST' });
      fetchTelemetry();
    } catch (e) {
      console.error("Toggle supervisor error:", e);
    }
  };

  const handlePanicFlat = async () => {
    try {
      await fetch('/api/trade/panic_flat', { method: 'POST' });
      fetchTelemetry();
    } catch (e) {
      console.error("Panic flat error:", e);
    }
  };

  const handleClosePosition = async (ticket) => {
    try {
      await fetch(`/api/trade/close/${ticket}`, { method: 'POST' });
      fetchTelemetry();
    } catch (e) {
      console.error("Close position error:", e);
    }
  };

  const handleQuickExecute = async (side) => {
    try {
      await fetch('/api/trade/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbol: 'XAUUSDm', side: side, price: 2748.50 })
      });
      fetchTelemetry();
    } catch (e) {
      console.error("Quick execute error:", e);
    }
  };

  const handleResetCircuitBreaker = async () => {
    try {
      await fetch('/api/circuit_breaker/reset', { method: 'POST' });
      fetchTelemetry();
    } catch (e) {
      console.error("Reset circuit breaker error:", e);
    }
  };

  const handleToggleAudio = () => {
    const isMuted = sound.toggleMute();
    setMuted(isMuted);
    if (!isMuted) sound.playTick();
  };

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-[#08090d] text-slate-100 font-sans">
      {/* Frosted Glass Header */}
      <HeaderNav
        telemetry={telemetry}
        onOpenAgents={() => setIsAgentsOpen(true)}
        onOpenDesk={() => setIsDeskOpen(true)}
        onOpenTelemetry={() => setIsTelemetryOpen(true)}
        onToggleSupervisor={handleToggleSupervisor}
        onPanicFlat={handlePanicFlat}
        muted={muted}
        onToggleAudio={handleToggleAudio}
      />

      {/* Main Trading Viewport (Chart-First) */}
      <main className="flex-1 flex flex-col min-h-0 relative">
        <ChartViewport matrix={telemetry?.market_matrix} />
      </main>

      {/* Persistent Bottom Execution & Positions Bar */}
      <PositionsBar
        positions={telemetry?.exness?.open_positions || []}
        onClosePosition={handleClosePosition}
        onQuickExecute={handleQuickExecute}
      />

      {/* Slide-over Drawers */}
      <AgentDrawer
        isOpen={isAgentsOpen}
        onClose={() => setIsAgentsOpen(false)}
        telemetry={telemetry}
      />

      <DecisionDeskDrawer
        isOpen={isDeskOpen}
        onClose={() => setIsDeskOpen(false)}
        telemetry={telemetry}
      />

      <TelemetryDrawer
        isOpen={isTelemetryOpen}
        onClose={() => setIsTelemetryOpen(false)}
        telemetry={telemetry}
        onResetCircuitBreaker={handleResetCircuitBreaker}
      />
    </div>
  );
}
