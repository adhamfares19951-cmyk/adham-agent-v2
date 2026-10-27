"""Senior Software Engineering & Self-Healing Code Agent for adham-agent.

Features:
- Powered by DeepSeek (provider="deepseek" with automatic failover to Gemini Flash).
- Generates complete, production-ready code, MQL5 algo trading strategies, SQL queries, and bug fixes.
- Uses strict Pydantic schemas (CodeSolutionSchema, CodeFilePlan) for deterministic architectural code delivery.
- Executes and verifies tasks via the SQLite agent_tasks blackboard.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from config.settings import settings
from core.database import db_manager, DatabaseManager
from core.llm import llm_engine, LLMEngine

logger = logging.getLogger("adham_agent.agents.dev")


# =============================================================================
# Pydantic Schemas for Strict Structured Output
# =============================================================================

class CodeFilePlan(BaseModel):
    """Concrete file creation or modification artifact."""
    file_path: str = Field(description="Relative or absolute path of the target file to create or modify")
    explanation: str = Field(description="Technical explanation of the module, functions, and architecture")
    code_content: str = Field(description="Complete, fully-implemented production source code with zero placeholders or TODOs")


class CodeSolutionSchema(BaseModel):
    """Comprehensive engineering solution blueprint."""
    task_summary: str = Field(description="Executive technical summary of the problem and engineering approach")
    architectural_rationale: str = Field(description="Explanation of architectural patterns, algorithms, and complexity trade-offs")
    files_to_create_or_modify: List[CodeFilePlan] = Field(description="Concrete file artifacts generated to solve the task")
    verification_command: str = Field(description="Shell or pytest command to independently verify the solution")
    complexity_level: str = Field(default="MEDIUM", description="Task complexity rating: LOW, MEDIUM, HIGH, or CRITICAL")


class DevAgent:
    """Senior Software & DevOps Engineering Agent."""

    def __init__(
        self,
        db: Optional[DatabaseManager] = None,
        llm: Optional[LLMEngine] = None,
    ) -> None:
        self.db = db or db_manager
        self.llm = llm or llm_engine
        self.base_dir = settings.WORKSPACE_DATA_DIR.parent

    async def solve_engineering_task(
        self,
        specification: str,
        target_files: Optional[List[str]] = None,
        apply_files: bool = False,
    ) -> CodeSolutionSchema:
        """Engineer a complete production code solution using DeepSeek / Gemini dual engine."""
        system_instruction = (
            "You are a Principal Software Architect, Senior Full-Stack Engineer, and Algorithmic Trading Developer. "
            "You write robust, scalable, modern production code following clean architecture, SOLID principles, and "
            "async-first design. You specialize in Python 3.11+ (FastAPI, AsyncIO, Pydantic v2), PHP (Laravel), "
            "MetaTrader 5 (MQL5 Expert Advisors), SQL (PostgreSQL, SQLite), and Linux/DevOps.\n\n"
            "STRICT RULES:\n"
            "1. NEVER use placeholders, `pass`, or `# TODO` in core logic.\n"
            "2. All code files must be fully implemented, syntactically valid, and ready to execute.\n"
            "3. Include robust error handling and type hints."
        )

        user_prompt = f"Engineering Task Specification:\n\"\"\"\n{specification}\n\"\"\"\n"
        if target_files:
            user_prompt += f"Target Files to update or reference: {', '.join(target_files)}\n"

        logger.info("DevAgent solving engineering task (primary: deepseek)...")
        solution = await self.llm.generate_structured(
            prompt=user_prompt,
            response_schema=CodeSolutionSchema,
            system_instruction=system_instruction,
            provider="deepseek",
            temperature=0.3,
        )

        if apply_files:
            for file_plan in solution.files_to_create_or_modify:
                full_path = self.base_dir / file_plan.file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(file_plan.code_content, encoding="utf-8")
                logger.info("DevAgent wrote file artifact: %s", full_path)

        return solution

    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch blackboard task assigned to dev_agent."""
        task_type = task.get("task_type", "").upper().strip()
        payload = task.get("payload_json", {})
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except Exception:
                payload = {}

        logger.info("DevAgent processing task_type: %s", task_type)

        if task_type in ("SOLVE_CODE_TASK", "DEBUG_CODE", "GENERATE_CODE", "GENERATE_MQL5", "GENERATE_SQL"):
            specification = payload.get("specification") or payload.get("task") or payload.get("description", "")
            target_files = payload.get("target_files", [])
            apply_files = bool(payload.get("apply_files", False))

            solution = await self.solve_engineering_task(
                specification=specification,
                target_files=target_files,
                apply_files=apply_files,
            )

            return {
                "status": "SUCCESS",
                "task_summary": solution.task_summary,
                "complexity": solution.complexity_level,
                "verification_command": solution.verification_command,
                "files_count": len(solution.files_to_create_or_modify),
                "solution": solution.model_dump(),
            }

        else:
            raise ValueError(f"DevAgent does not support task_type: '{task_type}'")


# Singleton instance
dev_agent = DevAgent()
