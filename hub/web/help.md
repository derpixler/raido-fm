# Create a Station

Every RAIDO station consists of two parts: the **Station** (broadcaster, genre, positioning) and the **DJ** (personality, bio, quirks).

## Station-ID

Unique technical ID. Lowercase only, no special characters, max. 15 characters.

Good: `kosmischerwind`, `synthwave42`
Bad: `Mein Sender!`, `BEST_STATION_EVER`

## Claim

The station's slogan. Max. **6 words**. Concise, distinctive, memorable.

> "No algorithm. No control. Just frequency."
> "No signal. Just frequency."
> "Rewind the future."

## Genre + Subgenres

Main genre + 3–5 subgenres, separated by commas. The subgenres define the musical direction and determine which tracks the LLM generates.

Genre examples: `jazz`, `80s`, `techno`, `dark ambient`, `krautrock`, `italo disco`, `shoegaze`, `city pop`

## Target Audience

Who is the station for? Concise, precise, helps the DJ find the right tone.

> "Night people, headphone types, boundary crossers"
> "Nostalgics, 35+, after-work listeners"

## Short Description

The station's positioning in 2–3 sentences. Explains the character of the station — not the DJ.

---

## DJ — The Personality

The DJ is the core of every station. The LLM automatically generates matching track libraries for the selected genre combination.

### DJ Name

The stage name under which the DJ broadcasts. Must be a **100% fictional character** — no real people, no imitations.

Good: `Neon Nadler`, `Orion Wellenreiter`, `Synthia Void`
Prohibited: `Thomas Gottschalk`, `Elke Heidenreich`, `Howard Stern`

### Real Name

The legal name behind the DJ character. Part of the bio — makes the character believable.

`Neon Nadler (Klaus-Dieter Nadler)`

### Age, Origin, Family, Hobbies

Makes the DJ human. No AI clichés ("I am an AI"), but real, fictional biographies.

> Age: 52
> Origin: Düsseldorf
> Family: divorced, one son (17)
> Hobbies: vinyl flea markets, synth restoration

### DJ since

The year the DJ started. Choose realistically depending on age and genre.

> Miles Hertz: 1985 (jazz aficionado, decades of experience)
> Synthia Void: 2015 (pirate radio, younger generation)

### Max. Moderation

Maximum character count per moderation. Default: **800**. Night stations or minimalist DJs tend toward 300–400.

### Personality

The DJ's character in 2–3 sentences. This is the most important part of the prompt — it determines HOW the DJ speaks.

> *"relaxed jazz aficionado with dry humor, never cynical"*
> *"almost invisible, speaks only when necessary, every word weighs"*

### Tone / Tonality

A comparison that describes the speech style. Helps the LLM find the right tone.

> *"clear, conversational — like NPR or BBC Radio 6"*
> *"whispered, minimal — like a lighthouse that morses"*

### Vita

3–5 sentences of backstory. The DJ's fictional career — brings the character to life.

> *"Former jazz critic, behind the microphone since 1985. Hosted in Hamburg basement clubs before anyone thought jazz was cool."*

### Avatar Prompt

English-language prompt for AI image generation (DALL-E, Stable Diffusion). Should describe a portrait.

> *"Portrait of a 52-year-old German radio DJ, warm smile, slightly wild greying hair, vintage Members Only jacket, neon pink headphones..."*

### Quirks

3–4 recurring peculiarities of the DJ. These are the "running gags" that make the DJ recognizable.

> - "lovingly calls songs 'little darlings'"
> - "counts the oscillators in every synth track"
> - "says goodbye on Fridays with a weekend motto"

---

## Validation

Upon launch, every persona is automatically checked:

- **LLM Validator**: Checks for real stations, real people, imitations
- **Hard Filter**: Blocks criminal content (hate speech, etc.)
- **Prompt Injection Check**: Prevents system instructions in persona texts

Violation → Persona is rejected with explanation.

---

## Tips for Good Personas

1. **Less is more** — a strong DJ has 1–2 distinctive traits, not 10
2. **Show genre knowledge** — the DJ should really know the genre (bio, hobbies)
3. **No superlatives** — "The best DJ of all time" is not a character
4. **Rough edges** — likable flaws make characters believable
5. **Naming matters** — the DJ name is the first thing listeners read
6. **Claim ≠ Description** — the claim is a slogan, the description is context
