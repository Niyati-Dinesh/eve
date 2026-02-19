"""
E.V.E. MASTER CONTROLLER v9.0 - "THE VALIDATOR"
NEW FEATURES:
- Task Planning: Breaks complex tasks into steps
- Answer Validation: Checks quality before returning
- Multi-step Execution: Sequential task handling
"""
import sys, os

# ── Path setup: make local modules and backend package importable ─────────────
_HERE = os.path.dirname(os.path.abspath(__file__))          # .../master_controller/
_BACKEND = os.path.abspath(os.path.join(_HERE, ".."))       # .../backend/
_PROJECT = os.path.abspath(os.path.join(_HERE, "..", "..")) # .../E.V.E/

for _p in [_HERE, _BACKEND, _PROJECT]:
    if _p not in sys.path:
        sys.path.insert(0, _p)
# ─────────────────────────────────────────────────────────────────────────────

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Response
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from typing import Dict, Optional, List
import uvicorn
import asyncio
import sys
import time
import requests
import base64
import json
from contextlib import asynccontextmanager
from groq import Groq
import os

# Fix Windows event loop
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Import modules
from core.database import (
    init_database, register_agent, update_agent_heartbeat,
    get_available_agents, create_task, store_execution_result,
    log_system_event, get_system_stats, store_message,
    create_or_get_conversation, get_last_n_messages, assign_task_to_agent
)
from core.config import MASTER_HOST, MASTER_PORT, MASTER_ID, GROQ_API_KEY

# NEW IMPORTS
from task_planner import TaskPlanner
from answer_validator import AnswerValidator
from context_manager import ContextManager

# ENHANCED SYSTEMS (v9.5)
from worker_health_monitor import WorkerHealthMonitor
from response_cache import ResponseCache
from performance_analytics import PerformanceAnalytics

from workers.document_parser import parse_document


# =============================================================================
# INTELLIGENT CORE - Now with Planning & Validation
# =============================================================================

