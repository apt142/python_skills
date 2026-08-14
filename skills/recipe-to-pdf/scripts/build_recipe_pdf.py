#!/usr/bin/env python3
"""
Render a recipe JSON file into a print-ready PDF using headless Chrome.

The thumbnail is downloaded and inlined as a data URI so the PDF stands alone.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from html import escape
from pathlib import Path

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

CHROME_PATHS = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
]

MAX_IMAGE_BYTES = 8 * 1024 * 1024
# Above this, fall back to the smaller crop rather than bloating the PDF.
PREFERRED_IMAGE_BYTES = 2 * 1024 * 1024


def find_chrome() -> str:
    for path in CHROME_PATHS:
        if os.path.exists(path):
            return path
    for name in ("google-chrome", "chromium", "chromium-browser", "microsoft-edge"):
        found = shutil.which(name)
        if found:
            return found
    sys.exit("No Chrome/Chromium found. Install Google Chrome to render PDFs.")


def candidate_urls(url: str) -> list[str]:
    """A small WordPress crop prints soft, so try the full-size original first."""
    match = re.search(r"-(\d+)x(\d+)(\.\w+)$", url)
    if match and int(match.group(1)) < 600:
        return [url[: match.start()] + match.group(3), url]
    return [url]


def download_image(url: str) -> tuple[str, bytes] | None:
    try:
        request = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(request, timeout=20) as response:
            content_type = response.headers.get("Content-Type", "image/jpeg").split(";")[0]
            payload = response.read(MAX_IMAGE_BYTES + 1)
    except Exception as error:
        print(f"Could not fetch {url} ({error}).", file=sys.stderr)
        return None
    if not content_type.startswith("image/") or len(payload) > MAX_IMAGE_BYTES:
        return None
    return content_type, payload


def image_data_uri(url: str) -> str:
    """Download the thumbnail and inline it so the PDF stands alone. "" if unavailable."""
    if not url or url.startswith("data:"):
        return url or ""

    candidates = candidate_urls(url)
    fallback = None
    for index, candidate in enumerate(candidates):
        result = download_image(candidate)
        if result is None:
            continue
        content_type, payload = result
        is_last = index == len(candidates) - 1
        if len(payload) <= PREFERRED_IMAGE_BYTES or is_last:
            return f"data:{content_type};base64," + base64.b64encode(payload).decode("ascii")
        fallback = fallback or (content_type, payload)

    if fallback:
        return f"data:{fallback[0]};base64," + base64.b64encode(fallback[1]).decode("ascii")
    print("Thumbnail skipped.", file=sys.stderr)
    return ""


def slugify(title: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", title).strip("-")
    return slug or "recipe"


def render_groups(groups: list[dict], key: str, list_tag: str) -> str:
    chunks = []
    for group in groups:
        if not group.get(key):
            continue
        if group.get("heading"):
            chunks.append(f"<h3>{escape(group['heading'])}</h3>")
        items = "".join(f"<li>{escape(entry)}</li>" for entry in group[key])
        chunks.append(f"<{list_tag}>{items}</{list_tag}>")
    return "\n".join(chunks)


def render_html(recipe: dict, css: str) -> str:
    meta_parts = [
        ("time", recipe.get("time")),
        ("author", recipe.get("author")),
        ("url", recipe.get("source_url")),
    ]
    meta = "".join(
        f'<span class="{name}">{escape(value)}</span>' for name, value in meta_parts if value
    )

    thumbnail = image_data_uri(recipe.get("image_url", ""))
    thumbnail_tag = f'<img class="thumb" src="{thumbnail}" alt="">' if thumbnail else ""

    blocks = []
    if recipe.get("description"):
        blocks.append(f'<p class="description">{escape(recipe["description"])}</p>')

    ingredients = render_groups(recipe.get("ingredient_groups", []), "items", "ul")
    if ingredients:
        blocks.append(f"<section><h2>Ingredients</h2>{ingredients}</section>")

    instructions = render_groups(recipe.get("instruction_groups", []), "steps", "ol")
    if instructions:
        blocks.append(f"<section><h2>Instructions</h2>{instructions}</section>")

    details = recipe.get("details") or {}
    if details:
        cells = "".join(
            f"<div><strong>{escape(label)}:</strong> {escape(value)}</div>"
            for label, value in details.items()
        )
        blocks.append(f'<section><h2>Details</h2><div class="details">{cells}</div></section>')

    notes = recipe.get("notes") or []
    if notes:
        items = "".join(f"<li>{escape(note)}</li>" for note in notes)
        blocks.append(f'<section class="notes"><h2>Notes</h2><ul>{items}</ul></section>')

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{escape(recipe.get("title", "Recipe"))}</title>
<style>
{css}
</style>
</head>
<body>
<header>
  <div class="titleblock">
    <h1>{escape(recipe.get("title", "Recipe"))}</h1>
    <p class="meta">{meta}</p>
  </div>
  {thumbnail_tag}
</header>
{chr(10).join(blocks)}
</body>
</html>
"""


def print_to_pdf(chrome: str, html_path: Path, pdf_path: Path) -> None:
    # Passing --user-data-dir makes Chrome hang after writing the file, so it is omitted.
    options = [
        "--disable-gpu",
        "--hide-scrollbars",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_path}",
        html_path.as_uri(),
    ]
    for headless in ("--headless", "--headless=new"):
        try:
            subprocess.run([chrome, headless, *options], capture_output=True, text=True, timeout=60)
        except subprocess.TimeoutExpired:
            pass  # Chrome sometimes lingers after a successful write.
        if pdf_path.exists() and pdf_path.stat().st_size > 0:
            return
    sys.exit("Chrome did not produce a PDF.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("recipe_json")
    parser.add_argument("-o", "--output", help="PDF path (default: ~/Downloads/<Title>.pdf)")
    parser.add_argument("--keep-html", action="store_true", help="keep the intermediate HTML")
    args = parser.parse_args()

    recipe = json.loads(Path(args.recipe_json).read_text(encoding="utf-8"))
    css = (Path(__file__).resolve().parent.parent / "style.css").read_text(encoding="utf-8")

    pdf_path = Path(
        args.output
        or Path.home() / "Downloads" / f"{slugify(recipe.get('title', 'recipe'))}.pdf"
    ).expanduser()
    pdf_path.parent.mkdir(parents=True, exist_ok=True)

    html_path = pdf_path.with_suffix(".html")
    html_path.write_text(render_html(recipe, css), encoding="utf-8")

    try:
        print_to_pdf(find_chrome(), html_path, pdf_path)
    finally:
        if not args.keep_html:
            html_path.unlink(missing_ok=True)

    print(f"Wrote {pdf_path} ({pdf_path.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
