from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from mutagen import File as MutagenFile


@dataclass
class AudioMeta:
    title: str
    artist: str
    duration_sec: int


def read_audio_metadata(path: str) -> Optional[AudioMeta]:
    p = Path(path)
    if not p.exists():
        return None

    mf = MutagenFile(path)
    if mf is None or mf.info is None:
        return None

    duration = int(getattr(mf.info, 'length', 0) or 0)

    title = ''
    artist = ''

    tags = getattr(mf, 'tags', None)
    if tags:
        # Try common tag keys
        for k in ('TIT2', 'title', 'TITLE'):
            if k in tags:
                v = tags.get(k)
                title = str(v[0]) if isinstance(v, (list, tuple)) else str(v)
                break
        for k in ('TPE1', 'artist', 'ARTIST'):
            if k in tags:
                v = tags.get(k)
                artist = str(v[0]) if isinstance(v, (list, tuple)) else str(v)
                break

    if not title:
        title = p.stem
    if not artist:
        artist = 'Unknown'

    return AudioMeta(title=title, artist=artist, duration_sec=duration)
