#!/usr/bin/env python3
"""
generate-ad.py — Ad image generation via Google Gemini API.

Usage (run from project root):
  python3 scripts/generate-ad.py brands/[brand]/ads/[output-folder]

Reads ad-spec.json from the output folder.
Optionally uses a product image as reference input.
Output: [product-slug]-v1.png (auto-increments if file already exists)

Requires GOOGLE_API_KEY in .env at the project root.
"""

import base64
import json
import os
import sys
from pathlib import Path

import requests


GEMINI_MODEL = "gemini-3.1-flash-image-preview"
GEMINI_URL   = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)

MIME_MAP = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}


# ---------------------------------------------------------------------------
# Load API key from .env
# ---------------------------------------------------------------------------

def _load_env() -> None:
    if os.environ.get("GOOGLE_API_KEY"):
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


def _check_key() -> str:
    key = os.environ.get("GOOGLE_API_KEY", "")
    if not key:
        sys.exit(
            "Error: GOOGLE_API_KEY not found.\n"
            "Add GOOGLE_API_KEY=your_key to a .env file at the project root."
        )
    return key


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _encode_image(path: Path) -> dict:
    mime = MIME_MAP.get(path.suffix.lower(), "image/jpeg")
    data = base64.b64encode(path.read_bytes()).decode()
    return {"inline_data": {"mime_type": mime, "data": data}}


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
            "Usage: python3 scripts/generate-ad.py "
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

    api_key = _check_key()

    print(f"\nGenerating ad — {brand} / {product}")
    print(f"Model: {GEMINI_MODEL}")

    parts = [{"text": prompt}]

    if product_image:
        img_path = Path(product_image)
        if not img_path.exists():
            sys.exit(f"Error: Product image not found: {img_path}")
        print(f"  Reference image: {img_path.name}")
        parts.append(_encode_image(img_path))

    body = {
        "contents": [{"parts": parts}],
        "generationConfig": {"responseModalities": ["IMAGE", "TEXT"]},
    }

    print("Generating...")
    resp = requests.post(
        f"{GEMINI_URL}?key={api_key}",
        json=body,
        timeout=180,
    )

    if not resp.ok:
        sys.exit(f"Error from Google API ({resp.status_code}):\n{resp.text}")

    result = resp.json()

    image_b64 = None
    for part in result.get("candidates", [{}])[0].get("content", {}).get("parts", []):
        if "inlineData" in part:
            image_b64 = part["inlineData"]["data"]
            break

    if not image_b64:
        sys.exit(f"Error: No image in response.\n{json.dumps(result, indent=2)}")

    slug     = product.lower().replace(" ", "-")
    out_path = _next_version(output_dir, slug)
    out_path.write_bytes(base64.b64decode(image_b64))

    print(f"\nSaved → {out_path}")


if __name__ == "__main__":
    main()
