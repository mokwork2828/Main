#!/usr/bin/env python3
"""
generate-ad.py — Ad image generation via GPT Image 2 on FAL.

Usage (run from project root):
  python3 skills/generate-ad.py brands/[brand]/ads/[output-folder]

Reads ad-spec.json from the output folder.
Uploads the product image and generates via GPT Image 2.
Output: [product-slug]-v1.png (auto-increments if file already exists)

Requires FAL_KEY in .env at the project root.
"""

import json
import os
import sys
from pathlib import Path

import fal_client
import requests


EDIT_MODEL    = "openai/gpt-image-2/edit"
TXT2IMG_MODEL = "openai/gpt-image-2"


# ---------------------------------------------------------------------------
# Load FAL key from .env
# ---------------------------------------------------------------------------

def _load_env() -> None:
    if os.environ.get("FAL_KEY"):
        return
    search = Path.cwd()
    for _ in range(5):
        env_file = search / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if key not in os.environ:
                    os.environ[key] = val
            return
        parent = search.parent
        if parent == search:
            break
        search = parent


_load_env()


def _check_key() -> None:
    key = os.environ.get("FAL_KEY", "")
    if not key:
        sys.exit(
            "Error: FAL_KEY not found.\n"
            "Add FAL_KEY=your_key to a .env file at the project root."
        )
    os.environ["FAL_KEY"] = key


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _upload(path: Path, label: str) -> str:
    print(f"  Uploading {label}...", end=" ", flush=True)
    url = fal_client.upload_file(str(path))
    print("done")
    return url


def _save(url: str, dest: Path) -> None:
    resp = requests.get(url, timeout=120)
    resp.raise_for_status()
    dest.write_bytes(resp.content)


def _next_version(folder: Path, slug: str) -> Path:
    v = 1
    while (folder / f"{slug}-v{v}.png").exists():
        v += 1
    return folder / f"{slug}-v{v}.png"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(
            "Usage: python3 skills/generate-ad.py "
            "brands/[brand]/ads/[output-folder]"
        )

    output_dir = Path(sys.argv[1])
    spec_path  = output_dir / "ad-spec.json"

    if not spec_path.exists():
        sys.exit(f"Error: ad-spec.json not found at {spec_path}")

    with open(spec_path) as f:
        spec = json.load(f)

    prompt        = spec.get("prompt", "").strip()
    product_image = spec.get("product_image", "")
    brand         = spec.get("brand", "brand")
    product       = spec.get("product", "product")

    if not prompt:
        sys.exit("Error: No prompt found in ad-spec.json.")

    _check_key()

    print(f"\nGenerating ad — {brand} / {product}")

    image_urls = []

    if product_image:
        img_path = Path(product_image)
        if not img_path.exists():
            sys.exit(f"Error: Product image not found: {img_path}")
        image_urls.append(_upload(img_path, img_path.name))

    model = EDIT_MODEL if image_urls else TXT2IMG_MODEL
    print(f"Model: {model}")
    print("Generating...")

    result = fal_client.run(
        model,
        arguments={
            "prompt":      prompt,
            "image_size":  {"width": 1024, "height": 1792},
            "num_images":  1,
            "quality":     "high",
            **({"image_urls": image_urls} if image_urls else {}),
        },
    )

    images = result.get("images", [])
    if not images or not images[0].get("url"):
        sys.exit("Error: No image returned from FAL.")

    slug     = product.lower().replace(" ", "-")
    out_path = _next_version(output_dir, slug)
    _save(images[0]["url"], out_path)

    print(f"\nSaved → {out_path}")


if __name__ == "__main__":
    main()
