import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Cpu, Shield, TrendingUp, Radio, Activity, CheckCircle, MessageSquare } from 'lucide-react';
import { sound } from '../utils/audio';

const AGENT_CONFIGS = [
  { name: 'Alex', role: 'Chief Quant (PA_01)', icon: TrendingUp, color: 'text-blue-400', border: 'border-blue-500/20', bg: 'bg-blue-500/10' },
  { name: 'Marcus', role: 'Risk Guardian (PA_02)', icon: Shield, color: 'text-emerald-400', border: 'border-emerald-500/20', bg: 'bg-emerald-500/10' },
  { name: 'David', role: 'Macro Strategist (PA_03)', icon: Activity, color: 'text-amber-400', border: 'border-amber-500/20', bg: 'bg-amber-500/10' },
  { name: 'Sophia', role: 'Brand Director (Conta_1612)', icon: Radio, color: 'text-purple-400', border: 'border-purple-500/20', bg: 'bg-purple-500/10' },
  { name: 'Leo', role: 'Execution Trader (PA_14)', icon: CheckCircle, color: 'text-cyan-400', border: 'border-cyan-500/20', bg: 'bg-cyan-500/10' },
  { name: 'Mia', role: 'Copywriter (PA_07)', icon: MessageSquare, color: 'text-pink-400', border: 'border-pink-500/20', bg: 'bg-pink-500/10' },
  { name: 'AI Brain', role: 'Neural Central Overseer', icon: Cpu, color: 'text-indigo-400', border: 'border-indigo-500/20', bg: 'bg-indigo-500/10' },
];

export default function AgentDrawer({ isOpen, onClose, telemetry }) {
  const agents = telemetry?.agents || [];
  const agentMessages = telemetry?.agent_messages || [];
  const brain = telemetry?.ai_brain || {};

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
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

          {/* Slide-over Panel */}
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
                <Cpu className="w-4 h-4 text-blue-400" />
                <span className="font-semibold text-sm tracking-wide text-white">
                  AI Autonomous Workforce
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-blue-500/15 text-blue-300 font-bold">
                  7 Active
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

            {/* Content Body */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {/* Central Brain Telemetry Card */}
              <div className="p-3.5 rounded-xl bg-gradient-to-br from-indigo-500/10 via-purple-500/5 to-transparent border border-indigo-500/20">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                    <span className="text-xs font-bold text-indigo-300 uppercase tracking-wider">
                      Neural Brain Status
                    </span>
                  </div>
                  <span className="text-xs font-mono font-bold text-indigo-200">
                    IQ {brain?.metrics?.system_iq || 185}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                  <div className="bg-white/[0.02] p-2 rounded border border-white/[0.04]">
                    <span className="text-slate-500 block text-[10px]">Audited Decisions</span>
                    <span className="text-slate-200 font-semibold">{brain?.metrics?.decisions_audited || 128}</span>
                  </div>
                  <div className="bg-white/[0.02] p-2 rounded border border-white/[0.04]">
                    <span className="text-slate-500 block text-[10px]">Mistakes Prevented</span>
                    <span className="text-emerald-400 font-semibold">{brain?.metrics?.mistakes_prevented || 34}</span>
                  </div>
                </div>
              </div>

              {/* 7 AI Agents Bento Cards */}
              <div className="space-y-2.5">
                <span className="text-xs font-semibold text-slate-400 tracking-wider uppercase">
                  Stationed Robots
                </span>
                <div className="grid grid-cols-1 gap-2">
                  {AGENT_CONFIGS.map((cfg) => {
                    const Icon = cfg.icon;
                    return (
                      <motion.div
                        key={cfg.name}
                        whileHover={{ scale: 1.01 }}
                        className={`p-3 rounded-xl bg-white/[0.02] border ${cfg.border} hover:bg-white/[0.04] transition-all flex items-center justify-between`}
                      >
                        <div className="flex items-center space-x-3">
                          <div className={`p-2 rounded-lg ${cfg.bg}`}>
                            <Icon className={`w-4 h-4 ${cfg.color}`} />
                          </div>
                          <div>
                            <div className="flex items-center space-x-1.5">
                              <span className="text-sm font-semibold text-slate-200">{cfg.name}</span>
                              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.8)]" />
                            </div>
                            <span className="text-[11px] text-slate-500">{cfg.role}</span>
                          </div>
                        </div>

                        <span className="text-[10px] font-mono font-medium text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                          ONLINE
                        </span>
                      </motion.div>
                    );
                  })}
                </div>
              </div>

              {/* Live Agent Debate Transcript */}
              <div className="space-y-2 pt-2">
                <span className="text-xs font-semibold text-slate-400 tracking-wider uppercase">
                  Live Debate & Thought Stream
                </span>
                <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                  {agentMessages && agentMessages.slice(0, 15).map((msg, idx) => (
                    <div key={idx} className="p-2.5 rounded-lg bg-white/[0.02] border border-white/[0.05] text-xs">
                      <div className="flex items-center justify-between mb-1 text-[10px] font-mono text-slate-500">
                        <span className="text-blue-400 font-semibold">{msg.agent}</span>
                        <span>{msg.time}</span>
                      </div>
                      <p className="text-slate-300 leading-relaxed font-sans">{msg.text}</p>
                    </div>
                  ))}
                  {(!agentMessages || agentMessages.length === 0) && (
                    <div className="text-xs text-slate-500 italic p-2">
                      Standing by for multi-agent market debate...
                    </div>
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
