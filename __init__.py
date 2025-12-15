from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from anki.notes import Note
from aqt import gui_hooks, mw
from aqt.qt import (
    QAction,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QEventLoop,
    QFormLayout,
    QGroupBox,
    QLineEdit,
    QMessageBox,
    QComboBox,
    QInputDialog,
    QSpinBox,
    QVBoxLayout,
    QScrollArea,
    QWidget,
)
from aqt.browser import Browser


# --- Qt Network imports (prefer aqt.qt, fall back to PyQt6/PyQt5) ---
try:
    # Some Anki builds may re-export these from aqt.qt
    from aqt.qt import QNetworkAccessManager, QNetworkRequest, QUrl  # type: ignore
except Exception:
    try:
        # Anki 25.x Qt6 (PyQt6)
        from PyQt6.QtCore import QUrl  # type: ignore
        from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest  # type: ignore
    except Exception:
        try:
            # Older Qt5
            from PyQt5.QtCore import QUrl  # type: ignore
            from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest  # type: ignore
        except Exception:
            QNetworkAccessManager = None  # type: ignore
            QNetworkRequest = None  # type: ignore
            QUrl = None  # type: ignore


# =============================================================================
# UI text (English)
# =============================================================================

ADDON_NAME = "AI Card Divider"
MENU_ACTION = "AI Card Divider: Split Long Answers..."
DIALOG_QUERY_TITLE = "AI Card Divider"
DIALOG_QUERY_PROMPT = (
    "Enter the search query for the notes you want to process.\n"
    "Example: deck:Internal tag:med"
)
MSG_NO_NOTES_TITLE = "No Notes Found"
MSG_NO_NOTES_BODY = "No notes matched the given search query."
MSG_NO_LONG_TITLE = "No Long Answers"
MSG_CONFIRM_TITLE = "Confirm"
MSG_DONE_TITLE = ADDON_NAME

PROGRESS_TITLE = "Splitting long answers with AI..."
PROGRESS_STEP_FMT = "Processing note {idx}/{total}..."


def show_error_dialog(msg: str) -> None:
    QMessageBox.critical(mw, f"{ADDON_NAME} - Error", msg)


# =============================================================================
# Config (numbered keys for a neat config.json order)
# =============================================================================
#
# Goal:
# - Keep the add-on behavior unchanged
# - Make config.json visually ordered by using numbered keys (01_, 02_, ...)
# - Backward compatible: accept BOTH numbered keys and the old unnumbered keys
#
# Canonical (internal) keys used by the code:
#   question_field, answer_field, max_answer_chars, output_language, max_cards,
#   provider, openai_model, openai_api_key_env, openai_api_base,
#   gemini_model, gemini_api_key_env, gemini_api_base,
#   temperature, max_output_tokens, tag_for_new, tag_for_original
#

_CONFIG_ITEMS = [
    # (canonical_key, numbered_key, default_value, legacy_keys[])
    ("question_field", "01_question_field", "Front", []),
    ("answer_field", "02_answer_field", "Back", []),
    ("max_answer_chars", "03_max_answer_chars", 220, []),
    ("output_language", "04_output_language", "English", []),
    ("max_cards", "05_max_cards", 5, []),

    ("provider", "06_provider", "openai", []),

    # OpenAI (legacy keys are supported: model/api_key_env/api_base)
    ("openai_model", "07_openai_model", "gpt-4o-mini", ["model"]),
    ("openai_api_key_env", "08_openai_api_key_env", "OPENAI_API_KEY", ["api_key_env"]),
    ("openai_api_base", "09_openai_api_base", "https://api.openai.com/v1/chat/completions", ["api_base"]),

    # Gemini (legacy keys can also be used: model/api_key_env/api_base)
    ("gemini_model", "10_gemini_model", "gemini-2.5-flash", ["model"]),
    ("gemini_api_key_env", "11_gemini_api_key_env", "GEMINI_API_KEY", ["api_key_env"]),
    ("gemini_api_base", "12_gemini_api_base", "https://generativelanguage.googleapis.com/v1beta", ["api_base"]),

    ("temperature", "13_temperature", 0.2, []),
    ("max_output_tokens", "14_max_output_tokens", 500, []),

    ("tag_for_new", "15_tag_for_new", "SplitFromLong", []),
    ("tag_for_original", "16_tag_for_original", "LongAnswerSplitSource", []),
]

