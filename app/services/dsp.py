from __future__ import annotations

import numpy as np


def rms(x: np.ndarray) -> float:
    x = np.asarray(x, dtype=np.float32)
    return float(np.sqrt(np.mean(np.square(x)) + 1e-12))


def peak(x: np.ndarray) -> float:
    x = np.asarray(x, dtype=np.float32)
    return float(np.max(np.abs(x)) + 1e-12)


def apply_boost_chain(x: np.ndarray, target_rms: float = 0.15, limiter_ceiling: float = 0.98) -> np.ndarray:
    """Simple 'radio-style' chain: RMS normalization + soft-knee limiter.

    This is intentionally lightweight; it is meant to provide consistent loudness.
    Input/output: mono float32 in [-1,1].
    """
    x = np.asarray(x, dtype=np.float32)

    cur = rms(x)
    if cur > 1e-6:
        gain = target_rms / cur
    else:
        gain = 1.0
    y = x * gain

    # Soft clip / limiter
    # tanh-based waveshaper with ceiling control
    y = np.tanh(y)
    m = np.max(np.abs(y))
    if m > limiter_ceiling:
        y = y * (limiter_ceiling / m)

    return y.astype(np.float32)
