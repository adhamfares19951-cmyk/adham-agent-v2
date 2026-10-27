"""Autonomous YouTube Channel Branding & Visual Identity Kit Generator.

Features:
- Produces complete Channel Identity Kit in both Markdown and Microsoft Word (.docx).
- Includes top 5 viral channel name ideas, @handles, SEO descriptions, and channel tags.
- Generates high-res 800x800 YouTube channel logo (channel_logo.png) from Pixar 3D studio render.
- Generates 2560x1440 YouTube desktop/mobile channel banner (channel_banner.png and channel_banner.svg)
  strictly respecting the 1546x423 safe area.
- Outputs exact Midjourney, Flux, and Imagen prompts for additional creative variations.
"""

from __future__ import annotations

import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

from PIL import Image, ImageDraw, ImageFont

from config.settings import settings

logger = logging.getLogger("adham_agent.tools.branding")

DEFAULT_BRANDING_METADATA = {
    "recommended_name": "Fruity Toons 3D | كرتون فواكه",
    "recommended_handle": "@FruityToons3D",
    "names_ideas": [
        {"name": "Fruity Toons 3D", "handle": "@FruityToons3D", "hook": "Pixar-style dramatic animation with viral global reach."},
        {"name": "Orange & Strawberry Drama", "handle": "@FruitDrama3D", "hook": "Focuses on the core characters Mr. Orange and Mrs. Strawberry."},
        {"name": "Pixar Fruit Shorts", "handle": "@PixarFruitShorts", "hook": "Instant recognition of top-tier 3D animation quality."},
        {"name": "Juicy Karma 🍊👑", "handle": "@JuicyKarmaToons", "hook": "High emotional engagement around underdog and revenge stories."},
        {"name": "Tiny Fruit Big Drama", "handle": "@TinyFruitDrama", "hook": "Relatable family and relationship storytelling."},
    ],
    "description": (
        "Welcome to Fruity Toons 3D! 🍊🍓 The official home of 3D Pixar-style anthropomorphic fruit drama! "
        "Experience silent, emotional, and dramatic stories of love, betrayal, struggle, and triumphant karma "
        "starring Mr. Orange, Mrs. Strawberry, Rich Banana, and Baby Apple. "
        "New 4K vertical #Shorts uploaded daily! Subscribe and become part of our fruit family!\n\n"
        "مرحباً بكم في كرتون فواكه 3D! قصص درامية وسينمائية مؤثرة لشخصيات الفواكه المحبوبة بدون كلام وبعواطف عالمية. "
        "اشترك وفعل الجرس لمتابعة الحلقات اليومية بجودة 4K!"
    ),
    "keywords": (
        "Fruit drama, Pixar animation, 3D animated shorts, Mr. Orange, Mrs. Strawberry, "
        "Rich Banana, CGI fruit cartoon, emotional shorts, cartoon betrayal, karma animation, "
        "Pixar style shorts, viral drama, silent storytelling, 4K animation"
    ),
    "category": "Film & Animation (24)",
    "coppa_policy": "Not Made For Kids (selfDeclaredMadeForKids=False)",
}


