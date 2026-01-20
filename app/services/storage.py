from __future__ import annotations

import json
from pathlib import Path
from typing import Tuple

from app.models.entities import AppState


def save_state_to_file(state: AppState, file_path: str) -> None:
    p = Path(file_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    data = state.to_dict()
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def load_state_from_file(file_path: str) -> AppState:
    p = Path(file_path)
    data = json.loads(p.read_text(encoding='utf-8'))
    return AppState.from_dict(data)
