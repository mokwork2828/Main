#!/usr/bin/env python3
"""
generate_ads.py — Ad Image Generator (Google AI Studio / Imagen 4)
Reads prompts.json, fires each prompt to Imagen 4 via the Google AI Studio API,
decodes the base64 responses, saves images, and builds an HTML gallery.

Usage:
    python generate_ads.py --brand-dir brands/my-brand
    python generate_ads.py --brand-dir brands/my-brand --templates 1,7,13
"""

import os
import sys
import json
import base64
import argparse
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("Missing dependency: pip install requests")


# ── Config ────────────────────────────────────────────────────────────────────

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
if not GOOGLE_API_KEY:
    sys.exit("GOOGLE_API_KEY environment variable not set. Run: export GOOGLE_API_KEY='your-key'")

IMAGEN_MODEL = "imagen-4.0-generate-001"
BASE_URL     = f"https://generativelanguage.googleapis.com/v1beta/models/{IMAGEN_MODEL}:predict"
HEADERS      = {"Content-Type": "application/json", "x-goog-api-key": GOOGLE_API_KEY}

NUM_IMAGES   = 4     # Imagen 4 supports up to 4 per request

# Imagen 4 supported aspect ratios: 1:1, 3:4, 4:3, 9:16, 16:9
# Map any unsupported ratios to the nearest equivalent
ASPECT_RATIO_MAP = {
    "1:1":  "1:1",
    "4:5":  "3:4",   # nearest supported to 4:5
    "3:4":  "3:4",
    "2:3":  "3:4",
    "4:3":  "4:3",
    "3:2":  "4:3",
    "9:16": "9:16",
    "16:9": "16:9",
    "21:9": "16:9",
}


# ── Image Generation ──────────────────────────────────────────────────────────

def generate_images(prompt_data: dict) -> list[bytes]:
    """Call Imagen 4 and return a list of raw PNG bytes."""
    raw_ratio    = prompt_data.get("aspect_ratio", "1:1")
    aspect_ratio = ASPECT_RATIO_MAP.get(raw_ratio, "1:1")
    if aspect_ratio != raw_ratio:
        print(f"  Aspect ratio {raw_ratio} → mapped to {aspect_ratio} (nearest Imagen 4 support)")

    payload = {
        "instances": [
            {"prompt": prompt_data["prompt"]}
        ],
        "parameters": {
            "sampleCount":   NUM_IMAGES,
            "aspectRatio":   aspect_ratio,
            "outputOptions": {"mimeType": "image/png"},
            "safetySetting": "block_low_and_above",
        },
    }

    resp = requests.post(BASE_URL, headers=HEADERS, json=payload, timeout=120)
    resp.raise_for_status()
    predictions = resp.json().get("predictions", [])
    if not predictions:
        raise ValueError(f"No predictions in response: {resp.text}")
    return [base64.b64decode(p["bytesBase64Encoded"]) for p in predictions]


# ── Save ──────────────────────────────────────────────────────────────────────

def save_prompt_results(prompt_data: dict, images: list[bytes], outputs_dir: Path) -> list[Path]:
    """Save all images + prompt.txt for a single prompt."""
    num    = str(prompt_data["template_number"]).zfill(2)
    name   = prompt_data["template_name"].lower().replace(" ", "-")
    folder = outputs_dir / f"{num}-{name}"
    folder.mkdir(parents=True, exist_ok=True)

    (folder / "prompt.txt").write_text(prompt_data["prompt"], encoding="utf-8")

    saved = []
    for i, img_bytes in enumerate(images, start=1):
        dest = folder / f"{name}_v{i}.png"
        dest.write_bytes(img_bytes)
        print(f"  Saved image {i}/{len(images)} → {dest.name}")
        saved.append(dest)

    return saved


# ── HTML Gallery ──────────────────────────────────────────────────────────────

HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{brand} — Ad Gallery</title>
<style>
  body {{ font-family: system-ui, sans-serif; background: #0f0f0f; color: #eee; margin: 0; padding: 24px; }}
  h1   {{ font-size: 1.6rem; margin-bottom: 4px; }}
  .meta {{ color: #888; font-size: 0.85rem; margin-bottom: 32px; }}
  .template {{ margin-bottom: 48px; }}
  .template h2 {{ font-size: 1rem; font-weight: 600; border-bottom: 1px solid #333; padding-bottom: 8px; margin-bottom: 16px; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px; }}
  .card img {{ width: 100%; border-radius: 8px; display: block; }}
  .card span {{ display: block; font-size: 0.72rem; color: #666; margin-top: 4px; }}
</style>
</head>
<body>
<h1>{brand} — Generated Ad Gallery</h1>
<p class="meta">Generated {generated_at} &nbsp;·&nbsp; {total_images} images across {total_templates} templates</p>
{sections}
</body>
</html>
"""

def build_gallery(brand: str, generated_at: str, outputs_dir: Path) -> None:
    """Walk outputs/ and build index.html gallery."""
    sections     = []
    total_images = 0

    for folder in sorted(outputs_dir.iterdir()):
        if not folder.is_dir():
            continue
        imgs = sorted(folder.glob("*.png")) + sorted(folder.glob("*.jpg"))
        if not imgs:
            continue

        total_images += len(imgs)
        cards = "\n".join(
            f'<div class="card"><img src="{img.relative_to(outputs_dir.parent)}" loading="lazy"><span>{img.name}</span></div>'
            for img in imgs
        )
        sections.append(
            f'<div class="template"><h2>{folder.name}</h2>'
            f'<div class="grid">{cards}</div></div>'
        )

    html = HTML_TEMPLATE.format(
        brand=brand,
        generated_at=generated_at,
        total_images=total_images,
        total_templates=len(sections),
        sections="\n".join(sections),
    )

    gallery_path = outputs_dir.parent / "index.html"
    gallery_path.write_text(html, encoding="utf-8")
    print(f"\nGallery saved → {gallery_path}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate ads via Google AI Studio / Imagen 4")
    parser.add_argument("--templates", help="Comma-separated template numbers to run, e.g. 1,7,13")
    parser.add_argument("--brand-dir", help="Path to brand folder (default: current directory)", default=".")
    args = parser.parse_args()

    brand_dir    = Path(args.brand_dir).resolve()
    prompts_file = brand_dir / "prompts.json"
    outputs_dir  = brand_dir / "outputs"

    if not prompts_file.exists():
        sys.exit(f"prompts.json not found in {brand_dir}")

    with open(prompts_file, encoding="utf-8") as f:
        data = json.load(f)

    brand        = data.get("brand", "Unknown Brand")
    generated_at = data.get("generated_at", "")
    prompts      = data.get("prompts", [])

    if args.templates:
        selected = {int(t.strip()) for t in args.templates.split(",")}
        prompts  = [p for p in prompts if p["template_number"] in selected]
        print(f"Filtered to templates: {sorted(selected)}")

    if not prompts:
        sys.exit("No prompts to process.")

    outputs_dir.mkdir(parents=True, exist_ok=True)

    total     = len(prompts)
    all_saved = []

    for idx, prompt_data in enumerate(prompts, start=1):
        num  = prompt_data["template_number"]
        name = prompt_data["template_name"]
        print(f"\n── [{idx}/{total}] Template {num}: {name} ──────────────────────────────")
        print(f"  Model: {IMAGEN_MODEL}")

        try:
            images = generate_images(prompt_data)
            saved  = save_prompt_results(prompt_data, images, outputs_dir)
            all_saved.extend(saved)
            print(f"  ✓ {len(saved)} image(s) saved")
        except Exception as e:
            print(f"  ✗ FAILED: {e}")
            continue

    print("\n── Building HTML gallery ─────────────────────────────────────")
    build_gallery(brand, generated_at, outputs_dir)
    print(f"\nDone. {len(all_saved)} images generated.")


if __name__ == "__main__":
    main()
