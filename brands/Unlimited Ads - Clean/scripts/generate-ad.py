#!/usr/bin/env python3
"""
generate-ad.py — Ad image generation via Google Gemini API.

Usage (run from project root):
  python3 scripts/generate-ad.py brands/[brand]/ads/[output-folder]

Reads ad-spec.json from the output folder.
Supports two image inputs:
  product_image   — what the bag looks like (required for accuracy)
  reference_image — scene/composition/mood reference (optional, Polène etc.)
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

    prompt          = spec.get("prompt", "").strip()
    reference_image = spec.get("reference_image", "")
    brand           = spec.get("brand", "brand")
    product         = spec.get("product", "product")

    # Support both product_images (array) and product_image (single, legacy)
    product_images = spec.get("product_images") or []
    if not product_images and spec.get("product_image"):
        product_images = [spec["product_image"]]

    if not prompt:
        sys.exit("Error: No prompt found in ad-spec.json.")

    api_key = _check_key()

    print(f"\nGenerating ad — {brand} / {product}")
    print(f"Model: {GEMINI_MODEL}")

    parts = []

    # Build instruction based on what inputs are provided
    n = len(product_images)
    if n > 0 and reference_image:
        parts.append({"text": (
            f"Create an original product advertisement photograph. "
            f"The first {n} image{'s are' if n > 1 else ' is'} different angles of the same bag — "
            f"together they show its complete silhouette, strap, hardware, leather texture, and color. "
            f"Reproduce this exact bag faithfully in the final image. "
            f"The last image is a mood and lighting reference only — draw inspiration from its environment type, lighting quality, and atmosphere, but create an original composition. Do not copy or replicate the reference scene directly. "
            f"Critical rules for realism: "
            f"(1) Light the bag consistently with the scene — same light direction, color temperature, and shadow quality as the environment. The bag must feel physically present in the scene, not composited. "
            f"(2) When a model carries the bag, the strap hangs at shoulder length — the bag opening sits at the bottom of the bust, the bottom of the bag at the top to mid-hip. The strap has natural tension from the bag's weight pulling it downward. The bag hangs with gravity, not floating or rigid. "
            f"(3) If the model holds the bag by hand, the hand and arm respond naturally to the weight — slight downward pull, natural grip."
        )})
    elif n > 0:
        parts.append({"text": (
            f"Create an original product advertisement photograph. "
            f"The {n} image{'s are' if n > 1 else ' is'} different angles of the same bag. "
            f"Reproduce the bag exactly as shown, lit naturally within the scene."
        )})

    for img in product_images:
        img_path = Path(img)
        if not img_path.exists():
            sys.exit(f"Error: Product image not found: {img_path}")
        print(f"  Product image:   {img_path.name}")
        parts.append(_encode_image(img_path))

    if reference_image:
        ref_path = Path(reference_image)
        if not ref_path.exists():
            sys.exit(f"Error: Reference image not found: {ref_path}")
        print(f"  Scene reference: {ref_path.name}")
        parts.append(_encode_image(ref_path))

    parts.append({"text": prompt})

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
