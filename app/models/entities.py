from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Literal, Any

ItemType = Literal['audiofile', 'spotify', 'dynamic_text', 'stream']


@dataclass
class Track:
    id: str
    source: Literal['audiofile', 'spotify']
    title: str
    artist: str
    duration_sec: int
    path: Optional[str] = None           # audiofile
    spotify_uri: Optional[str] = None    # spotify


@dataclass
class Stream:
    id: str
    name: str
    url: str
    country: str = ''
    language: str = ''
    genre: str = ''
    topic: str = ''


@dataclass
class UserVariable:
    name: str
    file_path: str


@dataclass
class DynamicText:
    id: str
    name: str
    text_cs: str
    # Languages config is stored as a separate config file per message in the state (serialized dict).
    languages_config: dict[str, Any] = field(default_factory=dict)


@dataclass
class PlaylistItem:
    item_type: ItemType
    ref_id: str  # Track.id or DynamicText.id or Stream.id


@dataclass
class ScheduleEvent:
    id: str
    day_index: int  # 0=Mon .. 6=Sun
    time_hhmm: str  # 'HH:MM'
    item_type: ItemType
    ref_id: str
    # For streams (draw blocks): optional duration (minutes) & end time.
    duration_min: Optional[int] = None


@dataclass
class ScheduleStreamBlock:
    id: str
    day_index: int
    start_hhmm: str
    end_hhmm: str
    stream_id: str


@dataclass
class Settings:
    spotify_api_key: str = ''
    openai_api_key: str = ''
    azure_tts_key: str = ''
    azure_tts_region: str = ''


@dataclass
class HotkeyButton:
    index: int  # 0..7
    item_type: Optional[ItemType] = None
    ref_id: Optional[str] = None
    label: str = ''


@dataclass
class AppState:
    tracks: list[Track] = field(default_factory=list)
    streams: list[Stream] = field(default_factory=list)
    dynamic_texts: list[DynamicText] = field(default_factory=list)
    user_variables: list[UserVariable] = field(default_factory=list)
    playlist: list[PlaylistItem] = field(default_factory=list)  # loop (<=50)
    schedule_events: list[ScheduleEvent] = field(default_factory=list)  # pin events
    schedule_stream_blocks: list[ScheduleStreamBlock] = field(default_factory=list)
    hotkeys: list[HotkeyButton] = field(default_factory=lambda: [HotkeyButton(i) for i in range(8)])
    settings: Settings = field(default_factory=Settings)

    def to_dict(self) -> dict:
        def dc(o):
            if hasattr(o, '__dict__'):
                return o.__dict__
            return o
        return {
            'tracks': [dc(x) for x in self.tracks],
            'streams': [dc(x) for x in self.streams],
            'dynamic_texts': [dc(x) for x in self.dynamic_texts],
            'user_variables': [dc(x) for x in self.user_variables],
            'playlist': [dc(x) for x in self.playlist],
            'schedule_events': [dc(x) for x in self.schedule_events],
            'schedule_stream_blocks': [dc(x) for x in self.schedule_stream_blocks],
            'hotkeys': [dc(x) for x in self.hotkeys],
            'settings': dc(self.settings),
        }

    @staticmethod
    def from_dict(d: dict) -> 'AppState':
        s = AppState()
        s.tracks = [Track(**x) for x in d.get('tracks', [])]
        s.streams = [Stream(**x) for x in d.get('streams', [])]
        s.dynamic_texts = [DynamicText(**x) for x in d.get('dynamic_texts', [])]
        s.user_variables = [UserVariable(**x) for x in d.get('user_variables', [])]
        s.playlist = [PlaylistItem(**x) for x in d.get('playlist', [])]
        s.schedule_events = [ScheduleEvent(**x) for x in d.get('schedule_events', [])]
        s.schedule_stream_blocks = [ScheduleStreamBlock(**x) for x in d.get('schedule_stream_blocks', [])]
        s.hotkeys = [HotkeyButton(**x) for x in d.get('hotkeys', [])]
        s.settings = Settings(**d.get('settings', {}))
        # Ensure exactly 8 hotkeys
        if len(s.hotkeys) < 8:
            existing = {h.index for h in s.hotkeys}
            for i in range(8):
                if i not in existing:
                    s.hotkeys.append(HotkeyButton(i))
            s.hotkeys.sort(key=lambda x: x.index)
        if len(s.hotkeys) > 8:
            s.hotkeys = sorted(s.hotkeys, key=lambda x: x.index)[:8]
        return s
