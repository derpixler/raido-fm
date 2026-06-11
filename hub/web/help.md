# Station erstellen

Jede RAIDO-Station besteht aus zwei Teilen: der **Station** (Sender, Genre, Positionierung) und dem **DJ** (Persoenlichkeit, Bio, Quirks).

## Station-ID

Eindeutige technische ID. Nur Kleinbuchstaben, keine Sonderzeichen, max. 15 Zeichen.

Gut: `kosmischerwind`, `synthwave42`
Schlecht: `Mein Sender!`, `BEST_STATION_EVER`

## Claim

Der Slogan des Senders. Max. **6 Worte**. Praegnant, markant, einpraegsam.

> "No algorithm. No control. Just frequency."
> "Kein Signal. Nur Frequenz."
> "Rewind the future."

## Genre + Subgenres

Hauptgenre + 3–5 Subgenres, durch Komma getrennt. Die Subgenres definieren die musikalische Ausrichtung und bestimmen, welche Tracks die LLM generiert.

Genre-Beispiele: `jazz`, `80s`, `techno`, `dark ambient`, `krautrock`, `italo disco`, `shoegaze`, `city pop`

## Zielgruppe

Fuer wen ist der Sender? Knapp, praezise, hilft dem DJ den richtigen Ton zu treffen.

> "Nachtmenschen, Kopfhoerer-Typen, Grenzgaenger"
> "Nostalgiker, 35+, Feierabend-Hoerer"

## Kurzbeschreibung

Die Positionierung des Senders in 2–3 Saetzen. Erklaert den Charakter des Senders — nicht des DJs.

---

## DJ — Die Persoenlichkeit

Der DJ ist der Kern jeder Station. Die LLM generiert automatisch passende Track-Libraries zur gewaehlten Genre-Kombination.

### DJ-Name

Der Kuenstlername, unter dem der DJ sendet. Muss eine **100% fiktive Figur** sein — keine echten Personen, keine Imitationen.

Gut: `Neon Nadler`, `Orion Wellenreiter`, `Synthia Void`
Verboten: `Thomas Gottschalk`, `Elke Heidenreich`, `Howard Stern`

### Real Name

Der buergerliche Name hinter der DJ-Figur. Gehoert zur Bio — macht die Figur glaubwuerdig.

`Neon Nadler (Klaus-Dieter Nadler)`

### Alter, Herkunft, Familie, Hobbies

Machen den DJ menschlich. Keine KI-Klischees ("Ich bin eine KI"), sondern echte, fiktive Biografien.

> Alter: 52
> Herkunft: Duesseldorf
> Familie: geschieden, ein Sohn (17)
> Hobbies: Vinyl-Flohmaerkte, Synth-Restaurierung

### DJ seit

Das Jahr, in dem der DJ begonnen hat. Je nach Alter und Genre realistisch waehlen.

> Miles Hertz: 1985 (Jazz-Kenner, jahrzehntelange Erfahrung)
> Synthia Void: 2015 (Piratensender, juengere Generation)

### Max. Moderation

Maximale Zeichenzahl pro Moderation. Standard: **800**. Nachtsender oder minimalistische DJs eher 300–400.

### Persoenlichkeit

Der Charakter des DJs in 2–3 Saetzen. Dies ist der wichtigste Prompt-Teil — er bestimmt, WIE der DJ spricht.

> *"relaxter Jazz-Kenner mit trockenem Humor, nie zynisch"*
> *"fast unsichtbar, spricht nur wenn noetig, jedes Wort wiegt"*

### Ton / Tonalitaet

Ein Vergleich, der den Sprachstil beschreibt. Hilft dem LLM, den richtigen Ton zu treffen.

> *"klar, konversationell — wie NPR oder BBC Radio 6"*
> *"gefluestert, minimal — wie ein Leuchtturm der morst"*

### Vita

3–5 Saetze Lebenslauf. Die fiktive Karriere des DJs — macht die Figur lebendig.

> *"Ehemaliger Jazz-Kritiker, seit 1985 hinter dem Mikrofon. Hat in Hamburger Kellerclubs moderiert, bevor irgendwer Jazz cool fand."*

### Avatar Prompt

Englischsprachiger Prompt fuer eine KI-Bildgenerierung (DALL-E, Stable Diffusion). Sollte ein Portraet beschreiben.

> *"Portrait of a 52-year-old German radio DJ, warm smile, slightly wild greying hair, vintage Members Only jacket, neon pink headphones..."*

### Quirks

3–4 wiederkehrende Eigenheiten des DJs. Das sind die "running gags", die den DJ wiedererkennbar machen.

> - "nennt Songs liebevoll 'Schaetzchen'"
> - "zaehlt bei jedem Synth-Track die Oszillatoren"
> - "verabschiedet sich freitags mit einem Wochenend-Motto"

---

## Validierung

Beim Starten wird jede Persona automatisch geprueft:

- **LLM-Validator**: Prueft auf echte Sender, echte Personen, Imitationen
- **Hard-Filter**: Blockiert strafrechtlich relevante Inhalte (Volksverhetzung etc.)
- **Prompt-Injection-Check**: Verhindert Systemanweisungen in Persona-Texten

Verstoss → Persona wird abgelehnt mit Begruendung.

---

## Tipps fuer gute Personas

1. **Weniger ist mehr** — ein starker DJ hat 1–2 markante Eigenschaften, nicht 10
2. **Genre-Wissen zeigen** — der DJ sollte das Genre wirklich kennen (Vita, Hobbies)
3. **Keine Superlative** — "Der beste DJ aller Zeiten" ist kein Charakter
4. **Ecken und Kanten** — sympathische Fehler machen Figuren glaubwuerdig
5. **Naming matters** — der DJ-Name ist das Erste, was Hoerer lesen
6. **Claim ≠ Beschreibung** — der Claim ist ein Slogan, die Description ist Kontext