DEFAULT_CONFIG_NUMBERED: Dict[str, Any] = {num_key: default for (_, num_key, default, __) in _CONFIG_ITEMS}


# =============================================================================
# Custom config GUI (opened from Tools → Add-ons → Config)
# =============================================================================


def _strip_legacy_keys(conf: Dict[str, Any]) -> Dict[str, Any]:
    """
    Keep unknown keys, but remove canonical keys and legacy OpenAI/Gemini generic keys
    to avoid duplicates in config.json.
    """
    drop = set()
    for canonical, numbered, _default, legacy in _CONFIG_ITEMS:
        drop.add(canonical)
        for lk in legacy:
            drop.add(lk)  # e.g. model/api_key_env/api_base
    # legacy keys that could exist outside the table (extra safety)
    drop |= {"model", "api_key_env", "api_base"}

    cleaned = dict(conf)
    for k in list(cleaned.keys()):
        if k in drop:
            cleaned.pop(k, None)
    return cleaned


def _write_numbered_config(values_by_numbered_key: Dict[str, Any]) -> None:
    raw = mw.addonManager.getConfig(__name__) or {}
    raw = _strip_legacy_keys(raw)
    raw.update(values_by_numbered_key)
    mw.addonManager.writeConfig(__name__, raw)


class NoWheelSpinBox(QSpinBox):
    def wheelEvent(self, event):
        event.ignore()  # 数値を変えない（親のスクロールに回る）


class NoWheelDoubleSpinBox(QDoubleSpinBox):
    def wheelEvent(self, event):
        event.ignore()

class NoWheelComboBox(QComboBox):
    def wheelEvent(self, event):
        event.ignore()


class ConfigDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"{ADDON_NAME} - Settings")
        self.setMinimumWidth(720)  # 必要なら後で下げてもOK

        conf = get_config()  # canonical view

        # --- Dialog root ---
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        # --- Scroll area (content only) ---
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)

        content = QWidget(scroll)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(12)

        scroll.setWidget(content)
        root.addWidget(scroll, 1)

        # --- General ---
        box_general = QGroupBox("General")
        form_general = QFormLayout(box_general)
        form_general.setVerticalSpacing(10)
        form_general.setHorizontalSpacing(14)

        self.question_field = QLineEdit(str(conf.get("question_field", "Front")))
        self.answer_field = QLineEdit(str(conf.get("answer_field", "Back")))

        self.max_answer_chars = NoWheelSpinBox()
        self.max_answer_chars.setRange(1, 200000)
        self.max_answer_chars.setValue(int(conf.get("max_answer_chars", 220)))

        self.output_language = NoWheelComboBox()
        self.output_language.setEditable(True)
        self.output_language.addItems(["English", "Japanese"])
        self.output_language.setCurrentText(str(conf.get("output_language", "English")))

        self.max_cards = NoWheelSpinBox()
        self.max_cards.setRange(1, 50)
        self.max_cards.setValue(int(conf.get("max_cards", 5)))

        form_general.addRow("Question field", self.question_field)
        form_general.addRow("Answer field", self.answer_field)
        form_general.addRow("Max answer chars", self.max_answer_chars)
        form_general.addRow("Output language", self.output_language)
        form_general.addRow("Max cards", self.max_cards)
        content_layout.addWidget(box_general)

        # --- Provider ---
        box_provider = QGroupBox("Provider")
        form_provider = QFormLayout(box_provider)
        form_provider.setVerticalSpacing(10)
        form_provider.setHorizontalSpacing(14)

        self.provider = NoWheelComboBox()
        self.provider.addItems(["openai", "gemini"])
        self.provider.setCurrentText(str(conf.get("provider", "openai")).lower())
        form_provider.addRow("Provider", self.provider)
        content_layout.addWidget(box_provider)

        # --- OpenAI ---
        box_openai = QGroupBox("OpenAI")
        form_openai = QFormLayout(box_openai)
        form_openai.setVerticalSpacing(10)
        form_openai.setHorizontalSpacing(14)

        self.openai_model = QLineEdit(str(conf.get("openai_model", "gpt-4o-mini")))
        self.openai_api_key_env = QLineEdit(str(conf.get("openai_api_key_env", "OPENAI_API_KEY")))
        self.openai_api_base = QLineEdit(str(conf.get("openai_api_base", "https://api.openai.com/v1/chat/completions")))

        form_openai.addRow("Model", self.openai_model)
        form_openai.addRow("API key env", self.openai_api_key_env)
        form_openai.addRow("API base", self.openai_api_base)
        content_layout.addWidget(box_openai)

        # --- Gemini ---
        box_gemini = QGroupBox("Gemini")
        form_gemini = QFormLayout(box_gemini)
        form_gemini.setVerticalSpacing(10)
        form_gemini.setHorizontalSpacing(14)

        self.gemini_model = QLineEdit(str(conf.get("gemini_model", "gemini-2.5-flash")))
        self.gemini_api_key_env = QLineEdit(str(conf.get("gemini_api_key_env", "GEMINI_API_KEY")))
        self.gemini_api_base = QLineEdit(str(conf.get("gemini_api_base", "https://generativelanguage.googleapis.com/v1beta")))

        form_gemini.addRow("Model", self.gemini_model)
        form_gemini.addRow("API key env", self.gemini_api_key_env)
        form_gemini.addRow("API base", self.gemini_api_base)
        content_layout.addWidget(box_gemini)

        # --- Generation ---
        box_gen = QGroupBox("Generation")
        form_gen = QFormLayout(box_gen)
        form_gen.setVerticalSpacing(10)
        form_gen.setHorizontalSpacing(14)

        self.temperature = NoWheelDoubleSpinBox()
        self.temperature.setRange(0.0, 2.0)
        self.temperature.setSingleStep(0.05)
        self.temperature.setValue(float(conf.get("temperature", 0.2)))

        self.max_output_tokens = NoWheelSpinBox()
        self.max_output_tokens.setRange(1, 200000)
        self.max_output_tokens.setValue(int(conf.get("max_output_tokens", 500)))

        form_gen.addRow("Temperature", self.temperature)
        form_gen.addRow("Max output tokens", self.max_output_tokens)
        content_layout.addWidget(box_gen)

        # --- Tags ---
        box_tags = QGroupBox("Tags")
        form_tags = QFormLayout(box_tags)
        form_tags.setVerticalSpacing(10)
        form_tags.setHorizontalSpacing(14)

        self.tag_for_new = QLineEdit(str(conf.get("tag_for_new", "SplitFromLong")))
        self.tag_for_original = QLineEdit(str(conf.get("tag_for_original", "LongAnswerSplitSource")))
        form_tags.addRow("Tag for new notes", self.tag_for_new)
        form_tags.addRow("Tag for original note", self.tag_for_original)
        content_layout.addWidget(box_tags)

        # --- Buttons (fixed, not inside scroll) ---
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.btn_reset = btns.addButton("Reset to defaults", QDialogButtonBox.ButtonRole.ResetRole)
        btns.accepted.connect(self._on_save)
        btns.rejected.connect(self.reject)
        self.btn_reset.clicked.connect(self._on_reset)

        root.addWidget(btns)

        # Enable/disable blocks based on provider (nice UX)
        self.provider.currentTextChanged.connect(self._refresh_provider_state)
        self._refresh_provider_state(self.provider.currentText())

    def _refresh_provider_state(self, provider: str) -> None:
        p = (provider or "").strip().lower()
        is_openai = p != "gemini"
        # Keep both visible, but disable the inactive one for clarity.
        self.openai_model.setEnabled(is_openai)
        self.openai_api_key_env.setEnabled(is_openai)
        self.openai_api_base.setEnabled(is_openai)

        self.gemini_model.setEnabled(not is_openai)
        self.gemini_api_key_env.setEnabled(not is_openai)
        self.gemini_api_base.setEnabled(not is_openai)

    def _on_reset(self) -> None:
        defaults = {num_key: default for (_c, num_key, default, _legacy) in _CONFIG_ITEMS}
        # General
        self.question_field.setText(str(defaults["01_question_field"]))
        self.answer_field.setText(str(defaults["02_answer_field"]))
        self.max_answer_chars.setValue(int(defaults["03_max_answer_chars"]))
        self.output_language.setCurrentText(str(defaults["04_output_language"]))
        self.max_cards.setValue(int(defaults["05_max_cards"]))
        # Provider
        self.provider.setCurrentText(str(defaults["06_provider"]))
        # OpenAI
        self.openai_model.setText(str(defaults["07_openai_model"]))
        self.openai_api_key_env.setText(str(defaults["08_openai_api_key_env"]))
        self.openai_api_base.setText(str(defaults["09_openai_api_base"]))
        # Gemini
        self.gemini_model.setText(str(defaults["10_gemini_model"]))
        self.gemini_api_key_env.setText(str(defaults["11_gemini_api_key_env"]))
        self.gemini_api_base.setText(str(defaults["12_gemini_api_base"]))
        # Generation
        self.temperature.setValue(float(defaults["13_temperature"]))
        self.max_output_tokens.setValue(int(defaults["14_max_output_tokens"]))
        # Tags
        self.tag_for_new.setText(str(defaults["15_tag_for_new"]))
        self.tag_for_original.setText(str(defaults["16_tag_for_original"]))

    def _on_save(self) -> None:
        out: Dict[str, Any] = {
            "01_question_field": self.question_field.text().strip() or "Front",
            "02_answer_field": self.answer_field.text().strip() or "Back",
            "03_max_answer_chars": int(self.max_answer_chars.value()),
            "04_output_language": (self.output_language.currentText().strip() or "English"),
            "05_max_cards": int(self.max_cards.value()),
            "06_provider": (self.provider.currentText().strip().lower() or "openai"),

            "07_openai_model": self.openai_model.text().strip() or "gpt-4o-mini",
            "08_openai_api_key_env": self.openai_api_key_env.text().strip() or "OPENAI_API_KEY",
            "09_openai_api_base": self.openai_api_base.text().strip() or "https://api.openai.com/v1/chat/completions",

            "10_gemini_model": self.gemini_model.text().strip() or "gemini-2.5-flash",
            "11_gemini_api_key_env": self.gemini_api_key_env.text().strip() or "GEMINI_API_KEY",
            "12_gemini_api_base": self.gemini_api_base.text().strip() or "https://generativelanguage.googleapis.com/v1beta",

            "13_temperature": float(self.temperature.value()),
            "14_max_output_tokens": int(self.max_output_tokens.value()),

            "15_tag_for_new": self.tag_for_new.text().strip() or "SplitFromLong",
            "16_tag_for_original": self.tag_for_original.text().strip() or "LongAnswerSplitSource",
        }

        _write_numbered_config(out)
        QMessageBox.information(self, ADDON_NAME, "Settings saved.")
        self.accept()


