"""
E.V.E. Master Controller Configuration - FINAL PRODUCTION
Real Workers: Image Generation, Documentation, Coding
Always route to best worker (multithreading enabled)
"""

import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

import sys
sys.stdout.reconfigure(encoding='utf-8')



SECRET_KEY = os.getenv("SECRET_KEY", "ORCHESTRATION2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours


# =============================================================================
# MASTER CONTROLLER SETTINGS
# =============================================================================

MASTER_HOST = "0.0.0.0"
MASTER_PORT = 8001
MASTER_ID = os.getenv("MASTER_ID", "master-1")

MASTER_HEARTBEAT_INTERVAL = 3
MASTER_TIMEOUT = 10
WORKER_HEARTBEAT_INTERVAL = 3
WORKER_TIMEOUT = 10
HEALTH_CHECK_INTERVAL = 5

# =============================================================================
# AI MODEL CONFIGURATION - GROQ (groq/compound)
# =============================================================================

AI_PROVIDER = "groq"
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
MASTER_AI_MODEL = "groq/compound"  # Best for intelligent routing

AI_MAX_TOKENS = 1000
AI_TEMPERATURE = 0.7
AI_TIMEOUT = 30

# =============================================================================
# DATABASE CONFIGURATION - PostgreSQL on Aiven
# =============================================================================

DB_TYPE = os.getenv("DB_TYPE", "postgresql")

# Get absolute path to SSL certificate
_current_dir = os.path.dirname(os.path.abspath(__file__))
_ssl_cert_path = os.path.join(_current_dir, os.getenv("DB_SSL_CA", "ca.pem"))

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME", "defaultdb"),
    "sslmode": "require",
    "sslrootcert": _ssl_cert_path
}

# =============================================================================
# CONTEXT ENGINE SETTINGS
# =============================================================================

MAX_CONTEXT_MESSAGES = 10
CONTEXT_RELEVANCE_THRESHOLD = 0.7

REFERENCE_KEYWORDS = [
    "that", "this", "it", "those", "them",
    "earlier", "before", "previous", "above",
    "continue", "also", "additionally", "same",
    "the code", "the document", "the text", "the image",
    "my previous", "last time", "from earlier",
    "what you said", "as mentioned", "you showed"
]

# =============================================================================
# WORKER SPECIALIZATIONS - YOUR REAL WORKERS
# =============================================================================

WORKER_SPECIALIZATIONS = {
    # Worker-3: Coding (Python, JavaScript, debugging)
    "coding": [
        "python", "javascript", "java", "code", "function", 
        "debug", "programming", "algorithm", "api", "class",
        "write code", "implement", "develop", "script", "bug",
        "fix code", "refactor", "test", "unit test", "error",
        "c++", "rust", "go", "typescript", "react", "node",
        "html", "css", "sql", "database", "backend", "frontend"
    ],
    
    # Worker-2: Documentation (Reports, guides, technical writing)
    "documentation": [
        "write document", "documentation", "report", "guide",
        "manual", "readme", "api docs", "technical writing",
        "user guide", "tutorial", "instructions", "specification",
        "how to", "explain how", "document this", "create docs",
        "write about", "describe", "summarize", "outline",
        "proposal", "whitepaper", "requirements", "overview",
        "help text", "release notes", "changelog", "wiki"
    ],
    
    # Worker-1: Image Generation (DALL-E, Stable Diffusion, etc.)
    "image_generation": [
        "generate image", "create image", "draw", "picture",
        "illustration", "graphic", "design", "logo", "icon",
        "visualize", "diagram", "chart", "infographic",
        "generate photo", "create artwork", "render", "3d model",
        "dalle", "stable diffusion", "midjourney", "image of",
        "show me", "make a picture", "visual", "sketch",
        "banner", "poster", "thumbnail", "avatar", "mockup"
    ]
}

# =============================================================================
# FEATURE FLAGS
# =============================================================================

ENABLE_AI_ROUTING = True                # Use groq/compound for routing
ENABLE_CONTEXT_ENGINE = True            # Detect conversation continuity
ENABLE_MASTER_FAILOVER = True           # Multi-master support
ENABLE_WARMUP = True                    # Generate initial performance data
ENABLE_PERFORMANCE_TRACKING = True      # Learn from worker performance

# =============================================================================
# WARM-UP CONFIGURATION
# =============================================================================

WARMUP_ENABLED = True
WARMUP_TASKS_PER_TYPE = 3

WARMUP_TEST_TASKS = {
    "coding": [
        "Write a Python function to reverse a string",
        "Create a function to check if a number is prime",
        "Implement binary search algorithm"
    ],
    "documentation": [
        "Write a user guide for a todo app",
        "Create API documentation for a REST endpoint",
        "Write installation instructions for a Python package"
    ],
    "image_generation": [
        "Generate an image of a sunset over mountains",
        "Create a logo for a tech startup",
        "Design an icon for a mobile app"
    ]
}

# =============================================================================
# LOGGING
# =============================================================================

LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# =============================================================================
# STARTUP MESSAGE
# =============================================================================

print("\n" + "="*60)
print("✅ CONFIGURATION LOADED - PRODUCTION READY")
print("="*60)
print(f"Master ID: {MASTER_ID}")
print(f"AI Provider: {AI_PROVIDER}")
print(f"AI Model: {MASTER_AI_MODEL} 🧠")
print(f"Database: {DB_TYPE}")

if DB_TYPE == "postgresql":
    print(f"\nPostgreSQL Configuration:")
    print(f"   Host: {DB_CONFIG.get('host', 'Not configured')}")
    print(f"   Port: {DB_CONFIG.get('port', 'Not configured')}")
    print(f"   Database: {DB_CONFIG.get('database', 'Not configured')}")
    print(f"   SSL: {DB_CONFIG.get('sslmode', 'Not configured')}")

if not GROQ_API_KEY:
    print("\n⚠️  WARNING: No Groq API key!")
    print("   Set GROQ_API_KEY in .env")
    print("   Get key from: https://console.groq.com/")
else:
    print(f"\n✅ Groq API key configured")

print("\n🎯 Worker Configuration (Your Real Workers):")
print("   Worker-1: Image Generation (DALL-E, Stable Diffusion)")
print("   Worker-2: Documentation (Reports, guides, writing)")
print("   Worker-3: Coding (Python, JavaScript, debugging)")

print("\n⚙️  Routing Strategy:")
print("   ✅ ALWAYS route to best worker for task type")
print("   ✅ Best worker multithreads (handles multiple tasks)")
print("   ✅ Ensures highest quality results")
print("   ✅ Learns from performance history")

print("\n💾 Database Storage:")
print("   ✅ All user questions stored")
print("   ✅ All AI responses stored")
print("   ✅ Conversation continuity tracked")
print("   ✅ Worker performance metrics logged")
print("   ✅ Context automatically detected")

print("\n💡 Using groq/compound for maximum intelligence!")
print("="*60 + "\n")