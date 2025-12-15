# Anki AI Splitter

AnkiWeb: https://ankiweb.net/shared/by-author/2117859718

Long “wall-of-text” answers are hard to review. This add-on uses an AI model to split one long Anki card into multiple shorter Q&A cards while keeping your original note intact.

## Features
- AI-powered splitting of long answers into smaller Q&A items
- Preview splits before applying
- Keeps original note as-is and creates new child cards/notes
- Configurable prompts and split granularity

## Requirements
- An API key for an AI provider (OpenAI, Gemini, or other supported provider)
- Internet connection for AI requests

## Installation
1. Tools → Add-ons → Open Add-ons Folder.
2. Copy the add-on folder into the add-ons directory.
3. Restart Anki.

## Usage
- Select a note → Tools → AI Splitter → Preview split.
- Review suggested cards and accept to create them.

## Configuration
Edit `config.json`:
- provider (e.g., "openai" or "gemini")
- api_key (store securely; follow provider guidance)
- max_chunk_length, prompt template, target fields

Example:
```json
{
  "provider": "openai",
  "model": "gpt-4o-mini",
  "prompt_template": "Split this answer into multiple question–answer pairs..."
}
```

## Privacy & Safety
Card content is sent to the selected AI provider. Do not send private or sensitive data unless you accept provider terms.

## Issues & Support
Please include Anki version, add-on version, and an example note when filing bugs.

## License
See LICENSE.
