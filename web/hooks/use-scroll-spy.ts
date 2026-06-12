"use client";

import { useEffect, useState } from "react";

type ScrollSpyResult = {
  /** ID of the currently active section. */
  activeId: string;
  /** IDs of all already-read (scrolled past) sections. */
  readIds: Set<string>;
};

/** Detection line at 30 % of the viewport height. */
const ACTIVE_LINE_RATIO = 0.3;

/**
 * Scroll spy based on the native IntersectionObserver — no external library.
 *
 * The observer only triggers recalculation on visibility changes (cheap).
 * Active is the *last* section whose top edge is above the detection line.
 * At the bottom of the page the last section is explicitly set active —
 * otherwise short sections at the very bottom might never scroll up far
 * enough to become active.
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
        // Bottom reached → last section is considered active.
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

    // IntersectionObserver as a cheap trigger for recalculations.
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
