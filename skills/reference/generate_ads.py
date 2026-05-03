
#!/usr/bin/env python3
"""
generate_ads.py — Nano Banana 2 Ad Image Generator
Reads prompts.json, uploads product images to FAL storage,
fires each prompt to the correct FAL endpoint, downloads results,
and builds an HTML gallery.

Usage:
    python generate_ads.py                        # all prompts
    python generate_ads.py --templates 1,7,13     # specific templates only
"""

import os
import sys
import json
import time
import argparse
import mimetypes
import urllib.request
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("Missing dependency: pip install requests")


# ── Config ────────────────────────────────────────────────────────────────────

FAL_KEY = os.environ.get("FAL_KEY", "")
if not FAL_KEY:
    sys.exit("FAL_KEY environment variable not set. Run: export FAL_KEY='your-key'")

HEADERS = {"Authorization": f"Key {FAL_KEY}", "Content-Type": "application/json"}

ENDPOINT_TEXT  = "fal-ai/nano-banana-2"
ENDPOINT_EDIT  = "fal-ai/nano-banana-2/edit"

BASE_URL       = "https://fal.run"
QUEUE_URL      = "https://queue.fal.run"
STORAGE_URL    = "https://storage.fal.run"

NUM_IMAGES     = 4       # images generated per prompt
RESOLUTION     = "2K"    # 0.5K | 1K | 2K | 4K
POLL_INTERVAL  = 3       # seconds between status checks
MAX_WAIT       = 300     # max seconds to wait per job


# ── FAL Storage Upload ────────────────────────────────────────────────────────

def upload_image(image_path: Path) -> str:
    """Upload a local image to FAL storage and return its public URL."""
    mime, _ = mimetypes.guess_type(str(image_path))
    mime = mime or "application/octet-stream"

    with open(image_path, "rb") as f:
        data = f.read()

    resp = requests.post(
        STORAGE_URL,
        headers={"Authorization": f"Key {FAL_KEY}", "Content-Type": mime},
        data=data,
        timeout=60,
    )
    resp.raise_for_status()
    url = resp.json().get("url") or resp.json().get("access_url")
    if not url:
        raise ValueError(f"No URL in FAL storage response: {resp.text}")
    print(f"  Uploaded {image_path.name} → {url}")
    return url


def upload_product_images(product_images_dir: Path) -> list[str]:
    """Upload all product images in the folder and return their URLs."""
    exts = {".png", ".jpg", ".jpeg", ".webp"}
    images = [p for p in product_images_dir.iterdir() if p.suffix.lower() in exts]

    if not images:
        print("  No product images found in product-images/")
        return []

    print(f"  Found {len(images)} product image(s) — uploading…")
    urls = []
    for img in images[:14]:   # Nano Banana 2 accepts up to 14 reference images
        urls.append(upload_image(img))
    return urls


# ── FAL Queue ─────────────────────────────────────────────────────────────────

def submit_job(endpoint: str, payload: dict) -> str:
    """Submit a job to the FAL queue and return the request_id."""
    url = f"{QUEUE_URL}/{endpoint}"
    resp = requests.post(url, headers=HEADERS, json=payload, timeout=30)
    resp.raise_for_status()
    request_id = resp.json().get("request_id")
    if not request_id:
        raise ValueError(f"No request_id in response: {resp.text}")
    return request_id


