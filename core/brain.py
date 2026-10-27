"""The Master CEO Orchestrator & Swarm Router for adham-agent.

Implements rule 1, 3, and 4 from ARCHITECTURE.md:
- Decomposes high-level natural language user goals (Arabic & English) into structured sub-agent tasks.
- Routes tasks to specialized agents (youtube_agent, hunter_agent, dev_agent, sys_agent).
- Coordinates parallel swarm execution via asyncio.gather and SQLite agent_tasks blackboard.
- Updates task lifecycle states (PENDING -> IN_PROGRESS -> COMPLETED/FAILED).
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from agents.dev_agent import dev_agent, DevAgent
from agents.hunter_agent import hunter_agent, HunterAgent
from agents.sys_agent import sys_agent, SysAgent
from agents.youtube_agent import youtube_agent, YouTubeAgent
from core.database import db_manager, DatabaseManager
from core.llm import llm_engine, LLMEngine

logger = logging.getLogger("adham_agent.brain")


# =============================================================================
# Pydantic Schemas for Intent Decomposition & Swarm Planning
# =============================================================================

class SubAgentTask(BaseModel):
    """Atomic task decomposed from user goal and assigned to a specialized sub-agent."""
    assigned_agent: str = Field(
        description="Target agent identifier. MUST be exactly one of: 'youtube_agent', 'hunter_agent', 'dev_agent', 'sys_agent'"
    )
    task_type: str = Field(
        description="Specific actionable task type (e.g., 'GENERATE_SCRIPT', 'ANALYZE_JOB', 'SOLVE_CODE_TASK', 'MONITOR_HEALTH')"
    )
    payload: Dict[str, Any] = Field(
        description="Structured key-value arguments required by the target agent to execute the task"
    )
    priority: int = Field(default=1, description="Execution priority from 1 (normal) to 5 (urgent)")
    rationale: str = Field(description="Architectural reason explaining why this task is needed to achieve the user goal")


class SwarmExecutionPlan(BaseModel):
    """Structured decomposition of an overarching natural language command into multi-agent tasks."""
    user_intent_summary: str = Field(description="High-level synthesis of what the user wants to accomplish")
    detected_language: str = Field(description="Language of user command ('ar' for Arabic, 'en' for English)")
    tasks: List[SubAgentTask] = Field(description="List of 1 or more atomic tasks dispatched to sub-agents")


class MasterBrain:
    """Master CEO Orchestrator coordinating all autonomous sub-agents across the system."""

    def __init__(
        self,
        db: Optional[DatabaseManager] = None,
        llm: Optional[LLMEngine] = None,
        youtube: Optional[YouTubeAgent] = None,
        hunter: Optional[HunterAgent] = None,
        dev: Optional[DevAgent] = None,
        sys_mon: Optional[SysAgent] = None,
    ) -> None:
        self.db = db or db_manager
        self.llm = llm or llm_engine
        self.youtube_agent = youtube or youtube_agent
        self.hunter_agent = hunter or hunter_agent
        self.dev_agent = dev or dev_agent
        self.sys_agent = sys_mon or sys_agent

        self.agent_registry = {
            "youtube_agent": self.youtube_agent,
            "hunter_agent": self.hunter_agent,
            "dev_agent": self.dev_agent,
            "sys_agent": self.sys_agent,
        }
        self.agents_registry = self.agent_registry

    async def plan_and_dispatch(self, user_goal: str) -> List[str]:
        """Decompose a natural language prompt into atomic sub-agent tasks and post to blackboard."""
        system_instruction = (
            "You are MasterBrain, the Chief AI Systems Orchestrator & Executive Swarm Router for 'adham-agent'. "
            "Your role is to understand user commands (in Arabic or English), decompose multi-part requests into "
            "independent tasks, and assign each task to the exact right specialized sub-agent.\n\n"
            "AVAILABLE SUB-AGENTS & CAPABILITIES:\n"
            "1. 'youtube_agent':\n"
            "   - Task types: 'PRODUCE_VIDEO', 'GENERATE_SCRIPT', 'CHECK_READY_VIDEOS'\n"
            "   - Payload fields for 'PRODUCE_VIDEO': {'theme': str, 'scene_count': int}\n"
            "   - Payload fields for 'GENERATE_SCRIPT': {'theme': str, 'scene_count': int}\n"
            "   - Use when user asks for: YouTube Shorts, 3D fruit drama, produce/render videos, video scripts, stories, or viral ideas.\n"
            "2. 'hunter_agent':\n"
            "   - Task types: 'ANALYZE_JOB', 'GENERATE_CV_PROPOSAL'\n"
            "   - Payload fields: {'job_title': str, 'job_description': str, 'platform': str, 'url': str}\n"
            "   - Use when user asks for: job applications, freelance proposals, cover letters, CV tailored docs.\n"
            "3. 'dev_agent':\n"
            "   - Task types: 'SOLVE_CODE_TASK', 'DEBUG_CODE', 'GENERATE_MQL5', 'GENERATE_SQL'\n"
            "   - Payload fields: {'specification': str, 'target_files': list[str], 'apply_files': bool}\n"
            "   - Use when user asks for: coding, bug fixing, MQL5 algo trading bots, database queries, scripts.\n"
            "4. 'sys_agent':\n"
            "   - Task types: 'MONITOR_HEALTH', 'INSPECT_READY_VIDEOS', 'ROTATE_LOGS'\n"
            "   - Payload fields: {}\n"
            "   - Use when user asks for: system status, health checks, disk space, log cleanup, or video scans.\n\n"
            "DECOMPOSITION RULES:\n"
            "- If a command mentions multiple domains (e.g. 'make a video script AND prepare a job proposal'), "
            "create SEPARATE tasks for each domain.\n"
            "- Always formulate detailed, high-quality payloads with clear specifications so sub-agents can succeed autonomously."
        )

        user_prompt = f"User Command / Goal:\n\"\"\"\n{user_goal}\n\"\"\""

        logger.info("MasterBrain analyzing and decomposing goal: '%s'...", user_goal)
        plan: SwarmExecutionPlan = await self.llm.generate_structured(
            prompt=user_prompt,
            response_schema=SwarmExecutionPlan,
            system_instruction=system_instruction,
            provider="gemini",
            temperature=0.3,
        )

        logger.info(
            "MasterBrain generated execution plan: %s (%d tasks, language: %s)",
            plan.user_intent_summary,
            len(plan.tasks),
            plan.detected_language,
        )

        created_task_ids: List[str] = []
        for sub_task in plan.tasks:
            agent_key = sub_task.assigned_agent.lower().strip()
            if agent_key not in self.agent_registry:
                logger.warning("Unknown agent '%s' mapped to 'dev_agent' fallback", agent_key)
                agent_key = "dev_agent"

            task_id = await self.db.add_task(
                assigned_agent=agent_key,
                task_type=sub_task.task_type,
                payload=sub_task.payload,
            )
            created_task_ids.append(task_id)
            logger.info("Dispatched task #%s to '%s' (Type: %s)", task_id, agent_key, sub_task.task_type)

        return created_task_ids

    async def _execute_single_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single blackboard task via its assigned sub-agent."""
        task_id = task["id"]
        assigned_agent = task.get("assigned_agent", "").lower().strip()

        agent_instance = self.agent_registry.get(assigned_agent)
        if not agent_instance:
            err_msg = f"No agent registered under key '{assigned_agent}'"
            logger.error(err_msg)
            await self.db.update_task_status(task_id, status="FAILED", error_message=err_msg)
            return {"task_id": task_id, "status": "FAILED", "error": err_msg}

        try:
            # Mark IN_PROGRESS
            await self.db.update_task_status(task_id, status="IN_PROGRESS")
            logger.info("Agent '%s' started executing task #%s...", assigned_agent, task_id)

            # Delegate to specialized agent
            result = await agent_instance.process_task(task)

            # Mark COMPLETED
            await self.db.update_task_status(task_id, status="COMPLETED", result=result)
            logger.info("Agent '%s' successfully completed task #%s!", assigned_agent, task_id)
            return {"task_id": task_id, "status": "COMPLETED", "result": result}

        except Exception as e:
            error_str = f"Execution failed in {assigned_agent}: {type(e).__name__}: {str(e)}"
            logger.error("Task #%s failed: %s", task_id, error_str, exc_info=True)
            await self.db.update_task_status(task_id, status="FAILED", error_message=error_str)
            return {"task_id": task_id, "status": "FAILED", "error": error_str}

    async def execute_pending_swarm(self) -> Dict[str, Any]:
        """Fetch all PENDING tasks from the blackboard and execute them concurrently."""
        pending_tasks = await self.db.get_pending_tasks()
        if not pending_tasks:
            logger.info("No PENDING tasks on blackboard.")
            return {"status": "IDLE", "executed_count": 0, "results": []}

        logger.info("Executing swarm of %d PENDING tasks concurrently...", len(pending_tasks))

        # Parallel asynchronous execution across all agents
        execution_coroutines = [self._execute_single_task(task) for task in pending_tasks]
        results = await asyncio.gather(*execution_coroutines, return_exceptions=False)

        completed_count = sum(1 for r in results if r.get("status") == "COMPLETED")
        failed_count = sum(1 for r in results if r.get("status") == "FAILED")

        summary = {
            "status": "COMPLETED" if failed_count == 0 else "PARTIAL",
            "total_executed": len(results),
            "completed_count": completed_count,
            "failed_count": failed_count,
            "results": results,
        }
        logger.info(
            "Swarm execution finished: %d succeeded, %d failed out of %d.",
            completed_count,
            failed_count,
            len(results),
        )
        return summary

    async def execute_goal(self, user_goal: str) -> Dict[str, Any]:
        """High-level autonomous workflow: Plan, dispatch, and immediately execute swarm to completion."""
        task_ids = await self.plan_and_dispatch(user_goal)
        swarm_result = await self.execute_pending_swarm()
        swarm_result["dispatched_task_ids"] = task_ids
        swarm_result["user_goal"] = user_goal
        return swarm_result


# Singleton instance
master_brain = MasterBrain()