def open_addon_config_gui() -> None:
    dlg = ConfigDialog(mw)
    dlg.exec()



def _resolve_conf_value(
    raw: Dict[str, Any],
    canonical_key: str,
    numbered_key: str,
    default_value: Any,
    legacy_keys: List[str],
) -> Any:
    if numbered_key in raw:
        return raw[numbered_key]
    if canonical_key in raw:
        return raw[canonical_key]
    for lk in legacy_keys:
        if lk in raw:
            return raw[lk]
    return default_value


def get_config() -> Dict[str, Any]:
    """
    Load config.json and return a dict with canonical keys guaranteed.

    - Accepts numbered keys (01_...) for nicer ordering in config.json
    - Accepts old unnumbered keys (question_field, ...)
    - Accepts legacy OpenAI/Gemini keys (model/api_key_env/api_base)
    """
    raw = mw.addonManager.getConfig(__name__) or {}

    # Create a canonicalized view (but keep any unknown keys as-is for future-proofing)
    merged: Dict[str, Any] = dict(raw)

    for canonical, numbered, default, legacy in _CONFIG_ITEMS:
        merged[canonical] = _resolve_conf_value(raw, canonical, numbered, default, legacy)

    return merged


def save_config(conf: Dict[str, Any]) -> None:
    """
    Save config back to config.json.

    Note: This function is kept for future use; the add-on currently does not
    auto-write config. If you choose to write, prefer numbered keys.
    """
    mw.addonManager.writeConfig(__name__, conf)


# =============================================================================
# Models
# =============================================================================

@dataclass
class SplitCard:
    question: str
    answer: str


# =============================================================================
# HTTP helpers
# =============================================================================

