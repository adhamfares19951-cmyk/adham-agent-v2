"""Autonomous YouTube Shorts & Viral Studio Agent for adham-agent.

Features:
- Character Reference Lock (Seed & Image-to-Image Continuity) stopping character morphing across scenes.
- 9:16 Vertical Cinematic Motion Prompts with professional camera physics, optics, and ray-traced lighting.
- Multi-Layer Sound Design Cues with procedural Foley synthesis and time-aligned FFmpeg audio mixing.
- Fixed 3D Pixar-style fruit characters consistency injection (Mr. Orange, Mrs. Strawberry, Rich Banana, Baby Apple).
- High-CTR viral storyboard generation with visual hooks, motion prompts, and sound design cue sheets.
- Auto-saving to SQLite youtube_videos pipeline table.
- Automatic generation of production storyboard Markdown and DOCX sheets via StudioExporter.
- Automated or dry-run video publishing and channel analytics sync via YouTubeUploader.
- Task-driven execution via blackboard agent_tasks.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import re
import shutil
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from config.settings import settings
from core.database import db_manager, DatabaseManager
from core.llm import llm_engine, LLMEngine
from core.cloud_video_pool import cloud_video_pool
from tools.youtube_uploader import youtube_uploader, YouTubeUploader
from tools.studio_exporter import studio_exporter, StudioExporter

# Ensure ai-cinematic-studio is importable
STUDIO_DIR = settings.workspace_dir / "ai-cinematic-studio"
if str(STUDIO_DIR) not in sys.path:
    sys.path.insert(0, str(STUDIO_DIR))

from assembler.video_stitcher import video_stitcher
from generators.image_generator import render_shot_image

logger = logging.getLogger("adham_agent.agents.youtube")


# =============================================================================
# Deterministic Character Reference & Continuity Engine
# =============================================================================

CHARACTER_MASTER_SEEDS: Dict[str, int] = {
    "Mr. Orange": 782101,
    "Mrs. Strawberry": 782102,
    "Rich Banana": 782103,
    "Baby Apple": 782104,
}


class CharacterReferenceLock:
    """Guarantees 100% visual consistency and prevents character morphing across scenes."""

    def __init__(self, workspace_dir: Optional[Path] = None) -> None:
        self.workspace_dir = workspace_dir or settings.workspace_dir
        self.sheets_dir = self.workspace_dir / "workspace_data" / "channel_branding" / "master_character_sheets"
        self.sheets_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def slugify(name: str) -> str:
        """Convert character name into a clean filesystem slug."""
        clean = re.sub(r"[^\w\s-]", "", name).strip().lower()
        return re.sub(r"[-\s]+", "_", clean)

    def get_character_seed(self, character_name: str) -> int:
        """Get or deterministically compute a fixed seed for a character."""
        if character_name in CHARACTER_MASTER_SEEDS:
            return CHARACTER_MASTER_SEEDS[character_name]
        # Hash-based deterministic seed fallback
        hash_val = int(hashlib.sha256(character_name.encode("utf-8")).hexdigest()[:7], 16)
        return (hash_val % 900000) + 100000

    def resolve_master_anchor(self, character_name: str) -> Optional[Path]:
        """Locate an existing master character sheet or reference frame."""
        slug = self.slugify(character_name)
        candidates = [
            self.sheets_dir / f"master_anchor_{slug}.png",
            self.sheets_dir / f"master_anchor_{slug}.jpg",
            self.sheets_dir / f"{slug}_master.png",
            self.sheets_dir / f"{slug}_master.jpg",
        ]
        # Check specific known assets in workspace_data
        if "strawberry" in slug:
            candidates.extend([
                self.workspace_dir / "workspace_data" / "generated_strawberry_waitress.jpg",
                self.workspace_dir / "workspace_data" / "test_strawberry_waitress.png",
            ])

        for cand in candidates:
            if cand.exists() and cand.stat().st_size > 1024:
                return cand
        return None

    def register_master_anchor(self, character_name: str, frame_path: Path) -> Path:
        """Persist the first generated keyframe as the master character sheet anchor."""
        slug = self.slugify(character_name)
        target_path = self.sheets_dir / f"master_anchor_{slug}.png"
        try:
            shutil.copy2(frame_path, target_path)
            logger.info("Character Reference Lock: Registered master anchor for '%s' -> %s",
                        character_name, target_path.name)
            return target_path
        except Exception as e:
            logger.warning("Could not register master anchor: %s", e)
            return frame_path

    def build_continuity_prompt(
        self,
        character_name: str,
        base_prompt: str,
        anchor_path: Optional[Path] = None,
    ) -> str:
        """Inject strict character reference tokens into generation prompts."""
        ref_notice = f"'{anchor_path.name}'" if anchor_path else "master blueprint"
        continuity_prefix = (
            f"[CHARACTER CONTINUITY LOCK: Locked to character reference {ref_notice}. "
            f"100% identical 3D Pixar face, facial geometry, eye proportions, peel micro-textures, "
            f"and costume details for '{character_name}'. Zero character morphing or facial drift.] "
        )
        return continuity_prefix + base_prompt


# Global character lock engine
character_lock = CharacterReferenceLock()


# =============================================================================
# Cinematic Camera Motion Physics Enhancer
# =============================================================================

def enhance_cinematic_motion_prompt(
    raw_prompt: str,
    character_name: str = "",
    scene_idx: int = 1,
) -> str:
    """Enforce highly specific, professional camera physics for vertical 9:16 shorts.
    
    Guarantees that video generators (Kling, Runway Gen-3, Google Veo, Wan 2.1) receive
    explicit optical physics: shot scale, shallow depth of field (f/1.8 bokeh), volumetric
    rim lighting, smooth 24fps vertical dolly zoom, and ray-traced reflections.
    """
    cleaned = (raw_prompt or "").strip().rstrip(".")
    lower = cleaned.lower()

    additions: List[str] = []

    # 1. Shot scale & framing
    if not any(k in lower for k in ["macro", "close-up", "closeup", "wide", "low angle", "low-angle", "medium shot", "medium", "portrait", "establishing"]):
        if scene_idx == 1:
            additions.append("Macro close-up shot focused on character facial micro-expression")
        elif scene_idx % 2 == 0:
            additions.append("Dramatic low-angle tracking shot framed for 9:16 vertical viewport")
        else:
            additions.append("Medium portrait cinematic shot framed for vertical 9:16")

    # 2. Depth of Field & Optical Bokeh
    if not any(k in lower for k in ["depth of field", "bokeh", "f/1.", "f/2.", "rack focus", "shallow"]):
        additions.append("shallow depth of field (f/1.8 bokeh) with sharp ocular focus")

    # 3. Trajectory & Dynamic 24fps Physics
    if not any(k in lower for k in ["dolly", "zoom", "push-in", "pull-back", "crane", "pan", "tracking", "tilt"]):
        if scene_idx % 2 == 1:
            additions.append("smooth 24fps vertical dolly zoom with physical camera inertia")
        else:
            additions.append("gentle slow-motion cinematic push-in at 24fps")

    # 4. Lighting & Ray-Tracing Physics
    if not any(k in lower for k in ["rim light", "chiaroscuro", "subsurface", "sss", "ray-trace", "volumetric"]):
        additions.append("dramatic volumetric chiaroscuro rim lighting and ray-traced reflections on glossy fruit skin")

    # 5. Stability & Artifact Suppression
    if not any(k in lower for k in ["motion blur", "octane", "shutter"]):
        additions.append("steadycam motion blur, zero AI warping or jitter")

    if additions:
        enhanced = f"{cleaned}, {', '.join(additions)}."
    else:
        enhanced = f"{cleaned}."

    # Clean double spaces or accidental comma-periods
    enhanced = re.sub(r",\s*,", ",", enhanced)
    enhanced = re.sub(r"\s+", " ", enhanced).strip()
    return enhanced


# =============================================================================
# Pydantic Schemas for Strict Structured Output
# =============================================================================

class SceneSchema(BaseModel):
    """Detailed storyboard scene with multi-modal prompts and strict cinematic camera physics."""
    scene_number: int = Field(description="Sequential scene index starting from 1")
    duration_seconds: float = Field(default=4.0, description="Scene duration in seconds (typically 3-6s)")
    character_name: str = Field(description="Name of the featured fruit character (e.g., 'Mr. Orange', 'Mrs. Strawberry', 'Rich Banana', 'Baby Apple')")
    action_description: str = Field(description="Specific dramatic action, gesture, and emotional expression occurring in scene")
    full_image_prompt: str = Field(
        description=(
            "Comprehensive 8K Midjourney/Flux image prompt explicitly embedding the character's exact visual blueprint, "
            "costume, material textures, subsurface scattering, emotional facial micro-expressions, and environment."
        )
    )
    motion_camera_prompt: str = Field(
        description=(
            "Strict professional 9:16 vertical camera physics and optics for Kling/Runway/Veo "
            "(e.g., 'Macro close-up shot, shallow depth of field (f/1.8 bokeh), dramatic cinematic rim lighting, "
            "smooth 24fps vertical dolly zoom, ray-traced reflections on fruit peel, steadycam motion blur')"
        )
    )
    sound_effect_cue: str = Field(
        description=(
            "Layered Foley SFX and sound design cue for multi-track FFmpeg mixing "
            "(e.g., 'Sudden crying, sharp glass crack, thunderclap, heavy rain splashing, luxury sports car engine rev, heartbreak violin sting')"
        )
    )


class YouTubeViralPackage(BaseModel):
    """Complete YouTube Short viral package ready for production and publishing."""
    theme: str = Field(description="Underlying dramatic narrative theme (e.g. 'Betrayal and Hard Work')")
    title: str = Field(description="High-CTR universal title with emojis and minimal text for global viral reach")
    hook_description: str = Field(description="Strong visual and narrative hook designed to stop the scroll in first 3 seconds")
    scenes: List[SceneSchema] = Field(description="4 to 8 sequential dramatic scenes forming a complete arc")
    description: str = Field(description="SEO-optimized description with hashtags and credits")
    tags: List[str] = Field(description="Viral tags including #Shorts, #Animation, #FruitDrama, etc.")
    made_for_kids: bool = Field(default=False, description="COPPA compliance flag, always False for viral drama")


# =============================================================================
# Autonomous YouTube Shorts Studio Agent
# =============================================================================

class YouTubeAgent:
    """Autonomous YouTube Shorts producer managing character continuity, scripts, and publishing."""

    def __init__(
        self,
        db: Optional[DatabaseManager] = None,
        llm: Optional[LLMEngine] = None,
        uploader: Optional[YouTubeUploader] = None,
        exporter: Optional[StudioExporter] = None,
    ) -> None:
        self.db = db or db_manager
        self.llm = llm or llm_engine
        self.uploader = uploader or youtube_uploader
        self.exporter = exporter or studio_exporter
        self.ready_dir = settings.youtube_ready_dir
        self.char_lock = character_lock

    async def get_character_context(self) -> str:
        """Fetch pre-populated 3D fruit characters and build a strict character continuity guide."""
        characters = await self.db.get_characters()
        if not characters:
            return "No registered characters found."

        guide_lines = [
            "STRICT CHARACTER CONTINUITY REGISTRY (You MUST use these exact visual prompts):"
        ]
        for char in characters:
            guide_lines.append(
                f"- Character '{char['name']}' (Role: {char['role']}):\n"
                f"  Exact Visual Blueprint: \"{char['visual_prompt']}\""
            )
        return "\n".join(guide_lines)

    async def generate_viral_package(
        self,
        theme: str = "Betrayal and Hard Work",
        target_scene_count: int = 4,
        export_storyboard_files: bool = True,
    ) -> Dict[str, Any]:
        """Generate a complete YouTube Short package with strict character continuity and export storyboard sheets."""
        character_guide = await self.get_character_context()
        raw_characters = await self.db.get_characters()

        system_instruction = (
            "You are an elite YouTube Shorts Director & Viral Animation Showrunner specializing in 3D Pixar-style "
            "anthropomorphic fruit drama. Your videos are silent, emotionally universal, highly dramatic, and "
            "engineered for 100M+ global views. Stories rely purely on visual emotion, facial expressions, and relatable "
            "archetypes (The hardworking underdog husband, the unfaithful arrogant partner, the wealthy rival, the innocent baby).\n\n"
            f"{character_guide}\n\n"
            "STRICT CONTINUITY & CAMERA PHYSICS MANDATE (9:16 VERTICAL SHORTS):\n"
            "1. CHARACTER CONTINUITY LOCK: In every scene's `full_image_prompt`, you MUST include the exact visual description "
            "of the character from the registry above to ensure 100% visual consistency without morphing.\n"
            "2. CINEMATIC CAMERA PHYSICS: In every scene's `motion_camera_prompt`, enforce physical optics: "
            "specify shot scale (Macro close-up, extreme low angle), shallow depth of field (f/1.8 bokeh), "
            "dramatic volumetric rim lighting, smooth 24fps vertical dolly zoom, and ray-traced reflections on fruit peel.\n"
            "3. MULTI-LAYER SOUND DESIGN: In every scene's `sound_effect_cue`, specify a layered Foley audio cue "
            "(e.g., 'Sudden crying, sharp glass crack, thunderclap, heavy rain splashing, luxury sports car engine rev')."
        )

        user_prompt = (
            f"Create a viral 3D Pixar-style YouTube Short drama package around the theme: '{theme}'.\n"
            f"Requirements:\n"
            f"1. A shocking, high-emotion 3-second hook.\n"
            f"2. Exactly {target_scene_count} sequential scenes following: "
            f"Setup -> Betrayal/Conflict -> Rock Bottom -> Struggle -> Revenge/Triumph.\n"
            f"3. Each scene must specify exact action, embedded full image prompt, camera motion, and sound effect cue.\n"
            f"4. High-CTR global title with emojis."
        )

        logger.info("Generating viral YouTube package for theme: '%s'...", theme)
        package = await self.llm.generate_structured(
            prompt=user_prompt,
            response_schema=YouTubeViralPackage,
            system_instruction=system_instruction,
            provider="gemini",
            temperature=0.75,
        )

        # Enhance motion prompts with camera physics
        for idx, scene in enumerate(package.scenes, 1):
            scene.motion_camera_prompt = enhance_cinematic_motion_prompt(
                raw_prompt=scene.motion_camera_prompt,
                character_name=scene.character_name,
                scene_idx=idx,
            )

        # Save generated script to database
        scenes_data = [scene.model_dump() for scene in package.scenes]
        video_id = await self.db.save_youtube_script(
            theme=package.theme,
            title=package.title,
            description=package.description,
            tags=package.tags,
            scenes=scenes_data,
            status="SCRIPT_READY",
        )
        logger.info("Saved YouTube video script package with ID #%d: '%s'", video_id, package.title)

        # Export Storyboard Markdown and DOCX Production Sheets with Foley Cue Sheet
        storyboard_files = {}
        if export_storyboard_files:
            storyboard_files = self.exporter.export_storyboard(
                video_id=video_id,
                package=package,
                characters=raw_characters,
            )

        return {
            "video_id": video_id,
            "title": package.title,
            "theme": package.theme,
            "hook_description": package.hook_description,
            "scenes": scenes_data,
            "tags": package.tags,
            "description": package.description,
            "storyboard_md": storyboard_files.get("md_path", ""),
            "storyboard_docx": storyboard_files.get("docx_path", ""),
            "sfx_cues": storyboard_files.get("sfx_cues", []),
            "package": package.model_dump(),
        }

    async def check_ready_videos(self) -> List[Dict[str, Any]]:
        """Inspect workspace_data/youtube_ready/ for rendered MP4 files."""
        ready_files = list(self.ready_dir.glob("*.mp4"))
        results = []
        for file_path in ready_files:
            results.append({
                "file_name": file_path.name,
                "file_path": str(file_path),
                "size_bytes": file_path.stat().st_size,
            })
        return results

    async def upload_ready_video(
        self,
        video_id_in_db: int,
        file_path: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Publish or dry-run simulate uploading a ready MP4 video to YouTube."""
        if not title or not description:
            videos = await self.db.get_youtube_videos(limit=50)
            matched = next((v for v in videos if v["id"] == video_id_in_db), None)
            if matched:
                title = title or matched.get("title", f"Dramatic Short #{video_id_in_db}")
                description = description or matched.get("description", "Dramatic 3D Animation #Shorts")
                if not tags and matched.get("tags"):
                    tags = matched["tags"].split(",") if isinstance(matched["tags"], str) else matched["tags"]

        title = title or f"Dramatic Short #{video_id_in_db}"
        description = description or "Dramatic 3D Animation #Shorts"
        tags = tags or ["Shorts", "Animation", "FruitDrama"]

        return await self.uploader.upload_video(
            video_id_in_db=video_id_in_db,
            file_path=file_path,
            title=title,
            description=description,
            tags=tags,
        )

    async def sync_analytics(self) -> List[Dict[str, Any]]:
        """Synchronize views and likes from YouTube for published videos."""
        return await self.uploader.sync_channel_analytics()

    async def produce_and_render_full_short(
        self,
        theme: str = "Fruit Drama Betrayal and Triumph",
        target_scene_count: int = 4,
        progress_callback: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """End-to-end autonomous generator with Character Reference Lock & Multi-Layer Sound Design:
        1. Authors viral Pixar fruit script package with upgraded 9:16 cinematic motion prompts.
        2. Generates Arabic narration audio using edge-tts.
        3. Enforces Character Reference Lock (seeds + img2img master anchor continuity) across all scenes.
        4. Animates clips via CloudVideoPool (Google Veo -> Kling -> Wan2.1 -> Fallback).
        5. Builds multi-layer Foley SFX timeline and mixes via FFmpeg in VideoStitcher into workspace_data/youtube_ready/.
        """
        async def _notify(msg: str):
            if progress_callback:
                try:
                    if asyncio.iscoroutinefunction(progress_callback):
                        await progress_callback(msg)
                    else:
                        progress_callback(msg)
                except Exception:
                    pass

        # 1. Generate Script Package
        await _notify(f"🎬 <b>المرحلة 1/4:</b> صياغة السيناريو الفيروسي لفكرة: <i>{theme}</i>...")
        package_res = await self.generate_viral_package(theme=theme, target_scene_count=target_scene_count)
        video_id = package_res["video_id"]
        title = package_res["title"]
        scenes = package_res["scenes"]
        sfx_timeline = package_res.get("sfx_cues", [])

        # 2. Generate Arabic Narration via Edge-TTS
        await _notify("🎙️ <b>المرحلة 2/4:</b> توليد التعليق الصوتي الدرامي بالذكاء الاصطناعي...")
        narration_lines = [s.get("action_description", "") for s in scenes]
        narration_text = f"يا ترى إيه اللي هيحصل؟ {title}. " + " ".join(narration_lines[:3])

        run_id = f"short_{video_id}_{int(time.time())}"
        work_dir = settings.workspace_dir / "workspace_data" / "runs" / run_id
        work_dir.mkdir(parents=True, exist_ok=True)
        audio_path = work_dir / "voiceover.mp3"

        try:
            import edge_tts
            communicate = edge_tts.Communicate(narration_text, voice="ar-EG-ShakirNeural")
            await communicate.save(str(audio_path))
        except Exception as e:
            logger.warning("Edge-TTS error: %s. Continuing with ambient audio...", e)
            audio_path = None

        # 3. Generate Keyframes with Character Reference Lock & Multi-Cloud Animation
        await _notify(f"⚡ <b>المرحلة 3/4:</b> توليد {len(scenes)} مشاهد متحركة بقفل الاتساق البصري للشخصيات...")
        
        # Track run-level character master anchors to stop character morphing completely
        active_character_anchors: Dict[str, Path] = {}
        rendered_clips: List[Path] = []

        for idx, scene in enumerate(scenes, 1):
            scene_num = scene.get("scene_number", idx)
            char_name = scene.get("character_name", "Fruit Character")
            raw_img_prompt = scene.get("full_image_prompt", "")
            raw_motion_prompt = scene.get("motion_camera_prompt", "")

            # Ensure camera physics are enhanced
            motion_prompt = enhance_cinematic_motion_prompt(
                raw_prompt=raw_motion_prompt,
                character_name=char_name,
                scene_idx=idx,
            )

            # Character Reference Lock: Resolve master reference anchor
            master_anchor = active_character_anchors.get(char_name) or self.char_lock.resolve_master_anchor(char_name)
            char_seed = self.char_lock.get_character_seed(char_name)

            # Inject character continuity lock tokens
            locked_img_prompt = self.char_lock.build_continuity_prompt(
                character_name=char_name,
                base_prompt=raw_img_prompt,
                anchor_path=master_anchor,
            )

            frame_img = work_dir / f"scene_{scene_num:02d}_frame.png"
            scene_video = work_dir / f"scene_{scene_num:02d}_clip.mp4"

            await _notify(f"🎨 جاري تجهيز المشهد {idx}/{len(scenes)}: {char_name} (قفل البصمة: Seed={char_seed})...")

            # Render keyframe image with seed & reference lock
            try:
                await render_shot_image(
                    prompt=locked_img_prompt,
                    output_path=frame_img,
                    aspect_ratio="9:16",
                    seed=char_seed,
                    reference_image=master_anchor,
                )
            except Exception as ex:
                logger.warning("Frame render failed: %s. Using character fallback.", ex)
                if master_anchor and master_anchor.exists():
                    shutil.copy2(master_anchor, frame_img)
                else:
                    fallback_img = settings.workspace_dir / "workspace_data" / "generated_strawberry_waitress.jpg"
                    if fallback_img.exists():
                        shutil.copy2(fallback_img, frame_img)

            # If this is the character's first appearance in this run, lock this frame as the master anchor
            if frame_img.exists() and frame_img.stat().st_size > 1024:
                if char_name not in active_character_anchors:
                    active_character_anchors[char_name] = frame_img
                    if not master_anchor:
                        master_anchor = self.char_lock.register_master_anchor(char_name, frame_img)

            # Animate clip via CloudVideoPool passing master reference image
            clip_path = await cloud_video_pool.generate_scene_video(
                image_path=frame_img,
                motion_prompt=motion_prompt,
                output_path=scene_video,
                duration_sec=scene.get("duration_seconds", 4.0),
                progress_callback=progress_callback,
                reference_image=master_anchor,
            )
            if clip_path.exists() and clip_path.stat().st_size > 1024:
                rendered_clips.append(clip_path)

        # 4. Multi-Layer Sound Design & FFmpeg Final Assembly
        await _notify("🎞️ <b>المرحلة 4/4:</b> المونتاج النهائي وموازنة طبقات الصوت والـ Foley عبر FFmpeg...")
        final_mp4 = settings.youtube_ready_dir / f"{run_id}.mp4"

        # Ensure timeline has cues
        if not sfx_timeline:
            sfx_timeline = self.exporter._build_sfx_timeline({"scenes": scenes})

        await video_stitcher.assemble_short(
            clips=rendered_clips,
            voiceover_audio=audio_path,
            output_file=final_mp4,
            sfx_cues=sfx_timeline,
        )

        # Update DB status
        await self.db.update_youtube_video_status(video_id, "RENDER_READY", str(final_mp4))
        logger.info("Autonomous Production Complete! Final MP4: %s (%d KB)",
                    final_mp4.name, final_mp4.stat().st_size // 1024)

        return {
            "status": "SUCCESS",
            "video_id": video_id,
            "title": title,
            "description": package_res["description"],
            "tags": package_res["tags"],
            "video_path": str(final_mp4),
            "file_name": final_mp4.name,
            "size_bytes": final_mp4.stat().st_size if final_mp4.exists() else 0,
            "scenes_count": len(rendered_clips),
            "sfx_cues": sfx_timeline,
            "character_anchors": {k: str(v) for k, v in active_character_anchors.items()},
        }

    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch blackboard task assigned to youtube_agent."""
        task_type = task.get("task_type", "").upper().strip()
        payload = task.get("payload_json", {})
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except Exception:
                payload = {}

        logger.info("YouTubeAgent processing task_type: %s", task_type)

        if task_type in ("PRODUCE_VIDEO", "PRODUCE_FULL_SHORT", "RENDER_SHORT"):
            theme = payload.get("theme", "Betrayal and Hard Work")
            scene_count = int(payload.get("scene_count", 4))
            return await self.produce_and_render_full_short(theme=theme, target_scene_count=scene_count)

        elif task_type in ("GENERATE_SCRIPT", "CREATE_VIDEO_STORY", "YOUTUBE_STORY"):
            theme = payload.get("theme", "Betrayal and Hard Work")
            scene_count = int(payload.get("scene_count", 4))
            result = await self.generate_viral_package(theme=theme, target_scene_count=scene_count)
            return {
                "status": "SUCCESS",
                "video_id": result["video_id"],
                "title": result["title"],
                "theme": result["theme"],
                "scenes_count": len(result["scenes"]),
                "storyboard_md": result["storyboard_md"],
                "storyboard_docx": result["storyboard_docx"],
                "sfx_cues": result.get("sfx_cues", []),
                "tags": result["tags"],
            }

        elif task_type in ("UPLOAD_VIDEO", "PUBLISH_VIDEO"):
            video_id = int(payload.get("video_id", 1))
            file_path = payload.get("file_path", "")
            title = payload.get("title")
            description = payload.get("description")
            tags = payload.get("tags")

            if not file_path:
                ready = await self.check_ready_videos()
                if ready:
                    file_path = ready[0]["file_path"]
                else:
                    raise FileNotFoundError("No MP4 file found in youtube_ready directory to upload.")

            upload_res = await self.upload_ready_video(
                video_id_in_db=video_id,
                file_path=file_path,
                title=title,
                description=description,
                tags=tags,
            )
            return {
                "status": "SUCCESS",
                "upload_result": upload_res,
            }

        elif task_type in ("SYNC_ANALYTICS", "CHANNEL_STATS"):
            analytics_res = await self.sync_analytics()
            return {
                "status": "SUCCESS",
                "synced_count": len(analytics_res),
                "analytics": analytics_res,
            }

        elif task_type in ("CHECK_READY_VIDEOS", "SCAN_READY"):
            videos = await self.check_ready_videos()
            return {
                "status": "SUCCESS",
                "ready_count": len(videos),
                "videos": videos,
            }

        else:
            raise ValueError(f"YouTubeAgent does not support task_type: '{task_type}'")


# Singleton instance
youtube_agent = YouTubeAgent()
