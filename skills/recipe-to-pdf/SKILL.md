---
name: recipe-to-pdf
description: Turns a recipe URL into a consistently formatted, print-ready PDF with ads and navigation stripped. Use when the user shares a recipe or cooking link and wants it printed, saved as a PDF, cleaned up, or reformatted for the kitchen.
---

# Recipe to PDF

Converts a recipe web page into a clean one- or two-page PDF for printing.

## Layout

Every recipe uses this structure:

```
Recipe Name
How long it takes | Author | Origin URL

Then ingredients by phase/part

Then instructions

Notes at the bottom.
```

The recipe's photo sits as a thumbnail in the top right corner. A "Details" strip
(prep/cook time, yield, category) goes just above Notes. The layout is fixed in
`style.css` — do not restyle per recipe.

## Always strip

The point is a page you can cook from, so exclude anything that is not the recipe:

- Ads, sponsored blocks, newsletter and subscribe prompts
- Buttons, navigation, share/print/save widgets, "Cook Mode" toggles
- Equipment and "special tools" sections (these are affiliate link cards)
- Comments, ratings, related-post links, the blogger's preamble story
- Nutrition popups

The scripts filter these out. Skim the extracted JSON and delete anything that slipped through.

## Workflow

**1. Extract**

```bash
python3 ~/.cursor/skills/recipe-to-pdf/scripts/fetch_recipe.py "<url>" -o /tmp/recipe.json
```

Reads the page's schema.org Recipe JSON-LD, then recovers phase headings and notes
from the HTML. Warnings go to stderr.

**2. Review the JSON before building.** Extraction is best effort — read the file and fix:

- Ingredient phases are correct and no ingredient was dropped
- Instruction steps are in order and free of widget text
- Times and yield match what the page displays
- Notes contain recipe notes, not comments or affiliate lists
- `title` is the recipe name, not the page's SEO title

If the page has no JSON-LD, the script emits a skeleton. Fetch the page and fill the
JSON in by hand — many sites also have a `/print/` URL with far less markup.

**3. Build**

```bash
python3 ~/.cursor/skills/recipe-to-pdf/scripts/build_recipe_pdf.py /tmp/recipe.json
```

Writes `~/Downloads/<Recipe-Name>.pdf`. Use `-o <path>` for somewhere else and
`--keep-html` to inspect the markup. Requires Google Chrome.

**4. Verify** the PDF renders correctly, then show the user the page images and the path.

```bash
qlmanage -t -s 1400 -o /tmp ~/Downloads/<Recipe-Name>.pdf   # page 1 only, no install
```

For every page, render with PyMuPDF:

```bash
python3 -m venv /tmp/pdfenv && /tmp/pdfenv/bin/pip install -q -i https://pypi.org/simple pymupdf
/tmp/pdfenv/bin/python -c "
import pymupdf
d = pymupdf.open('$HOME/Downloads/Recipe-Name.pdf')
for i, p in enumerate(d): p.get_pixmap(dpi=100).save(f'/tmp/pg{i+1}.png')
"
```

The `-i https://pypi.org/simple` flag matters: pip may default to a private index.

## Recipe JSON

Only `title` is required. Omit or empty any field to drop that part of the layout.

```json
{
  "title": "Brownie Batter Butter Cake",
  "time": "1 hour 50 minutes",
  "author": "Jenna Barnard",
  "source_url": "https://butternutbakeryblog.com/brownie-batter-butter-cake/",
  "image_url": "https://.../brownie-batter-butter-cake.png",
  "description": "A chocolate twist on classic gooey butter cake.",
  "ingredient_groups": [
    { "heading": "Chocolate Cake", "items": ["1/4 cup (55g) unsalted butter, melted"] },
    { "heading": "Brownie Batter Cream", "items": ["8 oz full fat cream cheese, room temp"] }
  ],
  "instruction_groups": [
    { "heading": "Chocolate Cake", "steps": ["Preheat the oven to 350F..."] }
  ],
  "details": { "Prep Time": "20 minutes", "Cook Time": "35 minutes", "Yield": "12 slices" },
  "notes": ["Keep in a container in the refrigerator."]
}
```

Use `"heading": ""` when a recipe has no phases; the group renders as a plain list.

## Notes on output

- Aim for one or two pages. Prefer a break between sections over shrinking type —
  this gets printed and read from across a counter.
- The thumbnail is downloaded and embedded, so the PDF is self-contained. A missing
  or unreachable image is skipped and the layout still works.
- Chrome sometimes lingers after writing the PDF; the build script treats a written
  file as success. Never pass `--user-data-dir`, which makes Chrome hang.