class IntelligentRouter:
    """
    The ONE brain that makes ALL decisions.
    NOW with task planning and answer validation!
    """
    
    def __init__(self, groq_api_key: str):
        self.client = Groq(api_key=groq_api_key) if groq_api_key else None
        self.worker_stats = {}  # Simple success tracking
        
        # NEW: Add planner, validator, and context manager
        self.planner = TaskPlanner(groq_api_key)
        self.validator = AnswerValidator(groq_api_key)
        self.context_manager = ContextManager(groq_api_key)
        
        # ENHANCED SYSTEMS (v9.5)
        self.health_monitor = WorkerHealthMonitor()
        self.cache = ResponseCache(ttl_seconds=3600, max_entries=1000)
        self.analytics = PerformanceAnalytics()
        
        # Start health monitoring
        self.health_monitor.start_monitoring()
        
        print("🧠 Router initialized with:")
        print("   ✅ Task Planner")
        print("   ✅ Answer Validator")
        print("   ✅ Context Manager")
        print("   💓 Health Monitor")
        print("   💾 Response Cache (1hr TTL, 1000 max)")
        print("   📊 Performance Analytics")
    
    def decide_and_route(self, message: str, files: List[Dict] = None, 
                        conversation_history: List[Dict] = None) -> dict:
        """
        Single intelligent decision: 
        - Should master answer directly?
        - Or route to which worker type?
        
        ENHANCED: Now understands varied question formats and user intent
        """
        
        if not self.client:
            print("   ⚠️  No AI client available - using fallback routing")
            return {"handler": "worker", "worker_type": "general", "reasoning": "No AI"}
        
        print(f"\n🤔 Analyzing request: '{message[:100]}...'")
        prompt = self._build_decision_prompt(message, files, conversation_history)
        
        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            handler = (result.get("handler") or "worker").lower().strip()
            worker_type = (result.get("worker_type") or "general").lower().strip()
            reasoning = result.get("reasoning") or "AI decision"
            
            # Validate and normalize worker types
            valid_types = ["coding", "documentation", "analysis", "general"]
            
            # Handle common variations and typos
            type_aliases = {
                "code": "coding",
                "programming": "coding",
                "development": "coding",
                "doc": "documentation",
                "docs": "documentation",
                "writing": "documentation",
                "analyze": "analysis",
                "research": "analysis",
                "data": "analysis"
            }
            
            worker_type = type_aliases.get(worker_type, worker_type)
            
            if worker_type not in valid_types:
                print(f"   ⚠️ Invalid worker type '{worker_type}', using 'general'")
                worker_type = "general"
            
            print(f"🧠 AI Decision: {handler.upper()}")
            print(f"   Type: {worker_type}")
            print(f"   Reason: {reasoning}")
            
            return {
                "handler": handler,
                "worker_type": worker_type,
                "reasoning": reasoning
            }
            
        except Exception as e:
            print(f"⚠️ AI decision failed: {e}")
            return {"handler": "worker", "worker_type": "general", "reasoning": f"Error"}
    
    def _build_decision_prompt(self, message: str, files: List[Dict], history: List[Dict]) -> str:
        """Build intelligent prompt with context - ENHANCED for varied question formats"""
        
        file_info = ""
        if files:
            file_types = [f.get('filename', '').split('.')[-1] for f in files]
            file_info = f"\nFiles: {len(files)} ({', '.join(file_types)})"
        
        context_info = ""
        if history and len(history) > 0:
            context_info = f"\nConversation: {len(history)} messages"
        
        prompt = f"""You are an intelligent task router. Analyze the user's request and understand what they're REALLY asking for, regardless of exact words used.

USER REQUEST: "{message}"{file_info}{context_info}

DECISION OPTIONS:

1. MASTER handles: Simple greetings, casual chat, basic facts you can answer directly without specialized processing.

2. WORKER handles: Tasks requiring specialized capabilities:
   - "coding" → Anything involving programming/software (creating, debugging, optimizing, implementing ANY kind of code or program)
   - "documentation" → Anything involving writing/explaining (reports, guides, explanations, summaries, documentation)
   - "analysis" → Anything involving research/evaluation/comparison (analyzing data, researching topics, comparing options, finding insights)
   - "general" → Other tasks that need processing but don't fit above

YOUR TASK:
Understand the USER'S INTENT from their natural language. Don't look for specific keywords - understand what they're trying to accomplish.

Examples of INTENT recognition:
- If they want you to create/build/make/write/develop ANY form of program/software/code/script → coding
- If they want you to fix/debug/solve problems in code → coding
- If they want you to write/create/compose ANY document/explanation/guide → documentation
- If they want you to examine/study/investigate/compare/evaluate anything → analysis
- If they're just chatting or asking simple factual questions → master

Think: "What is this person trying to achieve?" not "What words did they use?"

Respond with JSON:
{{
  "handler": "master|worker",
  "worker_type": "coding|documentation|analysis|general",
  "reasoning": "what the user actually wants to accomplish"
}}"""
        
        return prompt
    
    def select_best_worker(self, worker_type: str, available: List[Dict]) -> Optional[Dict]:
        """Select best worker based on performance tracking"""
        
        if not available:
            print(f"   ❌ No workers available for type: {worker_type}")
            return None
        
        print(f"   🔍 Selecting from {len(available)} available {worker_type} worker(s):")
        
        scored = []
        for worker in available:
            name = worker['agent_name']
            
            # Check health status first
            health = self.health_monitor.check_worker_health(name)
            if health in ["dead", "unhealthy"]:
                print(f"      ⚠️ Skipping {name} - health: {health}")
                continue
            
            # Get stats from both old tracking and new analytics
            stats = self.worker_stats.get(name, {'success': 0, 'total': 0})
            worker_metrics = self.analytics.worker_metrics.get(name)
            
            if stats['total'] > 0:
                success_rate = stats['success'] / stats['total']
            else:
                success_rate = 0.9  # Assume good performance for new workers
            
            # Enhanced scoring with health bonus
            score = success_rate + (min(stats['total'], 10) * 0.01)
            if health == "healthy":
                score *= 1.1  # 10% bonus for healthy workers
            elif health == "degraded":
                score *= 0.9  # 10% penalty for degraded
            
            scored.append((worker, score, success_rate))
            print(f"      • {name}: {success_rate:.1%} success ({stats['total']} tasks) - Score: {score:.3f} [{health}]")
        
        if not scored:
            print(f"   ⚠️ All workers unhealthy - using fallback")
            return None  # Return None to trigger master fallback
        
        best = max(scored, key=lambda x: x[1])
        print(f"   ✅ Selected: {best[0]['agent_name']} (Best score: {best[1]:.3f})")
        return best[0]
    
    def log_result(self, worker_name: str, success: bool, duration: float = 0, quality_score: Optional[float] = None):
        """Track worker performance"""
        if worker_name not in self.worker_stats:
            self.worker_stats[worker_name] = {'success': 0, 'total': 0}
        
        self.worker_stats[worker_name]['total'] += 1
        if success:
            self.worker_stats[worker_name]['success'] += 1
        else:
            # Record failure in health monitor
            self.health_monitor.record_failure(worker_name)
        
        # Record in analytics
        self.analytics.record_worker_task(worker_name, success, duration, quality_score)
    
    def answer_directly(self, message: str, conversation_history: List[Dict] = None) -> str:
        """Master answers simple questions directly"""
        
        if not self.client:
            return "I'm offline. Please try again later."
        
        messages = []
        
        if conversation_history:
            for msg in conversation_history[-5:]:
                role = "user" if msg['role'] == 'user' else "assistant"
                messages.append({"role": role, "content": msg['content']})
        
        messages.append({"role": "user", "content": message})
        
        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                max_tokens=800,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"I encountered an error: {str(e)[:100]}"

