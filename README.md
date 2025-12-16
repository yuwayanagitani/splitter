# AI Card Splitter

**AI Card Splitter** is an Anki add-on that uses AI to **automatically split a single flashcard into multiple, smaller cards**.  
It is designed to help learners avoid oversized cards and maintain an effective **spaced repetition workflow**, especially for complex subjects such as medicine, biology, and law.

---

## 🔗 AnkiWeb Page

This add-on is officially published on **AnkiWeb**:

👉 https://ankiweb.net/shared/info/728208605

Installing from AnkiWeb is recommended for the easiest setup and automatic updates.

---

## 🎯 Key Features

- Split one card into multiple cards using AI  
- Works directly from the **Reviewer screen**  
- Supports **OpenAI** and **Google Gemini** models  
- Designed for minimal UI interruption and fast workflow  
- Preserves original content while generating new notes  
- Optimized for large decks and batch learning

---

## 🚀 How It Works

1. You review a card that feels too large or overloaded.  
2. Trigger **AI Card Splitter** from the review menu.  
3. The add-on sends the card content to the AI model.  
4. AI proposes multiple smaller Q&A pairs.  
5. New cards are created automatically in Anki.

This approach follows the principle:  
**“One fact, one card.”**

---

## 📦 Installation

### ✅ From AnkiWeb (Recommended)

1. Open Anki  
2. Go to **Tools → Add-ons → Browse & Install**  
3. Search for **AI Card Splitter**  
4. Install and restart Anki

### 📁 From GitHub (Manual)

1. Download or clone this repository  
2. Place it into:  
   `Anki2/addons21/anki-ai-splitter`  
3. Restart Anki

---

## 🔑 API Key Setup

This add-on requires an API key for the selected provider.

| Provider | Environment Variable |
|--------|----------------------|
| OpenAI | `OPENAI_API_KEY` |
| Gemini | `GEMINI_API_KEY` |

Set the key via:
- System environment variables, or  
- The add-on configuration screen

---

## ⚙️ Configuration

Open:

**Tools → Add-ons → AI Card Splitter → Config**

Main options include:

- AI provider selection (OpenAI / Gemini)  
- Model name  
- Output language  
- Split aggressiveness (number / granularity of cards)  
- Handling of original card (keep / tag / modify)

---

## 🧪 Usage

### Split the current card

During review:

**More → AI Card Splitter**

The add-on analyzes the current card and generates multiple new cards automatically.

---

## ⚠️ Notes on Privacy

Card contents are sent to external AI services.  
Avoid using cards that contain sensitive or personal information unless you understand the provider’s data policy.

---

## 🛠 Troubleshooting

| Problem | Solution |
|-------|----------|
| No card selected | Run from the Reviewer screen |
| API error | Check API key and network |
| Unexpected splits | Adjust split settings or model |
| Nothing happens | Confirm the add-on is enabled |

---

## 📜 License

MIT License

---

## 🔧 Related Add-ons

- **AI Card Explainer** – Generate explanations for cards  
- **AI Card Translator** – Translate cards during review  

These add-ons are designed to work together as a modular AI-powered Anki ecosystem.
