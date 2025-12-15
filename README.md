# Anki AI Splitter

Long "wall-of-text" answers are hard to review. Anki AI Splitter uses an AI model to split one long Anki note (or card) into multiple shorter Q&A cards while keeping the original note intact. This makes reviewing long answers easier, improves Active Recall, and helps you convert exposition-style notes into compact question/answer pairs.

Repository: [yuwayanagitani/anki-ai-splitter](https://github.com/yuwayanagitani/anki-ai-splitter)

Table of contents
- Features
- Screenshots
- Requirements
- Installation
  - Install from Anki (if distributed via AnkiWeb)
  - Manual install (recommended for developers)
- Configuration
- Usage
  - In the Editor
  - In the Browser (batch splitting)
- Options & settings explained
- Example
- Tips & prompt customization
- Troubleshooting
- Privacy & Security
- Development & Contributing
- License
- Support

---

## Features
- Split a single long answer/explanation into multiple concise Q&A pairs using an AI model.
- Keep the original note intact (you can choose to keep or duplicate).
- Map newly generated Q&A to your note fields (customizable).
- Tag new notes, optionally add a suffix/prefix to note titles.
- Preview generated splits before committing them to your collection.
- Batch-split multiple notes from the Browser.
- Support for remote AI APIs (OpenAI, Hugging Face Inference, or any compatible HTTP endpoint) and configurable model settings.

---

## Screenshots
(Replace these with actual screenshots of the add-on UI)
- Editor split dialog
- Browser batch-split flow
- Preview of generated Q&A notes

---

## Requirements
- Anki 2.1.x (tested on the latest 2.1 series). Compatibility with older versions is not guaranteed.
- Internet connection if you use a hosted AI provider (OpenAI, Hugging Face, etc).
- API key for the AI provider you choose (unless using a self-hosted/local model).
- Typical Python runtime and libraries are provided by Anki; if additional third-party packages are required they will be documented in the repository.

---

## Installation

### Option A — Install from AnkiWeb (recommended if available)
1. Open Anki.
2. Tools → Add-ons → Get Add-ons...
3. Enter the add-on code (if published on AnkiWeb) and install.
4. Restart Anki.

(If this add-on is published on AnkiWeb, the listing will provide the code.)

### Option B — Manual install (clone from GitHub)
Install into Anki's `addons21` folder:

1. Find your addons folder:
   - Windows: `%APPDATA%\Anki2\addons21`
   - macOS: `~/Library/Application Support/Anki2/addons21`
   - Linux: `~/.local/share/Anki2/addons21`

2. Clone the repository into a new directory inside `addons21`:
   - Example (replace the path with yours):
     ```
     cd "<path to addons21>"
     git clone https://github.com/yuwayanagitani/anki-ai-splitter anki-ai-splitter
     ```
3. Restart Anki.

Notes:
- If the add-on depends on extra Python packages that are not present in Anki's bundled Python environment, see the Development section for how to install them into Anki's Python environment.

---

## Configuration
After installing, open the add-on configuration to set your model and API credentials.

1. Tools → Add-ons.
2. Select "Anki AI Splitter" from the list.
3. Click "Config" (or open add-on Preferences from the add-on menu if available).

Typical configuration options:
- Provider: `openai`, `huggingface`, `custom-http`
- API key / Endpoint URL / Additional headers
- Default model (e.g., `gpt-4o`, `gpt-4`, `gpt-3.5-turbo`, or a Hugging Face model id)
- Default max tokens / temperature / top_p
- Default field mapping (which fields hold generated `Question` and `Answer`)
- Default behavior for keeping original note, tagging new notes, and previewing

Important:
- Store API keys securely. Do not commit API keys into the repository or share them publicly.

---

## Usage

This add-on works in two places: the Editor (single note) and the Browser (batch notes).

### In the Editor (split a single note)
1. Open or create the note you want to split in the Editor.
2. Populate the field that contains the long answer/explanation (for example: `Back`, `Explanation`).
3. Open the add-on dialog:
   - Usually accessible via a toolbar button, menu entry (e.g., Tools → AI Splitter → Split Current Note), or a context menu inside the Editor.
4. Configure options (or use defaults):
   - Choose the model/provider
   - Number of Q&A pairs (or let the AI decide)
   - Max length per answer/question
   - Whether to keep the original note or create new separate notes
   - Field mapping for `Question` and `Answer`
5. Click "Preview" to see the proposed Q&A splits (recommended).
6. Review the generated Q&As. Edit any Q/A text in preview if needed.
7. Click "Apply" (or "Commit") to create new notes/cards in your collection.

Result:
- New notes are created according to your field mapping and tagging preferences.
- The original note is preserved or modified depending on your setting.

### In the Browser (batch split multiple notes)
1. Open the Browser.
2. Filter/select the notes you want to process (multiselect).
3. Right-click → Tools → AI Splitter → Split Selected Notes (or use the add-on's Browser menu item).
4. Configure batch options (model, keep originals, tags).
5. Start the batch job.
6. For each note, the tool can either auto-apply the generated splits or open a preview dialog for manual review (configurable).

Batch mode notes:
- Batch processing can trigger many API calls — watch your rate limits and quotas.
- Consider testing with 1–5 notes first.

---

## Options & settings explained

- Provider: The backend AI provider; affects how prompts and authentication are handled.
- Model: Which AI model to use (size and behavior differ).
- Max splits: Maximum number of Q&A pairs to generate.
- Temperature: Controls randomness. 0.0 = deterministic; 0.7 = creative.
- Max tokens / Response length: Limit output size to avoid truncated or overly long answers.
- Field mapping: Map the AI-generated `Question` and `Answer` to your note fields (e.g., `Front` and `Back`).
- Keep original note: If enabled, the original note is left untouched and only new notes are created. If disabled, the original may be replaced or modified.
- Tagging: Add a tag (e.g., `ai-split`) to newly created notes for easy filtering.
- Preview before commit: Recommended for quality control.
- Preserve formatting/HTML: If your notes contain HTML or media, enable this option to preserve them where possible.
- Undo: The add-on should create operations that can be undone by Anki's built-in undo, but double-check after batch operations.

---

## Example

Input (single long answer in field `Explanation`):
> "Photosynthesis is the process by which green plants, algae, and some bacteria use sunlight to convert carbon dioxide and water into glucose and oxygen. The process occurs in chloroplasts and involves light-dependent reactions and the Calvin cycle. Light reactions capture light energy to make ATP and NADPH. Then the Calvin cycle uses ATP and NADPH to fix CO2 into organic molecules..."

Generated Q&A preview (example):
- Q1: What is photosynthesis?
  - A1: Photosynthesis is the process by which plants, algae, and some bacteria convert sunlight, carbon dioxide, and water into glucose and oxygen.
- Q2: Where does photosynthesis take place?
  - A2: Photosynthesis occurs in chloroplasts.
- Q3: What are the two main stages of photosynthesis?
  - A3: The light-dependent reactions and the Calvin cycle.
- Q4: What do the light-dependent reactions produce for the Calvin cycle?
  - A4: ATP and NADPH, which the Calvin cycle uses to fix CO2 into organic molecules.

You can edit any Q/A in the preview, then commit to create four new notes (or cards) according to your templates and field mapping.

---

## Tips & prompt customization
- Keep the prompt's instruction explicit: ask the model to "Create concise question-answer pairs" and constrain the number, tone, or length.
- If your notes include code blocks or special formatting, instruct the model to preserve markdown/HTML and keep code fences intact.
- Example prompt (internal, used by the add-on; you can customize):
  "You are a helpful assistant. Given the following explanation, generate up to {N} question-and-answer pairs suitable for Anki flashcards. Each question should be concise and test a single fact or concept. Keep answers short (1–2 sentences). Output as JSON array of objects with 'question' and 'answer' fields."
- Use preview mode to verify the model follows the requested format and constraints.
- If generation quality is low, try lowering temperature or changing model.

---

## Troubleshooting

- "No API key configured" — Open the add-on config and add your provider/API key.
- "Rate limit / 429" — You hit an API rate limit. Wait, lower batch size, or upgrade your plan.
- "Model returned malformed output" — Try enabling strict JSON output in settings or lower temperature. Use preview to manually correct.
- "Media / images lost" — Ensure 'preserve formatting' is enabled. If the add-on cannot reliably extract/attach media, perform a manual check.
- "Anki crash after install" — Remove the add-on folder from `addons21` and restart Anki, then open an issue with logs.

If you encounter an error, please open an issue at the repository with:
- Anki version
- Add-on version (commit/branch)
- Steps to reproduce
- Any error messages from Anki's debug console

---

## Privacy & Security
- Data sent to AI providers may contain your note content. Treat this as potentially sensitive.
- Consider using a self-hosted or local model if your notes contain private or sensitive information.
- Do not commit API keys or personal data to the repository.
- The add-on supports configuring different endpoints; point it to a private endpoint to keep data within your environment.

---

## Development & Contributing
Contributions, bug reports, and feature requests are welcome.

- To run locally:
  1. Clone the repository.
  2. Install dependencies (if any) into Anki's Python environment or a virtual environment used for testing.
  3. Copy the add-on folder into your `addons21` and restart Anki during development to test changes.

- Suggested workflow:
  - Fork the repo.
  - Create a feature branch: `git checkout -b feat/short-qas`
  - Make changes and test in Anki.
  - Open a pull request with a clear description and screenshots if applicable.

- Please follow repository code style and include tests where appropriate.

---

## License
See the repository `LICENSE` file for license details. If no license is present, contact the author before reusing code.

---

## Support
- Report bugs and request features via GitHub Issues: [Issues · yuwayanagitani/anki-ai-splitter](https://github.com/yuwayanagitani/anki-ai-splitter/issues)
- For local setup questions, include your Anki version and a minimal reproducible example.

---

Thank you for using Anki AI Splitter! If you find it helpful, please leave a star on the GitHub repo and consider contributing improvements or translations.
