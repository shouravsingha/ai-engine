import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export default function OdometerNumber({ value, prefix = '', suffix = '', decimals = 2, className = '' }) {
  const [prevValue, setPrevValue] = useState(value);
  const [direction, setDirection] = useState('up');

  useEffect(() => {
    if (value !== prevValue) {
      setDirection(value > prevValue ? 'up' : 'down');
      setPrevValue(value);
    }
  }, [value, prevValue]);

  const num = Number(value) || 0;
  const formatted = num.toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });

  return (
    <span className={`inline-flex items-baseline font-mono tracking-tight ${className}`}>
      {prefix && <span className="opacity-70 mr-0.5">{prefix}</span>}
      <AnimatePresence mode="popLayout" initial={false}>
        <motion.span
          key={formatted}
          initial={{ y: direction === 'up' ? 8 : -8, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: direction === 'up' ? -8 : 8, opacity: 0 }}
          transition={{ duration: 0.22, ease: [0.16, 1, 0.3, 1] }}
          className="inline-block"
        >
          {formatted}
        </motion.span>
      </AnimatePresence>
      {suffix && <span className="opacity-70 ml-0.5">{suffix}</span>}
    </span>
  );
}