# =============================================================================
# FILE PROCESSOR
# =============================================================================

class FileProcessor:
    """Handles file uploads and parsing"""
    
    @staticmethod
    async def process_uploads(files: List[UploadFile]) -> tuple[List[Dict], str]:
        """Process uploaded files"""
        if not files:
            return [], ""
        
        file_data = []
        parsed_texts = []
        
        print(f"🔎 Processing {len(files)} file(s)...")
        
        for file in files:
            content = await file.read()
            base64_content = base64.b64encode(content).decode('utf-8')
            
            file_data.append({
                "filename": file.filename,
                "content": base64_content,
                "mime_type": file.content_type,
                "size": len(content)
            })
            
            try:
                parsed = parse_document(file.filename, base64_content)
                if parsed and len(parsed.strip()) > 0:
                    parsed_texts.append(f"=== {file.filename} ===\n{parsed}")
                    print(f"   ✅ {file.filename} parsed ({len(content)} bytes)")
                else:
                    print(f"   🔎 {file.filename} ({len(content)} bytes)")
            except Exception as e:
                print(f"   ⚠️ {file.filename}: {e}")
        
        context = "\n\n".join(parsed_texts) if parsed_texts else ""
        return file_data, context

# =============================================================================
# WORKER EXECUTOR
# =============================================================================

class WorkerExecutor:
    """Executes tasks on workers with clean error handling"""
    
    @staticmethod
    def execute(worker: Dict, message: str, files: List[Dict] = None, 
                context: str = "", timeout: int = 120) -> tuple[str, bool, float, Dict]:
        """Execute task on worker - returns (output, success, duration, extra_data)"""
        
        url = f"http://{worker['host']}:{worker['port']}/execute"
        
        prompt = f"{context}\n\n{message}" if context else message
        
        payload = {"prompt": prompt}
        if files:
            payload["files"] = files
        
        print(f"   🔄 Calling {worker['agent_name']}...")
        start = time.time()
        
        try:
            response = requests.post(url, json=payload, timeout=timeout)
            duration = time.time() - start
            
            if response.status_code == 200:
                result = response.json()
                output = result.get("result", "")
                success = result.get("success", True)
                
                # Extract file data if present
                extra_data = {}
                if "file" in result:
                    extra_data["file"] = result["file"]
                    print(f"   📎 File data detected: {result['file'].get('filename', 'unknown')}")
                
                if not success or "error" in output.lower()[:100]:
                    return output, False, duration, extra_data
                
                print(f"   ✅ Success in {duration:.1f}s")
                if extra_data:
                    print(f"   📎 Returning with file data: {list(extra_data.keys())}")
                return output, True, duration, extra_data
            else:
                return f"Worker error: HTTP {response.status_code}", False, duration, {}
                
        except requests.Timeout:
            duration = time.time() - start
            return f"Worker timeout after {timeout}s", False, duration, {}
        except Exception as e:
            duration = time.time() - start
            return f"Worker error: {str(e)[:100]}", False, duration, {}

# =============================================================================
# GLOBAL STATE
# =============================================================================

router = None
file_processor = FileProcessor()
worker_executor = WorkerExecutor()

