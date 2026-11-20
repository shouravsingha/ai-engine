import React from 'react';
import { motion } from 'framer-motion';
import { 
  Users, 
  Layers, 
  Activity, 
  Volume2, 
  VolumeX, 
  AlertTriangle, 
  Play, 
  Pause,
  ShieldCheck,
  Cpu
} from 'lucide-react';
import OdometerNumber from './OdometerNumber';
import { sound } from '../utils/audio';

export default function HeaderNav({
  telemetry,
  onOpenAgents,
  onOpenDesk,
  onOpenTelemetry,
  onToggleSupervisor,
  onPanicFlat,
  muted,
  onToggleAudio
}) {
  const ex = telemetry?.exness || {};
  const gen3 = telemetry?.gen3 || {};
  const cb = gen3?.circuit_breaker || {};
  const isRunning = gen3?.is_running && !gen3?.is_paused;
  const isKilled = cb?.kill_switch_active;

  return (
    <header className="h-14 border-b border-white/[0.07] bg-[#0c0e14]/80 backdrop-blur-xl px-4 flex items-center justify-between select-none z-30 relative">
      {/* Brand & Connection Status */}
      <div className="flex items-center space-x-3">
        <div className="flex items-center space-x-2">
          <div className="w-2.5 h-2.5 rounded-full bg-blue-500 animate-pulse shadow-[0_0_10px_rgba(59,130,246,0.6)]" />
          <span className="font-bold text-sm tracking-wide bg-gradient-to-r from-slate-100 to-slate-400 bg-clip-text text-transparent">
            TRADING<span className="text-blue-400">AI</span>
          </span>
          <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20 font-semibold">
            PRO
          </span>
        </div>

        <div className="h-4 w-[1px] bg-white/10 mx-1" />

        {/* Exness MT5 Status */}
        <div className="hidden sm:flex items-center space-x-1.5 text-xs text-slate-400 font-mono">
          <span className={`w-1.5 h-1.5 rounded-full ${ex?.connected ? 'bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.6)]' : 'bg-amber-400'}`} />
          <span className="text-slate-300 font-medium">Exness MT5</span>
          <span className="text-slate-500">#{ex?.account_id || '434353249'}</span>
        </div>
      </div>

      {/* Center: Live Equity & Balance Metrics */}
      <div className="flex items-center space-x-6">
        <div className="flex items-center space-x-2">
          <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">Equity</span>
          <OdometerNumber
            value={ex?.equity || 205.47}
            prefix="$"
            decimals={2}
            className="text-sm font-semibold text-emerald-400"
          />
        </div>

        <div className="hidden md:flex items-center space-x-2">
          <span className="text-[11px] font-medium text-slate-500 uppercase tracking-wider">Balance</span>
          <OdometerNumber
            value={ex?.balance || 205.47}
            prefix="$"
            decimals={2}
            className="text-sm font-medium text-slate-300"
          />
        </div>

        <div className="hidden lg:flex items-center space-x-2">
          <span className="text-[11px] font-medium text-slate-500 uppercase tracking-wider">Shield</span>
          <span className="inline-flex items-center space-x-1 text-xs text-emerald-400/90 font-mono">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>0.01 lot</span>
          </span>
        </div>
      </div>

      {/* Right: Actions, Drawers, Controls */}
      <div className="flex items-center space-x-2">
        {/* Supervisor Pause/Resume */}
        <motion.button
          whileTap={{ scale: 0.95 }}
          onClick={() => {
            sound.playTick();
            onToggleSupervisor();
          }}
          className={`px-2.5 py-1 rounded-md text-xs font-mono font-medium flex items-center space-x-1.5 border transition-all ${
            isRunning
              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30 hover:bg-emerald-500/20'
              : 'bg-amber-500/10 text-amber-400 border-amber-500/30 hover:bg-amber-500/20'
          }`}
          title={isRunning ? "Click to Pause AI Trading" : "Click to Resume AI Trading"}
        >
          {isRunning ? <Pause className="w-3 h-3" /> : <Play className="w-3 h-3" />}
          <span>{isRunning ? 'ACTIVE' : 'PAUSED'}</span>
        </motion.button>

        {/* AI Agents Drawer Toggle */}
        <motion.button
          whileTap={{ scale: 0.95 }}
          onClick={() => {
            sound.playTick();
            onOpenAgents();
          }}
          className="px-2.5 py-1 rounded-md text-xs font-medium flex items-center space-x-1.5 bg-white/[0.04] text-slate-300 border border-white/[0.08] hover:bg-white/[0.08] hover:text-white transition-colors"
        >
          <Users className="w-3.5 h-3.5 text-blue-400" />
          <span className="hidden sm:inline">Agents</span>
          <span className="w-4 h-4 rounded-full bg-blue-500/20 text-blue-300 text-[10px] flex items-center justify-center font-mono">
            7
          </span>
        </motion.button>

        {/* Decision Desk Drawer Toggle */}
        <motion.button
          whileTap={{ scale: 0.95 }}
          onClick={() => {
            sound.playTick();
            onOpenDesk();
          }}
          className="px-2.5 py-1 rounded-md text-xs font-medium flex items-center space-x-1.5 bg-white/[0.04] text-slate-300 border border-white/[0.08] hover:bg-white/[0.08] hover:text-white transition-colors"
        >
          <Layers className="w-3.5 h-3.5 text-purple-400" />
          <span className="hidden sm:inline">Desk</span>
        </motion.button>

        {/* Telemetry Drawer Toggle */}
        <motion.button
          whileTap={{ scale: 0.95 }}
          onClick={() => {
            sound.playTick();
            onOpenTelemetry();
          }}
          className="p-1.5 rounded-md text-slate-400 hover:text-slate-200 hover:bg-white/[0.06] transition-colors"
          title="Telemetry & Logs"
        >
          <Activity className="w-4 h-4" />
        </motion.button>

        {/* Sound Toggle */}
        <button
          onClick={() => {
            onToggleAudio();
          }}
          className="p-1.5 rounded-md text-slate-400 hover:text-slate-200 hover:bg-white/[0.06] transition-colors"
          title={muted ? "Unmute Sound FX" : "Mute Sound FX"}
        >
          {muted ? <VolumeX className="w-4 h-4 text-slate-500" /> : <Volume2 className="w-4 h-4 text-blue-400" />}
        </button>

        {/* Emergency Panic Flat Kill-Switch */}
        <motion.button
          whileTap={{ scale: 0.92 }}
          onClick={() => {
            sound.playAlert();
            if (confirm("⚠️ EMERGENCY KILL-SWITCH: Close all open positions on Exness MT5 immediately?")) {
              onPanicFlat();
            }
          }}
          className="px-2.5 py-1 rounded-md text-xs font-semibold flex items-center space-x-1 bg-rose-500/15 text-rose-400 border border-rose-500/30 hover:bg-rose-500/25 transition-all"
          title="Emergency Panic Flat"
        >
          <AlertTriangle className="w-3.5 h-3.5" />
          <span className="hidden md:inline">FLATTEN</span>
        </motion.button>
      </div>
    </header>
  );
}
