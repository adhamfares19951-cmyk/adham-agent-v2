"""Production Storyboard & AI Video Prompt Sheet Exporter.

Features:
- Exports clean, copy-paste-ready Markdown storyboard files into workspace_data/youtube_ready/Storyboard_<video_id>.md.
- Generates elegant Microsoft Word (.docx) production sheets into workspace_data/youtube_ready/Storyboard_<video_id>.docx.
- Formats Midjourney/Flux image prompts, Kling/Runway motion prompts, and audio SFX cues scene by scene.
- Automatically invoked when YouTubeAgent authors new viral fruit animation scripts.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

from config.settings import settings

logger = logging.getLogger("adham_agent.tools.studio_exporter")


class StudioExporter:
    """Production storyboard and AI prompt sheet generator for video creation workflows."""

    def __init__(self, output_dir: Optional[Path] = None) -> None:
        self.output_dir = output_dir or settings.youtube_ready_dir

    def _build_sfx_timeline(self, pkg: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Compute exact start and end timestamps for multi-layer Foley sound design."""
        scenes = pkg.get("scenes", [])
        timeline = []
        current_time = 0.0
        for s in scenes:
            dur = float(s.get("duration_seconds", 4.0))
            timeline.append({
                "scene_number": s.get("scene_number", len(timeline) + 1),
                "character_name": s.get("character_name", "Character"),
                "start_time": round(current_time, 2),
                "end_time": round(current_time + dur, 2),
                "duration": dur,
                "cue": s.get("sound_effect_cue", "Dramatic impact"),
                "audio_layer": "Layer 3 (Foley SFX Accent)",
                "mix_level": "0.85 (-2dB, ducking ambient)",
            })
            current_time += dur
        return timeline

    def export_storyboard(
        self,
        video_id: int,
        package: Any,
        characters: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Export both Markdown and Word (.docx) storyboard production files with sound design cues."""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Normalize package to dict or model access
        pkg_data = package.model_dump() if hasattr(package, "model_dump") else (
            package if isinstance(package, dict) else dict(package)
        )

        md_path = self.output_dir / f"Storyboard_{video_id}.md"
        docx_path = self.output_dir / f"Storyboard_{video_id}.docx"
        sfx_timeline = self._build_sfx_timeline(pkg_data)

        self._export_markdown(video_id, pkg_data, characters or [], sfx_timeline, md_path)
        self._export_docx(video_id, pkg_data, sfx_timeline, docx_path)

        logger.info(
            "Storyboard #%d exported successfully to:\n- MD: %s\n- DOCX: %s",
            video_id,
            md_path.name,
            docx_path.name,
        )

        return {
            "video_id": str(video_id),
            "md_path": str(md_path),
            "docx_path": str(docx_path),
            "title": pkg_data.get("title", ""),
            "sfx_cues": sfx_timeline,
        }

    # =========================================================================
    # 1. Markdown Production Storyboard Export
    # =========================================================================

    def _export_markdown(
        self,
        video_id: int,
        pkg: Dict[str, Any],
        characters: List[Dict[str, Any]],
        sfx_timeline: List[Dict[str, Any]],
        output_file: Path,
    ) -> None:
        """Write clean, copy-paste-ready Markdown storyboard with isolated prompt codeblocks."""
        scenes = pkg.get("scenes", [])
        title = pkg.get("title", "Untitled YouTube Short")
        theme = pkg.get("theme", "Viral Drama")
        hook = pkg.get("hook_description", "")
        description = pkg.get("description", "")
        tags = pkg.get("tags", [])
        tags_str = ", ".join(f"#{t.lstrip('#')}" for t in tags)

        total_duration = sum(float(s.get("duration_seconds", 4.0)) for s in scenes)

        lines: List[str] = [
            f"# 🎬 Production Storyboard: {title}",
            f"> **Video ID**: #{video_id} | **Target Duration**: ~{total_duration:.1f}s | **Created**: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"> **Theme**: {theme} | **COPPA**: Made For Kids = False (Monetization & Comments Active)",
            "",
            "---",
            "",
            "## 📌 Executive Production Summary",
            f"- **High-CTR Title**: `{title}`",
            f"- **3-Second Scroll-Stop Hook**: {hook}",
            f"- **SEO Description**:\n```text\n{description}\n```",
            f"- **Tags**: {tags_str}",
            "",
        ]

        if characters:
            lines.extend([
                "---",
                "",
                "## 🎨 3D Character Continuity Blueprints",
                "Ensure every image generation uses the exact visual prompt below:",
                "",
            ])
            for char in characters:
                lines.extend([
                    f"### Character: **{char.get('name', 'Actor')}** ({char.get('role', 'Protagonist')})",
                    "```text",
                    char.get("visual_prompt", ""),
                    "```",
                    "",
                ])

        if sfx_timeline:
            lines.extend([
                "---",
                "",
                "## 🎧 Multi-Layer Sound Design & Foley Cue Sheet (FFmpeg Assembly Layering)",
                "Precise timecodes and audio mixing hierarchy for high-impact sound design:",
                "",
                "| Scene # | Timecode (Start - End) | Character | Foley & Audio SFX Cue | Audio Layer Priority | Mix Level |",
                "|---|---|---|---|---|---|",
            ])
            for cue_item in sfx_timeline:
                s_num = cue_item["scene_number"]
                tc = f"{cue_item['start_time']:.1f}s - {cue_item['end_time']:.1f}s"
                c_name = cue_item["character_name"]
                sfx_txt = cue_item["cue"]
                layer = cue_item["audio_layer"]
                mix = cue_item["mix_level"]
                lines.append(f"| Scene {s_num} | `{tc}` | **{c_name}** | *{sfx_txt}* | {layer} | `{mix}` |")
            lines.append("")

        lines.extend([
            "---",
            "",
            "## 🎥 Scene-by-Scene AI Generation Prompts",
            "Copy and paste directly into Midjourney / Flux (for images) and Kling / Runway Gen-3 (for motion):",
            "",
        ])

        for scene in scenes:
            num = scene.get("scene_number", 1)
            char_name = scene.get("character_name", "Character")
            dur = scene.get("duration_seconds", 4.0)
            action = scene.get("action_description", "")
            img_prompt = scene.get("full_image_prompt", "")
            motion_prompt = scene.get("motion_camera_prompt", "")
            sfx = scene.get("sound_effect_cue", "")

            lines.extend([
                f"### 📍 Scene {num}: {char_name} (~{dur}s)",
                f"**Dramatic Action**: {action}",
                "",
                "**1. Midjourney / Flux Image Prompt** (Copy & Paste):",
                "```text",
                img_prompt,
                "```",
                "",
                "**2. Kling / Runway Motion & Camera Direction** (Copy & Paste):",
                "```text",
                motion_prompt,
                "```",
                "",
                f"**3. 🔊 Sound Effect (SFX)**: *{sfx}*",
                "",
                "---",
                "",
            ])

        output_file.write_text("\n".join(lines), encoding="utf-8")

    # =========================================================================
    # 2. Microsoft Word (.docx) Production Sheet Export
    # =========================================================================

    def _export_docx(
        self,
        video_id: int,
        pkg: Dict[str, Any],
        sfx_timeline: List[Dict[str, Any]],
        output_file: Path,
    ) -> None:
        """Create a beautifully formatted Word document production sheet with audio layering."""
        doc = docx.Document()

        # Page margins
        for section in doc.sections:
            section.top_margin = Inches(0.75)
            section.bottom_margin = Inches(0.75)
            section.left_margin = Inches(0.8)
            section.right_margin = Inches(0.8)

        # Title
        title_text = pkg.get("title", "YouTube Short Storyboard")
        p_title = doc.add_paragraph()
        p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run_title = p_title.add_run(f"PRODUCTION STORYBOARD #{video_id}\n{title_text}")
        run_title.font.name = "Arial"
        run_title.font.size = Pt(18)
        run_title.font.bold = True
        run_title.font.color.rgb = RGBColor(20, 30, 55)

        # Subtitle
        p_sub = doc.add_paragraph()
        p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run_sub = p_sub.add_run("Autonomous 3D Fruit Drama Studio • Multi-Modal Generation Package")
        run_sub.font.name = "Arial"
        run_sub.font.size = Pt(10)
        run_sub.font.italic = True
        run_sub.font.color.rgb = RGBColor(100, 110, 125)

        doc.add_paragraph().paragraph_format.space_after = Pt(8)

        # Metadata Table
        table = doc.add_table(rows=4, cols=2)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False

        meta_rows = [
            ("Narrative Theme", pkg.get("theme", "Drama")),
            ("3-Second Scroll-Stop Hook", pkg.get("hook_description", "")),
            ("SEO Tags", ", ".join(pkg.get("tags", []))),
            ("COPPA & Monetization", "selfDeclaredMadeForKids = False (Monetization & Comments Enabled)"),
        ]

        for i, (k, v) in enumerate(meta_rows):
            cell_k = table.cell(i, 0)
            cell_v = table.cell(i, 1)
            cell_k.width = Inches(2.0)
            cell_v.width = Inches(4.8)

            p_k = cell_k.paragraphs[0]
            r_k = p_k.add_run(k)
            r_k.bold = True
            r_k.font.size = Pt(9.5)
            r_k.font.color.rgb = RGBColor(40, 50, 70)

            p_v = cell_v.paragraphs[0]
            r_v = p_v.add_run(v)
            r_v.font.size = Pt(9.5)

        doc.add_paragraph().paragraph_format.space_after = Pt(12)

        # Sound Design Section in Word Document
        if sfx_timeline:
            h_audio = doc.add_heading("Multi-Layer Sound Design & Foley Cue Sheet", level=1)
            h_audio.paragraph_format.space_before = Pt(12)
            h_audio.paragraph_format.space_after = Pt(6)

            audio_table = doc.add_table(rows=len(sfx_timeline) + 1, cols=4)
            audio_table.alignment = WD_TABLE_ALIGNMENT.CENTER
            audio_table.autofit = False

            headers = ["Scene / Timecode", "Character", "Foley SFX Cue", "Mix Priority"]
            widths = [Inches(1.8), Inches(1.5), Inches(2.3), Inches(1.2)]
            for col_idx, h_text in enumerate(headers):
                cell = audio_table.cell(0, col_idx)
                cell.width = widths[col_idx]
                p = cell.paragraphs[0]
                r = p.add_run(h_text)
                r.bold = True
                r.font.size = Pt(9.5)
                r.font.color.rgb = RGBColor(20, 30, 60)

            for row_idx, item in enumerate(sfx_timeline, 1):
                tc = f"Scene {item['scene_number']} ({item['start_time']:.1f}s-{item['end_time']:.1f}s)"
                vals = [tc, item['character_name'], item['cue'], item['audio_layer']]
                for col_idx, val in enumerate(vals):
                    cell = audio_table.cell(row_idx, col_idx)
                    cell.width = widths[col_idx]
                    p = cell.paragraphs[0]
                    r = p.add_run(val)
                    r.font.size = Pt(9.0)

            doc.add_paragraph().paragraph_format.space_after = Pt(12)

        doc.add_paragraph().paragraph_format.space_after = Pt(12)

        # Scenes Section
        h_scenes = doc.add_heading("Scene Breakdown & Prompt Directory", level=1)
        h_scenes.paragraph_format.space_before = Pt(12)
        h_scenes.paragraph_format.space_after = Pt(8)

        scenes = pkg.get("scenes", [])
        for scene in scenes:
            num = scene.get("scene_number", 1)
            char_name = scene.get("character_name", "Fruit Character")
            dur = scene.get("duration_seconds", 4.0)
            action = scene.get("action_description", "")
            img_prompt = scene.get("full_image_prompt", "")
            motion_prompt = scene.get("motion_camera_prompt", "")
            sfx = scene.get("sound_effect_cue", "")

            # Scene Header
            p_scene_h = doc.add_paragraph()
            r_sh = p_scene_h.add_run(f"Scene {num}: {char_name} ({dur}s)")
            r_sh.font.name = "Arial"
            r_sh.font.size = Pt(12)
            r_sh.font.bold = True
            r_sh.font.color.rgb = RGBColor(180, 50, 20)
            p_scene_h.paragraph_format.space_before = Pt(10)
            p_scene_h.paragraph_format.space_after = Pt(2)

            # Action
            p_act = doc.add_paragraph()
            r_act_lbl = p_act.add_run("Action & Expression: ")
            r_act_lbl.bold = True
            r_act_lbl.font.size = Pt(10)
            r_act_val = p_act.add_run(action)
            r_act_val.font.size = Pt(10)
            p_act.paragraph_format.space_after = Pt(4)

            # Image Prompt Box
            p_img_lbl = doc.add_paragraph()
            r_il = p_img_lbl.add_run("Midjourney / Flux Image Prompt:")
            r_il.bold = True
            r_il.font.size = Pt(9.5)
            r_il.font.color.rgb = RGBColor(30, 70, 140)
            p_img_lbl.paragraph_format.space_after = Pt(2)

            p_img = doc.add_paragraph()
            p_img.paragraph_format.left_indent = Inches(0.2)
            r_img = p_img.add_run(img_prompt)
            r_img.font.name = "Consolas"
            r_img.font.size = Pt(8.5)
            r_img.font.color.rgb = RGBColor(60, 60, 60)
            p_img.paragraph_format.space_after = Pt(4)

            # Motion Prompt Box
            p_mot_lbl = doc.add_paragraph()
            r_ml = p_mot_lbl.add_run("Kling / Runway Camera Motion Prompt:")
            r_ml.bold = True
            r_ml.font.size = Pt(9.5)
            r_ml.font.color.rgb = RGBColor(30, 110, 80)
            p_mot_lbl.paragraph_format.space_after = Pt(2)

            p_mot = doc.add_paragraph()
            p_mot.paragraph_format.left_indent = Inches(0.2)
            r_mot = p_mot.add_run(motion_prompt)
            r_mot.font.name = "Consolas"
            r_mot.font.size = Pt(8.5)
            r_mot.font.color.rgb = RGBColor(60, 60, 60)
            p_mot.paragraph_format.space_after = Pt(4)

            # SFX Cue
            p_sfx = doc.add_paragraph()
            r_sfx_lbl = p_sfx.add_run("Sound Effect (SFX): ")
            r_sfx_lbl.bold = True
            r_sfx_lbl.font.size = Pt(9.5)
            r_sfx_val = p_sfx.add_run(sfx)
            r_sfx_val.italic = True
            r_sfx_val.font.size = Pt(9.5)
            p_sfx.paragraph_format.space_after = Pt(8)

        output_file.parent.mkdir(parents=True, exist_ok=True)
        doc.save(str(output_file))


# Singleton instance
studio_exporter = StudioExporter()
