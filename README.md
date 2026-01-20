# Rádio Kája Jižák (Windows Desktop, Python)

Tento projekt je realizovatelná skeleton implementace desktop aplikace pro Windows dle zadání „Rádio Kája Jižák“.

Poznámka k integracím:
- Spotify, OpenAI a Azure TTS jsou připravené jako služby; pro reálné použití je nutné doplnit API klíče v kartě **Nastavení**.
- Stream playback je připraven s volitelnou podporou `ffmpeg` (doporučeno mít `ffmpeg.exe` v PATH).

## Požadavky
- Windows 10/11
- Python 3.10+

## Instalace

V terminálu (PowerShell) v kořeni projektu:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python -m app
```

## Struktura
- `app/` – zdrojové kódy
- `app/resources/` – zdroje (logo placeholder, mini namedays)

## SAVE/LOAD
Konfigurace se ukládá jako `.json` soubor (kompletní stav – databáze prvků, playlist, plán týdne, hotkeys, nastavení).

## Audio MONO (L = R)
Playback engine je navržen jako mono výstup (jeden kanál), který je posílán identicky do L/R.