def _extract_json_from_text(text: str) -> str:
    """
    Extract a JSON object substring from model output.

    Why this exists:
    - Some providers occasionally wrap JSON in Markdown code fences (```json ...).
    - Sometimes the closing fence is missing/truncated.
    - We therefore:
      1) strip a leading fence line if present (even if no closing fence),
      2) then extract the first balanced {...} JSON object, being string-aware.
    """
    text = (text or "").strip()

    # Strip a leading Markdown code fence (even if the closing fence is missing).
    if text.startswith("```"):
        lines = text.splitlines()
        if lines:
            # Drop opening fence line (``` or ```json)
            lines = lines[1:]
            # Drop closing fence line if present
            if lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines).strip()

    # Find and extract the first balanced JSON object.
    start = text.find("{")
    if start == -1:
        return text

    in_str = False
    esc = False
    depth = 0
    obj_start = -1

    for i in range(start, len(text)):
        ch = text[i]

        if in_str:
            if esc:
                esc = False
                continue
            if ch == "\\":  # escape in string
                esc = True
                continue
            if ch == '"':
                in_str = False
            continue

        # not in string
        if ch == '"':
            in_str = True
            continue
        if ch == "{":
            if depth == 0:
                obj_start = i
            depth += 1
            continue
        if ch == "}":
            if depth > 0:
                depth -= 1
                if depth == 0 and obj_start != -1:
                    return text[obj_start : i + 1]

    # If we get here, braces were not balanced (likely truncation). Best-effort fallback:
    end = text.rfind("}")
    if obj_start != -1 and end > obj_start:
        return text[obj_start : end + 1]
    return text


def _post_json(url: str, headers: Dict[str, str], data_bytes: bytes, prefer_qt: bool = True) -> bytes:
    """POST JSON to `url` and return raw response bytes."""
    if prefer_qt and QNetworkAccessManager is not None and QNetworkRequest is not None and QUrl is not None:
        manager = QNetworkAccessManager(mw)
        req = QNetworkRequest(QUrl(url))
        for key, value in headers.items():
            req.setRawHeader(key.encode("utf-8"), value.encode("utf-8"))

        reply = manager.post(req, data_bytes)
        loop = QEventLoop()

        def on_finished() -> None:
            loop.quit()

        reply.finished.connect(on_finished)
        loop.exec()

        resp_bytes = bytes(reply.readAll())

        if reply.error() and not resp_bytes:
            raise RuntimeError(f"Network error (Qt): {reply.errorString()}")

        return resp_bytes

    req = urllib.request.Request(url, data=data_bytes, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.read()
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "ignore")
        raise RuntimeError(f"HTTP error (urllib): {e.code}\n{detail}") from None
    except urllib.error.URLError as e:
        raise RuntimeError(f"Connection failed (urllib): {e}") from None
    except Exception as e:
        raise RuntimeError(f"Unexpected error (urllib): {e}") from None


def _get_env_key(env_name: str) -> str:
    key = os.environ.get(env_name, "").strip()
    if not key:
        raise RuntimeError(f"API key is missing. Please set environment variable '{env_name}'.")
    return key


def _provider(config: Dict[str, Any]) -> str:
    p = str(config.get("provider", "openai") or "openai").strip().lower()
    return "gemini" if p == "gemini" else "openai"


def _get_openai_settings(config: Dict[str, Any]) -> tuple[str, str, str]:
    # legacy keys: model/api_key_env/api_base (still supported)
    model = str(config.get("openai_model") or config.get("model") or "gpt-4o-mini")
    api_key_env = str(config.get("openai_api_key_env") or config.get("api_key_env") or "OPENAI_API_KEY")
    api_base = str(config.get("openai_api_base") or config.get("api_base") or "https://api.openai.com/v1/chat/completions")
    return model, api_key_env, api_base


def _get_gemini_settings(config: Dict[str, Any]) -> tuple[str, str, str]:
    # legacy keys: model/api_key_env/api_base (still supported)
    model = str(config.get("gemini_model") or config.get("model") or "gemini-2.5-flash")
    api_key_env = str(config.get("gemini_api_key_env") or config.get("api_key_env") or "GEMINI_API_KEY")
    api_base = str(config.get("gemini_api_base") or config.get("api_base") or "https://generativelanguage.googleapis.com/v1beta")
    return model, api_key_env, api_base


def _build_gemini_generatecontent_url(api_base: str, model: str) -> str:
    """Default: https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"""
    api_base = api_base.strip()
    if "{model}" in api_base:
        return api_base.format(model=model)

    if api_base.endswith("/"):
        api_base = api_base[:-1]

    if api_base.endswith("/models"):
        return f"{api_base}/{model}:generateContent"

    return f"{api_base}/models/{model}:generateContent"


