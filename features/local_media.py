import os
from pathlib import Path

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
