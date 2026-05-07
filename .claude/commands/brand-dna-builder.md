Run once per brand to research its visual identity and set up the workspace folder structure.

## Steps

1. Ask the user for the brand's website URL if not already provided.

2. Research the brand by fetching the website and any linked pages (about, products, press, Instagram if findable). Look for:
   - Brand name and one-line description
   - Color palette (exact hex codes if possible, otherwise descriptive)
   - Typography style (serif vs sans-serif, weight, feel)
   - Photography style (mood, lighting, backgrounds, composition)
   - Visual rules (what they always do, what they never do)
   - Brand voice (adjectives, tone, what they sound like)
   - Target customer (who buys this, how they talk about it)
   - Price positioning (luxury / mid-range / mass)

3. Determine a clean brand slug from the brand name (lowercase, hyphens, no spaces). Example: "Polène Paris" → `polene-paris`.

4. Create the following folder structure inside `brands/Unlimited Ads - Clean/workspace/brands/[brand-slug]/`:
   - `product-images/` (empty, ready for product photos)
   - `references/` (empty, ready for competitor/inspiration ads)
   - `ads/` (empty, where generated ads will be saved)

5. Write `brands/Unlimited Ads - Clean/workspace/brands/[brand-slug]/visual-brief.md` with this structure:

```
# [Brand Name] — Visual Brief

## Brand Overview
[One paragraph: what it is, who it's for, price point, vibe]

## Color Palette
- Primary: [color name] — #[hex]
- Secondary: [color name] — #[hex]
- Accent: [color name] — #[hex]
- Text: [color name] — #[hex]
- Background: [color name] — #[hex]

## Typography
- Headlines: [description]
- Body: [description]
- Style notes: [anything notable]

## Photography Style
[2–3 sentences describing lighting, mood, backgrounds, compositions, what makes their images recognizable]

## Visual Rules
**Always:**
- [rule]
- [rule]

**Never:**
- [rule]
- [rule]

## Brand Voice
[2 sentences on tone, language style, what they sound like in copy]

## Target Customer
[Who buys this. How they talk about it. What they care about.]

## Generation Modifier
[A compact visual instruction string for the image model — distills the above into a tight style directive. Example: "clean white backgrounds, warm natural light, soft shadows, minimal composition, luxury feel, no text overlays, editorial-grade product photography"]
```

6. Tell the user:
   - The brand slug used
   - Where the visual brief was saved
   - Where to drop their product image (`product-images/`)
   - Where to drop reference ads (`references/`) and that 5–8 references gives the best results
   - That they can run `/ad-generator` when ready
