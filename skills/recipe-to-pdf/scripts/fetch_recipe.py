#!/usr/bin/env python3
"""
Extract a recipe from a URL into the JSON shape that build_recipe_pdf.py consumes.

Core fields come from the page's schema.org Recipe JSON-LD. Ingredient group
headings and notes are recovered from the HTML, since JSON-LD flattens them.

Extraction is best effort: review the JSON and correct it before building.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from html import unescape

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

# Recipe plugin container class names, used to slice the HTML into sections.
MARKERS = {
    "ingredients": r"tasty-recipes-ingredients|wprm-recipe-ingredients|mv-create-ingredients|recipe-ingredients",
    "instructions": r"tasty-recipes-instructions|wprm-recipe-instructions|mv-create-instructions|recipe-instructions",
    "notes": r"tasty-recipes-notes|wprm-recipe-notes|mv-create-notes|recipe-notes",
    "tail": r"tasty-recipes-equipment|tasty-recipes-other-details|tasty-recipes-nutrition"
    r"|tasty-recipes-source|wprm-recipe-equipment|wprm-recipe-nutrition"
    r"|comment-respond|comments-area|comment-list|entry-comments|^comments$"
    r"|related-posts|post-navigation|entry-footer",
}

# Times, yield, and taxonomy rendered as labelled list items in the recipe card.
DETAIL_CLASSES = r"prep-time|cook-time|additional-time|custom-time|total-time|yield|category|method|cuisine"

# Interactive widgets and affiliate prompts that sit inside recipe card markup.
GENERIC_HEADINGS = re.compile(
    r"ingredients|instructions|directions|method|steps|notes|recipe notes", re.I
)

JUNK = re.compile(
    r"cook mode|prevent your screen|add to (shopping )?list|shop ingredients"
    r"|instacart|walmart|save recipe|print recipe|scale \d|pin recipe|affiliate"
    r"|\bsays:\s",  # comment bylines
    re.I,
)


def fetch_html(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", "replace")


def strip_tags(fragment: str) -> str:
    fragment = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", fragment)
    fragment = re.sub(r"(?is)<br\s*/?>", " ", fragment)
    text = re.sub(r"(?s)<[^>]+>", "", fragment)
    text = re.sub(r"\s+", " ", unescape(text)).strip()
    return text.lstrip("\u25a2\u25a1\u2610\u2022 ").strip()  # WPRM checkbox glyphs


def as_list(value) -> list:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def text_of(value) -> str:
    """Flatten a JSON-LD value that may be a string, dict, or list into text."""
    for item in as_list(value):
        if isinstance(item, str) and item.strip():
            return strip_tags(item)
        if isinstance(item, dict):
            for key in ("name", "text", "url", "@id"):
                if item.get(key):
                    return strip_tags(str(item[key]))
    return ""


def humanize_duration(iso: str) -> str:
    match = re.fullmatch(r"P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:\d+S)?)?", iso or "")
    if not match:
        return strip_tags(iso or "")
    days, hours, minutes = (int(group) if group else 0 for group in match.groups())
    hours += days * 24 + minutes // 60
    minutes %= 60
    parts = []
    if hours:
        parts.append(f"{hours} hour{'s' if hours > 1 else ''}")
    if minutes:
        parts.append(f"{minutes} minute{'s' if minutes > 1 else ''}")
    return " ".join(parts)


def walk_nodes(node):
    if isinstance(node, list):
        for item in node:
            yield from walk_nodes(item)
    elif isinstance(node, dict):
        yield node
        for key in ("@graph", "mainEntity", "mainEntityOfPage", "itemListElement"):
            if key in node:
                yield from walk_nodes(node[key])


def find_recipe_jsonld(html: str) -> dict | None:
    pattern = r'(?is)<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>'
    for block in re.finditer(pattern, html):
        try:
            data = json.loads(block.group(1).strip())
        except json.JSONDecodeError:
            continue
        for node in walk_nodes(data):
            if "Recipe" in [str(t) for t in as_list(node.get("@type"))]:
                return node
    return None


def remove_noise(html: str) -> str:
    """Drop scripts, styles, and comments so class names in CSS aren't mistaken for markup."""
    html = re.sub(r"(?is)<(script|style|noscript)\b.*?</\1>", " ", html)
    return re.sub(r"(?s)<!--.*?-->", " ", html)


def marker_pattern(key: str) -> str:
    return f'(?:class|id)="[^"]*(?:{MARKERS[key]})'


def slice_section(html: str, start_key: str, end_keys: list[str], limit: int = 60000) -> str:
    start = re.search(marker_pattern(start_key), html, re.I)
    if not start:
        return ""
    begin = start.start()
    end = len(html)
    for key in end_keys:
        match = re.search(marker_pattern(key), html[begin + 1 :], re.I)
        if match:
            end = min(end, begin + 1 + match.start())
    return html[begin : min(end, begin + limit)]


