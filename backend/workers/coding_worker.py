"""
Coding Worker for E.V.E. System - WITH FULL DOCUMENT PARSING
Specializes in: Programming, debugging, code generation, algorithms
Can read and process uploaded code files, documents, etc!
"""

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

import os
import time
import requests
import base64
from worker_base import BaseWorker

from document_parser import process_uploaded_files  # Import our new parser!
from openai import OpenAI



# Keywords that indicate an image generation task
IMAGE_KEYWORDS = [
    "generate image", "create image", "draw", "picture of", "image of",
    "generate a image", "create a image", "make image", "make a image",
    "illustration", "visualize", "sketch", "render image", "photo of",
    "generate picture", "create picture", "artwork", "design image",
    "generate an image", "create an image", "make an image", "an image of",
    "image showing", "picture showing", "photo showing",
    # Abbreviations
    "generate img", "create img", "make img", "img of",
    "generate pic", "create pic", "make pic", "pic of",
    "generate photo", "make photo"
]

class CodingWorker(BaseWorker):
    def __init__(self):
        super().__init__(
            worker_id="Worker-Coding",
            specialization="coding",
            port=5001
        )
        # Ollama Cloud (kimi-k2.5:cloud) primary, Groq fallback, NVIDIA fallback
        self.ollama_api_key = os.getenv("OLLAMA_API_KEY")
        self.ollama_model = "kimi-k2.5:cloud"
        self.ollama_client = None
        try:
            from ollama import Client
            # Connect to Ollama Cloud instead of localhost
            self.ollama_client = Client(host='https://ollama.com')
            print(f"✅ Ollama Cloud API ready (model: {self.ollama_model})")
            print(f"   🌐 Connected to: https://ollama.com")
        except ImportError:
            self.ollama_client = None
            print("⚠️  Ollama Python package not installed. Ollama Cloud will not be available.")
        except Exception as e:
            self.ollama_client = None
            print(f"⚠️  Ollama Cloud connection failed: {e}")

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print("❌ No GROQ_API_KEY found! Coding worker will not function.")
            raise ValueError("Missing GROQ_API_KEY")
        from groq import Groq
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"
        self.api_provider = "groq"
        print(f"✅ Groq API initialized (model: {self.model})")
        print(f"   ⚡ Using Groq Llama 3.3 70B (100% FREE, NO MONTHLY CAPS)")

        self.nvidia_api_key = os.getenv("NVIDIA_API_KEY")
        if not self.nvidia_api_key:
            print("❌ No NVIDIA_API_KEY found! NVIDIA fallback will not function.")
        else:
            self.nvidia_base_url = "https://integrate.api.nvidia.com/v1"
            self.nvidia_model = "moonshotai/kimi-k2-instruct-0905"
            self.nvidia_client = OpenAI(base_url=self.nvidia_base_url, api_key=self.nvidia_api_key)
            print(f"✅ NVIDIA fallback initialized (model: {self.nvidia_model})")
        self.image_model = "flux"
        print(f"📎 File processing enabled")
    
    def is_image_task(self, prompt: str) -> bool:
        """Check if the prompt is requesting image generation"""
        prompt_lower = prompt.lower()
        # Only trigger on EXPLICIT image generation phrases - not just keywords in content
        generation_phrases = [
            "generate image", "create image", "generate a image", "create a image",
            "generate an image", "create an image", "make an image", "make a image",
            "draw a", "draw an", "generate img", "create img", "generate pic",
            "create pic", "generate photo", "create photo", "draw me"
        ]
        return any(phrase in prompt_lower for phrase in generation_phrases)
    
    def process_uploaded_files(self, files: list) -> str:
        """Process uploaded files and extract code content"""
        if not files:
            return ""
        
        processed_content = "\n\n📎 **Uploaded Files Content:**\n\n"
        
        for file in files:
            filename = file.get("filename", "unknown")
            content_base64 = file.get("content", "")
            mime_type = file.get("mime_type", "unknown")
            
            print(f"   📄 Processing file: {filename} ({mime_type})")
            
            try:
                # Decode base64 content
                content_bytes = base64.b64decode(content_base64)
                
                # Try to decode as text (code files)
                content_text = content_bytes.decode('utf-8', errors='ignore')
                
                # Detect file type by extension
                if filename.endswith(('.py', '.js', '.java', '.cpp', '.c', '.cs', '.go', '.rs', '.php', '.rb', '.swift', '.kt')):
                    # Code file
                    lang = filename.split('.')[-1]
                    processed_content += f"### File: {filename} ({lang.upper()} code)\n```{lang}\n{content_text}\n```\n\n"
                    print(f"      ✅ Extracted {len(content_text)} characters of {lang.upper()} code")
                
                elif filename.endswith(('.html', '.css', '.xml', '.json', '.yaml', '.yml', '.md', '.txt')):
                    # Text/markup file
                    processed_content += f"### File: {filename}\n```\n{content_text}\n```\n\n"
                    print(f"      ✅ Extracted {len(content_text)} characters")
                
                else:
                    # Try as text anyway
                    if len(content_text) > 0 and len(content_text) < 50000:  # Reasonable text size
                        processed_content += f"### File: {filename}\n```\n{content_text}\n```\n\n"
                        print(f"      ✅ Extracted {len(content_text)} characters")
                    else:
                        processed_content += f"### File: {filename}\n*Binary file - {len(content_bytes)} bytes*\n\n"
                        print(f"      ℹ️ Binary file - {len(content_bytes)} bytes")
                    
            except Exception as e:
                processed_content += f"### File: {filename}\n*Error processing file: {str(e)}*\n\n"
                print(f"      ❌ Error processing: {e}")
        
        return processed_content
    
    async def execute_task(self, prompt: str, files: list = None):
        """Execute task - routes to coding or image generation"""
        
        # Process uploaded files with proper parsing
        file_content = ""
        if files:
            print(f"\n📎 Received {len(files)} file(s) - parsing...")
            file_content = process_uploaded_files(files)  # Use the new parser!
        
        if self.is_image_task(prompt):
            return await self.generate_image(prompt)
        else:
            # Add file content to prompt if available
            full_prompt = prompt
            if file_content:
                full_prompt = f"{prompt}\n\n{file_content}"
            
            return await self.execute_coding_task(full_prompt)
    
    async def generate_image(self, prompt: str):
        """Generate image using Pollinations API (instant, free)"""
        print(f"\n{'='*60}")
        print(f"🎨 IMAGE GENERATION REQUESTED")
        print(f"{'='*60}")
        print(f"Prompt: {prompt}")
        
        start_time = time.time()
        
        # Extract clean prompt
        clean_prompt = prompt
        if "=== Current Request ===" in prompt:
            parts = prompt.split("=== Current Request ===")
            if len(parts) > 1:
                clean_prompt = parts[1].strip()
                if clean_prompt.startswith("User:"):
                    clean_prompt = clean_prompt.replace("User:", "", 1).strip()
        
        try:
            import requests
            import base64
            from urllib.parse import quote
            
            print(f"🌐 Using Pollinations API...")
            
            # Pollinations API endpoint
            encoded_prompt = quote(clean_prompt)
            pollinations_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"
            
            # Get image
            response = requests.get(pollinations_url, timeout=30)
            
            if response.status_code == 200:
                img_base64 = base64.b64encode(response.content).decode('utf-8')
                execution_time = time.time() - start_time
                print(f"✅ Image generated in {execution_time:.2f}s")
                
                return {
                    "result": f"🎨 **Image Generated Successfully!**\n\n*Prompt: {clean_prompt}*\n\n![Generated Image](data:image/png;base64,{img_base64})",
                    "execution_time": execution_time,
                    "success": True,
                    "task_type": "image_generation"
                }
            else:
                raise Exception(f"Pollinations API returned status {response.status_code}")
        
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)
            print(f"❌ Image generation failed: {error_msg}")
            
            return {
                "result": f"❌ **Image Generation Failed**\n\nError: {error_msg}\n\nPlease try again.",
                "success": False,
                "execution_time": execution_time,
                "task_type": "image_generation"
            }
    
    async def execute_coding_task(self, prompt: str):
        """Execute coding task using Groq"""
        print(f"\n{'='*60}")
        print(f"🔥 CODING TASK RECEIVED")
        print(f"{'='*60}")
        print(f"Prompt: {prompt[:200]}...")
        
        start_time = time.time()
        
        # Use Ollama Cloud (kimi-k2.5:cloud) as primary, Groq as first fallback, NVIDIA as second fallback
        # 1. Try Ollama Cloud
        if self.ollama_client:
            try:
                response = self.ollama_client.chat(
                    model=self.ollama_model,
                    messages=[{"role": "user", "content": prompt}]
                )
                result = response['message']['content']
                execution_time = time.time() - start_time
                print(f"✅ Coding task completed with Ollama Cloud in {execution_time:.2f}s")
                return {
                    "result": result,
                    "success": True,
                    "execution_time": execution_time,
                    "task_type": "coding"
                }
            except Exception as ollama_error:
                print(f"❌ Ollama Cloud failed: {ollama_error}\nTrying Groq fallback...")
        # 2. Try Groq
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert programmer.

