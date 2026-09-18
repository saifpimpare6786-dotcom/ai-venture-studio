import { useState, useEffect, useRef } from 'react';

/**
 * useCountUp — Animates a number from 0 to a target value.
 * Used for consulting-grade score reveals on Dashboard mount.
 * 
 * @param {number} target - The target number to count up to
 * @param {number} duration - Animation duration in ms (default 1200)
 * @param {number} decimals - Decimal places to display (default 1)
 * @returns {number} The current animated value
 */
export function useCountUp(target, duration = 1200, decimals = 1) {
  const [value, setValue] = useState(0);
  const startTime = useRef(null);
  const rafId = useRef(null);

  useEffect(() => {
    if (target === 0 || target === null || target === undefined) {
      setValue(0);
      return;
    }

    startTime.current = performance.now();

    const animate = (now) => {
      const elapsed = now - startTime.current;
      const progress = Math.min(elapsed / duration, 1);
      
      // Ease-out cubic for deceleration feel
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = eased * target;

      setValue(Number(current.toFixed(decimals)));

      if (progress < 1) {
        rafId.current = requestAnimationFrame(animate);
      }
    };

    rafId.current = requestAnimationFrame(animate);

    return () => {
      if (rafId.current) cancelAnimationFrame(rafId.current);
    };
  }, [target, duration, decimals]);

  return value;
}