def html_details(html: str) -> dict:
    """Read the labelled detail list items, which show what the page actually displays."""
    details = {}
    pattern = rf'(?is)<li\b[^>]*class="[^"]*(?:{DETAIL_CLASSES})[^"]*"[^>]*>(.*?)</li>'
    for match in re.finditer(pattern, html):
        text = strip_tags(match.group(1))
        label, separator, value = text.partition(":")
        if separator and label.strip() and value.strip():
            details.setdefault(label.strip(), value.strip())
    return details


def grouped_items(region: str) -> list[dict]:
    """Split a region into heading-led groups of list items, in document order."""
    groups: list[dict] = []
    current = {"heading": "", "items": []}
    for match in re.finditer(r"(?is)<(h[2-6]|li)\b[^>]*>(.*?)</\1>", region):
        tag, text = match.group(1).lower(), strip_tags(match.group(2))
        if not text or JUNK.search(text):
            continue
        if tag.startswith("h"):
            if current["items"]:
                groups.append(current)
            # A heading that just names the section is not a phase.
            current = {"heading": "" if GENERIC_HEADINGS.fullmatch(text) else text, "items": []}
        else:
            current["items"].append(text)
    if current["items"]:
        groups.append(current)
    # A lone unnamed group means the page had no phase headings.
    return groups


def instruction_groups_from_jsonld(value) -> list[dict]:
    def steps_from(sequence) -> list[str]:
        steps = []
        for item in as_list(sequence):
            text = item if isinstance(item, str) else ""
            if isinstance(item, dict):
                text = item.get("text") or item.get("name") or ""
            text = strip_tags(str(text))
            if text and not JUNK.search(text):
                steps.append(text)
        return steps

    if isinstance(value, str):
        items = re.findall(r"(?is)<li\b[^>]*>(.*?)</li>", value)
        source = items if items else value.split("\n")
        return [{"heading": "", "steps": [s for s in (strip_tags(i) for i in source) if s]}]

    groups: list[dict] = []
    loose: list[str] = []
    for item in as_list(value):
        types = [str(t) for t in as_list(item.get("@type"))] if isinstance(item, dict) else []
        if "HowToSection" in types:
            groups.append(
                {
                    "heading": strip_tags(str(item.get("name", ""))),
                    "steps": steps_from(item.get("itemListElement")),
                }
            )
        else:
            loose.extend(steps_from(item))
    if loose:
        groups.append({"heading": "", "steps": loose})
    return groups


def build_details(recipe: dict, displayed: dict) -> dict:
    """Merge JSON-LD fields with the page's own labels, preferring what readers see."""
    details = {}
    extra_times = {
        label: value
        for label, value in displayed.items()
        if label.endswith("Time") and label != "Total Time"
    }
    for label, fallback in (
        ("Prep Time", humanize_duration(text_of(recipe.get("prepTime")))),
        ("Cook Time", humanize_duration(text_of(recipe.get("cookTime")))),
    ):
        value = extra_times.pop(label, fallback)
        if value:
            details[label] = value
    details.update(extra_times)

    for label, fallback in (
        ("Yield", text_of(recipe.get("recipeYield"))),
        ("Category", text_of(recipe.get("recipeCategory"))),
        ("Method", text_of(recipe.get("cookingMethod"))),
        ("Cuisine", text_of(recipe.get("recipeCuisine"))),
    ):
        value = displayed.get(label) or fallback
        if value:
            details[label] = value
    return details


def extract(url: str, raw_html: str) -> dict:
    recipe = find_recipe_jsonld(raw_html)
    if recipe is None:
        print("No Recipe JSON-LD found; emitting a skeleton to fill in by hand.", file=sys.stderr)
        recipe = {}

    html = remove_noise(raw_html)
    displayed = html_details(html)
    ingredients = [strip_tags(i) for i in as_list(recipe.get("recipeIngredient"))]
    html_groups = grouped_items(slice_section(html, "ingredients", ["instructions", "notes", "tail"]))

    # Trust the HTML grouping only when it accounts for every JSON-LD ingredient.
    if html_groups and (not ingredients or sum(len(g["items"]) for g in html_groups) >= len(ingredients)):
        ingredient_groups = html_groups
    else:
        ingredient_groups = [{"heading": "", "items": ingredients}]
        if ingredients:
            print("Ingredient phase headings not detected; check the page.", file=sys.stderr)

    note_groups = grouped_items(slice_section(html, "notes", ["tail"], limit=15000))
    notes = [item for group in note_groups for item in group["items"]]

    return {
        "title": text_of(recipe.get("name")) or "Untitled Recipe",
        "time": humanize_duration(text_of(recipe.get("totalTime"))) or displayed.get("Total Time", ""),
        "author": text_of(recipe.get("author")),
        "source_url": url,
        "image_url": text_of(recipe.get("image")),
        "description": text_of(recipe.get("description")),
        "ingredient_groups": ingredient_groups,
        "instruction_groups": instruction_groups_from_jsonld(recipe.get("recipeInstructions")),
        "details": build_details(recipe, displayed),
        "notes": notes,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url")
    parser.add_argument("-o", "--output", help="write JSON here instead of stdout")
    args = parser.parse_args()

    data = extract(args.url, fetch_html(args.url))
    text = json.dumps(data, indent=2, ensure_ascii=False)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(text + "\n")
        print(f"Wrote {args.output}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
