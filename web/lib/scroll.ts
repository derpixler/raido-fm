/** Scrollt sanft zu einer Section und respektiert reduzierte Bewegung. */
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

  // History aktualisieren, ohne einen harten Sprung auszulösen.
  if (history.replaceState) {
    history.replaceState(null, "", `#${id}`);
  }
}
