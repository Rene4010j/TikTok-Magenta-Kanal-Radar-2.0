"""
Wird von der GitHub Action nach Zeitplan ausgeführt.
Liest channels.json (welche Kanäle, welches Intervall),
prüft nur die Kanäle, deren Intervall seit dem letzten Check
abgelaufen ist, und schreibt Ergebnisse nach data/status.json
und data/events.json.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from tiktok_checker import CheckerError, check_for_new_video  # noqa: E402

CHANNELS_FILE = ROOT / "channels.json"
STATUS_FILE = ROOT / "data" / "status.json"
EVENTS_FILE = ROOT / "data" / "events.json"
MAX_EVENTS = 150
DEFAULT_INTERVAL = 20


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def is_due(entry: dict, interval_minutes: int) -> bool:
    last_checked = entry.get("last_checked_at")
    if not last_checked:
        return True
    elapsed = (datetime.now(timezone.utc) - datetime.fromisoformat(last_checked)).total_seconds() / 60
    return elapsed >= interval_minutes


def main():
    channels = load_json(CHANNELS_FILE, [])
    status = load_json(STATUS_FILE, {})
    events = load_json(EVENTS_FILE, [])

    active_usernames = set()
    changed = False

    for ch in channels:
        username = ch.get("username") or ch.get("profile_url", "").rstrip("/").split("@")[-1]
        profile_url = ch.get("profile_url") or f"https://www.tiktok.com/@{username}"
        interval_minutes = int(ch.get("interval_minutes", DEFAULT_INTERVAL))
        if not username:
            continue
        active_usernames.add(username)

        entry = status.get(username, {})
        if not is_due(entry, interval_minutes):
            continue

        print(f"Prüfe @{username} ...")
        changed = True
        try:
            new_video = check_for_new_video(profile_url, entry.get("last_video_id"))
            entry.update(
                {
                    "status": "ok",
                    "last_error": None,
                    "last_checked_at": now_iso(),
                }
            )
            if new_video:
                entry.update(
                    {
                        "last_video_id": new_video["id"],
                        "last_video_url": new_video["url"],
                        "last_video_title": new_video["title"],
                        "last_video_thumbnail": new_video.get("thumbnail"),
                        "last_video_uploaded_at": new_video.get("uploaded_at"),
                        "last_video_detected_at": now_iso(),
                    }
                )
                events.insert(
                    0,
                    {
                        "username": username,
                        "video_id": new_video["id"],
                        "video_url": new_video["url"],
                        "video_title": new_video["title"],
                        "detected_at": entry["last_video_detected_at"],
                    },
                )
                print(f"  -> Neues Video erkannt: {new_video['id']}")
        except CheckerError as e:
            entry.update(
                {"status": "error", "last_error": str(e), "last_checked_at": now_iso()}
            )
            print(f"  -> Fehler: {e}")

        status[username] = entry

    # Kanäle entfernen, die nicht mehr in channels.json stehen
    for username in list(status.keys()):
        if username not in active_usernames:
            del status[username]
            changed = True

    events = events[:MAX_EVENTS]

    if changed:
        save_json(STATUS_FILE, status)
        save_json(EVENTS_FILE, events)
        print("Änderungen gespeichert.")
    else:
        print("Kein Kanal fällig, keine Änderungen.")


if __name__ == "__main__":
    main()
