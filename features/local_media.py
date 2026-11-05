import json
import os
from pathlib import Path


TAG_CACHE_FILE = Path.home() / ".cache" / "xvb-lab" / "tags.json"

AUDIO_EXTENSIONS = {
    "aac", "aif", "aiff", "alac", "ape", "flac", "m4a", "m4b",
    "m4p", "mid", "midi", "mp3", "mpc", "oga", "ogg", "opus",
    "wav", "wma", "wv",
}
VIDEO_EXTENSIONS = {
    "3g2", "3gp", "asf", "avi", "flv", "m2ts", "m4v", "mkv",
    "mov", "mp4", "mpeg", "mpg", "mts", "ogv", "ts", "vob",
    "webm", "wmv",
}


def media_kind(path):
    extension = Path(path).suffix.lower().lstrip(".")
    if extension in AUDIO_EXTENSIONS:
        return "music"
    if extension in VIDEO_EXTENSIONS:
        return "video"
    return None


def iter_folder_batches(folder, batch_size=30):
    batch = []
    root = os.path.abspath(os.path.expanduser(folder))
    for current, directories, files in os.walk(root):
        directories[:] = sorted(
            (name for name in directories if not name.startswith(".")),
            key=str.casefold,
        )
        for name in sorted(files, key=str.casefold):
            if name.startswith("."):
                continue
            path = os.path.join(current, name)
            kind = media_kind(path)
            if kind:
                batch.append({
                    "name": Path(name).stem,
                    "path": path,
                    "kind": kind,
                })
                if len(batch) >= batch_size:
                    yield batch
                    batch = []
    if batch:
        yield batch


def scan_folder(folder):
    return [item for batch in iter_folder_batches(folder) for item in batch]


def scan_imported(paths):
    result = []
    for path in paths:
        absolute = os.path.abspath(os.path.expanduser(path))
        kind = media_kind(absolute)
        if kind and os.path.isfile(absolute):
            result.append({
                "name": Path(absolute).stem,
                "path": absolute,
                "kind": kind,
            })
    return result



def load_tag_cache():
    try:
        data = json.loads(TAG_CACHE_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError, TypeError):
        return {}


def save_tag_cache(cache):
    TAG_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporary = TAG_CACHE_FILE.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    temporary.replace(TAG_CACHE_FILE)


def read_media_tags(path, cache):
    try:
        modified = os.path.getmtime(path)
    except OSError:
        return "", "", "", ""
    cached = cache.get(path)
    if isinstance(cached, list) and len(cached) == 5 and cached[0] == modified:
        return tuple(cached[1:])
    try:
        import mutagen
    except ImportError:
        return "", "", "", ""
    title, artist, album, year = "", "", "", ""
    try:
        media = mutagen.File(path, easy=True)
        if media and media.tags:
            def value(key):
                raw = media.tags.get(key) or [""]
                return str(raw[0]).strip()
            title = value("title")
            artist = value("artist")
            album = value("album")
            date = value("date")
            year = date[:4] if date[:4].isdigit() else ""
    except Exception:
        pass
    cache[path] = [modified, title, artist, album, year]
    return title, artist, album, year
