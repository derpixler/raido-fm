"use client";

import { useEffect, useState } from "react";

type ScrollSpyResult = {
  /** ID der aktuell aktiven Section. */
  activeId: string;
  /** IDs aller bereits gelesenen (überschrittenen) Sections. */
  readIds: Set<string>;
};

/** Erkennungslinie bei 30 % der Viewport-Höhe. */
const ACTIVE_LINE_RATIO = 0.3;

/**
 * Scroll-Spy auf Basis des nativen IntersectionObserver — ohne externe Library.
 *
 * Der Observer triggert die Neuberechnung nur bei Sichtbarkeitswechseln (günstig).
 * Aktiv ist die *letzte* Section, deren Oberkante über der Erkennungslinie liegt.
 * Am Seitenende wird explizit die letzte Section aktiv — sonst könnten kurze
 * Sektionen ganz unten nie weit genug nach oben scrollen, um aktiv zu werden.
 */
export function useScrollSpy(ids: string[]): ScrollSpyResult {
  const [activeId, setActiveId] = useState<string>(ids[0] ?? "");
  const [readIds, setReadIds] = useState<Set<string>>(new Set());

  useEffect(() => {
    const elements = ids
      .map((id) => document.getElementById(id))
      .filter((el): el is HTMLElement => el !== null);

    if (elements.length === 0) return;

    let frame = 0;

    const compute = () => {
      const line = window.innerHeight * ACTIVE_LINE_RATIO;
      const doc = document.documentElement;
      const atBottom =
        window.innerHeight + window.scrollY >= doc.scrollHeight - 2;

      let active = ids[0];
      if (atBottom) {
        // Seitenende erreicht → letzte Section gilt als aktiv.
        active = ids[ids.length - 1];
      } else {
        for (const el of elements) {
          if (el.getBoundingClientRect().top <= line) active = el.id;
        }
      }

      setActiveId(active);
      setReadIds((prev) => {
        const activeIndex = ids.indexOf(active);
        const next = new Set(prev);
        for (let i = 0; i < activeIndex; i++) next.add(ids[i]);
        return next;
      });
    };

    const schedule = () => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(compute);
    };

    // IntersectionObserver als günstiger Trigger für Neuberechnungen.
    const observer = new IntersectionObserver(schedule, {
      threshold: [0, 0.25, 0.5, 0.75, 1],
    });
    elements.forEach((el) => observer.observe(el));

    window.addEventListener("scroll", schedule, { passive: true });
    window.addEventListener("resize", schedule, { passive: true });
    compute();

    return () => {
      cancelAnimationFrame(frame);
      observer.disconnect();
      window.removeEventListener("scroll", schedule);
      window.removeEventListener("resize", schedule);
    };
  }, [ids]);

  return { activeId, readIds };
}
