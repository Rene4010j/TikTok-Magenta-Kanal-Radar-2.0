import json
import re
import subprocess
from datetime import datetime, timezone

USERNAME_RE = re.compile(r"tiktok\.com/@([\w.\-]+)", re.IGNORECASE)


class CheckerError(Exception):
    pass


def parse_username(url_or_handle: str) -> tuple[str, str]:
    url_or_handle = url_or_handle.strip()
    m = USERNAME_RE.search(url_or_handle)
    if m:
        username = m.group(1)
    elif url_or_handle.startswith("@"):
        username = url_or_handle[1:]
    else:
        username = url_or_handle
    username = username.strip("/ ")
    if not username:
        raise CheckerError("Konnte keinen TikTok-Nutzernamen lesen.")
    return username, f"https://www.tiktok.com/@{username}"


def _run_yt_dlp(args: list[str], timeout: int = 45) -> dict:
    cmd = ["yt-dlp", "--no-warnings", "--skip-download", "-J"] + args
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError as e:
        raise CheckerError("yt-dlp nicht gefunden. pip install yt-dlp") from e
    except subprocess.TimeoutExpired as e:
        raise CheckerError("Zeitüberschreitung beim Abruf von TikTok.") from e

    if result.returncode != 0:
        stderr = (result.stderr or "").strip().splitlines()
        msg = stderr[-1] if stderr else "Unbekannter yt-dlp Fehler"
        raise CheckerError(msg[:300])

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise CheckerError("Antwort von yt-dlp konnte nicht gelesen werden.") from e


def get_latest_video_id(profile_url: str) -> dict:
    data = _run_yt_dlp(["--flat-playlist", "--playlist-items", "1", profile_url])
    entries = data.get("entries") or []
    if not entries:
        raise CheckerError("Keine Videos gefunden (privat oder leer?).")
    top = entries[0]
    video_id = top.get("id")
    video_url = top.get("url") or top.get("webpage_url")
    if not video_id:
        raise CheckerError("Video-ID konnte nicht ermittelt werden.")
    if video_url and not video_url.startswith("http"):
        video_url = f"https://www.tiktok.com/@{data.get('uploader_id', '')}/video/{video_id}"
    return {"id": video_id, "url": video_url}


def get_video_details(video_url: str) -> dict:
    data = _run_yt_dlp([video_url])
    uploaded_at = None
    ts = data.get("timestamp")
    if ts:
        uploaded_at = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
    elif data.get("upload_date"):
        try:
            uploaded_at = datetime.strptime(data["upload_date"], "%Y%m%d").replace(
                tzinfo=timezone.utc
            ).isoformat()
        except ValueError:
            uploaded_at = None
    return {
        "id": data.get("id"),
        "url": data.get("webpage_url") or video_url,
        "title": (data.get("title") or data.get("description") or "")[:200],
        "thumbnail": data.get("thumbnail"),
        "uploaded_at": uploaded_at,
    }


def check_for_new_video(profile_url: str, known_video_id: str | None) -> dict | None:
    latest = get_latest_video_id(profile_url)
    if known_video_id and latest["id"] == known_video_id:
        return None
    return get_video_details(latest["url"])
