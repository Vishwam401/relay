from PIL import Image, ImageDraw, ImageFont
import os

# Clean, professional dimensions for LinkedIn (1200 x 850)
W, H = 1200, 850

# Matte, authentic terminal dark theme (GitHub / Ray.so Dark Zinc style)
BG_COLOR = (18, 18, 20, 255)       # Solid matte charcoal
EDITOR_BG = (13, 13, 15, 255)      # Deep terminal black
BORDER_COLOR = (38, 38, 42, 255)   # Subtle 1px border
DIVIDER_COLOR = (28, 28, 32, 255)

img = Image.new('RGBA', (W, H), BG_COLOR)
draw = ImageDraw.Draw(img)

# Monospace font (Consolas) sized for perfect fit without clipping
font_mono = ImageFont.truetype('C:/Windows/Fonts/consola.ttf', 16)
font_mono_bold = ImageFont.truetype('C:/Windows/Fonts/consolab.ttf', 16)
font_col_title = ImageFont.truetype('C:/Windows/Fonts/consolab.ttf', 18)
font_mono_small = ImageFont.truetype('C:/Windows/Fonts/consola.ttf', 14)
font_ui = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 14)

# Outer terminal window container
pad_x = 40
pad_y = 40
card_w = W - (pad_x * 2)
card_h = H - (pad_y * 2)

draw.rounded_rectangle([pad_x, pad_y, pad_x + card_w, pad_y + card_h], radius=10, fill=EDITOR_BG, outline=BORDER_COLOR, width=1)

# Window title bar
title_bar_h = 42
draw.line([(pad_x, pad_y + title_bar_h), (pad_x + card_w, pad_y + title_bar_h)], fill=DIVIDER_COLOR, width=1)

# Subtle terminal window buttons (muted, not flashy)
dot_y = pad_y + 21
draw.ellipse([pad_x + 18, dot_y - 5, pad_x + 28, dot_y + 5], fill=(60, 60, 65, 255))
draw.ellipse([pad_x + 34, dot_y - 5, pad_x + 44, dot_y + 5], fill=(60, 60, 65, 255))
draw.ellipse([pad_x + 50, dot_y - 5, pad_x + 60, dot_y + 5], fill=(60, 60, 65, 255))

# Title bar text
bar_title = "PostgreSQL 16.14 · EXPLAIN query plan comparison under READ COMMITTED"
draw.text((pad_x + 75, pad_y + 12), bar_title, font=font_ui, fill=(130, 130, 140, 255))

# Center vertical divider
mid_x = W // 2
draw.line([(mid_x, pad_y + title_bar_h), (mid_x, pad_y + card_h - 48)], fill=DIVIDER_COLOR, width=1)

# Column coordinates
col1_x = pad_x + 28
col2_x = mid_x + 28
content_y = pad_y + title_bar_h + 24

# Column Headers
draw.text((col1_x, content_y), "VERSION 1: NAIVE CLAIM", font=font_col_title, fill=(244, 63, 94, 255))   # soft rose
draw.text((col2_x, content_y), "VERSION 2: GUARDED CLAIM", font=font_col_title, fill=(16, 185, 129, 255)) # soft emerald

start_code_y = content_y + 36
line_spacing = 28

plan_v1 = [
    "Update on jobs",
    "  InitPlan 1 (returns $0)",
    "    ->  Limit",
    "          ->  Sort (Sort Key: jobs_1.created_at, jobs_1.id)",
    "                ->  Seq Scan on jobs jobs_1",
    "                      Filter: (status = 'pending'::text)",
    "  ->  Index Scan using jobs_pkey on jobs",
    "        Index Cond: (id = $0)",
]

plan_v2 = [
    "Update on jobs",
    "  InitPlan 1 (returns $0)",
    "    ->  Limit",
    "          ->  Sort (Sort Key: jobs_1.created_at, jobs_1.id)",
    "                ->  Seq Scan on jobs jobs_1",
    "                      Filter: (status = 'pending'::text)",
    "  ->  Index Scan using jobs_pkey on jobs",
    "        Index Cond: (id = $0)",
    "        Filter: (status = 'pending'::text)   <-- THIS",
]

