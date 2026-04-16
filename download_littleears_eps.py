#!/usr/bin/env python3
import os
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

import fire

# Usage examples (Poetry):
#   poetry run python download_littleears_eps.py list
#   poetry run python download_littleears_eps.py download 1 10 --out=downloads
#   poetry run python download_littleears_eps.py download 1 10 --out=downloads --overwrite

DEFAULT_RSS = "https://feed.firstory.me/rss/user/ckso8a1mj2f8m098934qukxid"
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
    # Match patterns like EP1, EP.1, EP 1, EP01, 第1集, 第01集
    m = re.search(r"\bEP[.\s]*([0-9]+)\b", title, re.IGNORECASE)
    if m:
        return int(m.group(1))
    m = re.search(r"第\s*([0-9]+)\s*[集話话]", title)
    if m:
        return int(m.group(1))
    return None


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


def do_download(url: str, dest: Path, overwrite: bool):
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


class LittleEars:
    """Downloader for the Little Ears (小耳朵) podcast on Firstory."""

    def list(self, rss: str = DEFAULT_RSS):
        """List all available episodes with their numbers and titles."""
        channel = parse_rss(rss)
        items = extract_items(channel)
        if not items:
            print("No episodes found.", file=sys.stderr)
            raise SystemExit(1)
        print(f"{'#':>5}  {'EP':>5}  Title")
        print("-" * 60)
        for i, item in enumerate(items, 1):
            ep = episode_number(item["title"])
            ep_str = str(ep) if ep is not None else "?"
            print(f"{i:>5}  {ep_str:>5}  {item['title']}")

    def download(
        self,
        start: int,
        end: int,
        out: str = "downloads",
        rss: str = DEFAULT_RSS,
        overwrite: bool = False,
    ):
        """Download episodes by EP number range.

        Args:
            start: First EP number to download (inclusive).
            end: Last EP number to download (inclusive).
            out: Output directory.
            rss: RSS feed URL override.
            overwrite: Overwrite existing files.
        """
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
            print(
                f"No episodes with EP numbers in [{start}, {end}] found.\n"
                "Tip: run `list` to see all episodes and their EP numbers.",
                file=sys.stderr,
            )
            raise SystemExit(1)

        outdir = Path(out).expanduser()
        for item in selected:
            safe_title = sanitize_filename(item["title"])
            ext = guess_extension(item["url"], item["type"])
            filename = safe_title + ext
            dest = unique_path(outdir / filename) if not overwrite else outdir / filename
            ok = do_download(item["url"], dest, overwrite)
            status = "downloaded" if ok else "skipped"
            print(f"{status}: {dest}")

    def search(
        self,
        *keywords: str,
        out: str = "downloads",
        rss: str = DEFAULT_RSS,
        overwrite: bool = False,
        dry_run: bool = False,
    ):
        """Download episodes whose titles contain ANY of the given keywords.

        Args:
            keywords: One or more keywords to match against episode titles.
            out: Output directory.
            rss: RSS feed URL override.
            overwrite: Overwrite existing files.
            dry_run: Print matched episodes without downloading.
        """
        if not keywords:
            raise SystemExit("Provide at least one keyword.")

        if isinstance(overwrite, str):
            overwrite = overwrite.strip().lower() in {"1", "true", "yes", "y"}

        channel = parse_rss(rss)
        items = extract_items(channel)

        selected = [
            item for item in items
            if any(kw in item["title"] for kw in keywords)
        ]

        if not selected:
            print(
                f"No episodes matched keywords: {', '.join(keywords)}\n"
                "Tip: run `list` to see all episode titles.",
                file=sys.stderr,
            )
            raise SystemExit(1)

        print(f"Matched {len(selected)} episode(s):")
        for item in selected:
            print(f"  {item['title']}")

        if dry_run:
            return

        print()
        outdir = Path(out).expanduser()
        for item in selected:
            safe_title = sanitize_filename(item["title"])
            ext = guess_extension(item["url"], item["type"])
            filename = safe_title + ext
            dest = unique_path(outdir / filename) if not overwrite else outdir / filename
            ok = do_download(item["url"], dest, overwrite)
            status = "downloaded" if ok else "skipped"
            print(f"{status}: {dest}")


def main():
    fire.Fire(LittleEars)


if __name__ == "__main__":
    main()
