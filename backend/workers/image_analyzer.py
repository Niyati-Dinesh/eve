"""
Image Analyzer for E.V.E. System
Uses Gemini Vision API to analyze image content and determine routing
"""

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
import base64
import os
from typing import Dict, Tuple
import google.generativeai as genai




# Use Ollama Cloud Llava 34B as primary, Gemini as fallback
self_ollama_model = "llava:34b-cloud"
self_ollama_api_key = os.getenv("OLLAMA_API_KEY")
self_ollama_chat = None
try:
    import ollama
    self_ollama_chat = ollama.chat
    print(f"✅ Ollama Cloud API initialized (model: {self_ollama_model})")
    print(f"   ⚡ Using Ollama Llava 34B as primary for vision tasks")
except Exception as e:
    print(f"⚠️ Ollama Cloud init failed: {e}")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    print("✅ Gemini Vision API initialized (fallback)")
else:
    print("⚠️  No Gemini API key - Gemini fallback disabled")

def analyze_image_content(base64_content: str, user_message: str = "") -> Dict:
    """
    Analyze image using Gemini Vision to determine content type
    
    Args:
        base64_content: Base64 encoded image
        user_message: User's message for context
    
    Returns:
        {
            "content_type": "code_screenshot" | "textbook" | "diagram" | "general",
            "confidence": 0.0-1.0,
            "description": "What the image contains",
            "suggested_worker": "coding" | "documentation" | "analysis"
        }
    """
    
    if not GEMINI_API_KEY:
        print("⚠️  Gemini API not configured - using fallback analysis")
        return {
            "content_type": "general",
            "confidence": 0.5,
            "description": "Image detected but no vision analysis available",
            "suggested_worker": "analysis"
        }
    
    # TEMPORARILY DISABLED - Quota exceeded
    # TODO: Re-enable when quota resets or get paid tier
    print("⚠️  Gemini Vision temporarily disabled (quota exceeded)")
    return {
        "content_type": "general", 
        "confidence": 0.5,
        "description": "Image analysis unavailable - routing to Analysis Worker",
        "suggested_worker": "analysis"
    }

def parse_gemini_response(response_text: str) -> Dict:
    """Parse Gemini's response into structured data"""
    
    result = {
        "content_type": "general",
        "confidence": 0.5,
        "description": "Could not parse response",
        "suggested_worker": "analysis"
    }
    
    lines = response_text.split('\n')
    
    for line in lines:
        line = line.strip()
        
        if line.startswith("CONTENT_TYPE:"):
            result["content_type"] = line.split(":", 1)[1].strip().lower()
            
        elif line.startswith("CONFIDENCE:"):
            try:
                conf_str = line.split(":", 1)[1].strip()
                result["confidence"] = float(conf_str)
            except:
                result["confidence"] = 0.5
                
        elif line.startswith("DESCRIPTION:"):
            result["description"] = line.split(":", 1)[1].strip()
            
        elif line.startswith("SUGGESTED_WORKER:"):
            result["suggested_worker"] = line.split(":", 1)[1].strip().lower()
    
    return result

def should_analyze_image(filename: str) -> bool:
    """Check if file is an image that should be analyzed"""
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg']
    return any(filename.lower().endswith(ext) for ext in image_extensions)

# Test function
if __name__ == "__main__":
    print("Image Analyzer Utility")
    print("=" * 60)
    print("Uses Gemini Vision to analyze images and determine:")
    print("  - Is it a code screenshot?")
    print("  - Is it a textbook page?")
    print("  - Is it a diagram?")
    print("  - What worker should handle it?")
    print("\nReady to analyze images!")
