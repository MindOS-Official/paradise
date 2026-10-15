#!/usr/bin/env python3
"""
Mind Helper — Developer Feedback Gateway & Appropriateness Dispatcher
Enforces a strict 24-hour rate limit per user.
Inspects and analyzes feedback via MindHelperBrain before dispatching
to the developer mailbox (ruzgarcagdaspasalar@gmail.com).
The developer email is strictly hidden from user view.
"""

import os
import sys
import time
import json
import base64
import requests
from pathlib import Path
from datetime import datetime

from ai_brain import MindHelperBrain
from system_facts import get_live_telemetry

# Developer destination email encoded in Base64 (never displayed in user-facing UI)
# Decodes to: ruzgarcagdaspasalar@gmail.com
_DEV_ENCODED = b"cnV6Z2FyY2FnZGFzcGFzYWxhckBnbWFpbC5jb20="

def _get_dev_mailbox() -> str:
    """Returns the internal developer mailbox without exposing it to the UI."""
    return base64.b64decode(_DEV_ENCODED).decode("utf-8")

def get_state_file() -> Path:
    config_dir = Path.home() / ".config" / "mindhelper"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "feedback_state.json"

def get_history_log() -> Path:
    data_dir = Path.home() / ".local" / "share" / "mindhelper"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "feedback_sent.log"

def check_rate_limit() -> tuple[bool, str, int]:
    """
    Validates whether the user is eligible to submit daily feedback (once every 24 hours).
    Returns: (can_submit: bool, status_message: str, seconds_remaining: int)
    """
    state_file = get_state_file()
    if not state_file.exists():
        return True, "Ready for daily developer communion.", 0

    try:
        with open(state_file, "r") as f:
            data = json.load(f)
            last_ts = data.get("last_submission_timestamp", 0)
            now = time.time()
            elapsed = now - last_ts
            cooldown_period = 86400  # 24 hours in seconds

            if elapsed < cooldown_period:
                rem_seconds = int(cooldown_period - elapsed)
                rem_hours = rem_seconds // 3600
                rem_mins = (rem_seconds % 3600) // 60
                msg = (
                    f"Your previous message has already been conveyed to the developer. "
                    f"To preserve signal quality, one communion is permitted every 24 hours. "
                    f"Next window opens in {rem_hours}h {rem_mins}m."
                )
                return False, msg, rem_seconds
    except Exception:
        pass

    return True, "Ready for daily developer communion.", 0

def record_successful_submission(subject: str, message: str, category: str):
    """Updates the 24-hour rate limit timestamp and saves a local receipt."""
    now = time.time()
    state_file = get_state_file()
    state_data = {
        "last_submission_timestamp": now,
        "last_submission_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "category": category
    }
    with open(state_file, "w") as f:
        json.dump(state_data, f, indent=2)

    try:
        log_file = get_history_log()
        with open(log_file, "a") as f:
            entry = (
                f"[{datetime.now().isoformat()}] [{category}] {subject}\n"
                f"{message}\n"
                f"{'-' * 60}\n"
            )
            f.write(entry)
    except Exception:
        pass

def submit_feedback(category: str, subject: str, message: str, user_alias: str = "",
                    include_system: bool = False) -> tuple[bool, str]:
    """
    Analyzes feedback appropriateness with AI, then dispatches to developer email
    (via the formsubmit.co relay). System details (OS, kernel, uptime, RAM) are added only
    when the user ticks "include system info" in the form.
    """
    # 1. Check Rate Limit (24 hours)
    allowed, rate_msg, _ = check_rate_limit()
    if not allowed:
        return False, rate_msg

    # 2. Minimum substance check
    combined = f"{subject.strip()} {message.strip()}"
    if len(combined) < 10:
        return False, "Feedback is too brief. Please provide a clear explanation (minimum 10 characters)."

    # 3. AI Appropriateness Inspection
    brain = MindHelperBrain()
    is_appropriate, reason = brain.validate_content(combined)
    if not is_appropriate:
        return False, f"Mind Helper Analysis: Feedback was declined. {reason}"

    # 4. Prepare payload for developer mailbox
    target_email = _get_dev_mailbox()
    payload = {
        "_subject": f"[Mind Helper Feedback] [{category.upper()}] {subject}",
        "Category": category,
        "Subject": subject,
        "Sender": user_alias.strip() or "MindOS User",
        "Feedback": message,
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "_captcha": "false"
    }
    if include_system:  # yalnızca kullanıcı formda işaretlediyse
        telemetry = get_live_telemetry()
        payload.update({
            "System_OS": telemetry.get("os_name", "MindOS Paradise"),
            "Kernel": telemetry.get("kernel", "Unknown"),
            "Uptime": telemetry.get("uptime_str", "Unknown"),
            "RAM_Usage": f"{telemetry.get('mem_used_gb')}G / {telemetry.get('mem_total_gb')}G ({telemetry.get('mem_percent')}%)",
        })

    # Dispatch via FormSubmit AJAX endpoint
    try:
        url = f"https://formsubmit.co/ajax/{target_email}"
        headers = {
            "User-Agent": "MindHelper-Feedback/1.0 (MindOS)",
            "Accept": "application/json",
            "Origin": "https://mindos-official.github.io",
            "Referer": "https://mindos-official.github.io/"
        }
        resp = requests.post(url, data=payload, headers=headers, timeout=8)

        is_success = False
        message_returned = ""
        try:
            res_json = resp.json()
            is_success = str(res_json.get("success", "")).lower() == "true"
            message_returned = res_json.get("message", "")
        except Exception:
            is_success = resp.status_code in [200, 201]

        if is_success:
            record_successful_submission(subject, message, category)
            return True, (
                "Feedback analyzed and approved. Mind Helper has securely forwarded your message "
                "directly to the developer. Your daily communion is now recorded."
            )
        elif "activation" in message_returned.lower() or "activate" in message_returned.lower():
            # FormSubmit initial activation email
            record_successful_submission(subject, message, category)
            return True, (
                "Feedback analyzed and dispatched. An activation request was forwarded to the developer mailbox. "
                "Your message is recorded for this 24-hour cycle."
            )
        else:
            # Gönderilemedi: kullanıcıya dürüstçe söylenir, günlük hak harcanmaz, metin kaybolmaz
            path = save_unsent(subject, message, category)
            return False, (
                f"Feedback could not be delivered (service response: {message_returned or resp.status_code}). "
                f"Your message was saved to {path} so you can try again later."
            )
    except Exception:
        path = save_unsent(subject, message, category)
        return False, (
            "No internet connection, so the feedback was not sent. "
            f"Your message was saved to {path} so you can try again later."
        )


def save_unsent(subject: str, message: str, category: str) -> Path:
    """Gönderilemeyen geri bildirimi kullanıcının kendi klasörüne kaydeder"""
    path = get_history_log().with_name("feedback_unsent.log")
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now():%Y-%m-%d %H:%M}] [{category}] {subject}\n{message}\n{'-' * 60}\n")
    except Exception:
        pass
    return path

if __name__ == "__main__":
    print("Rate limit check:", check_rate_limit())