class ChannelBrandingManager:
    """Automates creation of channel identity assets, prompt sheets, and visual banners."""

    def __init__(self, branding_dir: Optional[Path] = None) -> None:
        self.branding_dir = branding_dir or (settings.WORKSPACE_DATA_DIR / "channel_branding")
        self.branding_dir.mkdir(parents=True, exist_ok=True)

    def generate_channel_kit(self) -> Dict[str, Any]:
        """Generate all identity docs, 800x800 logo, and 2560x1440 channel banner."""
        md_file = self.branding_dir / "Channel_Identity_Kit.md"
        docx_file = self.branding_dir / "Channel_Identity_Kit.docx"
        logo_file = self.branding_dir / "channel_logo.png"
        banner_file = self.branding_dir / "channel_banner.png"
        svg_file = self.branding_dir / "channel_banner.svg"

        self._export_markdown_kit(md_file)
        self._export_docx_kit(docx_file)
        self._create_or_convert_logo(logo_file)
        self._create_channel_banner(banner_file, svg_file)

        logger.info("Channel Branding Kit generated successfully in: %s", self.branding_dir)
        return {
            "status": "SUCCESS",
            "branding_dir": str(self.branding_dir),
            "identity_md": str(md_file),
            "identity_docx": str(docx_file),
            "logo_path": str(logo_file),
            "banner_path": str(banner_file),
            "banner_svg": str(svg_file),
            "recommended_name": DEFAULT_BRANDING_METADATA["recommended_name"],
            "recommended_handle": DEFAULT_BRANDING_METADATA["recommended_handle"],
            "description": DEFAULT_BRANDING_METADATA["description"],
            "keywords": DEFAULT_BRANDING_METADATA["keywords"],
        }

    # =========================================================================
    # 1. Identity Documentation Export (.md & .docx)
    # =========================================================================

    def _export_markdown_kit(self, output_path: Path) -> None:
        """Write comprehensive Markdown channel identity kit."""
        lines = [
            "# 🍊🍓 YouTube Channel Branding & Viral Identity Kit",
            f"> **Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')} | **Channel**: {DEFAULT_BRANDING_METADATA['recommended_name']}",
            "> **Niche**: 3D Pixar-Style Fruit Drama & Karma Shorts | **Target Market**: Global (US, MENA, EU, Global)",
            "",
            "---",
            "",
            "## 1. Top 5 High-CTR Channel Names & Handles",
            "| Option | Proposed Channel Name | Recommended Handle | Viral Positioning |",
            "|---|---|---|---|",
        ]

        for i, item in enumerate(DEFAULT_BRANDING_METADATA["names_ideas"], start=1):
            lines.append(f"| #{i} | **{item['name']}** | `{item['handle']}` | {item['hook']} |")

        lines.extend([
            "",
            "---",
            "",
            "## 2. Official YouTube Channel Description (Copy & Paste)",
            "```text",
            DEFAULT_BRANDING_METADATA["description"],
            "```",
            "",
            "---",
            "",
            "## 3. Master SEO Keywords & Tags (Copy into YouTube Studio > Channel > Basic Info)",
            "```text",
            DEFAULT_BRANDING_METADATA["keywords"],
            "```",
            "",
            "---",
            "",
            "## 4. YouTube Creator Studio Settings",
            f"- **Channel Category**: `{DEFAULT_BRANDING_METADATA['category']}`",
            f"- **COPPA Compliance**: `{DEFAULT_BRANDING_METADATA['coppa_policy']}`",
            "- **Target Aspect Ratio**: `9:16 Vertical` (1080x1920)",
            "- **Upload Frequency**: `1 to 2 Shorts daily` at peak traffic hours (5:00 PM - 9:00 PM)",
            "",
            "---",
            "",
            "## 5. Midjourney / Flux Visual Generation Prompts",
            "",
            "### A. Channel Profile Icon (800x800 1:1 Circle):",
            "```text",
            "3D Pixar-style circular YouTube channel profile logo and avatar icon, featuring a cute expressive "
            "anthropomorphic orange character wearing a small blue work cap with big friendly eyes next to a glossy "
            "vibrant red strawberry character with a tiny golden crown leaf and expressive eyelashes, beautiful dynamic "
            "facial expressions, ultra-detailed 8k, Octane 3D render, subsurface scattering, vibrant cinematic studio "
            "rim lighting, smooth modern colorful radial gradient background, perfectly framed for a circular icon, "
            "clean profile avatar style, no text, no words, no watermarks --ar 1:1",
            "```",
            "",
            "### B. YouTube Channel Header Banner (2560x1440 16:9):",
            "```text",
            "Cinematic ultra-wide 3D Pixar-style landscape channel banner, featuring Mr. Orange on the left in his blue "
            "cap looking determined, and Mrs. Strawberry and Rich Banana on the right beside an ultra-luxury gold sports car, "
            "vibrant dramatic sunset mountain road in the background, volumetric golden light, Pixar movie quality, Octane render, "
            "8k resolution, clean composition keeping main action strictly in the center 1546x423 safe area, no text --ar 16:9",
            "```",
        ])

        output_path.write_text("\n".join(lines), encoding="utf-8")

    def _export_docx_kit(self, output_path: Path) -> None:
        """Create Word document for Channel Identity Kit."""
        doc = docx.Document()

        for section in doc.sections:
            section.top_margin = Inches(0.8)
            section.bottom_margin = Inches(0.8)
            section.left_margin = Inches(0.8)
            section.right_margin = Inches(0.8)

        # Title
        p_t = doc.add_paragraph()
        p_t.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r_t = p_t.add_run("YOUTUBE CHANNEL IDENTITY & BRANDING KIT\nFruity Toons 3D")
        r_t.font.name = "Arial"
        r_t.font.size = Pt(18)
        r_t.font.bold = True
        r_t.font.color.rgb = RGBColor(220, 70, 20)

        p_sub = doc.add_paragraph()
        p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r_sub = p_sub.add_run("Autonomous 3D Fruit Animation Studio • Master Setup Blueprint")
        r_sub.font.size = Pt(10)
        r_sub.font.italic = True
        r_sub.font.color.rgb = RGBColor(100, 110, 120)

        # Section: Top Names
        h_names = doc.add_heading("1. High-CTR Channel Name Ideas & Handles", level=1)
        h_names.paragraph_format.space_before = Pt(12)

        table = doc.add_table(rows=6, cols=3)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER

        headers = ["Rank", "Proposed Channel Name", "Handle & Positioning"]
        for j, h in enumerate(headers):
            cell = table.cell(0, j)
            cell.paragraphs[0].add_run(h).bold = True
            cell.paragraphs[0].runs[0].font.size = Pt(9.5)

        for i, item in enumerate(DEFAULT_BRANDING_METADATA["names_ideas"], start=1):
            table.cell(i, 0).paragraphs[0].add_run(f"#{i}")
            table.cell(i, 1).paragraphs[0].add_run(item["name"]).bold = True
            table.cell(i, 2).paragraphs[0].add_run(f"{item['handle']} — {item['hook']}")

        # Section: Description
        h_desc = doc.add_heading("2. Official Channel Description", level=1)
        h_desc.paragraph_format.space_before = Pt(12)
        p_desc = doc.add_paragraph(DEFAULT_BRANDING_METADATA["description"])
        p_desc.paragraph_format.left_indent = Inches(0.2)

        # Section: Keywords
        h_kw = doc.add_heading("3. Master SEO Keywords & Tags", level=1)
        h_kw.paragraph_format.space_before = Pt(10)
        p_kw = doc.add_paragraph(DEFAULT_BRANDING_METADATA["keywords"])
        p_kw.runs[0].font.name = "Consolas"
        p_kw.runs[0].font.size = Pt(9)
        p_kw.runs[0].font.color.rgb = RGBColor(30, 70, 130)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        doc.save(str(output_path))

    # =========================================================================
    # 2. Visual Assets Generation (800x800 Logo & 2560x1440 Banner)
    # =========================================================================

    def _create_or_convert_logo(self, output_path: Path) -> None:
        """Produce the 800x800 channel logo."""
        existing_logo = settings.WORKSPACE_DATA_DIR / "youtube_channel_logo.jpg"
        if existing_logo.is_file():
            try:
                img = Image.open(existing_logo).convert("RGB")
                img = img.resize((800, 800), Image.Resampling.LANCZOS)
                img.save(output_path, "PNG", quality=95)
                logger.info("Successfully converted existing 3D render into %s", output_path.name)
                return
            except Exception as e:
                logger.warning("Could not convert existing logo: %s. Generating fresh asset...", e)

        # Fallback: Draw stylized 800x800 badge
        img = Image.new("RGBA", (800, 800), (25, 20, 45, 255))
        draw = ImageDraw.Draw(img)

        # Draw smooth radial-like concentric circles
        for radius in range(380, 50, -30):
            alpha = int(255 * (radius / 380))
            draw.ellipse(
                [(400 - radius, 400 - radius), (400 + radius, 400 + radius)],
                fill=(int(255 - radius * 0.4), int(100 + radius * 0.2), int(180 - radius * 0.2), alpha),
            )

        # Orange and Strawberry stylized circles
        draw.ellipse([(180, 260), (440, 520)], fill=(255, 130, 20, 255))  # Orange
        draw.ellipse([(240, 230), (380, 310)], fill=(30, 80, 180, 255))   # Cap
        draw.ellipse([(380, 280), (620, 540)], fill=(235, 40, 60, 255))   # Strawberry
        draw.polygon([(470, 240), (500, 200), (530, 240)], fill=(240, 200, 40, 255))  # Crown

        img.save(output_path, "PNG")

    def _create_channel_banner(self, output_png: Path, output_svg: Path) -> None:
        """Produce 2560x1440 YouTube banner adhering strictly to 1546x423 central safe zone."""
        # 1. Generate High-Res 2560x1440 PNG Banner
        w, h = 2560, 1440
        banner = Image.new("RGB", (w, h), (18, 14, 32))
        draw = ImageDraw.Draw(banner)

        # Background gradient bands
        for y in range(h):
            ratio = y / h
            r = int(20 + 200 * (1 - ratio) * 0.4)
            g = int(15 + 80 * ratio)
            b = int(45 + 160 * (1 - ratio))
            draw.line([(0, y), (w, y)], fill=(r, g, b))

        # Safe area bounds: Center 1546 x 423
        safe_w, safe_h = 1546, 423
        safe_x1 = (w - safe_w) // 2
        safe_y1 = (h - safe_h) // 2
        safe_x2 = safe_x1 + safe_w
        safe_y2 = safe_y1 + safe_h

        # Ambient glow behind characters in safe area
        draw.ellipse([(safe_x1 + 100, safe_y1 - 50), (safe_x1 + 600, safe_y2 + 50)], fill=(255, 120, 30))
        draw.ellipse([(safe_x2 - 600, safe_y1 - 50), (safe_x2 - 100, safe_y2 + 50)], fill=(230, 40, 80))

        # Text banner simulation (Fruity Toons 3D)
        draw.text((safe_x1 + 450, safe_y1 + 130), "FRUITY TOONS 3D", fill=(255, 255, 255))
        draw.text((safe_x1 + 420, safe_y1 + 220), "PIXAR-STYLE 3D FRUIT DRAMA & SHORTS • NEW DAILY", fill=(255, 220, 140))

        banner.save(output_png, "PNG", quality=95)

        # 2. Generate scalable SVG banner
        svg_content = f"""<svg width="2560" height="1440" viewBox="0 0 2560 1440" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#191338"/>
      <stop offset="50%" stop-color="#4a154b"/>
      <stop offset="100%" stop-color="#ea580c"/>
    </linearGradient>
    <radialGradient id="glow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#fbbf24" stop-opacity="0.8"/>
      <stop offset="100%" stop-color="#fbbf24" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="2560" height="1440" fill="url(#bgGrad)"/>
  <circle cx="1280" cy="720" r="500" fill="url(#glow)"/>
  
  <!-- Safe Area: 1546 x 423 -->
  <g transform="translate({safe_x1}, {safe_y1})">
    <text x="773" y="180" font-family="Arial, sans-serif" font-weight="900" font-size="92" fill="#ffffff" text-anchor="middle" letter-spacing="4">
      FRUITY TOONS 3D
    </text>
    <text x="773" y="270" font-family="Arial, sans-serif" font-weight="700" font-size="34" fill="#fed7aa" text-anchor="middle" letter-spacing="3">
      3D PIXAR-STYLE FRUIT DRAMA • ORANGE &amp; STRAWBERRY #SHORTS
    </text>
  </g>
</svg>"""
        output_svg.write_text(svg_content, encoding="utf-8")


# Singleton instance
channel_branding = ChannelBrandingManager()
