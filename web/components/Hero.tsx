"use client";

import { motion } from "framer-motion";
import { Presentation, Radio } from "lucide-react";
import Link from "next/link";

import { AudioPlayer } from "@/components/AudioPlayer";
import { AudioWave } from "@/components/AudioWave";
import { GithubIcon } from "@/components/icons";
import { buttonVariants } from "@/components/ui/button";
import { asset } from "@/lib/asset";
import { cn } from "@/lib/utils";

const GITHUB_URL = "https://github.com/derpixler/raido-fm";

const fadeUp = {
  hidden: { opacity: 0, y: 24 },
  show: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.4, delay: i * 0.08, ease: "easeOut" as const },
  }),
};

export function Hero() {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
      className="relative flex min-h-[34rem] flex-col justify-end overflow-hidden border-b border-border lg:min-h-[44rem]"
    >
      {/* Graffiti studio as Hero background */}
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={asset("/we-are-not-your-bots-RAIDO-FM.webp")}
        alt="WE ARE NOT YOUR BOTS — RAIDO FM, spray-painted on a studio wall"
        className="absolute inset-0 size-full object-cover"
        fetchPriority="high"
        decoding="async"
      />

      {/* Gradient overlays for readability + purple atmosphere */}
      <div className="absolute inset-0 bg-gradient-to-t from-background via-background/85 via-35% to-transparent" />
      <div className="absolute inset-0 bg-gradient-to-r from-background/90 via-background/30 to-transparent" />
      <div className="pointer-events-none absolute -bottom-1/3 left-0 h-2/3 w-2/3 rounded-full bg-primary/20 blur-[120px]" />

      {/* Animated audio waves as subtle accent bottom right */}
      <AudioWave className="pointer-events-none absolute -right-6 bottom-0 hidden h-64 w-[28rem] opacity-50 md:block" />

      <div className="relative z-10 mx-auto w-full max-w-7xl px-5 pb-12 pt-10 sm:px-8 sm:pb-16 lg:px-12 lg:pb-20">
        <div className="grid items-center gap-10 lg:grid-cols-[minmax(0,1fr)_auto] lg:gap-14">
          {/* Left column: text & content */}
          <div className="max-w-2xl">
            <motion.span
              custom={0}
              initial="hidden"
              animate="show"
              variants={fadeUp}
              className="inline-flex items-center gap-2 rounded-full border border-border bg-surface/70 px-3 py-1 text-xs font-medium text-muted backdrop-blur"
            >
              <Radio className="size-3.5 text-primary-glow" />
              Open-Source · Autonomous AI Radio
            </motion.span>

            <motion.h1
              custom={1}
              initial="hidden"
              animate="show"
              variants={fadeUp}
              className="mt-5 text-balance text-4xl font-semibold tracking-tight text-white sm:text-5xl lg:text-6xl"
            >
              A Manifest for Autonomous AI Radio
            </motion.h1>

            <motion.p
              custom={2}
              initial="hidden"
              animate="show"
              variants={fadeUp}
              className="mt-5 max-w-xl text-pretty text-lg leading-relaxed text-white sm:text-xl"
            >
              An open-source manifest for operating one or more digital radio
              stations entirely moderated and curated by an AI (Large Language
              Model). Inspired by the{" "}
              <a
                href="https://bruceramos.substack.com/p/the-autonomy-test-the-music-business"
                target="_blank"
                rel="noreferrer noopener"
                className="font-medium text-primary-glow underline decoration-primary-glow/40 underline-offset-4 transition-colors hover:decoration-primary-glow"
              >
                Andon FM experiment
              </a>{" "}
              from{" "}
              <a
                href="https://andonlabs.com"
                target="_blank"
                rel="noreferrer noopener"
                className="font-medium text-primary-glow underline decoration-primary-glow/40 underline-offset-4 transition-colors hover:decoration-primary-glow"
              >
                Andon Labs
              </a>
              .
            </motion.p>

            <motion.p
              custom={3}
              initial="hidden"
              animate="show"
              variants={fadeUp}
              className="mt-4 max-w-xl text-pretty text-base leading-relaxed text-white/80"
            >
              An AI-generated audio summary of this manifest: the
              architecture, the DJ agent&apos;s personality, the 5-stage
              safety system, and the philosophical implications — condensed
              into one listen. Fittingly, the voice itself is synthetic.
            </motion.p>

            <motion.div
              custom={4}
              initial="hidden"
              animate="show"
              variants={fadeUp}
              className="mt-8 flex flex-wrap items-center gap-4"
            >
              <a
                href={GITHUB_URL}
                target="_blank"
                rel="noreferrer noopener"
                className={cn(
                  buttonVariants({ variant: "outline", size: "lg" }),
                )}
              >
                <GithubIcon className="size-4" />
                View on GitHub
              </a>
              <Link
                href="/slides"
                className={cn(buttonVariants({ variant: "ghost", size: "lg" }))}
              >
                <Presentation className="size-4" />
                Slides
              </Link>
            </motion.div>

            <motion.dl
              custom={5}
              initial="hidden"
              animate="show"
              variants={fadeUp}
              className="mt-10 grid max-w-md grid-cols-3 gap-6"
            >
              {[
                { value: "24/7", label: "Live operation" },
                { value: "~€5", label: "per month" },
                { value: "∞", label: "Stations" },
              ].map((stat) => (
                <div key={stat.label}>
                  <dt className="text-2xl font-semibold text-white">
                    {stat.value}
                  </dt>
                  <dd className="mt-1 text-sm text-white/60">{stat.label}</dd>
                </div>
              ))}
            </motion.dl>
          </div>

          {/* Right column: square cover + audio player */}
          <motion.div
            custom={2}
            initial="hidden"
            animate="show"
            variants={fadeUp}
            className="flex w-full flex-col gap-4 lg:w-[24rem]"
          >
            <div className="relative aspect-square w-full overflow-hidden rounded-2xl border border-border shadow-[0_24px_60px_-20px_rgba(0,0,0,0.8)]">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={asset("/raido-cover.webp")}
                alt="RAIDO FM — We are not your bots. No algorithm. No control. Just frequency."
                className="size-full object-cover"
                decoding="async"
              />
            </div>
            <AudioPlayer
              src={asset("/Why_RAIDO_fakes_human_mistakes.mp3")}
              title="Why RAIDO fakes human mistakes"
              subtitle="Audio Summary · AI-generated"
              className="max-w-none"
            />
          </motion.div>
        </div>
      </div>
    </motion.div>
  );
}
