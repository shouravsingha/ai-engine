import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Activity, ShieldCheck, Terminal, RotateCcw } from 'lucide-react';
import { sound } from '../utils/audio';

export default function TelemetryDrawer({ isOpen, onClose, telemetry, onResetCircuitBreaker }) {
  const gen3 = telemetry?.gen3 || {};
  const cb = gen3?.circuit_breaker || {};
  const logs = telemetry?.logs || [];

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => {
              sound.playTick();
              onClose();
            }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40"
          />

          <motion.aside
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 26, stiffness: 260 }}
            className="fixed top-0 right-0 w-full max-w-md h-full bg-[#0d0f17]/95 border-l border-white/[0.08] backdrop-blur-2xl shadow-2xl z-50 flex flex-col select-none"
          >
            {/* Header */}
            <div className="h-14 border-b border-white/[0.07] px-5 flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Activity className="w-4 h-4 text-emerald-400" />
                <span className="font-semibold text-sm tracking-wide text-white">
                  Telemetry & System Logs
                </span>
              </div>
              <button
                onClick={() => {
                  sound.playTick();
                  onClose();
                }}
                className="p-1 rounded text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {/* Circuit Breaker Status Card */}
              <div className="p-3.5 rounded-xl bg-white/[0.02] border border-white/[0.08] space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center space-x-1.5">
                    <ShieldCheck className="w-4 h-4 text-emerald-400" />
                    <span>Circuit Breaker</span>
                  </span>
                  <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded border ${
                    cb?.kill_switch_active
                      ? 'bg-rose-500/15 text-rose-400 border-rose-500/30'
                      : (cb?.is_cooling_down ? 'bg-amber-500/15 text-amber-400 border-amber-500/30' : 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30')
                  }`}>
                    {cb?.kill_switch_active ? 'HALTED' : (cb?.is_cooling_down ? 'COOLDOWN' : 'ARMED (NORMAL)')}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                  <div className="bg-white/[0.02] p-2 rounded border border-white/[0.04]">
                    <span className="text-slate-500 block text-[10px]">Consecutive Losses</span>
                    <span className="text-slate-200 font-bold">{cb?.consecutive_losses || 0} / 3</span>
                  </div>
                  <div className="bg-white/[0.02] p-2 rounded border border-white/[0.04]">
                    <span className="text-slate-500 block text-[10px]">Cycles Executed</span>
                    <span className="text-slate-200 font-bold">{gen3?.cycle_count || 0}</span>
                  </div>
                </div>

                {cb?.kill_switch_active && (
                  <button
                    onClick={() => {
                      sound.playSuccess();
                      onResetCircuitBreaker();
                    }}
                    className="w-full py-1.5 rounded-lg text-xs font-mono font-bold bg-amber-500/15 text-amber-400 border border-amber-500/30 hover:bg-amber-500/25 transition-all flex items-center justify-center space-x-1.5"
                  >
                    <RotateCcw className="w-3.5 h-3.5" />
                    <span>Reset Circuit Breaker</span>
                  </button>
                )}
              </div>

              {/* Raw System Logs */}
              <div className="space-y-2">
                <span className="text-xs font-semibold text-slate-400 tracking-wider uppercase flex items-center space-x-1.5">
                  <Terminal className="w-3.5 h-3.5" />
                  <span>Real-Time Engine Stream</span>
                </span>
                <div className="p-3 rounded-xl bg-black/50 border border-white/[0.06] font-mono text-[11px] space-y-1.5 max-h-80 overflow-y-auto">
                  {logs && logs.map((log, idx) => (
                    <div key={idx} className="text-slate-400 leading-relaxed border-b border-white/[0.02] pb-1">
                      {log}
                    </div>
                  ))}
                  {(!logs || logs.length === 0) && (
                    <div className="text-slate-600 italic">No logs recorded yet.</div>
                  )}
                </div>
              </div>
            </div>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  );
}
