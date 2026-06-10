import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Erzeugt aus einem Überschriftstext eine URL-sichere ID — kompatibel zur
 * GitHub-Slug-Logik (Mehrfach-Bindestriche bleiben erhalten), damit die
 * Anker-Links innerhalb der readme.md weiterhin funktionieren.
 */
export function slugify(text: string): string {
  return text
    .toLowerCase()
    .trim()
    .replace(/[^\p{L}\p{N}\s-]/gu, "")
    .replace(/\s/g, "-");
}
