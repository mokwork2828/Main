# Unlimited Ads — Setup Guide

Generate high-quality, brand-accurate ads for any product.
One product image in. One finished ad out.

---

## What You Need Before Starting

### 1. Claude Code
Download at [claude.ai/code](https://claude.ai/code) or install the extension inside VS Code / Cursor.
You'll need a free Anthropic account — sign up at [claude.ai](https://claude.ai).

### 2. A FAL API Key
Sign up at [fal.ai](https://fal.ai) → Dashboard → API Keys → copy your key.
Cost is roughly $0.12 per ad at high quality.

---

## Setup (5 minutes, once)

### Step 1 — Open the folder in Claude Code
Open Claude Code. Click **Open Folder** and select the `Unlimited Ads` folder you downloaded.

### Step 2 — Add your FAL key
Open the `.env` file inside the folder. Replace `your-key-here` with your FAL key:
```
FAL_KEY=sk-your-actual-key-here
```
Save the file.

### Step 3 — Install Python dependencies
Open the terminal inside Claude Code and run:
```
pip3 install fal-client requests
```

That's it for setup. Now you're ready to create ads.

---

## Creating Your First Ad

### Step 1 — Set up your brand
Type this in the Claude Code chat:
```
/brand-dna-builder
```
Claude will ask for your brand's website URL. Give it the URL and it will research the brand automatically — colors, photography style, visual rules. Takes about 2 minutes.

### Step 2 — Add your product image
After brand setup, Claude will tell you exactly where to drop your product image.
It will be a folder like: `workspace/brands/your-brand/product-images/`

Drop in one clean product photo. Name it clearly with lowercase and hyphens:
```
the-rice-wash.jpg
face-serum.jpg
black-hoodie.jpg
```

### Step 3 — Add reference ads (optional, but recommended)
Drop competitor ads or visual inspiration into:
`workspace/brands/your-brand/references/`

These can be screenshots of Instagram ads, competitor campaigns, anything that shows the visual direction you want. **5–8 images gives the best results.** The more consistent the style across references, the sharper the output.

### Step 4 — Generate your ad
Type in the chat:
```
/ad-generator
```
Claude will:
1. Analyze your reference images (if any)
2. Research how real customers talk about your product
3. Write a creative brief and show it to you
4. Wait for your approval before spending any credits
5. Generate the ad once you say go

Your ad is saved to: `workspace/brands/your-brand/ads/`

---

## Running More Ads

**Same brand, new product:**
Drop a new product image into `product-images/` and run `/ad-generator` again.
Claude will ask which product if there are multiple images.

**Same brand, different visual direction:**
Swap out the images in `references/` and run `/ad-generator`.

**New brand:**
Run `/brand-dna-builder` again with the new brand's URL.
Each brand gets its own folder and never interferes with others.

---

## Tips

- **The brief is your checkpoint.** Claude always pauses before generating. If the direction feels wrong, tell it what to change — don't just say go.
- **References make a real difference.** Without them the output is good. With 5–8 strong references it's significantly better.
- **One product image is enough.** Clean, front-facing, good resolution. The model reproduces the packaging accurately from a single shot.
- **Regenerating is cheap.** If you don't love the output, say what to change and regenerate. Each image is ~$0.12.

---

## Troubleshooting

**"FAL_KEY not found"**
Check your `.env` file — make sure there are no spaces around the `=` sign.

**"No brand found"**
You need to run `/brand-dna-builder` before `/ad-generator`.

**Generation fails with a server error**
FAL occasionally has brief outages. Wait 30 seconds and try again.

**The brand research came back thin**
Some brand websites block automated fetching. If this happens, Claude will ask you a few quick questions about the brand instead.
