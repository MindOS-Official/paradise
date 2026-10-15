#!/usr/bin/env python3
"""
Mind Helper — Atmospheric Telemetry & Awakening Protocol
Fetches live local weather conditions and produces chillingly polite greetings.
Dispatches desktop notifications upon system awakening.
"""

import os
import time
import requests
import json

_WEATHER_CACHE = {
    "timestamp": 0,
    "data": None
}

def _weather_allowed() -> bool:
    """wttr.in konumu IP adresinden tahmin eder; kullanıcı izin vermedikçe istek yapılmaz"""
    try:
        import mindos_prefs
        return mindos_prefs.get("weather")
    except Exception:
        return False


def get_atmospheric_status(timeout=3) -> dict:
    """
    Fetches atmospheric conditions with local in-memory caching (15 min).
    """
    now = time.time()
    if not _weather_allowed():
        return {"available": False, "temp_c": "--", "humidity": "--", "condition": "", "city": ""}
    if _WEATHER_CACHE["data"] and (now - _WEATHER_CACHE["timestamp"] < 900):
        return _WEATHER_CACHE["data"]

    try:
        url = "https://wttr.in/?format=j1"
        headers = {"User-Agent": "MindHelper/1.0 (MindOS Paradise; Linux)"}
        resp = requests.get(url, headers=headers, timeout=timeout)
        if resp.status_code == 200:
            data = resp.json()
            cur = data["current_condition"][0]
            temp_c = cur.get("temp_C", "?")
            humidity = cur.get("humidity", "?")
            desc = cur.get("weatherDesc", [{}])[0].get("value", "Stillness")
            city = ""
            try:
                area = data.get("nearest_area", [{}])[0]
                city = area.get("areaName", [{}])[0].get("value", "")
            except Exception:
                pass

            res = {
                "available": True,
                "temp_c": temp_c,
                "humidity": humidity,
                "condition": desc.strip(),
                "city": city or "Local Atmosphere"
            }
            _WEATHER_CACHE["timestamp"] = now
            _WEATHER_CACHE["data"] = res
            return res
    except Exception:
        pass

    fallback = {
        "available": False,
        "temp_c": "--",
        "humidity": "--",
        "condition": "Silent Void",
        "city": "Unknown Coordinates"
    }
    return fallback

def generate_awakening_greeting() -> dict:
    """Builds a chilling, polite awakening greeting for Mind Helper."""
    weather = get_atmospheric_status()

    if weather["available"]:
        temp = weather["temp_c"]
        cond = weather["condition"]
        city = weather["city"]

        commentary = (
            f"Local atmosphere in {city}: {temp}°C, {cond}. "
            f"MindOS Paradise system vitals are nominal and ready for your workflow."
        )
        short_greeting = f"{city} • {temp}°C, {cond}"
    else:
        commentary = (
            "MindOS Paradise system vitals are nominal. "
            "Mind Helper is active and ready to assist with system administration and Linux guidance."
        )
        short_greeting = "MindOS Paradise • System Ready"

    full_message = (
        f"✦ Welcome to MindOS Paradise ✦\n\n"
        f"{commentary}\n\n"
        f"Launch Mind Helper from the dock anytime for Linux administration guides and assistance."
    )

    return {
        "title": "MindOS Paradise • System Ready",
        "weather": weather,
        "short_greeting": short_greeting,
        "full_message": full_message
    }

def send_desktop_notification(greeting_data: dict = None):
    """Dispatches a desktop notification on system startup."""
    if greeting_data is None:
        greeting_data = generate_awakening_greeting()

    title = greeting_data["title"]
    body = greeting_data["full_message"]

    try:
        import gi
        gi.require_version('Notify', '0.7')
        from gi.repository import Notify
        Notify.init("MindHelper")

        for candidate in [
            "/usr/share/mindhelper/assets/mindhelper.png",
            "/usr/share/mindhelper/assets/mindhelper.svg",
            os.path.expanduser("~/mindhelper/assets/mindhelper.png"),
            os.path.expanduser("~/mindhelper/assets/mindhelper.svg"),
            "/usr/share/icons/hicolor/scalable/apps/mindhelper.svg",
            "/usr/share/icons/hicolor/512x512/apps/mindhelper.png",
        ]:
            if os.path.exists(candidate):
                icon_path = candidate
                break
        else:
            icon_path = "dialog-information"

        n = Notify.Notification.new(title, body, icon_path)
        n.set_urgency(1)
        n.show()
        return True
    except Exception:
        try:
            import subprocess
            subprocess.run(["notify-send", "-a", "Mind Helper", title, body], check=False)
            return True
        except Exception:
            return False

if __name__ == "__main__":
    g = generate_awakening_greeting()
    print("Greeting:", g["short_greeting"])
    print("Message:\n", g["full_message"])