# Draw V1 Code
for i, line in enumerate(plan_v1):
    y = start_code_y + (i * line_spacing)
    if "Index Cond:" in line:
        draw.text((col1_x, y), line, font=font_mono_bold, fill=(244, 114, 182, 255)) # pink accent
    elif "Filter:" in line:
        draw.text((col1_x, y), line, font=font_mono, fill=(252, 211, 77, 255))     # amber
    elif "InitPlan" in line:
        draw.text((col1_x, y), line, font=font_mono, fill=(192, 132, 252, 255))    # purple
    elif "Update on" in line:
        draw.text((col1_x, y), line, font=font_mono_bold, fill=(56, 189, 248, 255))# cyan
    else:
        draw.text((col1_x, y), line, font=font_mono, fill=(161, 161, 170, 255))

# Draw V2 Code
for i, line in enumerate(plan_v2):
    y = start_code_y + (i * line_spacing)
    if "<-- THIS" in line:
        bbox = draw.textbbox((col2_x - 4, y - 3), line, font=font_mono_bold)
        draw.rounded_rectangle([bbox[0] - 4, bbox[1] - 2, bbox[2] + 8, bbox[3] + 4], radius=4, fill=(40, 32, 10, 255), outline=(234, 179, 8, 200), width=1)
        draw.text((col2_x, y), line, font=font_mono_bold, fill=(253, 224, 71, 255))
    elif "Index Cond:" in line:
        draw.text((col2_x, y), line, font=font_mono_bold, fill=(244, 114, 182, 255))
    elif "Filter:" in line:
        draw.text((col2_x, y), line, font=font_mono, fill=(252, 211, 77, 255))
    elif "InitPlan" in line:
        draw.text((col2_x, y), line, font=font_mono, fill=(192, 132, 252, 255))
    elif "Update on" in line:
        draw.text((col2_x, y), line, font=font_mono_bold, fill=(56, 189, 248, 255))
    else:
        draw.text((col2_x, y), line, font=font_mono, fill=(161, 161, 170, 255))

# Verdict / Outcome Section (Perfect tabular alignment, 120px label offset)
verdict_y = start_code_y + (10 * line_spacing) + 12
draw.line([(pad_x + 20, verdict_y - 12), (pad_x + card_w - 20, verdict_y - 12)], fill=DIVIDER_COLOR, width=1)
label_offset = 125

# V1 Verdict
draw.text((col1_x, verdict_y), "Outcome:", font=font_mono, fill=(113, 113, 122, 255))
draw.text((col1_x + label_offset, verdict_y), "claims the same row twice", font=font_mono_bold, fill=(251, 113, 133, 255))

draw.text((col1_x, verdict_y + 28), "Mechanism:", font=font_mono, fill=(113, 113, 122, 255))
draw.text((col1_x + label_offset, verdict_y + 28), "EvalPlanQual rechecks (id = $0) -> passes", font=font_mono, fill=(161, 161, 170, 255))

draw.text((col1_x, verdict_y + 54), "Table trace:", font=font_mono, fill=(113, 113, 122, 255))
draw.text((col1_x + label_offset, verdict_y + 54), "None. Row status='running' looks clean", font=font_mono, fill=(140, 140, 150, 255))

# V2 Verdict
draw.text((col2_x, verdict_y), "Outcome:", font=font_mono, fill=(113, 113, 122, 255))
draw.text((col2_x + label_offset, verdict_y), "rowcount = 0, correctly (safe)", font=font_mono_bold, fill=(52, 211, 153, 255))

draw.text((col2_x, verdict_y + 28), "Mechanism:", font=font_mono, fill=(113, 113, 122, 255))
draw.text((col2_x + label_offset, verdict_y + 28), "EvalPlanQual rechecks status='pending' -> fails", font=font_mono, fill=(161, 161, 170, 255))

draw.text((col2_x, verdict_y + 54), "Table trace:", font=font_mono, fill=(113, 113, 122, 255))
draw.text((col2_x + label_offset, verdict_y + 54), "Safe, but unblocked worker got 0 work", font=font_mono, fill=(140, 140, 150, 255))

# Bottom clean footnote bar
foot_y = pad_y + card_h - 36
draw.line([(pad_x, foot_y - 8), (pad_x + card_w, foot_y - 8)], fill=DIVIDER_COLOR, width=1)
draw.text((pad_x + 20, foot_y), "A predicate recheck only rechecks your predicate, not your intent.", font=font_mono_small, fill=(160, 160, 170, 255))
draw.text((pad_x + card_w - 295, foot_y), "Relay · github.com/Vishwam401/relay", font=font_mono_small, fill=(110, 110, 120, 255))

out_path = 'docs/blog/assets/plan_diff_linkedin.png'
img.save(out_path, 'PNG')
print(f'Successfully generated clean engineering visual: {out_path}')
