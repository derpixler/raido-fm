station:
  id: <short-id>
  name: auto
  claim: "<max 6 words>"
  description: >
    <2-3 sentences positioning>
  lang_definition: >
    <5-8 sentences detailed description>
  genre: <main-genre>
  subgenres: [<3-5 subgenres>]
  target_audience: "<target audience>"
  timezone: Europe/Berlin
  language: en

dj:
  name: "<dj-artist-name>"
  personality: "<2-3 sentences character>"
  tone: "<tonality, comparison>"
  max_moderation_chars: 800
  bio:
    real_name: "<legal name>"
    age: <number>
    origin: "<city/region>"
    family: "<family status, details>"
    hobbies: "<3-4 hobbies>"
    since_year: <year>
    vita: >
      <3-5 sentences resume>
    avatar_prompt: >
      <english prompt for portrait generation>
  quirks:
    - "<quirk 1>"
    - "<quirk 2>"
    - "<quirk 3>"
  forbidden_topics: ["politics", "religion"]

tracks_file: tracks_<station-id>.json

program_grid:
  impulse_slot_minute: 30

rules:
  no_repeat_hours: 4
  max_same_genre_in_a_row: 2
