import hashlib
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



def cache_cover_art(path):
    extension = Path(path).suffix.lower()
    if extension not in AUDIO_EXTENSIONS:
        return None
    folder = Path(path).parent
    stem = Path(path).stem
    candidates = [
        folder / (stem + ".jpg"), folder / (stem + ".jpeg"), folder / (stem + ".png"),
        folder / "cover.jpg", folder / "cover.jpeg", folder / "cover.png",
        folder / "folder.jpg", folder / "folder.jpeg", folder / "folder.png",
    ]
    source = next((candidate for candidate in candidates if candidate.is_file()), None)
    data = None
    if source is not None:
        try:
            modified = source.stat().st_mtime
            cache_key = f"{source}|{modified}"
            data = source.read_bytes()
        except OSError:
            data = None
    else:
        try:
            modified = os.path.getmtime(path)
        except OSError:
            return None
        cache_key = f"{path}|{modified}"
        try:
            import mutagen
            media = mutagen.File(path)
            if media is not None:
                pictures = getattr(media, "pictures", None) or []
                if pictures:
                    data = pictures[0].data
                elif media.tags:
                    for key in media.tags.keys():
                        if str(key).startswith("APIC"):
                            data = media.tags[key].data
                            break
                    if data is None and "covr" in media.tags:
                        data = bytes(media.tags["covr"][0])
                    if data is None and "metadata_block_picture" in media.tags:
                        import base64
                        from mutagen.flac import Picture
                        data = Picture(base64.b64decode(media.tags["metadata_block_picture"][0])).data
        except (ImportError, Exception):
            data = None
    if not data:
        return None
    cache_dir = Path.home() / ".cache" / "xvb-lab" / "covers"
    cache_dir.mkdir(parents=True, exist_ok=True)
    output = cache_dir / (hashlib.md5(cache_key.encode("utf-8")).hexdigest() + ".img")
    if not output.is_file() or output.stat().st_size == 0:
        temporary = output.with_suffix(".img.tmp")
        temporary.write_bytes(data)
        temporary.replace(output)
    return str(output)
