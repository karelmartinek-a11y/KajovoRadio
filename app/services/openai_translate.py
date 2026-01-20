from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TranslationResult:
    ok: bool
    text: str
    error: str = ''


def translate_text_openai(api_key: str, text: str, target_language: str, model: str = 'gpt-5.1') -> TranslationResult:
    """Translate text using OpenAI API."""

    if not api_key:
        return TranslationResult(ok=False, text='', error='OpenAI API key missing')

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)

        prompt = (
            "Translate the following message into the target language. "
            "Keep placeholders/variables unchanged. Return only the translated text.\n\n"
            f"TARGET LANGUAGE: {target_language}\n\n"
            "TEXT:\n"
            f"{text}"
        )

        resp = client.responses.create(
            model=model,
            input=prompt,
        )

        out = getattr(resp, 'output_text', '')
        if not out:
            # Defensive fallback for SDK output variations.
            try:
                out = resp.output[0].content[0].text  # type: ignore[attr-defined]
            except Exception:
                out = ''

        if not out:
            return TranslationResult(ok=False, text='', error='Empty translation response')

        return TranslationResult(ok=True, text=out)

    except Exception as e:
        return TranslationResult(ok=False, text='', error=str(e))