CRITICAL RULES:
- Answer the user's question DIRECTLY without meta-commentary
- DO NOT say \"You have asked...\" or \"In the context of...\"
- DO NOT explain what the user wanted
- Just provide the actual code or answer they're looking for

⚠️ LIMITATIONS:
- I CANNOT access live data, APIs, or real-time information
- I CANNOT get current sports scores, weather, or recent events
- My knowledge is from training data (cutoff: mid-2023)

When writing code:
- Provide well-structured, clean code with proper indentation
- Include helpful comments explaining key parts
- Add a brief explanation of how the code works
- Include example usage when appropriate
- Handle edge cases and add error handling where needed

When analyzing uploaded code files:
- Analyze the code carefully
- Identify bugs, improvements, or optimizations
- Provide specific, actionable feedback
- Show corrected code with explanations

Always write production-quality code that is readable and maintainable."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=2000,
                temperature=0.2
            )
            result = response.choices[0].message.content
            execution_time = time.time() - start_time
            print(f"✅ Coding task completed with Groq in {execution_time:.2f}s")
            return {
                "result": result,
                "success": True,
                "execution_time": execution_time,
                "task_type": "coding"
            }
        except Exception as e:
            print(f"❌ Groq failed: {e}\nTrying NVIDIA fallback...")
            # 3. Try NVIDIA fallback
            if hasattr(self, 'nvidia_client') and self.nvidia_api_key:
                try:
                    completion = self.nvidia_client.chat.completions.create(
                        model=self.nvidia_model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.6,
                        top_p=0.9,
                        max_tokens=4096,
                        stream=True
                    )
                    result = ""
                    for chunk in completion:
                        if not getattr(chunk, "choices", None):
                            continue
                        if chunk.choices[0].delta.content:
                            result += chunk.choices[0].delta.content
                    execution_time = time.time() - start_time
                    print(f"✅ Coding task completed with NVIDIA fallback in {execution_time:.2f}s")
                    return {
                        "result": result,
                        "success": True,
                        "execution_time": execution_time,
                        "task_type": "coding"
                    }
                except Exception as nvidia_error:
                    execution_time = time.time() - start_time
                    print(f"❌ NVIDIA fallback also failed: {nvidia_error}")
                    return {
                        "result": f"Error: {str(nvidia_error)}",
                        "success": False,
                        "execution_time": execution_time,
                        "task_type": "coding"
                    }
            else:
                execution_time = time.time() - start_time
                print(f"❌ No NVIDIA fallback available.")
                return {
                    "result": f"Error: {str(e)}",
                    "success": False,
                    "execution_time": execution_time,
                    "task_type": "coding"
                }


if __name__ == "__main__":
    worker = CodingWorker()
    worker.start()