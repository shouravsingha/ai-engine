import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Shield, X, ArrowUpRight, ArrowDownRight, Zap } from 'lucide-react';
import OdometerNumber from './OdometerNumber';
import { sound } from '../utils/audio';

export default function PositionsBar({ positions, onClosePosition, onQuickExecute }) {
  const openCount = positions?.length || 0;
  const totalPnL = positions?.reduce((acc, p) => acc + (Number(p.profit) || 0), 0) || 0;

  return (
    <footer className="h-16 border-t border-white/[0.07] bg-[#0b0d13]/90 backdrop-blur-xl px-4 flex items-center justify-between z-20 select-none">
      {/* Left: Open Positions Count & Summary */}
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Active Trades
          </span>
          <span className="px-1.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-white/10 text-white">
            {openCount}
          </span>
        </div>

        {openCount > 0 && (
          <div className="flex items-center space-x-2 font-mono text-xs">
            <span className="text-slate-500">Floating PnL:</span>
            <OdometerNumber
              value={totalPnL}
              prefix={totalPnL >= 0 ? '+$' : '-$'}
              decimals={2}
              className={`font-semibold ${totalPnL >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}
            />
          </div>
        )}
      </div>

      {/* Center: Scrollable Live Position Cards */}
      <div className="flex-1 max-w-2xl mx-4 overflow-x-auto flex items-center space-x-2 py-1 scrollbar-none">
        <AnimatePresence mode="popLayout">
          {positions && positions.map((pos) => {
            const isBuy = (pos.type === 0 || pos.side === 'BUY');
            const profit = Number(pos.profit) || 0;
            const isProfit = profit >= 0;

            return (
              <motion.div
                key={pos.ticket}
                initial={{ opacity: 0, scale: 0.95, y: 10 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.9, y: -10 }}
                transition={{ duration: 0.2 }}
                className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-white/[0.03] border border-white/[0.08] hover:border-white/20 transition-all font-mono text-xs shrink-0"
              >
                <div className={`flex items-center space-x-0.5 font-bold ${isBuy ? 'text-emerald-400' : 'text-rose-400'}`}>
                  {isBuy ? <ArrowUpRight className="w-3.5 h-3.5" /> : <ArrowDownRight className="w-3.5 h-3.5" />}
                  <span>{isBuy ? 'BUY' : 'SELL'}</span>
                </div>

                <span className="text-slate-300 font-medium">{pos.symbol || 'XAUUSDm'}</span>
                <span className="text-slate-500">{pos.volume || 0.01}</span>

                <div className={`font-semibold ${isProfit ? 'text-emerald-400' : 'text-rose-400'}`}>
                  {isProfit ? '+' : ''}${profit.toFixed(2)}
                </div>

                {pos.be_active && (
                  <span className="flex items-center text-[10px] text-emerald-400/80 bg-emerald-500/10 px-1 rounded" title="Break-Even Shield Locked">
                    <Shield className="w-2.5 h-2.5 mr-0.5" /> BE
                  </span>
                )}

                <button
                  onClick={() => {
                    sound.playTick();
                    onClosePosition(pos.ticket);
                  }}
                  className="p-1 rounded text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 transition-colors ml-1"
                  title="Close Position"
                >
                  <X className="w-3 h-3" />
                </button>
              </motion.div>
            );
          })}
        </AnimatePresence>

        {openCount === 0 && (
          <div className="text-xs text-slate-600 font-mono italic">
            No open exposure. AI Brain scanning for high-conviction 2.0R setups...
          </div>
        )}
      </div>

      {/* Right: Quick Trade Radar Action Buttons */}
      <div className="flex items-center space-x-2">
        <motion.button
          whileTap={{ scale: 0.93 }}
          onClick={() => {
            sound.playSuccess();
            onQuickExecute('BUY');
          }}
          className="px-3 py-1.5 rounded-md text-xs font-semibold font-mono bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 hover:bg-emerald-500/25 transition-all flex items-center space-x-1"
        >
          <Zap className="w-3 h-3" />
          <span>BUY 0.01</span>
        </motion.button>

        <motion.button
          whileTap={{ scale: 0.93 }}
          onClick={() => {
            sound.playSuccess();
            onQuickExecute('SELL');
          }}
          className="px-3 py-1.5 rounded-md text-xs font-semibold font-mono bg-rose-500/15 text-rose-400 border border-rose-500/30 hover:bg-rose-500/25 transition-all flex items-center space-x-1"
        >
          <Zap className="w-3 h-3" />
          <span>SELL 0.01</span>
        </motion.button>
      </div>
    </footer>
  );
}
