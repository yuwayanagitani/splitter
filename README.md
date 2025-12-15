# AI Card Divider (Anki Add-on)

AI Card Divider is an Anki add-on that helps you break up cards with long answers into multiple smaller, review-friendly Q&A cards using an AI model.

It is designed for workflows where your notes start as long explanations (e.g., lecture notes, textbook paragraphs, clinical summaries) and you want to convert them into short active-recall cards without doing manual copy/paste.

---

## What it does

When you run the add-on on a note whose answer is “too long” (over a character limit you set), it:

1. Sends the note’s question + long answer to an AI provider (OpenAI or Gemini)
2. Receives multiple short {question, answer} pairs (JSON)
3. Creates new notes in the same note type and deck
4. Adds tags so you can track what was created and avoid re-splitting the same source note

The original note is not deleted.

---

## Main entry points

The add-on provides two ways to run splitting:

### A) Tools menu (search query mode)

Menu item:
- Tools → AI Card Divider: Split Long Answers...

Flow:
- You enter a search query (e.g., `deck:Internal tag:med`)
- The add-on finds notes matching the query
- It processes only notes where the target answer field exceeds your configured length

### B) Browser context menu (selected notes mode)

In the Browser:
- Select notes
- Right-click → Split selected notes with AI

Only selected notes are processed (and only those exceeding the length threshold).

---

## Installation

### Option 1: AnkiWeb (recommended)
- Install the add-on from AnkiWeb (standard Anki add-on workflow)
- Restart Anki

### Option 2: GitHub / manual
- Place the add-on folder inside your Anki `addons21` directory
- Restart Anki

---

## Setup: API keys (required)

This add-on reads your API key from an environment variable.

Default environment variables:
- OpenAI: `OPENAI_API_KEY`
- Gemini: `GEMINI_API_KEY`

If the environment variable is missing, the add-on will show an error dialog.

Tip: environment variables must be available to the Anki process.

---

## Configuration

Open:
- Tools → Add-ons → select “AI Card Divider” → Config

This add-on registers a custom configuration dialog (so you don’t need to edit JSON by hand).

### General

- Question field  
  The field name used as the “question” text (default: `Front`)

- Answer field  
  The field name used as the “answer” text to split (default: `Back`)

- Max answer chars  
  Notes are processed only if the answer field exceeds this many characters (default: `220`)

- Output language  
  Language for both generated questions and answers (default: `English`, can also set `Japanese` or any custom text)

- Max cards  
  Maximum number of split cards to generate per source note (default: `5`)

### Provider

- Provider  
  Choose `openai` or `gemini`

### OpenAI

- Model (default: `gpt-4o-mini`)
- API key env (default: `OPENAI_API_KEY`)
- API base (default: `https://api.openai.com/v1/chat/completions`)

### Gemini

- Model (default: `gemini-2.5-flash`)
- API key env (default: `GEMINI_API_KEY`)
- API base (default: `https://generativelanguage.googleapis.com/v1beta`)

### Generation

- Temperature (default: `0.2`)
- Max output tokens (default: `500`)

### Tags

- Tag for new notes (default: `SplitFromLong`)
- Tag for original note (default: `LongAnswerSplitSource`)

These tags are important:

- New notes get:
  - `SplitFromLong`
  - `SplitFromLong_<SOURCE_NOTE_ID>` (to track provenance)

- The original note gets:
  - `LongAnswerSplitSource`

Notes with either tag are skipped on future runs to prevent accidental duplication.

---

## What gets copied into new notes

For each generated split card, the add-on creates a new note using the same note type as the original.

It copies all fields from the original note first, then overwrites:
- Question field → generated question
- Answer field → generated answer

Tags are based on the original note’s tags plus the new-note tags above.

The new note is added to the same deck as the original note’s first card (fallback: current deck).

---

## AI output rules (important)

The add-on asks the AI to return JSON only, with this structure:

- a single JSON object
- a `cards` list
- each item has `question` and `answer`

Additional constraints requested:
- no bullet lists
- no markdown
- no HTML
- answers should be concise (about 1–3 sentences)

Some providers sometimes wrap JSON in code fences; the add-on includes robust JSON extraction to handle that.

---

## Troubleshooting

### “API key is missing…”
Your environment variable is not set (or not visible to Anki).
- Set `OPENAI_API_KEY` or `GEMINI_API_KEY`
- Restart Anki after setting it

### “Failed to parse JSON in model response…”
The model returned non-JSON or truncated output.
Try:
- Increasing “Max output tokens”
- Using a more reliable model
- Keeping the input answer shorter (or splitting manually into smaller chunks first)

### Nothing happens / “No long answers”
Check:
- Field names match your note type (`Front` / `Back` by default)
- Your “Max answer chars” threshold is not too high
- The notes aren’t already tagged as processed

### Rate limits / HTTP errors
- Try fewer notes at once
- Switch provider/model
- Wait and retry

---

## Privacy / safety

This add-on sends note content (question + answer) to the selected AI provider.
Do not process sensitive or private data unless you understand and accept the provider’s data handling and policies.

---

## License

See the LICENSE file in this repository.