def _parse_split_cards_from_text(content: str) -> List[SplitCard]:
    if not content:
        raise RuntimeError("Model response was empty.")

    text = _extract_json_from_text(content)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse JSON in model response: {e}\ncontent={content[:500]!r}") from None

    cards_data = data.get("cards")
    if not isinstance(cards_data, list) or not cards_data:
        raise RuntimeError("Model response does not contain a non-empty 'cards' list.")

    result: List[SplitCard] = []
    for c in cards_data:
        if not isinstance(c, dict):
            continue
        q = str(c.get("question") or "").strip()
        a = str(c.get("answer") or "").strip()
        if not q or not a:
            continue
        result.append(SplitCard(question=q, answer=a))

    if not result:
        raise RuntimeError("No valid cards were produced from the model response.")

    return result


# =============================================================================
# Providers
# =============================================================================

def call_openai_to_split(question: str, answer: str, config: Dict[str, Any]) -> List[SplitCard]:
    model, api_key_env, api_base = _get_openai_settings(config)
    api_key = _get_env_key(api_key_env)

    output_lang = str(config.get("output_language", "English"))
    max_cards = int(config.get("max_cards", 5))
    temperature = float(config.get("temperature", 0.2))
    max_tokens = int(config.get("max_output_tokens", 500))

    system_prompt = (
        "You split one long flashcard into several shorter Q&A cards for Anki. "
        "Always respond with a single valid JSON object only."
    )

    user_prompt = f"""
Split the following flashcard into several smaller Q&A cards.

Language:
- Write both questions and answers in {output_lang}.

Rules:
- Create at most {max_cards} cards.
- Each answer should be concise: about 1–3 sentences.
- No bullet lists, no markdown, no HTML tags; plain text only.
- Keep important technical details (especially medical), but avoid long prose.
- Some overlap between cards is OK.

Return ONLY one JSON object in this format (no extra text):

{{
  "cards": [
    {{"question": "…", "answer": "…"}},
    ...
  ]
}}

Original question:
{question}

Original answer:
{answer}
""".strip()

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    data_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}

    resp_bytes = _post_json(api_base, headers, data_bytes, prefer_qt=True)

    try:
        resp_data = json.loads(resp_bytes.decode("utf-8"))
        content = resp_data["choices"][0]["message"]["content"]
    except Exception as e:
        raise RuntimeError(f"Failed to parse OpenAI response JSON: {e}\nraw={resp_bytes[:500]!r}") from None

    return _parse_split_cards_from_text(content)


def call_gemini_to_split(question: str, answer: str, config: Dict[str, Any]) -> List[SplitCard]:
    model, api_key_env, api_base = _get_gemini_settings(config)
    api_key = _get_env_key(api_key_env)

    url = _build_gemini_generatecontent_url(api_base, model)

    output_lang = str(config.get("output_language", "English"))
    max_cards = int(config.get("max_cards", 5))
    temperature = float(config.get("temperature", 0.2))
    max_output_tokens = int(config.get("max_output_tokens", 500))

    prompt = f"""
You split one long flashcard into several shorter Q&A cards for Anki.
Always respond with a single valid JSON object only.

Split the following flashcard into several smaller Q&A cards.

Language:
- Write both questions and answers in {output_lang}.

Rules:
- Create at most {max_cards} cards.
- Each answer should be concise: about 1–3 sentences.
- No bullet lists, no markdown, no HTML tags; plain text only.
- Keep important technical details (especially medical), but avoid long prose.
- Some overlap between cards is OK.

Return ONLY one JSON object in this format (no extra text):

{{
  "cards": [
    {{"question": "…", "answer": "…"}},
    ...
  ]
}}

Original question:
{question}

Original answer:
{answer}
""".strip()

    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": temperature, "maxOutputTokens": max_output_tokens, "responseMimeType": "application/json"},
    }

    data_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {"Content-Type": "application/json", "x-goog-api-key": api_key}

    resp_bytes = _post_json(url, headers, data_bytes, prefer_qt=True)

    try:
        resp_data = json.loads(resp_bytes.decode("utf-8"))
    except Exception as e:
        raise RuntimeError(f"Failed to parse Gemini response JSON: {e}\nraw={resp_bytes[:500]!r}") from None

    try:
        candidates = resp_data.get("candidates") or []
        if not candidates:
            raise RuntimeError(f"No candidates in response. raw={resp_data!r}")

        content_obj = candidates[0].get("content") or {}
        parts = content_obj.get("parts") or []
        if not parts:
            raise RuntimeError(f"No content.parts in response. raw={resp_data!r}")

        texts: List[str] = []
        for p in parts:
            t = p.get("text")
            if isinstance(t, str) and t.strip():
                texts.append(t)
        content_text = "\n".join(texts).strip()
        if not content_text:
            raise RuntimeError(f"Empty text in response parts. raw={resp_data!r}")
    except Exception as e:
        raise RuntimeError(f"Failed to extract text from Gemini response: {e}") from None

    return _parse_split_cards_from_text(content_text)


