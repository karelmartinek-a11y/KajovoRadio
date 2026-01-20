from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class TTSResult:
    ok: bool
    wav_path: str
    error: str = ''


def synthesize_to_wav(azure_key: str, azure_region: str, text: str, voice: str, out_wav_path: str) -> TTSResult:
    """Synthesize speech via Azure TTS into a WAV file."""
    if not azure_key or not azure_region:
        return TTSResult(ok=False, wav_path='', error='Azure TTS credentials missing')

    try:
        import azure.cognitiveservices.speech as speechsdk

        speech_config = speechsdk.SpeechConfig(subscription=azure_key, region=azure_region)
        speech_config.speech_synthesis_voice_name = voice

        audio_config = speechsdk.audio.AudioOutputConfig(filename=out_wav_path)
        synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

        result = synthesizer.speak_text_async(text).get()
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            return TTSResult(ok=True, wav_path=out_wav_path)
        return TTSResult(ok=False, wav_path='', error=str(result.reason))

    except Exception as e:
        return TTSResult(ok=False, wav_path='', error=str(e))
