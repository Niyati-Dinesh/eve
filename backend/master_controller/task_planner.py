"""
Task Planner for E.V.E. Master v9.0
Breaks complex tasks into sequential steps
"""

from groq import Groq
import json
from typing import List, Dict, Optional
from core.config import GROQ_API_KEY


class TaskPlanner:
    """
    Intelligent task planning system.
    Breaks complex tasks into simple steps.
    """

    def __init__(self, groq_api_key: str):
        self.client = Groq(api_key=groq_api_key) if groq_api_key else None

    def plan_task(self, message: str, files: List[Dict] = None) -> Dict:
        """
        Break a complex task into execution steps.

        Returns: {"steps": [...], "is_multi_step": bool, "reasoning": str}
        """

        if not self.client:
            return {
                "steps": ["general"],
                "is_multi_step": False,
                "reasoning": "No AI planner available - single step execution",
            }

        # Fast-path: catch image generation BEFORE hitting the LLM
        # so it is NEVER misrouted to coding/documentation
        if self._is_image_request(message):
            print("\n📋 TASK PLAN (fast-path):")
            print("   Steps: image_generation")
            print("   Multi-step: False")
            print("   Reason: User wants to generate/create/draw an image")
            return {
                "steps": ["image_generation"],
                "is_multi_step": False,
                "reasoning": "User wants to generate or create an image",
            }

        prompt = self._build_planning_prompt(message, files)

        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.2,
                response_format={"type": "json_object"},
            )

            result = json.loads(response.choices[0].message.content)

            if "steps" not in result or not isinstance(result["steps"], list):
                return self._default_plan()

            valid_types = {"coding", "documentation", "analysis", "general", "image_generation"}
            type_aliases = {
                "code": "coding", "programming": "coding", "development": "coding",
                "doc": "documentation", "docs": "documentation", "writing": "documentation",
                "analyze": "analysis", "research": "analysis", "data": "analysis",
                "image": "image_generation", "picture": "image_generation",
                "draw": "image_generation", "generate_image": "image_generation",
            }

            valid_steps = []
            for step in result["steps"]:
                s = step.lower().strip()
                s = type_aliases.get(s, s)
                if s in valid_types:
                    valid_steps.append(s)

            if not valid_steps:
                valid_steps = ["general"]

            plan = {
                "steps": valid_steps,
                "is_multi_step": len(valid_steps) > 1,
                "reasoning": result.get("reasoning", "AI task planning"),
            }

            print(f"\n📋 TASK PLAN:")
            print(f"   Steps: {' → '.join(plan['steps'])}")
            print(f"   Multi-step: {plan['is_multi_step']}")
            print(f"   Reason: {plan['reasoning']}")

            return plan

        except Exception as e:
            print(f"⚠️ Planning error: {str(e)[:100]}")
            return self._default_plan()

    # ──────────────────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────────────────

    _IMAGE_PHRASES = [
        "generate image", "generate an image", "generate a image",
        "create image", "create an image", "create a image",
        "make image", "make an image", "make a image",
        "draw a", "draw an", "draw me",
        "generate img", "create img", "make img",
        "generate pic", "create pic", "make pic",
        "generate photo", "create photo", "make photo",
        "generate picture", "create picture", "make picture",
        "image of", "picture of", "photo of",
        "render image", "render a", "visualize",
        "show me a picture", "show me an image",
    ]

    def _is_image_request(self, message: str) -> bool:
        """Return True if the message is clearly asking for image generation."""
        msg = message.lower()
        return any(phrase in msg for phrase in self._IMAGE_PHRASES)

    def _build_planning_prompt(self, message: str, files: List[Dict]) -> str:
        file_context = ""
        if files:
            file_types = [f.get("filename", "").split(".")[-1] for f in files]
            file_context = f"\n\nFiles attached: {len(files)} files ({', '.join(file_types)})"

        return f"""You are a smart task planner. Understand what the user REALLY wants and break it into logical steps.

USER REQUEST: "{message}"{file_context}

STEP CATEGORIES:
- "coding"           → Creating/fixing/working with any programs or code
- "documentation"    → Writing explanatory content, reports, guides, documents
- "analysis"         → Researching, analyzing, comparing, or evaluating information
- "image_generation" → Generating, creating, drawing, or rendering ANY image/picture/photo/artwork
- "general"          → Other tasks

CRITICAL RULE — IMAGE GENERATION:
ANY request to generate, create, draw, make, or render an image/picture/photo/artwork MUST use
"image_generation" as the step — NEVER "coding", even if it sounds like it could be implemented
with code. The user wants an actual image produced, not code that generates one.

Examples:
- "generate an image of a sunset"  → ["image_generation"]
- "create a picture of a cat"      → ["image_generation"]
- "draw a mountain landscape"      → ["image_generation"]
- "make a photo of a beach"        → ["image_generation"]

PLANNING RULES:
1. DEFAULT to SINGLE STEP — most requests need just one type of work.
2. Use MULTIPLE STEPS only when the user explicitly wants multiple DIFFERENT types of output.
3. Maximum 3 steps.

Other examples:
- "write code and a report"             → ["coding", "documentation"]
- "analyze data and write report"       → ["analysis", "documentation"]
- "write code to analyze"               → ["coding"]  (single step — just code)
- "research X and write about it"       → ["analysis", "documentation"]

Respond with JSON:
{{"steps": ["type1"], "reasoning": "what they want to accomplish"}}"""

    def _default_plan(self) -> Dict:
        return {
            "steps": ["general"],
            "is_multi_step": False,
            "reasoning": "Default single-step plan",
        }

    def should_continue_to_next_step(
        self, current_step: int, total_steps: int, current_result: str
    ) -> bool:
        error_indicators = [
            "error", "failed", "cannot", "unable to",
            "sorry", "apologize", "something went wrong",
        ]
        result_lower = current_result.lower()[:200]
        for indicator in error_indicators:
            if indicator in result_lower:
                print(f"   ⚠️ Step {current_step + 1} appears to have failed")
                print(f"   🛑 Stopping multi-step execution")
                return False

        if current_step < total_steps - 1:
            print(f"   ✅ Step {current_step + 1}/{total_steps} complete")
            print(f"   ➡️ Proceeding to step {current_step + 2}")
            return True

        return False


# ── Self-test ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Testing Task Planner")
    print("=" * 60)

    planner = TaskPlanner(GROQ_API_KEY)

    test_tasks = [
        "Write a Python function to calculate fibonacci",
        "Create a sorting algorithm and document how it works",
        "Debug this code and explain the fix",
        "Hello, how are you?",
        "Analyze sales data and write a summary report",
        "Generate an image of a sunset",
        "Create a picture of a mountain",
        "Draw a cat sitting on a mat",
        "Make an image of a futuristic city",
    ]

    for task in test_tasks:
        print(f"\n📝 Task: {task}")
        plan = planner.plan_task(task)
        print(f"   Result: {plan['steps']} — {plan['reasoning']}")

    print("\n" + "=" * 60)