def call_llm_to_split(question: str, answer: str, config: Dict[str, Any]) -> List[SplitCard]:
    if _provider(config) == "gemini":
        return call_gemini_to_split(question=question, answer=answer, config=config)
    return call_openai_to_split(question=question, answer=answer, config=config)


# =============================================================================
# Main flow (unchanged behavior)
# =============================================================================

def split_long_answers_for_query() -> None:
    config = get_config()

    default_query = "deck:current"
    query, ok = QInputDialog.getText(
        mw,
        DIALOG_QUERY_TITLE,
        DIALOG_QUERY_PROMPT,
        text=default_query,
    )
    if not ok or not query.strip():
        return

    note_ids = mw.col.find_notes(query.strip())
    if not note_ids:
        QMessageBox.information(mw, MSG_NO_NOTES_TITLE, MSG_NO_NOTES_BODY)
        return

    q_field = str(config["question_field"])
    a_field = str(config["answer_field"])
    max_len = int(config["max_answer_chars"])
    tag_new = str(config["tag_for_new"])
    tag_orig = str(config["tag_for_original"])

    skip_tags = {tag_new, tag_orig}

    long_notes: List[int] = []
    for nid in note_ids:
        note = mw.col.get_note(nid)
        if note is None:
            continue

        if set(note.tags) & skip_tags:
            continue

        if q_field not in note or a_field not in note:
            continue

        if len(note[a_field]) > max_len:
            long_notes.append(nid)

    if not long_notes:
        QMessageBox.information(
            mw,
            MSG_NO_LONG_TITLE,
            f"No notes had an answer longer than {max_len} characters in field '{a_field}'.",
        )
        return

    if (
        QMessageBox.question(
            mw,
            MSG_CONFIRM_TITLE,
            f"Found {len(long_notes)} notes with long answers.\n\n"
            "Proceed to create new split cards from these notes using AI?\n\n"
            "The original notes will NOT be deleted; a tag will be added to them.",
        )
        != QMessageBox.StandardButton.Yes
    ):
        return

    created_count = 0
    error_count = 0

    mw.progress.start(max=len(long_notes), label=PROGRESS_TITLE)

    try:
        for idx, nid in enumerate(long_notes, 1):
            mw.progress.update(label=PROGRESS_STEP_FMT.format(idx=idx, total=len(long_notes)), value=idx)

            note = mw.col.get_note(nid)
            if note is None:
                continue

            if q_field not in note or a_field not in note:
                continue

            question_text = note[q_field]
            answer_text = note[a_field]

            try:
                split_cards = call_llm_to_split(question=question_text, answer=answer_text, config=config)
            except Exception as e:
                error_count += 1
                show_error_dialog(
                    f"Error while splitting note {nid}:\n\n{str(e)}\n\nQuestion:\n{question_text[:200]}..."
                )
                continue

            notetype = note.note_type()
            cards = note.cards()
            deck_id = cards[0].did if cards else mw.col.decks.get_current_id()

            for sc in split_cards:
                new_note: Note = mw.col.new_note(notetype)

                # Copy all fields first
                for i, val in enumerate(note.fields):
                    if i < len(new_note.fields):
                        new_note.fields[i] = val

                new_note[q_field] = sc.question
                new_note[a_field] = sc.answer

                new_tags = set(note.tags)
                new_tags.add(tag_new)
                new_tags.add(f"{tag_new}_{nid}")
                new_note.tags = list(new_tags)

                mw.col.add_note(new_note, deck_id)
                created_count += 1

            # Tag the original note (for re-run prevention)
            orig_tags = set(note.tags)
            orig_tags.add(tag_orig)
            note.tags = list(orig_tags)
            note.flush()

    finally:
        mw.progress.finish()

    mw.col.save()
    mw.reset()

    msg = "Finished splitting long-answer cards.\n\n" f"New notes created: {created_count}"
    if error_count:
        msg += f"\nNotes failed: {error_count} (see error dialogs for details)."

    QMessageBox.information(mw, MSG_DONE_TITLE, msg)