# File storage for generated documents
generated_files = {}  # {file_id: {"data": bytes, "filename": str, "mime_type": str}}

# =============================================================================
# LIFESPAN
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    global router
    
    print("\n" + "="*60)
    print("🚀 E.V.E. MASTER v9.0 - THE VALIDATOR")
    print("="*60)
    print(f"Master ID: {MASTER_ID}")
    
    # Test database connection first
    try:
        print("\n🔍 Testing database connection...")
        init_database()
        print("✅ Database initialized and connected")
    except Exception as e:
        print(f"\n❌ DATABASE CONNECTION FAILED!")
        print(f"   Error: {str(e)}")
        print(f"\n🔧 Troubleshooting:")
        print(f"   1. Check if PostgreSQL is accessible")
        print(f"   2. Verify credentials in master_controller/.env")
        print(f"   3. Ensure ca.pem certificate exists")
        print(f"   4. Check network connectivity to database")
        raise
    
    router = IntelligentRouter(GROQ_API_KEY)
    print(f"🧠 AI Router: {'Active' if router.client else 'Disabled'}")
    
    print(f"\n✨ NEW IN v9.0:")
    print(f"   📋 Task Planning (multi-step execution)")
    print(f"   ✅ Answer Validation (quality checking)")
    print(f"   🧠 Intelligent Context Management (AI-selected history)")
    print(f"   🎯 AI-driven routing (no keyword restrictions)")
    
    print(f"\n✅ Master Ready")
    print(f"   🌐 Server: http://{MASTER_HOST}:{MASTER_PORT}")
    print("="*60 + "\n")
    
    yield
    
    print("\n🛑 Shutting down...")
    
    if router and router.validator:
        stats = router.validator.get_validation_stats()
        if stats.get('total_validations', 0) > 0:
            print("\n📊 Validation Statistics:")
            for key, value in stats.items():
                print(f"   {key}: {value}")
    
    print("✅ Shutdown complete")

# =============================================================================
# APP
# =============================================================================

