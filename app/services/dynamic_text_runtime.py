from __future__ import annotations

import datetime as _dt
from pathlib import Path
from typing import Dict


STANDARD_VARIABLES = {
    'hodina': 'hour',
    'aktuální čas': 'time',
    'aktuální den v týdnu': 'weekday',
    'aktuální číslo dne v měsíci': 'day',
    'aktuální měsíc': 'month',
    'aktuální rok': 'year',
    'aktuální datum bez roku': 'date_no_year',
    'aktuální svátek': 'nameday',
}


def get_nameday_cz(dt: _dt.datetime, mapping: Dict[str, str]) -> str:
    """Return Czech nameday for a date.

    mapping is expected to map 'MM-DD' -> 'Name'.
    This project ships a minimal mapping file for demo; production should include a full dataset.
    """
    key = dt.strftime('%m-%d')
    return mapping.get(key, '')


def render_dynamic_text(template_cs: str, at_time: _dt.datetime, user_vars: Dict[str, str], nameday_map: Dict[str, str]) -> str:
    """Render text with variables.

    Variable syntax: {{variable_name}}
    - Standard variables are supported by Czech display names from the spec.
    - User variables: program generates a .txt file; its content is substituted.
    """
    dt = at_time

    repl = {
        'hodina': f"{dt.hour}",
        'aktuální čas': dt.strftime('%H:%M'),
        'aktuální den v týdnu': dt.strftime('%A'),
        'aktuální číslo dne v měsíci': f"{dt.day}",
        'aktuální měsíc': f"{dt.month}",
        'aktuální rok': f"{dt.year}",
        'aktuální datum bez roku': dt.strftime('%-d. %-m.') if hasattr(dt, 'strftime') else '',
        'aktuální svátek': get_nameday_cz(dt, nameday_map),
    }
    # Merge user vars (already loaded from files)
    repl.update(user_vars)

    out = template_cs
    for k, v in repl.items():
        out = out.replace('{{' + k + '}}', v)
    return out


def load_user_variable_files(var_paths: Dict[str, str]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for name, fp in var_paths.items():
        p = Path(fp)
        if p.exists():
            try:
                out[name] = p.read_text(encoding='utf-8').strip()
            except Exception:
                out[name] = ''
        else:
            out[name] = ''
    return out
