/** Smooth-scrolls to a section, respecting reduced motion preferences. */
export function scrollToSection(id: string): void {
  const el = document.getElementById(id);
  if (!el) return;

  const prefersReduced = window.matchMedia(
    "(prefers-reduced-motion: reduce)",
  ).matches;

  el.scrollIntoView({
    behavior: prefersReduced ? "auto" : "smooth",
    block: "start",
  });

  // Update history without triggering a hard jump.
  if (history.replaceState) {
    history.replaceState(null, "", `#${id}`);
  }
}
