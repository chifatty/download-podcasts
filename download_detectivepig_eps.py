#!/usr/bin/env python3
import os
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

import fire

# Usage example (Poetry):
#   poetry run python download_detectivepig_eps.py 111 113 --out=downloads

DEFAULT_RSS = "https://feed.firstory.me/rss/user/cklw2tvilfnda0804tdm3oxho"
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://open.firstory.me/",
}


def localname(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def child_text(parent, name, default=""):
    for child in parent:
        if localname(child.tag) == name:
            return (child.text or "").strip()
    return default


def find_children(parent, name):
    return [c for c in parent if localname(c.tag) == name]


def sanitize_filename(name: str) -> str:
    name = name.replace("(", "（").replace(")", "）")
    name = re.sub(r"[\\/:*?\"<>|]", "_", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name.rstrip(". ")


def guess_extension(url: str, enclosure_type: str) -> str:
    path = urllib.parse.urlparse(url).path
    ext = os.path.splitext(path)[1]
    if ext:
        return ext
    if enclosure_type == "audio/mpeg":
        return ".mp3"
    if enclosure_type == "audio/mp4":
        return ".m4a"
    return ""


def parse_rss(rss_url: str):
    req = urllib.request.Request(rss_url, headers=DEFAULT_HEADERS)
    with urllib.request.urlopen(req) as f:
        data = f.read()
    root = ET.fromstring(data)
    channel = None
    for child in root:
        if localname(child.tag) == "channel":
            channel = child
            break
    if channel is None:
        raise RuntimeError("Invalid RSS: channel not found")
    return channel


def extract_items(channel):
    items = find_children(channel, "item")
    results = []
    for item in items:
        title = child_text(item, "title")
        enclosure = None
        for child in item:
            if localname(child.tag) == "enclosure":
                enclosure = child
                break
        if enclosure is None:
            continue
        url = enclosure.get("url", "")
        if not url:
            continue
        enclosure_type = enclosure.get("type", "")
        results.append(
            {
                "title": title,
                "url": url,
                "type": enclosure_type,
            }
        )
    return results


def episode_number(title: str):
    m = re.search(r"\bEP[.\s]*([0-9]+)\b", title, re.IGNORECASE)
    return int(m.group(1)) if m else None


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    i = 2
    while True:
        candidate = path.with_name(f"{stem}-{i}{suffix}")
        if not candidate.exists():
            return candidate
        i += 1


def download(url: str, dest: Path, overwrite: bool):
    if dest.exists() and not overwrite:
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    try:
        req = urllib.request.Request(url, headers=DEFAULT_HEADERS)
        with urllib.request.urlopen(req) as r, open(tmp, "wb") as f:
            while True:
                chunk = r.read(1024 * 1024)
                if not chunk:
                    break
                f.write(chunk)
        tmp.replace(dest)
        return True
    except Exception:
        if tmp.exists():
            tmp.unlink()
        raise


def download_eps(
    start: int,
    end: int,
    out: str = "downloads",
    rss: str = DEFAULT_RSS,
    overwrite: bool = False,
):
    """Download episodes by EP number range (EP.* only)."""
    try:
        start = int(start)
        end = int(end)
    except (TypeError, ValueError):
        raise SystemExit("start/end must be integers")

    if start > end:
        raise SystemExit("start must be <= end")

    if isinstance(overwrite, str):
        overwrite = overwrite.strip().lower() in {"1", "true", "yes", "y"}

    channel = parse_rss(rss)
    items = extract_items(channel)
    selected = []
    for item in items:
        num = episode_number(item["title"])
        if num is None:
            continue
        if start <= num <= end:
            selected.append(item)

    if not selected:
        print("No matching episodes found.", file=sys.stderr)
        raise SystemExit(1)

    outdir = Path(out)
    for item in selected:
        safe_title = sanitize_filename(item["title"])
        ext = guess_extension(item["url"], item["type"])
        filename = safe_title + ext
        dest = unique_path(outdir / filename) if not overwrite else outdir / filename
        ok = download(item["url"], dest, overwrite)
        status = "downloaded" if ok else "skipped"
        print(f"{status}: {dest}")


def main():
    fire.Fire(download_eps)


if __name__ == "__main__":
    main()
