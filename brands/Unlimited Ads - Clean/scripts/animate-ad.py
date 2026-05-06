#!/usr/bin/env python3
"""
animate-ad.py — Animate a generated ad via Kling v3 Pro on FAL.

Usage (run from project root):
  python3 scripts/animate-ad.py workspace/brands/[brand]/ads/[folder]/ref-[N]

Reads motion-spec.json and the generated PNG from the folder.
Output: [product-slug]-v1.mp4 saved in the same folder.

Requires FAL_KEY in .env at the project root.
"""

import json
import os
import sys
from pathlib import Path

import fal_client
import requests


MODEL = "fal-ai/kling-video/v3/pro/image-to-video"


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


def _upload(path: Path) -> str:
    print(f"  Uploading {path.name}...", end=" ", flush=True)
    url = fal_client.upload_file(str(path))
    print("done")
    return url


def _save(url: str, dest: Path) -> None:
    resp = requests.get(url, timeout=300)
    resp.raise_for_status()
    dest.write_bytes(resp.content)


def _next_version(folder: Path, slug: str) -> Path:
    v = 1
    while (folder / f"{slug}-v{v}.mp4").exists():
        v += 1
    return folder / f"{slug}-v{v}.mp4"


def _find_image(folder: Path) -> Path:
    for ext in ("*.png", "*.jpg", "*.jpeg"):
        matches = sorted(folder.glob(ext))
        if matches:
            return matches[-1]
    sys.exit(f"Error: No image found in {folder}. Generate the static ad first with /ad-generator.")


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(
            "Usage: python3 scripts/animate-ad.py "
            "workspace/brands/[brand]/ads/[folder]/ref-[N]"
        )

    output_dir = Path(sys.argv[1])
    spec_path  = output_dir / "motion-spec.json"

    if not spec_path.exists():
        sys.exit(f"Error: motion-spec.json not found at {spec_path}\nRun /ad-animator first to generate the motion brief.")

    with open(spec_path) as f:
        spec = json.load(f)

    motion_prompt = spec.get("motion_prompt", "").strip()
    duration      = str(spec.get("duration", "5"))

    product = "product"
    ad_spec_path = output_dir / "ad-spec.json"
    if ad_spec_path.exists():
        with open(ad_spec_path) as f:
            ad = json.load(f)
        product = ad.get("product", "product")

    if not motion_prompt:
        sys.exit("Error: No motion_prompt in motion-spec.json.")

    _check_key()

    image_path = _find_image(output_dir)
    print(f"\nAnimating — {product}")
    print(f"Source: {image_path.name}")
    print(f"Duration: {duration}s")

    image_url = _upload(image_path)

    print(f"Model: {MODEL}")
    print("Generating... (takes 2–4 minutes)")

    result = fal_client.run(
        MODEL,
        arguments={
            "start_image_url": image_url,
            "prompt":          motion_prompt,
            "negative_prompt": "camera movement, zoom, pan, tilt, morph, distortion, flickering, color shift, blur, text animation, warping",
            "duration":        duration,
            "generate_audio":  False,
            "cfg_scale":       0.5,
        },
    )

    video = result.get("video", {})
    video_url = video.get("url", "")

    if not video_url:
        sys.exit("Error: No video returned from FAL.")

    slug     = product.lower().replace(" ", "-")
    out_path = _next_version(output_dir, slug)
    print("Downloading...")
    _save(video_url, out_path)

    print(f"\nSaved → {out_path}")


if __name__ == "__main__":
    main()
