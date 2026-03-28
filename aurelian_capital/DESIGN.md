```markdown
# Design System Specification: The Digital Private Office

## 1. Overview & Creative North Star
The Creative North Star for this design system is **"The Digital Private Office."** 

We are moving away from the cluttered, high-frequency "trading terminal" aesthetic. Instead, we are building a space that feels like a high-end private banking suite—quiet, authoritative, and bespoke. This system rejects the generic "SaaS template" look in favor of a **High-End Editorial** experience. We achieve this through intentional asymmetry, extreme typographic contrast, and a rejection of traditional structural lines. Every pixel must feel like a conscious choice, not a default setting.

---

## 2. Colors: The Palette of Prestige
The color strategy is designed to balance the "Modern Minimalist" with "Traditional Wealth."

### Core Tones
- **Primary & Prestige:** We use `primary` (#745b00) and `primary_container` (#C5A021) to signify value. Gold is an accent, never a background. It is the "gold leaf" on the edge of a page.
- **The Bedrock:** `secondary` (#5e5e64) and its variants provide a deep slate-navy foundation that grounds the ethereal nature of the gold.
- **Market Semantics (A-Share Standard):**
    - **Positive/Gain:** `tertiary` (#bb171c) is our "China Red." It represents growth and prosperity.
    - **Negative/Retracement:** `error` (#ba1a1a) is strictly for loss and alerts. In this system, we interpret the "Green" requirement for A-share losses by utilizing a custom semantic mapping where necessary, though our core palette favors the sophisticated interplay of reds against slate.

### The "No-Line" Rule
**Explicit Instruction:** Designers are prohibited from using 1px solid borders to section content. Boundaries must be defined solely through background color shifts.
- To separate a section, place a `surface_container_low` (#f5f3f3) block against a `surface` (#fbf9f8) background. 
- Use tonal transitions to guide the eye. A border is a fence; a color shift is a horizon.

### Signature Textures & Glass
To provide "visual soul," use a subtle linear gradient on main CTAs: `primary` (#745b00) to `primary_container` (#c5a021) at a 135-degree angle. For floating overlays, apply **Glassmorphism**: use `surface_container_lowest` at 80% opacity with a `20px` backdrop blur to allow underlying slate tones to bleed through softly.

---

## 3. Typography: Editorial Authority
We utilize **Manrope** for its modern, geometric warmth and **Inter** for its technical precision.

- **The Power Scale:** Use `display-lg` (3.5rem) for portfolio totals and key wealth metrics. High-contrast sizing (pairing `display-lg` with `label-md`) creates the "Editorial" look found in premium finance journals.
- **Headlines & Titles:** `headline-lg` and `title-lg` use Manrope to convey a welcoming yet professional character.
- **Technical Precision:** Use `label-md` and `label-sm` (Inter) for all data points, tickers, and timestamps. Inter’s tall x-height ensures legibility in dense financial tables.
- **Hierarchy through Weight:** Avoid bolding everything. Use weight to distinguish "Action" (Medium/Semi-bold) from "Information" (Regular).

---

## 4. Elevation & Depth: Tonal Layering
Traditional shadows are often "dirty." We achieve depth through the **Layering Principle**.

### The Layering Principle
Depth is achieved by "stacking" the surface-container tiers.
- **Base Level:** `surface` (#fbf9f8).
- **In-Page Sections:** `surface_container_low` (#f5f3f3).
- **Floating Cards:** `surface_container_lowest` (#ffffff).
This creates a natural, soft lift that mimics fine stationery layered on a desk.

### Ambient Shadows
When a physical "float" is required (e.g., a primary action card), use an **Ambient Shadow**:
- **Color:** A tinted version of `on_surface` (e.g., #1b1c1c at 4-8% opacity).
- **Blur:** Large and diffused (20px to 40px). 
- Avoid tight, dark drop shadows which feel "cheap."

### The "Ghost Border" Fallback
If accessibility requires a container boundary, use a **Ghost Border**: `outline_variant` (#d0c5af) at 15% opacity. It should be felt, not seen.

---

## 5. Components: Refined Interaction

### Buttons
- **Primary:** Gold gradient (`primary` to `primary_container`) with `on_primary` (#ffffff) text. Radius: `md` (0.375rem).
- **Secondary:** Transparent background with a `Ghost Border` and `primary` text.
- **State Change:** On hover, increase the opacity of the `surface_tint` (#745b00) by 8%.

### Cards & Lists
- **The Divider Ban:** Never use horizontal lines to separate list items. Use the **Spacing Scale** `spacing-4` (1rem) as a vertical gutter, or alternate row colors between `surface` and `surface_container_low`.
- **Anatomy:** Cards use `rounded-lg` (0.5rem) and must rely on `surface_container_highest` for header backgrounds to distinguish metadata from content.

### Inputs & Fields
- **Modern Minimalist Style:** Inputs should not be boxes. Use a "bottom-line-only" approach or a subtle `surface_container_high` fill with no border. 
- **Error States:** Use `error` (#ba1a1a) text and a `surface_container_lowest` background to highlight the field, rather than a thick red border.

### Chips & Tags
- **Wealth Tags:** Use `secondary_container` (#e3e2e9) for neutral tags and `primary_fixed` (#ffe089) for "Premium" or "VIP" status indicators.

---

## 6. Do's and Don'ts

### Do:
- **Use Asymmetry:** Place a `display-lg` metric off-center to create a dynamic, modern layout.
- **Embrace White Space:** Use `spacing-12` (3rem) and `spacing-16` (4rem) to let high-value data "breathe."
- **Focus on Tonal Shifts:** Rely on the `surface` hierarchy for organization before considering any lines.

### Don't:
- **Don't use 100% Black:** Always use `on_surface` (#1b1c1c) for text to maintain a softer, premium contrast.
- **Don't use Standard Grids:** Break the grid with overlapping elements (e.g., a card slightly overlapping a hero background section) to create a custom, "crafted" feel.
- **Don't use 1px Dividers:** They cut the UI into pieces; we want the UI to feel like a continuous, flowing experience.
- **Don't Default to Shadows:** If the tonal shift between `surface_container_low` and `surface_container_lowest` is enough, omit the shadow entirely.

---
*Director's Final Note: This system is about the "Confidence of Silence." We do not need loud borders or bright colors to show value. The quality of the typography and the depth of the layers speak for the wealth they represent.*```