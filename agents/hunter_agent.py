"""Client Acquisition, Freelance & Career Hunter Agent for adham-agent.

Features:
- Ingests Adham's profile memory (Full-stack, FinTech MQL5, ISP MikroTik).
- Scores job relevance (0-100) and extracts client pain points & ATS keywords.
- Generates high-converting tailored proposals in Arabic or English.
- Automatically exports clean ATS-ready DOCX resumes via python-docx into workspace_data/generated_cvs/.
- Integrated with WebScraperTool to autonomously scrape URLs and discover public leads.
- Records leads and proposals in the SQLite leads_and_jobs table.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from pydantic import BaseModel, Field

from config.settings import settings
from core.database import db_manager, DatabaseManager
from core.llm import llm_engine, LLMEngine
from tools.web_scraper import web_scraper, WebScraperTool

logger = logging.getLogger("adham_agent.agents.hunter")


# =============================================================================
# Pydantic Schemas for Strict Structured Output
# =============================================================================

class JobProposalPackage(BaseModel):
    """Complete ATS assessment, tailored proposal, and customized CV bullets."""
    relevance_score: int = Field(description="Match rating from 0 to 100 based on Adham's actual experience")
    pain_points_analysis: str = Field(description="Identification of client's core technical challenges and business goals")
    required_ats_keywords: List[str] = Field(description="Essential technical and domain keywords required by the job")
    tailored_proposal: str = Field(description="Persuasive, highly customized proposal or cover letter in the language of the job post")
    tailored_cv_bullet_points: List[str] = Field(
        description="3 to 5 high-impact resume achievement bullets specifically emphasizing relevant experience"
    )
    cover_letter_subject: str = Field(description="Professional email or application subject line")


class HunterAgent:
    """Autonomous B2B Sales & Career Agent representing Adham's engineering credentials."""

    def __init__(
        self,
        db: Optional[DatabaseManager] = None,
        llm: Optional[LLMEngine] = None,
        scraper: Optional[WebScraperTool] = None,
    ) -> None:
        self.db = db or db_manager
        self.llm = llm or llm_engine
        self.scraper = scraper or web_scraper
        self.cvs_dir = settings.generated_cvs_dir

    async def get_profile_context(self) -> str:
        """Fetch Adham's verified profile memory records from SQLite."""
        profiles = await self.db.get_profile_memory()
        if not profiles:
            return "No profile memory found in database."

        sections = ["ADHAM ALHABBACH - VERIFIED PROFESSIONAL PROFILE:"]
        for p in profiles:
            sections.append(
                f"### {p['category']} - {p['title']}\n"
                f"Description: {p['content']}\n"
                f"Tags & Competencies: {p['skills_tags']}\n"
            )
        return "\n".join(sections)

    async def scrape_and_propose(self, url: str) -> Dict[str, Any]:
        """Autonomously scrape a live job posting URL, analyze requirements, and produce proposal & CV."""
        logger.info("HunterAgent scraping URL for job analysis: %s", url)
        scraped = await self.scraper.scrape_job_page(url)

        return await self.analyze_and_propose(
            job_title=scraped.get("title", "Software Engineer Position"),
            job_description=scraped.get("description", ""),
            platform=scraped.get("organization", "Web Job Posting"),
            url=url,
        )

    async def discover_and_hunt(
        self,
        keywords: Optional[List[str]] = None,
        auto_propose_top: bool = False,
    ) -> List[Dict[str, Any]]:
        """Discover live public job leads, persist them in database, and optionally propose for the best match."""
        leads = await self.scraper.discover_leads(keywords=keywords)
        saved_leads: List[Dict[str, Any]] = []

        for lead in leads:
            lead_id = await self.db.save_job_lead(
                platform=lead.get("platform", "Feed"),
                title=lead.get("title", "Tech Opportunity"),
                url=lead.get("url", ""),
                description=lead.get("description", ""),
                client_info=f"Organization: {lead.get('organization', 'Client')} | Location: {lead.get('location', 'Remote')}",
                status="FOUND",
            )
            saved_leads.append({
                "lead_id": lead_id,
                **lead,
            })

        logger.info("Saved %d discovered leads into database blackboard.", len(saved_leads))

        if auto_propose_top and saved_leads:
            top_lead = saved_leads[0]
            logger.info("Auto-proposing for top discovered lead: '%s'", top_lead["title"])
            proposal_res = await self.analyze_and_propose(
                job_title=top_lead["title"],
                job_description=top_lead.get("description", ""),
                platform=top_lead.get("platform", "Discovered Lead"),
                url=top_lead.get("url", ""),
            )
            top_lead["proposal_result"] = proposal_res

        return saved_leads

    async def analyze_and_propose(
        self,
        job_title: str,
        job_description: str,
        platform: str = "Direct Client",
        url: str = "",
    ) -> Dict[str, Any]:
        """Analyze job post, generate proposal & tailored CV, save lead, and export .docx."""
        profile_context = await self.get_profile_context()

        system_instruction = (
            "You are Adham's Principal Career Strategist and Executive B2B Technical Proposal Writer. "
            "Adham is a seasoned Lead Software Engineer and Infrastructure Systems Specialist with 10+ years of "
            "hands-on production delivery in:\n"
            "1. Enterprise Full-Stack Dev: PHP (Laravel), Python (AsyncIO, FastAPI), C#, SQLite/MySQL, Shamel POS.\n"
            "2. FinTech & Algo Trading: MetaTrader 5 (MT5), MQL5 Expert Advisors, Python quantitative backtesting, Gold XAU/USD.\n"
            "3. ISP Networking & SysAdmin: MikroTik RouterOS (Winbox, Bandwidth, VLAN, VPN), Active Directory, IT Support.\n\n"
            f"{profile_context}\n\n"
            "PROPOSAL WRITING RULES:\n"
            "- Write in the EXACT language of the job post (Arabic if the post is in Arabic, English if in English).\n"
            "- Address the client's explicit pain points in the first 2 sentences. Never use generic corporate fluff.\n"
            "- Highlight relevant production achievements directly related to their stack.\n"
            "- State clearly that Adham provides high availability, clean architecture, and rapid deployment."
        )

        user_prompt = (
            f"Analyze this job and generate a winning proposal and tailored CV package:\n\n"
            f"Job Title: {job_title}\n"
            f"Platform: {platform}\n"
            f"Job URL: {url}\n"
            f"Job Description:\n\"\"\"\n{job_description}\n\"\"\""
        )

        logger.info("HunterAgent analyzing job '%s' on %s...", job_title, platform)
        package = await self.llm.generate_structured(
            prompt=user_prompt,
            response_schema=JobProposalPackage,
            system_instruction=system_instruction,
            provider="gemini",
            temperature=0.7,
        )

        # Generate ATS DOCX Document
        safe_title = re.sub(r"[^a-zA-Z0-9_\u0600-\u06FF]", "_", job_title)[:35]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        docx_filename = f"CV_Adham_Alhabbash_{safe_title}_{timestamp}.docx"
        docx_path = self.cvs_dir / docx_filename

        self._export_ats_docx(
            job_title=job_title,
            package=package,
            output_path=docx_path,
        )

        # Save lead to database
        lead_url = url or f"local://job/{safe_title}/{timestamp}"
        lead_id = await self.db.save_job_lead(
            platform=platform,
            title=job_title,
            url=lead_url,
            description=job_description,
            client_info=f"Relevance Score: {package.relevance_score}%",
            generated_proposal=package.tailored_proposal,
            cv_path=str(docx_path),
            status="PROPOSED",
        )

        logger.info("Saved lead #%d and exported CV to: %s", lead_id, docx_path.name)
        return {
            "lead_id": lead_id,
            "job_title": job_title,
            "relevance_score": package.relevance_score,
            "proposal": package.tailored_proposal,
            "ats_keywords": package.required_ats_keywords,
            "cv_docx_path": str(docx_path),
            "docx_filename": docx_filename,
            "package": package.model_dump(),
        }

    def _export_ats_docx(
        self,
        job_title: str,
        package: JobProposalPackage,
        output_path: Path,
    ) -> None:
        """Create an ATS-friendly, elegant Word document containing tailored CV & Cover Letter."""
        doc = docx.Document()

        # Page margins
        for section in doc.sections:
            section.top_margin = Inches(0.8)
            section.bottom_margin = Inches(0.8)
            section.left_margin = Inches(0.8)
            section.right_margin = Inches(0.8)

        # Header: Name and Contact
        p_name = doc.add_paragraph()
        p_name.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run_name = p_name.add_run("ADHAM ALHABBACH")
        run_name.font.name = "Arial"
        run_name.font.size = Pt(20)
        run_name.font.bold = True
        run_name.font.color.rgb = RGBColor(26, 43, 76)

        p_title = doc.add_paragraph()
        p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run_title = p_title.add_run("Lead Systems & Software Engineer | FinTech & Enterprise Infrastructure")
        run_title.font.name = "Arial"
        run_title.font.size = Pt(11)
        run_title.font.bold = True
        run_title.font.color.rgb = RGBColor(70, 80, 95)

        p_contact = doc.add_paragraph()
        p_contact.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run_contact = p_contact.add_run("Palestine / Remote | LinkedIn / GitHub Portfolio | Verified Senior Consultant")
        run_contact.font.size = Pt(9.5)
        run_contact.font.color.rgb = RGBColor(100, 110, 120)

        # Section: Targeted Professional Summary
        h_summary = doc.add_heading("Professional Profile & Targeted Competencies", level=1)
        h_summary.paragraph_format.space_before = Pt(12)
        h_summary.paragraph_format.space_after = Pt(4)

        p_sum = doc.add_paragraph(
            f"Seasoned Lead Software & Systems Architect presenting verified 10+ years track record in enterprise "
            f"backend engineering (Laravel, Python FastAPI/AsyncIO), automated algorithmic trading systems (MT5 MQL5), "
            f"and ISP mission-critical infrastructure (MikroTik RouterOS). Tailored specifically for the {job_title} role."
        )
        p_sum.paragraph_format.space_after = Pt(8)

        # Section: Key ATS Competencies & Keywords
        h_skills = doc.add_heading("Core Technical Proficiencies & ATS Keywords", level=1)
        h_skills.paragraph_format.space_before = Pt(8)
        h_skills.paragraph_format.space_after = Pt(4)

        kw_text = " • ".join(package.required_ats_keywords)
        p_kw = doc.add_paragraph(kw_text)
        p_kw.runs[0].font.bold = True
        p_kw.runs[0].font.color.rgb = RGBColor(30, 60, 110)
        p_kw.paragraph_format.space_after = Pt(8)

        # Section: Tailored Key Achievements
        h_achieve = doc.add_heading("Targeted Technical Highlights", level=1)
        h_achieve.paragraph_format.space_before = Pt(8)
        h_achieve.paragraph_format.space_after = Pt(4)

        for bullet in package.tailored_cv_bullet_points:
            p_bullet = doc.add_paragraph(bullet, style="List Bullet")
            p_bullet.paragraph_format.space_after = Pt(3)

        # Section: Verified Core Production Projects
        h_projects = doc.add_heading("Featured Production Deliveries", level=1)
        h_projects.paragraph_format.space_before = Pt(10)
        h_projects.paragraph_format.space_after = Pt(4)

        projects = [
            ("Shamel POS App (Flutter / Dart / Android)", "High-performance point-of-sale system with weighted average costing, carton conversion, barcode scanning, offline-first SQLite, and atomic transactions."),
            ("Lead Preview Bot (Laravel 11 / Tailwind / Python)", "Enterprise lead intelligence platform supporting Google Places APIs, Apify scrapers, automated WhatsApp outreach, and real-time site audit engines."),
            ("GoldSMC MT5 Expert Advisor (MQL5 / Python)", "High-frequency algorithmic trading robot on XAU/USD featuring liquidity sweep detection, displacement filters, automated break-even and partial take-profit logic."),
            ("ISP Enterprise Infrastructure (MikroTik RouterOS)", "Architected multi-branch ISP network routing with bandwidth queue trees, VLAN segmentation, failover routing, and secure WireGuard VPN tunnels."),
        ]

        for p_name_proj, p_desc in projects:
            p_proj = doc.add_paragraph()
            r_pn = p_proj.add_run(f"• {p_name_proj}: ")
            r_pn.bold = True
            r_pn.font.color.rgb = RGBColor(40, 50, 70)
            p_proj.add_run(p_desc)
            p_proj.paragraph_format.space_after = Pt(3)

        # Section: Tailored Cover Letter / Proposal
        doc.add_page_break()
        h_prop = doc.add_heading(f"Proposal & Cover Letter: {job_title}", level=1)
        h_prop.paragraph_format.space_before = Pt(10)
        h_prop.paragraph_format.space_after = Pt(6)

        p_subj = doc.add_paragraph()
        run_sb = p_subj.add_run(f"Subject: {package.cover_letter_subject}")
        run_sb.bold = True
        p_subj.paragraph_format.space_after = Pt(8)

        for paragraph_text in package.tailored_proposal.split("\n\n"):
            if paragraph_text.strip():
                p = doc.add_paragraph(paragraph_text.strip())
                p.paragraph_format.space_after = Pt(6)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        doc.save(str(output_path))

    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch blackboard task assigned to hunter_agent."""
        task_type = task.get("task_type", "").upper().strip()
        payload = task.get("payload_json", {})
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except Exception:
                payload = {}

        logger.info("HunterAgent processing task_type: %s", task_type)

        if task_type in ("SCRAPE_JOB", "SCRAPE_JOB_PAGE"):
            url = payload.get("url", "")
            if not url:
                raise ValueError("SCRAPE_JOB task requires 'url' in payload")
            result = await self.scrape_and_propose(url=url)
            return {
                "status": "SUCCESS",
                "lead_id": result["lead_id"],
                "relevance_score": result["relevance_score"],
                "cv_docx_path": result["cv_docx_path"],
                "docx_filename": result["docx_filename"],
                "proposal_excerpt": result["proposal"][:300] + "...",
            }

        elif task_type in ("DISCOVER_LEADS", "HUNT_LEADS", "FIND_JOBS"):
            keywords = payload.get("keywords")
            auto_propose = payload.get("auto_propose_top", False)
            leads = await self.discover_and_hunt(keywords=keywords, auto_propose_top=auto_propose)
            return {
                "status": "SUCCESS",
                "leads_count": len(leads),
                "leads": leads,
            }

        elif task_type in ("ANALYZE_JOB", "GENERATE_CV_PROPOSAL", "PROPOSE_JOB"):
            job_title = payload.get("job_title", "")
            job_description = payload.get("job_description", "")
            platform = payload.get("platform", "Freelance Platform")
            url = payload.get("url", "")

            # If URL is provided without a description, scrape it first
            if url and not job_description:
                return await self.process_task({"task_type": "SCRAPE_JOB", "payload_json": payload})

            if not job_title:
                job_title = "Senior Full-Stack & Systems Engineer"

            result = await self.analyze_and_propose(
                job_title=job_title,
                job_description=job_description,
                platform=platform,
                url=url,
            )
            return {
                "status": "SUCCESS",
                "lead_id": result["lead_id"],
                "relevance_score": result["relevance_score"],
                "cv_docx_path": result["cv_docx_path"],
                "docx_filename": result["docx_filename"],
                "proposal_excerpt": result["proposal"][:300] + "...",
            }

        else:
            raise ValueError(f"HunterAgent does not support task_type: '{task_type}'")


# Singleton instance
hunter_agent = HunterAgent()
