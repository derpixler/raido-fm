"use client";

import { motion, useReducedMotion } from "framer-motion";
import { useMemo } from "react";

type AudioWaveProps = {
  bars?: number;
  className?: string;
};

/**
 * Animated audio visualization as pure SVG (no images).
 * Combines a pulsing equalizer bar, concentric signal rings
 * and subtle floating particles — all in purple accents.
 */
export function AudioWave({ bars = 28, className }: AudioWaveProps) {
  const prefersReduced = useReducedMotion();

  const equalizer = useMemo(
    () =>
      Array.from({ length: bars }, (_, i) => {
        const t = i / (bars - 1);
        // Bell curve: higher amplitude in the middle.
        const bell = Math.sin(t * Math.PI);
        return {
          base: 8 + bell * 46,
          peak: 18 + bell * 92,
          delay: i * 0.045,
          duration: 1 + bell * 0.9,
        };
      }),
    [bars],
  );

  const particles = useMemo(
    () =>
      Array.from({ length: 14 }, (_, i) => ({
        cx: 30 + ((i * 53) % 340),
        cy: 20 + ((i * 97) % 300),
        r: 1 + (i % 3),
        delay: (i % 7) * 0.4,
        duration: 4 + (i % 5),
      })),
    [],
  );

  return (
    <div className={className} aria-hidden="true">
      <svg
        viewBox="0 0 400 360"
        className="h-full w-full overflow-visible"
        role="presentation"
      >
        <defs>
          <linearGradient id="wave-grad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#A78BFA" />
            <stop offset="100%" stopColor="#8B5CF6" />
          </linearGradient>
          <radialGradient id="wave-glow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#8B5CF6" stopOpacity="0.35" />
            <stop offset="70%" stopColor="#8B5CF6" stopOpacity="0.05" />
            <stop offset="100%" stopColor="#8B5CF6" stopOpacity="0" />
          </radialGradient>
        </defs>

        {/* Soft background glow */}
        <circle cx="200" cy="180" r="170" fill="url(#wave-glow)" />

        {/* Concentric signal rings */}
        {[0, 1, 2].map((ring) => (
          <motion.circle
            key={ring}
            cx="200"
            cy="180"
            r="60"
            fill="none"
            stroke="#A78BFA"
            strokeWidth="1"
            initial={{ scale: 0.6, opacity: 0.5 }}
            animate={
              prefersReduced
                ? { scale: 1, opacity: 0.2 }
                : { scale: [0.6, 1.6], opacity: [0.5, 0] }
            }
            transition={{
              duration: 3.2,
              delay: ring * 1.05,
              repeat: Infinity,
              ease: "easeOut",
            }}
            style={{ transformOrigin: "200px 180px" }}
          />
        ))}

        {/* Equalizer */}
        <g transform="translate(0 180)">
          {equalizer.map((bar, i) => {
            const x = 30 + i * ((340 - 8) / (bars - 1));
            return (
              <motion.rect
                key={i}
                x={x}
                width="6"
                rx="3"
                fill="url(#wave-grad)"
                initial={{ height: bar.base, y: -bar.base / 2 }}
                animate={
                  prefersReduced
                    ? { height: bar.base, y: -bar.base / 2 }
                    : {
                        height: [bar.base, bar.peak, bar.base],
                        y: [-bar.base / 2, -bar.peak / 2, -bar.base / 2],
                      }
                }
                transition={{
                  duration: bar.duration,
                  delay: bar.delay,
                  repeat: Infinity,
                  ease: "easeInOut",
                }}
              />
            );
          })}
        </g>

        {/* Subtle floating particles */}
        {particles.map((p, i) => (
          <motion.circle
            key={i}
            cx={p.cx}
            cy={p.cy}
            r={p.r}
            fill="#A78BFA"
            initial={{ opacity: 0.1 }}
            animate={
              prefersReduced
                ? { opacity: 0.15 }
                : { opacity: [0.1, 0.5, 0.1], y: [0, -12, 0] }
            }
            transition={{
              duration: p.duration,
              delay: p.delay,
              repeat: Infinity,
              ease: "easeInOut",
            }}
          />
        ))}
      </svg>
    </div>
  );
}
