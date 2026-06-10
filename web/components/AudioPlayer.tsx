"use client";

import { Pause, Play } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { cn } from "@/lib/utils";

type AudioPlayerProps = {
  src: string;
  title?: string;
  subtitle?: string;
  className?: string;
};

function formatTime(seconds: number): string {
  if (!Number.isFinite(seconds)) return "0:00";
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

/** Kompakter, eigenständiger Audio-Player im Dark-Design (kein <audio>-UI). */
export function AudioPlayer({
  src,
  title = "Audio Summary",
  subtitle = "AI-generated podcast",
  className,
}: AudioPlayerProps) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [playing, setPlaying] = useState(false);
  const [current, setCurrent] = useState(0);
  const [duration, setDuration] = useState(0);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const onTime = () => setCurrent(audio.currentTime);
    const onMeta = () => setDuration(audio.duration);
    const onEnd = () => setPlaying(false);

    audio.addEventListener("timeupdate", onTime);
    audio.addEventListener("loadedmetadata", onMeta);
    audio.addEventListener("ended", onEnd);
    return () => {
      audio.removeEventListener("timeupdate", onTime);
      audio.removeEventListener("loadedmetadata", onMeta);
      audio.removeEventListener("ended", onEnd);
    };
  }, []);

  const toggle = () => {
    const audio = audioRef.current;
    if (!audio) return;
    if (audio.paused) {
      void audio.play();
      setPlaying(true);
    } else {
      audio.pause();
      setPlaying(false);
    }
  };

  const seek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const audio = audioRef.current;
    if (!audio) return;
    const value = Number(e.target.value);
    audio.currentTime = value;
    setCurrent(value);
  };

  const progress = duration > 0 ? (current / duration) * 100 : 0;

  return (
    <div
      className={cn(
        "flex w-full max-w-md items-center gap-4 rounded-xl border border-border bg-surface/70 p-3 pr-5 backdrop-blur",
        className,
      )}
    >
      <audio ref={audioRef} src={src} preload="metadata" />

      <button
        type="button"
        onClick={toggle}
        aria-label={playing ? "Pause" : "Play"}
        aria-pressed={playing}
        className="flex size-12 shrink-0 items-center justify-center rounded-full bg-primary text-white shadow-[0_0_0_1px_rgba(139,92,246,0.4),0_8px_30px_-8px_rgba(139,92,246,0.7)] transition-all duration-200 ease-out hover:bg-primary-glow hover:scale-105 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/60 focus-visible:ring-offset-2 focus-visible:ring-offset-background"
      >
        {playing ? (
          <Pause className="size-5 fill-current" />
        ) : (
          <Play className="size-5 translate-x-0.5 fill-current" />
        )}
      </button>

      <div className="min-w-0 flex-1">
        <div className="flex items-baseline justify-between gap-2">
          <p className="truncate text-sm font-medium text-foreground">
            {title}
          </p>
          <span className="shrink-0 font-mono text-xs tabular-nums text-muted">
            {formatTime(current)} / {formatTime(duration)}
          </span>
        </div>

        <div className="relative mt-2 h-1.5">
          <div className="absolute inset-0 rounded-full bg-border" />
          <div
            className="absolute inset-y-0 left-0 rounded-full bg-gradient-to-r from-primary to-primary-glow"
            style={{ width: `${progress}%` }}
          />
          <input
            type="range"
            min={0}
            max={duration || 0}
            step={0.1}
            value={current}
            onChange={seek}
            aria-label="Playback position"
            className="absolute inset-0 h-full w-full cursor-pointer appearance-none bg-transparent [&::-webkit-slider-thumb]:size-3 [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-white [&::-webkit-slider-thumb]:shadow [&::-moz-range-thumb]:size-3 [&::-moz-range-thumb]:appearance-none [&::-moz-range-thumb]:rounded-full [&::-moz-range-thumb]:border-0 [&::-moz-range-thumb]:bg-white"
          />
        </div>

        <p className="mt-1 truncate text-xs text-muted">{subtitle}</p>
      </div>
    </div>
  );
}
