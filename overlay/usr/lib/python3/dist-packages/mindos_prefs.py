"""MindOS kullanıcı tercihleri (~/.config/mindos/preferences.json).

İnternete kişisel veri gönderen özellikler (hava durumu: IP adresinden konum; Mind Helper'da
internet araması: sorulan sorular) açık onay olmadan çalışmaz: tercih kaydedilmemişse ya da
false ise kapalıdır (KVKK / GDPR). Güncelleme bildirimi varsayılan olarak açıktır.
Mind Helper, Mind Arc ve güncelleme bildirimi bu modülü ortak kullanır.
"""
import json
import os
from pathlib import Path

DEFAULTS = {"weather": False, "web_search": False, "update_notify": True}


def _path():
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")
    return Path(base) / "mindos" / "preferences.json"


def load():
    try:
        with open(_path(), encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def get(key):
    value = load().get(key)
    return DEFAULTS.get(key, False) if value is None else bool(value)


def is_set(key):
    return key in load()


def set(key, value):
    data = load()
    data[key] = bool(value)
    path = _path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
    os.replace(tmp, path)
