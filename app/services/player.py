from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Callable

import numpy as np
import sounddevice as sd
import soundfile as sf

from app.services.dsp import apply_boost_chain, rms, peak


@dataclass
class MeterState:
    rms: float = 0.0
    peak: float = 0.0


class AudioPlayer:
    """Mono (L=R) software player.

    - Plays local files using soundfile -> float32 mono.
    - Provides meters (RMS/peak) for the 'eye' indicator.
    - BOOST is a lightweight DSP chain.

    Stream playback is intentionally stubbed; see TODO in play_stream().
    """

    def __init__(self, sample_rate: int = 48000, blocksize: int = 1024):
        self.sample_rate = sample_rate
        self.blocksize = blocksize

        self._lock = threading.RLock()
        self._stop_flag = threading.Event()
        self._pause_flag = threading.Event()

        self._thread: Optional[threading.Thread] = None
        self._current_label: str = ''

        self.volume = 0.8
        self.mute = False
        self.boost = False

        self.meter = MeterState()
        self.on_track_end: Optional[Callable[[], None]] = None

    @property
    def is_playing(self) -> bool:
        t = self._thread
        return t is not None and t.is_alive() and not self._pause_flag.is_set()

    @property
    def is_running(self) -> bool:
        t = self._thread
        return t is not None and t.is_alive()

    @property
    def current_label(self) -> str:
        with self._lock:
            return self._current_label

    def stop(self) -> None:
        self._stop_flag.set()
        self._pause_flag.clear()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self._thread = None
        with self._lock:
            self._current_label = ''
        self.meter = MeterState()

    def pause(self) -> None:
        self._pause_flag.set()

    def resume(self) -> None:
        self._pause_flag.clear()

    def set_volume(self, v: float) -> None:
        self.volume = float(max(0.0, min(1.0, v)))

    def set_mute(self, m: bool) -> None:
        self.mute = bool(m)

    def set_boost(self, b: bool) -> None:
        self.boost = bool(b)

    def play_file(self, path: str, label: str = '') -> None:
        self.stop()
        self._stop_flag.clear()
        self._pause_flag.clear()
        with self._lock:
            self._current_label = label or Path(path).name
        self._thread = threading.Thread(target=self._run_file, args=(path,), daemon=True)
        self._thread.start()

    def play_stream(self, url: str, label: str = '') -> None:
        """Stream playback stub.

        Recommended approach for production:
        - Decode to PCM mono using ffmpeg (subprocess) and feed to the same output stream.

        This skeleton keeps the UI + scheduling architecture intact.
        """
        self.stop()
        with self._lock:
            self._current_label = label or url
        # Not implemented: indicate end immediately.
        if self.on_track_end:
            self.on_track_end()

    def _run_file(self, path: str) -> None:
        try:
            data, sr = sf.read(path, dtype='float32', always_2d=True)
        except Exception:
            if self.on_track_end:
                self.on_track_end()
            return

        # Convert to mono: average channels
        x = np.mean(data, axis=1).astype(np.float32)

        # Resample if needed (simple linear; good enough for skeleton)
        if sr != self.sample_rate:
            x = self._resample_linear(x, sr, self.sample_rate)

        idx = 0
        n = len(x)

        def callback(outdata, frames, time_info, status):
            nonlocal idx
            if self._stop_flag.is_set():
                raise sd.CallbackStop()

            if self._pause_flag.is_set():
                outdata[:] = 0
                self.meter = MeterState(rms=0.0, peak=0.0)
                return

            chunk = x[idx:idx+frames]
            if len(chunk) < frames:
                chunk = np.pad(chunk, (0, frames-len(chunk)))

            if self.boost:
                chunk = apply_boost_chain(chunk)

            if self.mute:
                chunk = np.zeros_like(chunk)
            else:
                chunk = chunk * self.volume

            # meters
            self.meter = MeterState(rms=rms(chunk), peak=peak(chunk))

            # Mono output but write as (frames, 2) so L=R
            stereo = np.repeat(chunk.reshape(-1, 1), 2, axis=1)
            outdata[:] = stereo

            idx += frames
            if idx >= n:
                raise sd.CallbackStop()

        try:
            with sd.OutputStream(samplerate=self.sample_rate, channels=2, blocksize=self.blocksize, dtype='float32', callback=callback):
                while not self._stop_flag.is_set() and idx < n:
                    time.sleep(0.05)
        except Exception:
            pass
        finally:
            if not self._stop_flag.is_set() and self.on_track_end:
                self.on_track_end()

    @staticmethod
    def _resample_linear(x: np.ndarray, sr_in: int, sr_out: int) -> np.ndarray:
        if sr_in == sr_out:
            return x
        ratio = sr_out / sr_in
        n_out = int(len(x) * ratio)
        if n_out <= 1:
            return x
        xi = np.linspace(0, len(x)-1, num=n_out, dtype=np.float32)
        x0 = np.floor(xi).astype(int)
        x1 = np.clip(x0 + 1, 0, len(x)-1)
        t = xi - x0
        return (1 - t) * x[x0] + t * x[x1]
