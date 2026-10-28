import math, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

WIDTH, HEIGHT = 1080, 1080
img = Image.new("RGBA", (WIDTH, HEIGHT), (11, 15, 25, 255))
draw = ImageDraw.Draw(img)

# 1. Background gradient / dark radial glow
glow_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
glow_draw = ImageDraw.Draw(glow_layer)

cx, cy = WIDTH // 2, HEIGHT // 2
for r in range(480, 50, -5):
    alpha = int(35 * (1 - r / 480))
    # Ambient purple/cyan blend
    glow_draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(138, 43, 226, alpha))

for r in range(260, 20, -5):
    alpha = int(50 * (1 - r / 260))
    glow_draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(0, 240, 255, alpha))

img = Image.alpha_composite(img, glow_layer)

# 2. Outer Neon Ring
ring_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
ring_draw = ImageDraw.Draw(ring_layer)

ring_r = 440
# Outer subtle border
ring_draw.ellipse([cx - ring_r, cy - ring_r, cx + ring_r, cy + ring_r], outline=(30, 41, 59, 255), width=4)
# Glowing accent arcs
ring_draw.arc([cx - ring_r, cy - ring_r, cx + ring_r, cy + ring_r], start=-45, end=45, fill=(0, 240, 255, 220), width=6)
ring_draw.arc([cx - ring_r, cy - ring_r, cx + ring_r, cy + ring_r], start=135, end=225, fill=(168, 85, 247, 220), width=6)

img = Image.alpha_composite(img, ring_layer)

# 3. Geometric 3D 'S' Symbol
symbol_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
sym_draw = ImageDraw.Draw(symbol_layer)

# Center of symbol slightly higher than center of canvas
scx, scy = cx, cy - 80

# Sleek connected polygon points for modern futuristic S / Infinity Tech
# Top loop of S
top_points = [
    (scx + 120, scy - 180),
    (scx - 80, scy - 180),
    (scx - 140, scy - 120),
    (scx - 140, scy - 40),
    (scx - 70, scy + 10),
    (scx + 70, scy + 10),
    (scx + 110, scy - 30),
    (scx + 50, scy - 30),
    (scx + 20, scy - 10),
    (scx - 60, scy - 10),
    (scx - 80, scy - 50),
    (scx - 80, scy - 110),
    (scx - 50, scy - 130),
    (scx + 120, scy - 130)
]

# Draw smooth curves for S using polygons and thick smooth lines
# We can draw layered thick bezier-like arcs or stylized angular geometric ribbons:
# Ribbon 1 (Top right to center): Cyan
sym_draw.line([(scx + 130, scy - 160), (scx - 50, scy - 160), (scx - 120, scy - 90), 
               (scx - 120, scy - 20), (scx + 60, scy + 20), (scx + 120, scy + 80), 
               (scx + 120, scy + 150), (scx + 50, scy + 210), (scx - 130, scy + 210)], 
              fill=(0, 240, 255, 255), width=36, joint="curve")

# Ribbon 2 (Inner glowing core): Purple/Violet
sym_draw.line([(scx + 120, scy - 150), (scx - 40, scy - 150), (scx - 110, scy - 90), 
               (scx - 110, scy - 30), (scx + 50, scy + 20), (scx + 110, scy + 80), 
               (scx + 110, scy + 140), (scx + 40, scy + 200), (scx - 120, scy + 200)], 
              fill=(168, 85, 247, 240), width=18, joint="curve")

# Inner high-intensity energy line (Pure white / electric cyan)
sym_draw.line([(scx + 110, scy - 150), (scx - 30, scy - 150), (scx - 100, scy - 90), 
               (scx - 100, scy - 30), (scx + 40, scy + 20), (scx + 100, scy + 80), 
               (scx + 100, scy + 130), (scx + 30, scy + 190), (scx - 110, scy + 190)], 
              fill=(255, 255, 255, 230), width=6, joint="curve")

# Futuristic lightning notch in the center
sym_draw.polygon([
    (scx - 10, scy - 10),
    (scx + 35, scy - 30),
    (scx + 10, scy + 5),
    (scx + 45, scy + 5),
    (scx - 15, scy + 45),
    (scx, scy + 15),
    (scx - 25, scy + 15)
], fill=(255, 220, 50, 255))

# Add slight blur glow to symbol layer and merge
sym_glow = symbol_layer.filter(ImageFilter.GaussianBlur(radius=8))
img = Image.alpha_composite(img, sym_glow)
img = Image.alpha_composite(img, symbol_layer)

# 4. Typography
text_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
txt_draw = ImageDraw.Draw(text_layer)

font_paths = [
    "C:/Windows/Fonts/bahnschrift.ttf",
    "C:/Windows/Fonts/segoeuib.ttf",
    "C:/Windows/Fonts/arialbd.ttf"
]
font_main = None
font_sub = None
font_gcc = None

for fp in font_paths:
    if os.path.exists(fp):
        try:
            font_main = ImageFont.truetype(fp, 72)
            font_sub = ImageFont.truetype(fp, 26)
            font_gcc = ImageFont.truetype(fp, 32)
            break
        except Exception:
            continue

if not font_main:
    font_main = ImageFont.load_default()
    font_sub = ImageFont.load_default()
    font_gcc = ImageFont.load_default()

# SMART STORE text
title = "SMART STORE"
bbox = txt_draw.textbbox((0, 0), title, font=font_main)
tw = bbox[2] - bbox[0]
txt_draw.text((cx - tw // 2, cy + 220), title, font=font_main, fill=(255, 255, 255, 255))

# Tagline / Handle: @smartstore.gcc
sub = "GCC • INNOVATION & TECH"
sbox = txt_draw.textbbox((0, 0), sub, font=font_sub)
sw = sbox[2] - sbox[0]
txt_draw.text((cx - sw // 2, cy + 310), sub, font=font_sub, fill=(0, 240, 255, 200))

# Small Badge: @smartstore.gcc
handle = "@smartstore.gcc"
hbox = txt_draw.textbbox((0, 0), handle, font=font_gcc)
hw = hbox[2] - hbox[0]
badge_pad = 18
badge_x1 = cx - hw // 2 - badge_pad
badge_y1 = cy + 355
badge_x2 = cx + hw // 2 + badge_pad
badge_y2 = cy + 405

txt_draw.rounded_rectangle([badge_x1, badge_y1, badge_x2, badge_y2], radius=15, 
                           fill=(19, 27, 46, 220), outline=(168, 85, 247, 180), width=2)
txt_draw.text((cx - hw // 2, cy + 363), handle, font=font_gcc, fill=(255, 255, 255, 240))

img = Image.alpha_composite(img, text_layer)

# Convert to RGB for saving high quality PNG & JPEG
final_img = img.convert("RGB")
out_dir = "C:/Projects/adham-agent/workspace_data"
os.makedirs(out_dir, exist_ok=True)
png_path = os.path.join(out_dir, "smartstore_logo.png")
jpg_path = os.path.join(out_dir, "smartstore_logo.jpg")

final_img.save(png_path, "PNG", quality=100)
final_img.save(jpg_path, "JPEG", quality=95)

# Also save copy in web_platform
web_logo = "C:/Projects/adham-agent/web_platform/logo.png"
final_img.save(web_logo, "PNG", quality=100)

print("Logo saved successfully to:", png_path)
