"""
Documentation Worker for E.V.E. System - WITH FULL DOCUMENT PARSING
Specializes in: Technical writing, documentation, guides, manuals
Can read and process .docx, .pdf, .txt and other document files!
NOW WITH PDF/DOCX FILE GENERATION!
"""

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
import os
import time
import requests
import base64
import asyncio
import google.generativeai as genai
from worker_base import BaseWorker
from document_parser import process_uploaded_files
from file_generator import generate_file

load_dotenv()

class DocumentationWorker(BaseWorker):
    def __init__(self):
        super().__init__(
            worker_id="Worker-Documentation",
            specialization="documentation",
            port=5002
        )
        
        # Use Ollama Cloud gemma3:27b-cloud as primary, Groq as fallback
        self.ollama_api_key = os.getenv("OLLAMA_API_KEY")
        self.ollama_model = "gemma3:27b-cloud"
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

        self.api_provider = None
        self.model = None
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key:
            try:
                from groq import Groq
                self.client = Groq(api_key=groq_key)
                self.api_provider = "groq"
                self.model = "llama-3.3-70b-versatile"
                print(f"✅ Groq API initialized (model: {self.model})")
                print(f"   ⚡ Using Groq Llama 3.3 70B as fallback")
            except Exception as e:
                print(f"⚠️  Groq init failed: {e}")

        if not self.api_provider:
            raise ValueError("No GROQ_API_KEY found! Documentation worker needs Groq API key.")

        # Image generation config
        self.image_model = "gptimage"
        print(f"🎨 Image generation enabled (Pollinations: {self.image_model})")
        print(f"📎 File processing enabled")
        print(f"📄 PDF/DOCX generation enabled")
    
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
        """
        Process uploaded files and extract content
        
        Files come as: [{"filename": "test.txt", "content": "base64...", "mime_type": "text/plain"}]
        """
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
                
                # Try to decode as text
                if "text" in mime_type or filename.endswith((".txt", ".md", ".py", ".js", ".html", ".css", ".json")):
                    content_text = content_bytes.decode('utf-8', errors='ignore')
                    processed_content += f"### File: {filename}\n```\n{content_text}\n```\n\n"
                    print(f"      ✅ Extracted {len(content_text)} characters")
                
                elif mime_type == "application/pdf":
                    # For PDFs, we'd need a PDF parser (not included yet)
                    processed_content += f"### File: {filename}\n*PDF file detected - {len(content_bytes)} bytes*\n\n"
                    print(f"      ⚠️ PDF detected - content extraction not yet implemented")
                
                else:
                    # Binary file
                    processed_content += f"### File: {filename}\n*Binary file - {len(content_bytes)} bytes ({mime_type})*\n\n"
                    print(f"      ℹ️ Binary file - {len(content_bytes)} bytes")
                    
            except Exception as e:
                processed_content += f"### File: {filename}\n*Error processing file: {str(e)}*\n\n"
                print(f"      ❌ Error processing: {e}")
        
        return processed_content
    
    async def execute_task(self, prompt: str, files: list = None):
        """Execute task - routes to documentation, image, or file generation"""

        # Process uploaded files with proper document parsing
        file_content = ""
        if files:
            print(f"\n📎 Received {len(files)} file(s) - parsing documents...")
            file_content = process_uploaded_files(files)

        # Check if it's an image task
        if self.is_image_task(prompt):
            return await self.generate_image(prompt)
        else:
            # Add file content to prompt if available
            full_prompt = prompt
            if file_content:
                full_prompt = f"{file_content}\n\n=== User Request ===\n{prompt}"
            return await self.execute_documentation_task(full_prompt)
    
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
    
    def detect_file_request(self, prompt: str) -> dict:
        """Detect if user wants PDF or DOCX file"""
        prompt_lower = prompt.lower()

        # Check for DOCX request FIRST (more specific)
        docx_keywords = ["docx", "doc file", "word", "generate docx", "create docx", "make docx", "word document", ".docx"]
        if any(kw in prompt_lower for kw in docx_keywords):
            title = "Document"
            if "on " in prompt_lower:
                topic = prompt_lower.split("on ")[-1].split()[0:3]
                title = "_".join(topic).replace(",", "").replace(".", "")
            elif "about " in prompt_lower:
                topic = prompt_lower.split("about ")[-1].split()[0:3]
                title = "_".join(topic).replace(",", "").replace(".", "")
            return {"type": "docx", "generate": True, "title": title.title()}

        # Check for PDF request (check after DOCX to avoid conflicts)
        pdf_keywords = ["pdf", "generate pdf", "create pdf", "make pdf", "generate me a pdf", "create me a pdf", ".pdf"]
        if any(kw in prompt_lower for kw in pdf_keywords):
            # Extract title from the topic mentioned
            title = "AI_Document"  # Default
            if "on " in prompt_lower:
                topic = prompt_lower.split("on ")[-1].split()[0:3]
                title = "_".join(topic).replace(",", "").replace(".", "")
            elif "about " in prompt_lower:
                topic = prompt_lower.split("about ")[-1].split()[0:3]
                title = "_".join(topic).replace(",", "").replace(".", "")
            else:
                title = "Document"
            return {"type": "pdf", "generate": True, "title": title.title()}

        return {"type": None, "generate": False, "title": "Document"}

    async def execute_documentation_task(self, prompt: str):
        """Execute documentation task using Groq"""
        print(f"\n{'='*60}")
        print(f"📥 DOCUMENTATION TASK RECEIVED")
        print(f"{'='*60}")
        print(f"Prompt: {prompt[:200]}...")

        start_time = time.time()

        try:
            full_prompt = f"""You are an expert technical writer and document analyst.

CRITICAL RULES:
- Answer the user's question DIRECTLY without meta-commentary
- DO NOT say \"You have asked...\" or \"In the context of...\"
- DO NOT explain what the user wanted or provide an \"Overview\" of their question
- Just provide the actual answer they're looking for
- DO NOT include instructions on how to generate PDFs or documents
- DO NOT add code examples for PDF generation
- The system will automatically handle file generation

⚠️ LIMITATIONS:
- I CANNOT access live data, real-time information, or the internet
- I CANNOT get current sports scores, match data, or recent events
- My knowledge is from training data (cutoff: mid-2023)

When analyzing documents:
- Extract and present the key information clearly
- Use proper structure with headings (##, ###)
- Summarize important sections
- Be concise and focused

When writing documentation:
- Use clear, professional language
- Include examples where helpful
- Use bullet points and numbered lists
- Add code snippets with proper formatting when relevant
- Format professionally with clear section headings

User request: {prompt}"""
            # Groq API call
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": full_prompt}],
                temperature=0.3,
                max_tokens=2500
            )
            result = response.choices[0].message.content
            execution_time = time.time() - start_time

            print(f"✅ Documentation task completed in {execution_time:.2f}s")
            print(f"Response length: {len(result)} characters\n")

            # Check if file generation is requested
            file_info = self.detect_file_request(prompt)
            print(f"🔍 File detection result: {file_info}")
            
            response_data = {
                "result": result,
                "success": True,
                "execution_time": execution_time,
                "task_type": "documentation"
            }

            if file_info["generate"]:
                try:
                    print(f"📄 Generating {file_info['type'].upper()} file...")
                    file_data, filename, mime_type = generate_file(
                        result, file_info["type"], file_info["title"]
                    )
                    file_base64 = base64.b64encode(file_data.getvalue()).decode('utf-8')
                    response_data["file"] = {
                        "filename": filename,
                        "content": file_base64,
                        "mime_type": mime_type
                    }
                    print(f"✅ File generated: {filename}")
                    print(f"✅ File added to response_data with {len(file_base64)} base64 chars")
                except Exception as e:
                    print(f"⚠️ File generation failed: {e}")
                    import traceback
                    traceback.print_exc()
                    response_data["result"] += f"\n\n⚠️ File generation failed: {str(e)}"
            else:
                print(f"ℹ️ No file generation requested")

            print(f"📤 Returning response with keys: {list(response_data.keys())}")
            return response_data

        except Exception as e:
            execution_time = time.time() - start_time
            print(f"❌ Documentation task failed: {e}\n")
            return {
                "result": f"Error: {str(e)}",
                "success": False,
                "execution_time": execution_time,
                "task_type": "documentation"
            }


if __name__ == "__main__":
    worker = DocumentationWorker()
    worker.start()