app = FastAPI(title="E.V.E. Master v9.0", version="9.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# MAIN ENDPOINT - Multi-Step Planning & Validation
# =============================================================================

@app.post("/process_message")
async def process_message(
    user_id: str = Form(...),
    message: str = Form(...),
    conversation_id: Optional[str] = Form(None),
    files: Optional[List[UploadFile]] = File(None)
):
    """
    Intelligent message processing v9.0
    - Task planning for complex requests
    - Multi-step execution
    - Answer validation before returning
    """
    
    start_time = time.time()
    
    print("\n" + "="*60)
    print(f"📨 MESSAGE: {message[:80]}...")
    print("="*60)
    
    # Setup conversation
    if not conversation_id:
        conversation_id = f"{user_id}_{int(time.time())}"
    
    create_or_get_conversation(conversation_id, user_id=1)
    store_message(conversation_id, 'user', message)
    
    # Process files
    file_data, file_context = await file_processor.process_uploads(files)
    
    # Get conversation history
    history = get_last_n_messages(conversation_id, n=10)
    
    # STEP 1: PLAN THE TASK
    print("\n📋 STEP 1: Task Planning")
    task_plan = router.planner.plan_task(message, file_data)
    
    # STEP 2: Execute based on plan
    response_text = None
    extra_data = {}
    
    if task_plan["is_multi_step"]:
        print(f"\n🎯 Multi-step execution: {len(task_plan['steps'])} steps")
        response_text, extra_data = await execute_multi_step(
            task_plan, message, file_data, file_context, history, conversation_id, user_id
        )
    else:
        step_type = task_plan['steps'][0]
        
        # MASTER HANDLES SIMPLE QUERIES DIRECTLY (no worker needed)
        if step_type == "general" and len(message.strip()) < 50:
            print(f"\n🧠 Simple query - Master handling directly")
            response_text = router.answer_directly(message, history)
            print(f"   ✅ Answered in 0.5s")
        else:
            print(f"\n🎯 Single-step execution: {step_type}")
            response_text, extra_data = await execute_single_step(
                step_type, message, file_data, file_context, history, conversation_id, user_id
            )
    
    # Store final response
    store_message(conversation_id, 'assistant', response_text)
    
    total_time = time.time() - start_time
    print(f"\n✅ Complete in {total_time:.2f}s")
    print("="*60 + "\n")
    
    # Build response with file data if present
    response_payload = {"response": response_text, "conversation_id": conversation_id}
    if extra_data and "file" in extra_data:
        response_payload["file"] = extra_data["file"]
        print(f"   📎 Including file in response: {extra_data['file'].get('filename', 'unknown')}")
    
    print(f"\n📤 Final response keys: {list(response_payload.keys())}")
    return response_payload


async def execute_single_step(
    step_type: str,
    message: str,
    file_data: List[Dict],
    file_context: str,
    history: List[Dict],
    conversation_id: str,
    user_id: str
) -> tuple[str, Dict]:
    """Execute a single task step with validation - ENHANCED with intelligent context
    Returns: (response_text, extra_data)
    """
    
    start_time = time.time()
    print(f"\n{'─'*60}")
    print(f"🎯 Executing Task: {step_type.upper()}")
    print(f"   Message: {message[:80]}...")
    print(f"{'─'*60}")
    
    task_id = create_task(user_id=1, task_desc=message, task_type=step_type, priority=1)
    
    # INTELLIGENT CONTEXT ANALYSIS
    print(f"\n📍 STEP 1: Context Analysis")
    smart_context, context_analysis = router.context_manager.get_smart_context(
        message, history, file_context
    )
    
    print(f"\n📍 STEP 2: Task Execution")
    print(f"   Planned step type: {step_type.upper()}")
    
    # Use the step_type from planner, don't re-route!
    response_text = None
    worker_name = None
    success = False
    duration = 0.0
    extra_data = {}
    max_retries = 2
    
    for attempt in range(max_retries):
        if attempt > 0:
            print(f"\n   🔄 Retry attempt {attempt + 1}/{max_retries}")
        
        print(f"\n📍 STEP 3: Worker Selection (Attempt {attempt + 1})")
        
        # Use the planned step_type directly - don't re-route!
        worker_type = step_type
        print(f"   🔍 Looking for {worker_type} worker...")
        available = get_available_agents(task_type=worker_type)
            
        # Enhanced fallback: Try related worker types if primary unavailable
        if not available:
            print(f"   ⚠️  No {worker_type} workers available - trying fallbacks...")
            fallback_map = {
                "coding": ["general", "analysis"],
                "documentation": ["general", "analysis"],
                "analysis": ["general", "documentation"],
                "general": ["analysis", "documentation", "coding"],
                "image_generation": ["coding", "analysis", "general"],  # any worker can generate images
            }
            fallbacks = fallback_map.get(worker_type, ["general"])
            for fallback_type in fallbacks:
                print(f"      • Trying {fallback_type}...")
                available = get_available_agents(task_type=fallback_type)
                if available:
                    print(f"   ✅ Found {len(available)} {fallback_type} worker(s)")
                    worker_type = fallback_type
                    break
        else:
            print(f"   ✅ Found {len(available)} {worker_type} worker(s)")
        
        if available:
            worker = router.select_best_worker(worker_type, available)
            
            if worker:
                print(f"   📤 Assigning task to {worker['agent_name']}...")
                try:
                    assign_task_to_agent(task_id, worker['agent_id'], order=attempt+1)
                except Exception as _assign_err:
                    # task_assignments PK conflict on retry is non-fatal
                    print(f"   ⚠️ Task assignment note: {_assign_err}")
                
                # Send smart context to worker
                response_text, success, duration, extra_data = worker_executor.execute(
                    worker, message, file_data, smart_context
                )
                worker_name = worker['agent_name']
                
                if success:
                    print(f"   ✅ Task completed by {worker_name} in {duration:.2f}s")
                else:
                    print(f"   ⚠️  Task failed on {worker_name} after {duration:.2f}s")
                
                store_execution_result(
                    task_id, worker['agent_id'], response_text, success, duration
                )
            else:
                # No healthy worker available - use master
                print("   🧠 No healthy worker - Master handling directly...")
                response_text = router.answer_directly(message, history)
                worker_name = "Master-Controller"
                success = True
                duration = 0.0
                extra_data = {}
        
        if not available or not response_text:
            print("   🧠 Master handling directly...")
            response_text = router.answer_directly(message, history)
            worker_name = "Master-Controller"
            success = True
            duration = 0.0
            extra_data = {}
        
        # VALIDATE THE ANSWER
        print("\n📍 STEP 4: Answer Validation")
        validation = router.validator.validate_answer(
            message, response_text, worker_name
        )
        
        print(f"   Quality Score: {validation['quality_score']}/10")
        print(f"   Assessment: {validation.get('issues', 'No issues')}")
        
        # Debug: Check if extra_data has file
        if extra_data and "file" in extra_data:
            print(f"   📎 File data present: {extra_data['file'].get('filename', 'unknown')}")
        
        # Enhanced logging with quality score after validation
        quality_score = validation.get('quality_score', None)
        router.log_result(worker_name, success, duration, quality_score)
        
        if not validation["should_retry"] or validation["quality_score"] >= 6:
            print("   ✅ Answer quality accepted")
            break
        else:
            print(f"   ⚠️  Quality too low (threshold: 6/10)")
            if attempt < max_retries - 1:
                print("   ↻ Retrying with different worker...")
            else:
                print("   ⚠️  Max retries reached - using current answer")
    
    execution_time = time.time() - start_time
    print(f"\n   ⏱️  Total execution time: {execution_time:.2f}s")
    if extra_data and "file" in extra_data:
        print(f"   📎 Returning with file: {extra_data['file'].get('filename', 'unknown')}")
    return response_text, extra_data


async def execute_multi_step(
    task_plan: Dict,
    message: str,
    file_data: List[Dict],
    file_context: str,
    history: List[Dict],
    conversation_id: str,
    user_id: str
) -> tuple[str, Dict]:
    """Execute multi-step task plan
    Returns: (response_text, extra_data)
    """
    
    steps = task_plan["steps"]
    accumulated_context = file_context
    final_response = ""
    final_extra_data = {}
    
    print(f"\n{'='*60}")
    print(f"🎯 MULTI-STEP EXECUTION: {len(steps)} steps")
    print(f"   Plan: {' → '.join(steps)}")
    print(f"{'='*60}")
    
    for i, step_type in enumerate(steps):
        print(f"\n{'─'*60}")
        print(f"📍 STEP {i + 1}/{len(steps)}: {step_type.upper()}")
        print(f"{'─'*60}")
        
        if i == 0:
            step_message = message
        else:
            step_message = f"""Continue from previous step.

Original task: {message}

Previous step result:
{final_response[:500]}...

Now perform: {step_type}"""
        
        step_response, step_extra_data = await execute_single_step(
            step_type, step_message, file_data, 
            accumulated_context, history, conversation_id, user_id
        )
        
        if i == 0:
            final_response = step_response
            final_extra_data = step_extra_data
        else:
            final_response = f"{final_response}\n\n---\n\n{step_response}"
            # Keep the last step's extra data (like files)
            if step_extra_data:
                final_extra_data = step_extra_data
        
        accumulated_context += f"\n\nStep {i + 1} ({step_type}) result:\n{step_response[:500]}"
        
        if router.planner.should_continue_to_next_step(i, len(steps), step_response):
            continue
        else:
            print(f"\n⚠️ Stopping execution after step {i + 1}")
            break
    
    print(f"\n{'='*60}")
    print(f"✅ Multi-step execution complete")
    print(f"{'='*60}")
    
    return final_response, final_extra_data


# =============================================================================
# AGENT MANAGEMENT
# =============================================================================

@app.post("/register_agent")
async def register_agent_endpoint(data: dict):
    """Register AI agent"""
    try:
        agent_name = data.get('agent_name')
        capability = data.get('capability')
        host = data.get('host', 'localhost')
        port = data.get('port', 5000)
        hardware_stats = data.get('hardware_stats', {})
        
        agent_id = register_agent(agent_name, capability, host, port, hardware_stats)

        # FIX: log_system_event only accepts log_type and message - no agent_id kwarg
        log_system_event("info", f"Agent {agent_name} registered (ID: {agent_id})")
        
        print(f"✅ Agent registered: {agent_name} (ID: {agent_id})")
        print(f"   Type: {capability}")
        
        return {"agent_id": agent_id, "message": f"Agent {agent_name} registered"}
        
    except Exception as e:
        print(f"❌ Registration failed: {e}")
        raise HTTPException(500, str(e))

@app.post("/agent_heartbeat")
async def agent_heartbeat_endpoint(data: dict):
    """Receive heartbeat from agent"""
    try:
        agent_name = data.get('agent_name')
        status = data.get('status', 'idle')
        hardware_stats = data.get('hardware_stats', {})
        
        update_agent_heartbeat(agent_name, status, hardware_stats)
        
        # Update health monitor
        if router:
            router.health_monitor.update_heartbeat(agent_name, status)
        
        return {"message": "Heartbeat received"}
        
    except Exception as e:
        return {"error": str(e)}

@app.get("/list_workers")
def list_workers():
    """Get system stats"""
    try:
        stats = get_system_stats()
        
        validation_stats = {}
        if router and router.validator:
            validation_stats = router.validator.get_validation_stats()
        
        return {
            "system": stats,
            "router_stats": router.worker_stats if router else {},
            "validation_stats": validation_stats,
            "version": "9.5 - The Ultimate"
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "version": "9.5",
        "ai_enabled": router.client is not None if router else False,
        "features": {
            "task_planning": True,
            "answer_validation": True,
            "multi_step_execution": True,
            "health_monitoring": True,
            "response_caching": True,
            "performance_analytics": True,
            "load_balancing": True
        }
    }

@app.get("/diagnostics")
def get_diagnostics():
    """Comprehensive system diagnostics and performance report"""
    try:
        if not router:
            return {"error": "Router not initialized"}
        
        # Get all system metrics
        health_report = router.health_monitor.get_health_report()
        cache_stats = router.cache.get_stats()
        analytics_report = router.analytics.get_comprehensive_report()
        validation_stats = router.validator.get_validation_stats()
        
        # Generate system health score (0-10)
        healthy_workers = health_report.get("healthy", 0)
        total_workers = health_report.get("total_workers", 1)
        worker_health_score = (healthy_workers / total_workers * 10) if total_workers > 0 else 0
        
        cache_efficiency = float(cache_stats.get("efficiency", "0%").rstrip('%'))
        cache_score = min(cache_efficiency / 10, 10)  # Up to 10 for 100% efficiency
        
        # Overall system score
        system_score = (
            worker_health_score * 0.4 +  # 40% worker health
            cache_score * 0.2 +          # 20% cache efficiency
            min(validation_stats.get("avg_quality", 0), 10) * 0.4  # 40% answer quality
        )
        
        return {
            "system_score": f"{system_score:.1f}/10",
            "timestamp": datetime.now().isoformat(),
            "version": "9.5 - The Ultimate",
            "worker_health": health_report,
            "cache_performance": cache_stats,
            "analytics": analytics_report,
            "validation_stats": validation_stats,
            "system_status": "excellent" if system_score >= 8.5 else "good" if system_score >= 7 else "degraded"
        }
    except Exception as e:
        return {"error": str(e), "details": "Diagnostics failed"}

@app.post("/cache/clear")
def clear_cache():
    """Clear response cache"""
    try:
        if router:
            router.cache.clear_all()
            return {"message": "Cache cleared successfully"}
        return {"error": "Router not initialized"}
    except Exception as e:
        return {"error": str(e)}

# File storage for downloads (in-memory)
_file_storage = {}

@app.post("/store_file")
async def store_file(data: dict):
    """Store generated file for download"""
    file_id = f"file_{int(time.time())}_{hash(data.get('filename', '')) % 10000}"
    _file_storage[file_id] = {
        "content": data.get("content"),
        "filename": data.get("filename"),
        "mime_type": data.get("mime_type", "application/octet-stream")
    }
    return {"file_id": file_id, "filename": data.get("filename")}

@app.get("/download/{file_id}")
async def download_file(file_id: str):
    """Download stored file"""
    if file_id not in _file_storage:
        raise HTTPException(404, "File not found")

    file_data = _file_storage[file_id]
    import base64
    content = base64.b64decode(file_data["content"])

    return Response(
        content=content,
        media_type=file_data["mime_type"],
        headers={"Content-Disposition": f'attachment; filename="{file_data["filename"]}"'}
    )

# =============================================================================
# RUN
# =============================================================================

if __name__ == "__main__":
    config = uvicorn.Config(
        app,
        host=MASTER_HOST,
        port=MASTER_PORT,
        log_level="info",
        timeout_keep_alive=30
    )
    server = uvicorn.Server(config)
    
    try:
        server.run()
    except KeyboardInterrupt:
        print("\n🛑 Master stopped by user")
    except Exception as e:
        print(f"\n❌ Master crashed: {e}")
        raise