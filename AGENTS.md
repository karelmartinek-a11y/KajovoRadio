# Repository Guidelines

## Jazyk a dokumentace
- Veškerá komunikace, dokumentace a poznámky v kódu i u placeholderů musí být výhradně v češtině; narazí-li Codex na poznámky v jiném jazyce, přeloží je do češtiny.

## Project Structure & Module Organization
- `app/main.py` and `app/__main__.py` start the desktop app (`python -m app`).
- `app/ui/` holds Qt windows, tabs, and widgets (`main_window.py`, `tabs.py`, `widgets/`).
- `app/services/` contains integrations and playback (`player.py`, `audio_metadata.py`, `openai_translate.py`, `azure_tts.py`, `storage.py`, `dsp.py`).
- `app/models/entities.py` defines data models; `app/resources/` stores bundled assets (`logo.png`, `namedays_cz_min.json`).
- Config/save data is JSON-based; keep generated config files out of version control.

## Build, Test, and Development Commands
- First-time setup (PowerShell): `python -m venv .venv`, `.\.venv\Scripts\activate`, `pip install -r requirements.txt`.
- Run the app: `python -m app` (ensure `ffmpeg.exe` is on `PATH` for stream playback).
- Lint/format: prefer `ruff` + `black` if added; otherwise follow PEP 8 manually.
- Manual smoke test: launch, open **Nastavení**, verify playback and TTS keys, load sample station/playlist.

## Coding Style & Naming Conventions
- Python 3.10+, 4-space indents, PEP 8; keep modules and functions `snake_case`, classes `PascalCase`.
- Type hints where practical; prefer `pydantic` models for structured data.
- Qt UI: keep signal/slot names descriptive (`on_<component>_<action>`); group widget styling in `ui/styles.py`.
- Keep services thin and side-effect aware; avoid coupling UI code into `services/`.

## Testing Guidelines
- No automated tests yet; target adding `tests/` with `pytest` (`pip install pytest`) and name files `test_*.py`.
- Cover: player pipeline (mono output), storage persistence, service error handling (OpenAI/Azure stubs), and UI smoke via Qt bot where possible.
- For now, run `python -m app` after changes and validate: load/save config JSON, play a sample stream, TTS prompt roundtrip, and UI tab navigation.

## Commit & Pull Request Guidelines
- There is no existing history; adopt Conventional Commits (`feat:`, `fix:`, `chore:`) with imperative subjects.
- Commit small, focused changes; include brief context in the body when touching audio/TTS behavior.
- PRs: state purpose, list manual/automated tests run, link related issue/task, and attach UI screenshots/gifs for visual changes.
- Avoid committing secrets (API keys) or generated config files; confirm `.venv/` and cache artifacts remain ignored.

## Security & Configuration Tips
- Enter API keys for OpenAI/Azure TTS via the **Nastavení** tab; do not hardcode them.
- Keep `ffmpeg.exe` on `PATH` for reliable playback; document if you ship a pinned binary.
- If adding new services, centralize IDs in `services/ids.py` and store credentials outside the repo (env vars or Windows Credential Manager).


## Kodovani A Cestina

- Vsechny textove soubory, zdrojove kody, konfigurace, prompty, dokumentace a poznamky se musi vytvaret a upravovat v `UTF-8 bez BOM`.
- Pokud uzivatel vyslovne neurci jinak, komunikace s uzivatelem musi byt v cestine.
- Dokumentace se musi psat v cestine.
- Poznamky a komentare v kodu se musi psat v cestine.
