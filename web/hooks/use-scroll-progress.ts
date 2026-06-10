"use client";

import { useEffect, useState } from "react";

/**
 * Liefert den Lesefortschritt als Wert zwischen 0 und 1, berechnet aus der
 * Scroll-Position relativ zur scrollbaren Gesamthöhe des Dokuments.
 */
export function useScrollProgress(): number {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    let frame = 0;

    const update = () => {
      const doc = document.documentElement;
      const scrollable = doc.scrollHeight - doc.clientHeight;
      const value = scrollable > 0 ? doc.scrollTop / scrollable : 0;
      setProgress(Math.min(1, Math.max(0, value)));
    };

    const onScroll = () => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(update);
    };

    update();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll, { passive: true });
    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
    };
  }, []);

  return progress;
}
