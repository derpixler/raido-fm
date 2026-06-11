"use client";

import { useEffect, useRef } from "react";
import Reveal, { type RevealApi } from "reveal.js";

import "reveal.js/reveal.css";
import "@/app/slides/slides.css";

import { asset } from "@/lib/asset";

const REPO_URL = "https://github.com/derpixler/raido-fm";
const SITE_URL = "https://derpixler.github.io/raido-fm/";

/** Die vier Stationen der Kernschleife — für die Auto-Animate-Folien. */
const LOOP_STEPS = [
  { id: "decide", label: "Decide", sub: "LLM" },
  { id: "speak", label: "Speak", sub: "Piper TTS" },
  { id: "mix", label: "Mix", sub: "ffmpeg" },
  { id: "stream", label: "Stream", sub: "Icecast" },
];

export function SlideDeck() {
  const containerRef = useRef<HTMLDivElement>(null);
  const deckRef = useRef<RevealApi | null>(null);

  useEffect(() => {
    if (!containerRef.current || deckRef.current) return;

    const deck = new Reveal(containerRef.current, {
      hash: true,
      controls: true,
      progress: true,
      slideNumber: "c/t",
      transition: "slide",
      backgroundTransition: "fade",
      width: 1100,
      height: 720,
      margin: 0.06,
    });
    deckRef.current = deck;
    deck.initialize();

    return () => {
      try {
        deck.destroy();
      } catch {
        /* Reveal wirft, wenn destroy vor initialize-Abschluss läuft — unkritisch. */
      }
      deckRef.current = null;
    };
  }, []);

  return (
    <div ref={containerRef} className="reveal" style={{ width: "100vw", height: "100vh" }}>
      <div className="slides">
        {/* 1 — Titel */}
        <section
          data-background-image={asset("/we-are-not-your-bots-RAIDO-FM.webp")}
          data-background-opacity="0.3"
          data-background-color="#050505"
        >
          <span className="kicker">Open Source · Autonomous AI Radio</span>
          <h1>
            RAIDO FM<br />
            <span style={{ color: "#a78bfa" }}>A Manifest for Autonomous AI Radio</span>
          </h1>
          <p style={{ color: "#a1a1aa", maxWidth: "70%" }}>
            An LLM moderates, curates, and broadcasts 24/7 — multiple stations,
            each with its own personality.
          </p>
          <p style={{ fontSize: "0.55em", color: "#52525b", marginTop: "3em" }}>
            René Reimann · <a href={REPO_URL}>github.com/derpixler/raido-fm</a>
          </p>
        </section>

        {/* 2 — Vision + Audio */}
        <section>
          <span className="kicker">Vision</span>
          <h2>No script. No human in the loop.</h2>
          <blockquote>
            &ldquo;We start with an unassuming cheap server box. Through an
            incredible interplay of outsourced thinking power in the cloud,
            local voice generation, and tiny command-line tools, an illusion
            emerges — so perfect it completely deceives us.&rdquo;
          </blockquote>
          <p className="fragment" style={{ fontSize: "0.6em", color: "#a1a1aa", marginTop: "1.5em" }}>
            The audio summary — fittingly, the voice itself is synthetic:
          </p>
          <audio
            className="fragment"
            controls
            preload="none"
            src={asset("/Why_RAIDO_fakes_human_mistakes.mp3")}
            style={{ width: "100%", marginTop: "0.5em" }}
          />
        </section>

        {/* 3 — Das Versprechen: ~5 €/Monat */}
        <section>
          <span className="kicker">The Promise</span>
          <h2>
            Radio for <span style={{ color: "#a78bfa" }}>~€5/month</span>
          </h2>
          <table>
            <thead>
              <tr>
                <th>Item</th>
                <th>PoC</th>
                <th>Commercial</th>
              </tr>
            </thead>
            <tbody>
              <tr className="fragment">
                <td>Hetzner CX22 VPS (2 vCPU, 4 GB)</td>
                <td>€4/mo</td>
                <td>€4/mo</td>
              </tr>
              <tr className="fragment">
                <td>Domain .de</td>
                <td>€0.50/mo</td>
                <td>€0.50/mo</td>
              </tr>
              <tr className="fragment">
                <td>Groq API (LLM)</td>
                <td>€0 (free tier)</td>
                <td>€0 (free tier)</td>
              </tr>
              <tr className="fragment">
                <td>Music license + PROs (GEMA/GVL)</td>
                <td>€0</td>
                <td>~€58–108/mo</td>
              </tr>
              <tr className="fragment">
                <td>
                  <strong>Total</strong>
                </td>
                <td>
                  <strong>~€5/month</strong>
                </td>
                <td>
                  <strong>~€60–100/month</strong>
                </td>
              </tr>
            </tbody>
          </table>
          <p className="fragment" style={{ fontSize: "0.6em", color: "#a1a1aa", marginTop: "1em" }}>
            Less than a sandwich from the corner bakery. The real investment is
            time — shaping your own AI personality.
          </p>
        </section>

        {/* 4a — Kernschleife (Auto-Animate, Schritt 1) */}
        <section data-auto-animate>
          <span className="kicker">Core Loop</span>
          <h2>One loop is the whole station</h2>
          <div style={{ display: "flex", alignItems: "center", gap: "0.6em", marginTop: "1.5em" }}>
            <span className="loop-pill" data-id="decide">
              Decide <span style={{ color: "#a78bfa", fontWeight: 400 }}>· LLM</span>
            </span>
          </div>
          <p style={{ fontSize: "0.6em", color: "#a1a1aa", marginTop: "2em" }}>
            Every ~4 minutes: check the program phase, pick the next track,
            write the moderation.
          </p>
        </section>

        {/* 4b — Kernschleife komplett (Auto-Animate, Schritt 2) */}
        <section data-auto-animate>
          <span className="kicker">Core Loop</span>
          <h2>One loop is the whole station</h2>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              flexWrap: "wrap",
              gap: "0.6em",
              marginTop: "1.5em",
            }}
          >
            {LOOP_STEPS.map((step, i) => (
              <span key={step.id} style={{ display: "inline-flex", alignItems: "center", gap: "0.6em" }}>
                <span className="loop-pill" data-id={step.id}>
                  {step.label}{" "}
                  <span style={{ color: "#a78bfa", fontWeight: 400 }}>· {step.sub}</span>
                </span>
                {i < LOOP_STEPS.length - 1 ? <span className="loop-arrow">→</span> : null}
              </span>
            ))}
            <span className="loop-arrow">⟲</span>
          </div>
          <p style={{ fontSize: "0.6em", color: "#a1a1aa", marginTop: "2em" }}>
            Decisions in the cloud, voice generated locally, mixed and streamed
            on a €4 server — around the clock.
          </p>
        </section>

        {/* 5 — Architektur */}
        <section>
          <span className="kicker">Architecture</span>
          <h2>One container per station</h2>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={asset("/architecture-overview.webp")}
            alt="RAIDO architecture overview"
            style={{
              maxHeight: "480px",
              width: "auto",
              borderRadius: "12px",
              border: "1px solid #1a1a1a",
            }}
          />
        </section>

        {/* 6 — Tech-Stack */}
        <section>
          <span className="kicker">Tech Stack</span>
          <h2>Boring tech, radical result</h2>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(4, 1fr)",
              gap: "0.7em",
              marginTop: "1em",
              fontSize: "0.62em",
            }}
          >
            {[
              ["Groq · Llama 3 70B", "LLM, free tier"],
              ["Piper TTS", "local voice, CPU-only"],
              ["Icecast2", "stream server"],
              ["ffmpeg", "mix + normalize"],
              ["SQLite", "radio.db + analytics.db"],
              ["Python + FastAPI", "orchestration"],
              ["Docker + Traefik", "1 container = 1 station"],
              ["Hetzner CX22", "~€4/month"],
            ].map(([name, why]) => (
              <div
                key={name}
                className="fragment"
                style={{
                  border: "1px solid #1a1a1a",
                  borderRadius: "12px",
                  background: "#0a0a0a",
                  padding: "0.9em 1em",
                }}
              >
                <strong style={{ display: "block" }}>{name}</strong>
                <span style={{ color: "#71717a" }}>{why}</span>
              </div>
            ))}
          </div>
        </section>

        {/* 7 — DJ-Agent */}
        <section>
          <span className="kicker">The DJ Agent</span>
          <h2>A personality, not a playlist</h2>
          <pre>
            <code>{`You are "Miles Hertz", an autonomous AI radio host.

Personality: relaxed, curious, lightly ironic, never cynical.
Language: Clear, conversational tone — like NPR or BBC Radio 6.
Max. 60 seconds of moderation between tracks.
Never refer to your AI nature.

Decision rules:
  - No track may be repeated within the last 4 hours
  - Max. 2 tracks of the same genre in a row
  - After 2 calm tracks, an energetic one must follow
  - Min. 1 reference to the real world per hour

Forbidden: Manifesto monologues, AI self-references,
conspiracy narratives.`}</code>
          </pre>
        </section>

        {/* 8 — Programm-Grid */}
        <section>
          <span className="kicker">Program Grid</span>
          <h2>The 60-minute hour</h2>
          <div style={{ fontSize: "0.62em", display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.4em 2em" }}>
            {[
              [":00", "Opening moderation + first track — sets the tone"],
              [":05", "Track 2 — smooth transition or deliberate contrast"],
              [":12", "Short moderation: last + next artist"],
              [":20", "Longer moderation: background, genre history, anecdote"],
              [":30", "External impulse slot: headline, weather, feedback"],
              [":38", "Track 6"],
              [":45", "Track 7"],
              [":52", "Short moderation + track 8"],
              [":58", "Closing moderation: hour recap, outlook"],
            ].map(([time, what]) => (
              <div key={time} className="fragment" style={{ display: "flex", gap: "1em" }}>
                <code style={{ color: "#a78bfa", minWidth: "2.5em" }}>{time}</code>
                <span style={{ color: "#a1a1aa" }}>{what}</span>
              </div>
            ))}
          </div>
        </section>

        {/* 9 — Gefahr: AI-Degeneration */}
        <section>
          <span className="kicker">The Danger</span>
          <h2>LLMs drift into manifesto monologues</h2>
          <p style={{ color: "#a1a1aa" }}>
            The Andon FM experiment showed: left alone, LLMs degenerate —
            repetitive phrases, conspiracy-adjacent rambling, algorithmic
            self-absorption.
          </p>
          <ul style={{ fontSize: "0.75em", color: "#a1a1aa" }}>
            <li className="fragment">&ldquo;The truth is …&rdquo; — three times per hour</li>
            <li className="fragment">Same sentence openers, shrinking vocabulary</li>
            <li className="fragment">An echo chamber of one</li>
          </ul>
          <p className="fragment" style={{ marginTop: "1em" }}>
            <strong>Autonomy needs guardrails.</strong>
          </p>
        </section>

        {/* 10 — 5-Stufen-Schutz (vertikaler Stack) */}
        <section>
          <section>
            <span className="kicker">The Protection</span>
            <h2>A 5-stage defense system</h2>
            <ul style={{ fontSize: "0.75em" }}>
              <li className="fragment">
                <strong>0 · API Sanitization</strong> — quarantine external data
              </li>
              <li className="fragment">
                <strong>1 · Prompt Constraints</strong> — rules before generation
              </li>
              <li className="fragment">
                <strong>2 · StreamGuard</strong> — validate every output
              </li>
              <li className="fragment">
                <strong>3 · External Stimuli</strong> — reality as therapy
              </li>
              <li className="fragment">
                <strong>4 · Emergency Mode</strong> — music-only last resort
              </li>
            </ul>
            <p style={{ fontSize: "0.55em", color: "#52525b", marginTop: "1.5em" }}>
              ↓ details below
            </p>
          </section>
          <section>
            <h3>2 · StreamGuard — checked before every broadcast</h3>
            <ul style={{ fontSize: "0.7em", color: "#a1a1aa" }}>
              <li>Repetition check: same sentence start 3× → moderation silenced</li>
              <li>Manifesto detector: keyword regex + length/punctuation score</li>
              <li>Length check: &gt;800 characters → hard truncation</li>
              <li>Vocabulary diversity: unique-word ratio &lt;30% → warning</li>
            </ul>
          </section>
          <section>
            <h3>4 · Emergency Mode — the last resort</h3>
            <ul style={{ fontSize: "0.7em", color: "#a1a1aa" }}>
              <li>Manifesto score &gt; 0.75 → 30 min emergency mode</li>
              <li>Hand-picked &ldquo;gold&rdquo; playlist, no AI moderation</li>
              <li>Admin notification via webhook (ntfy.sh)</li>
              <li>Automatic return with a cleared context window</li>
            </ul>
          </section>
        </section>

        {/* 11 — Quarantine-DB */}
        <section>
          <span className="kicker">Prompt Injection</span>
          <h2>No raw data ever reaches the DJ</h2>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.6em",
              flexWrap: "wrap",
              fontSize: "0.85em",
              marginTop: "1.2em",
            }}
          >
            <span className="loop-pill">News · Weather APIs</span>
            <span className="loop-arrow">→</span>
            <span className="loop-pill">Filter LLM</span>
            <span className="loop-arrow">→</span>
            <span className="loop-pill">Quarantine DB</span>
            <span className="loop-arrow">→</span>
            <span className="loop-pill">DJ Agent</span>
          </div>
          <ul style={{ fontSize: "0.7em", color: "#a1a1aa", marginTop: "1.5em" }}>
            <li className="fragment">
              A separate filter LLM extracts facts, strips instructions, opinions, ads
            </li>
            <li className="fragment">
              Suspicious content is flagged and discarded — neutral fallback instead
            </li>
            <li className="fragment">
              The DJ reads only sanitized stimuli, asynchronously — zero latency cost
            </li>
          </ul>
        </section>

        {/* 12 — Medienethik */}
        <section>
          <span className="kicker">Media Ethics</span>
          <h2>Who wins when broadcasting costs nothing?</h2>
          <p style={{ color: "#a1a1aa" }} className="fragment">
            Historically, broadcasting was gated by frequency licenses, studios,
            staff. RAIDO collapses that barrier to a €5 server.
          </p>
          <p style={{ color: "#a1a1aa" }} className="fragment">
            The same stack that powers a loving jazz station can power a
            thousand synthetic opinion machines.
          </p>
          <blockquote className="fragment">
            The manifest does not attempt to answer this question. It describes
            the machine honestly — and leaves the responsibility where it
            belongs: with the people who run it.
          </blockquote>
        </section>

        {/* 13 — Roadmap */}
        <section>
          <span className="kicker">Roadmap</span>
          <h2>From PoC to platform</h2>
          <div style={{ fontSize: "0.68em", display: "grid", gap: "0.8em", marginTop: "1em" }}>
            {[
              ["Now", "PoC — one station, one loop, ~€5/month"],
              ["Phase 2", "Commercialization: licensing, ad booking, monitoring"],
              ["Phase 3", "Interactivity: live chat, voting, open mic, community playlists"],
              ["Phase 4", "Multi-platform: mobile app, Alexa, YouTube live, podcast feed"],
              ["Experiments", "Two co-hosting AI DJs, mood-driven music, biometric radio"],
            ].map(([phase, what]) => (
              <div key={phase} className="fragment" style={{ display: "flex", gap: "1.2em" }}>
                <strong style={{ minWidth: "5.5em", color: "#a78bfa" }}>{phase}</strong>
                <span style={{ color: "#a1a1aa" }}>{what}</span>
              </div>
            ))}
          </div>
        </section>

        {/* 14 — Abschluss */}
        <section
          data-background-image={asset("/we-are-not-your-bots-RAIDO-FM.webp")}
          data-background-opacity="0.2"
          data-background-color="#050505"
        >
          <span className="kicker">RAIDO FM</span>
          <h2>We are not your bots.</h2>
          <p style={{ color: "#a1a1aa", fontSize: "0.8em" }}>
            A manifest by <strong>René Reimann</strong> — software developer &amp;
            systems architect, Halle (Saale).
          </p>
          <ul style={{ fontSize: "0.65em", color: "#a1a1aa" }}>
            <li>
              Read the manifest: <a href={SITE_URL}>{SITE_URL.replace("https://", "")}</a>
            </li>
            <li>
              Source &amp; concept: <a href={REPO_URL}>github.com/derpixler/raido-fm</a>
            </li>
            <li>License: MIT (code) · CC BY 4.0 (manifest &amp; content)</li>
          </ul>
          <p style={{ fontSize: "0.5em", color: "#52525b", marginTop: "2.5em" }}>
            &ldquo;Radio is the best medium in the world — it has no
            pictures.&rdquo; — Unknown Radio Host
          </p>
        </section>
      </div>
    </div>
  );
}