def on_profile_did_open() -> None:
    # Register custom Config dialog (Tools → Add-ons → Config)
    # This does NOT add buttons to the Tools menu.
    if hasattr(mw.addonManager, "setConfigAction"):
        try:
            mw.addonManager.setConfigAction(__name__, open_addon_config_gui)
        except Exception:
            # If something unexpected happens, we simply skip custom config action.
            pass

def add_tools_menu_action() -> None:
    action = QAction(MENU_ACTION, mw)
    action.triggered.connect(split_long_answers_for_query)
    mw.form.menuTools.addAction(action)

def split_selected_notes_in_browser(browser: Browser) -> None:
    config = get_config()

    note_ids = browser.selectedNotes()
    if not note_ids:
        QMessageBox.information(
            browser,
            ADDON_NAME,
            "No notes selected.",
        )
        return

    q_field = str(config["question_field"])
    a_field = str(config["answer_field"])
    max_len = int(config["max_answer_chars"])
    tag_new = str(config["tag_for_new"])
    tag_orig = str(config["tag_for_original"])

    skip_tags = {tag_new, tag_orig}

    target_notes: List[int] = []

    for nid in note_ids:
        note = mw.col.get_note(nid)
        if note is None:
            continue
        if set(note.tags) & skip_tags:
            continue
        if q_field not in note or a_field not in note:
            continue
        if len(note[a_field]) > max_len:
            target_notes.append(nid)

    if not target_notes:
        QMessageBox.information(
            browser,
            ADDON_NAME,
            f"No selected notes had an answer longer than {max_len} characters.",
        )
        return

    if (
        QMessageBox.question(
            browser,
            "Confirm",
            f"{len(target_notes)} selected notes will be split using AI.\n\nProceed?",
        )
        != QMessageBox.StandardButton.Yes
    ):
        return

    created_count = 0
    error_count = 0

    mw.progress.start(
        max=len(target_notes),
        label="Splitting selected notes with AI...",
    )

    try:
        for i, nid in enumerate(target_notes, 1):
            mw.progress.update(
                label=f"Processing note {i}/{len(target_notes)}...",
                value=i,
            )

            note = mw.col.get_note(nid)
            if note is None:
                continue

            try:
                split_cards = call_llm_to_split(
                    question=note[q_field],
                    answer=note[a_field],
                    config=config,
                )
            except Exception as e:
                error_count += 1
                show_error_dialog(
                    f"Error while splitting note {nid}:\n\n{str(e)}"
                )
                continue

            notetype = note.note_type()
            cards = note.cards()
            deck_id = cards[0].did if cards else mw.col.decks.get_current_id()

            for sc in split_cards:
                new_note: Note = mw.col.new_note(notetype)

                # copy all fields
                for idx, val in enumerate(note.fields):
                    if idx < len(new_note.fields):
                        new_note.fields[idx] = val

                new_note[q_field] = sc.question
                new_note[a_field] = sc.answer

                new_tags = set(note.tags)
                new_tags.add(tag_new)
                new_tags.add(f"{tag_new}_{nid}")
                new_note.tags = list(new_tags)

                mw.col.add_note(new_note, deck_id)
                created_count += 1

            note.tags = list(set(note.tags) | {tag_orig})
            note.flush()

    finally:
        mw.progress.finish()

    mw.col.save()
    mw.reset()

    QMessageBox.information(
        browser,
        ADDON_NAME,
        f"Finished splitting selected notes.\n\n"
        f"New notes created: {created_count}\n"
        f"Errors: {error_count}",
    )


def on_browser_context_menu(browser: Browser, menu) -> None:
    action = QAction("Split selected notes with AI", browser)
    action.triggered.connect(
        lambda: split_selected_notes_in_browser(browser)
    )
    menu.addAction(action)


gui_hooks.browser_will_show_context_menu.append(on_browser_context_menu)

gui_hooks.profile_did_open.append(lambda: add_tools_menu_action())

gui_hooks.profile_did_open.append(on_profile_did_open)
