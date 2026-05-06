# Unlimited Ads — AI Ad Generator

Generate high-quality, brand-accurate ads for any product. One product image in, one finished ad out.

Built on Claude Code + GPT Image 2 via FAL.

---

## What This Does

Give it a brand and a product image. It researches how real customers talk about the product, analyzes any competitor or inspiration ads you provide, writes a creative brief for your approval, then generates the ad.

Every ad is grounded in three things:
1. **Brand DNA** — visual rules, color system, photography style, voice
2. **Customer language** — what real people say about the product (not marketing copy)
3. **Reference intelligence** — what's working visually in the market (optional, but powerful)

---

## The Three Skills

### `/brand-dna-builder`
Run once per brand. Give it a website URL — it researches the brand, builds the visual brief, and sets up the folder structure. Takes 2–3 minutes.

### `/ad-generator`
Run whenever you want an ad. Picks up the brand DNA automatically, checks for reference images, researches the product, writes a brief, waits for your approval, then generates. One reference = one ad. Drop in 10 references, get 10 ads.

### `/ad-animator`
Run after `/ad-generator` to animate a static ad. Analyzes the image, identifies elements with natural movement, writes a motion brief for your approval, then generates a 5-second video via Kling 3.0.

---

## The Flow

```
1. Run /brand-dna-builder
   → Give it the brand URL
   → It saves workspace/brands/[brand]/visual-brief.md
   → It creates product-images/ and references/ folders

2. Drop your product image into:
   workspace/brands/[brand]/product-images/
   (one clean product shot, named clearly: the-rice-wash.jpg)

3. Drop reference ads into:
   workspace/brands/[brand]/references/
   (competitor ads, Pinterest, anything showing the visual direction you want)
   → Each reference becomes one ad — 10 references = 10 ads

4. Run /ad-generator
   → Analyzes every reference separately
   → Researches product + customer language
   → Writes one brief per reference → waits for your approval
   → Generates all ads in sequence

5. Optional — Run /ad-animator on any generated ad
   → Analyzes the image for natural motion
   → Writes a motion brief → waits for your approval
   → Generates a 5-second video via Kling 3.0

6. Output saved to:
   workspace/brands/[brand]/ads/[product-slug]_[timestamp]/ref-1/, ref-2/, etc.
```

---

## Folder Structure

```
Unlimited Ads/
├── CLAUDE.md                          ← you are here
├── .env                               ← add your FAL_KEY here
├── scripts/
│   ├── generate-ad.py                 ← generation script (don't edit)
│   └── animate-ad.py                  ← animation script (don't edit)
└── workspace/
    └── brands/
        └── [brand-name]/
            ├── visual-brief.md        ← created by /brand-dna-builder
            ├── product-images/        ← drop your product image here
            ├── references/            ← drop competitor/inspiration ads here
            └── ads/                   ← generated ads saved here
                └── [product]_[date]/
                    ├── ref-1/
                    │   ├── ad-spec.json
                    │   ├── [product]-v1.png
                    │   ├── motion-spec.json
                    │   └── [product]-v1.mp4
                    └── ref-2/ ...
```

---

## Setup

1. Get a FAL API key at fal.ai → Settings → API Keys
2. Open `.env` at the project root and replace `your-key-here` with your key
3. Install dependencies: `pip3 install fal-client requests`
4. Run `/brand-dna-builder` with your brand's URL
5. Drop in your product image and reference ads
6. Run `/ad-generator`
7. Run `/ad-animator` on any output you want as video

---

## Tips

- **References make a real difference.** 3–5 competitor or inspiration ads in the references/ folder gives the brief a visual target. Without them the generator works fine — with them it works better.
- **One product image is enough.** Clean, front-facing, good resolution. The model reproduces the packaging accurately from one shot.
- **The brief is your checkpoint.** The generator always pauses for approval before spending any credits. Read it — if the direction feels wrong, say so and adjust before generating.
- **Update brand DNA any time.** Run `/brand-dna-builder` again to overwrite the visual brief if the brand evolves or you want to refine the Generation Modifier.

---

## Skills Reference

| Skill | What it does | When to run |
|---|---|---|
| `/brand-dna-builder` | Researches brand, saves visual-brief.md, creates folder structure | Once per brand |
| `/ad-generator` | Analyzes refs, researches product, writes brief, generates ads | Every time you want ads |
| `/ad-animator` | Analyzes a generated ad, writes motion brief, generates video via Kling 3.0 | After /ad-generator |