def poll_job(endpoint: str, request_id: str) -> dict:
    """Poll until the job is complete and return the result."""
    status_url = f"{QUEUE_URL}/{endpoint}/requests/{request_id}/status"
    result_url = f"{QUEUE_URL}/{endpoint}/requests/{request_id}"
    elapsed = 0

    while elapsed < MAX_WAIT:
        resp = requests.get(status_url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        status = resp.json().get("status")

        if status == "COMPLETED":
            result = requests.get(result_url, headers=HEADERS, timeout=30)
            result.raise_for_status()
            return result.json()

        if status in ("FAILED", "CANCELLED"):
            raise RuntimeError(f"Job {request_id} ended with status: {status}")

        print(f"    Status: {status} … ({elapsed}s elapsed)")
        time.sleep(POLL_INTERVAL)
        elapsed += POLL_INTERVAL

    raise TimeoutError(f"Job {request_id} did not complete within {MAX_WAIT}s")


def generate_images(prompt_data: dict, image_urls: list[str]) -> list[dict]:
    """
    Call the correct FAL endpoint and return a list of image dicts
    with 'url' and optionally 'content_type'.
    """
    needs_product = prompt_data.get("needs_product_images", False)
    endpoint = ENDPOINT_EDIT if (needs_product and image_urls) else ENDPOINT_TEXT

    payload = {
        "prompt":       prompt_data["prompt"],
        "aspect_ratio": prompt_data.get("aspect_ratio", "1:1"),
        "num_images":   NUM_IMAGES,
        "output_format": "png",
        "resolution":   RESOLUTION,
    }

    if endpoint == ENDPOINT_EDIT and image_urls:
        payload["image_urls"] = image_urls

    print(f"  Endpoint: {endpoint}")
    request_id = submit_job(endpoint, payload)
    print(f"  Job submitted: {request_id}")
    result = poll_job(endpoint, request_id)

    images = result.get("images") or []
    return images


# ── Download & Save ───────────────────────────────────────────────────────────

def download_image(url: str, dest: Path) -> None:
    """Download an image from a URL and save it to dest."""
    resp = requests.get(url, timeout=60, stream=True)
    resp.raise_for_status()
    with open(dest, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)


def save_prompt_results(prompt_data: dict, images: list[dict], outputs_dir: Path) -> list[Path]:
    """Save all images + prompt.txt for a single prompt into the outputs folder."""
    num    = str(prompt_data["template_number"]).zfill(2)
    name   = prompt_data["template_name"].lower().replace(" ", "-")
    folder = outputs_dir / f"{num}-{name}"
    folder.mkdir(parents=True, exist_ok=True)

    # Save prompt text
    (folder / "prompt.txt").write_text(prompt_data["prompt"], encoding="utf-8")

    saved = []
    for i, img in enumerate(images, start=1):
        url  = img.get("url") or img.get("access_url") or img
        ext  = ".png"
        dest = folder / f"{name}_v{i}{ext}"
        print(f"  Downloading image {i}/{len(images)} → {dest.name}")
        download_image(url, dest)
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
    sections = []
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
    parser = argparse.ArgumentParser(description="Generate ads via Nano Banana 2 / FAL API")
    parser.add_argument("--templates", help="Comma-separated template numbers to run, e.g. 1,7,13")
    parser.add_argument("--brand-dir", help="Path to brand folder (default: current directory)", default=".")
    args = parser.parse_args()

    brand_dir = Path(args.brand_dir).resolve()
    prompts_file = brand_dir / "prompts.json"
    product_images_dir = brand_dir / "product-images"
    outputs_dir = brand_dir / "outputs"

    # ── Load prompts.json ──
    if not prompts_file.exists():
        sys.exit(f"prompts.json not found in {brand_dir}")

    with open(prompts_file, encoding="utf-8") as f:
        data = json.load(f)

    brand        = data.get("brand", "Unknown Brand")
    generated_at = data.get("generated_at", "")
    prompts      = data.get("prompts", [])

    # ── Filter templates if requested ──
    if args.templates:
        selected = {int(t.strip()) for t in args.templates.split(",")}
        prompts = [p for p in prompts if p["template_number"] in selected]
        print(f"Filtered to templates: {sorted(selected)}")

    if not prompts:
        sys.exit("No prompts to process.")

    outputs_dir.mkdir(parents=True, exist_ok=True)

    # ── Upload product images once ──
    print("\n── Uploading product images ──────────────────────────────────")
    product_image_urls: list[str] = []
    if product_images_dir.exists():
        product_image_urls = upload_product_images(product_images_dir)
    else:
        print("  product-images/ folder not found — skipping uploads.")

    # ── Process each prompt ───────────────────────────────────────────────────
    total = len(prompts)
    all_saved = []

    for idx, prompt_data in enumerate(prompts, start=1):
        num  = prompt_data["template_number"]
        name = prompt_data["template_name"]
        print(f"\n── [{idx}/{total}] Template {num}: {name} ──────────────────────────────")

        try:
            images = generate_images(prompt_data, product_image_urls)
            saved  = save_prompt_results(prompt_data, images, outputs_dir)
            all_saved.extend(saved)
            print(f"  ✓ {len(saved)} image(s) saved")
        except Exception as e:
            print(f"  ✗ FAILED: {e}")
            continue

    # ── Build gallery ──
    print("\n── Building HTML gallery ─────────────────────────────────────")
    build_gallery(brand, generated_at, outputs_dir)

    print(f"\nDone. {len(all_saved)} images generated.")


if __name__ == "__main__":
    main()
