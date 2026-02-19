"""
Analysis Worker for E.V.E. System - WITH FULL DOCUMENT PARSING
Specializes in: Multi-step logical reasoning, decision evaluation, trend analysis
Can read and analyze .docx, .pdf, .txt and data files!
"""


from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

import os
import time
import requests
import base64

from groq import Groq
from worker_base import BaseWorker
from document_parser import process_uploaded_files



# Keywords that indicate an image generation task
IMAGE_KEYWORDS = [
    "generate image", "create image", "draw", "picture of", "image of",
    "generate a image", "create a image", "make image", "make a image",
    "illustration", "visualize", "sketch", "render image", "photo of",
    "generate picture", "create picture", "artwork", "design image",
    "generate an image", "create an image", "make an image", "an image of",
    "image showing", "picture showing", "photo showing","generate any image",
    # Abbreviations
    "generate img", "create img", "make img", "img of",
    "generate pic", "create pic", "make pic", "pic of",
    "generate photo", "make photo"
]

class AnalysisWorker(BaseWorker):
    def __init__(self):
        super().__init__(
            worker_id="Worker-Analysis",
            specialization="analysis",
            port=5003
        )
        
        # Use Ollama Cloud qwen3-next as primary, Groq as fallback
        self.ollama_api_key = os.getenv("OLLAMA_API_KEY")
        self.ollama_model = "qwen3-next"
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
        else:
            print("⚠️  No GROQ_API_KEY found! Groq fallback disabled.")

        # Image generation config (GPT Image - higher quality)
        self.image_model = "gptimage"
        print(f"🎨 Image generation enabled (Pollinations: {self.image_model})")
        print(f"📎 File processing enabled")
        print(f"🧠 Analysis & Reasoning capabilities active")
    
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
        """Process uploaded files and extract data for analysis"""
        if not files:
            return ""
        
        processed_content = "\n\n📎 **Uploaded Files for Analysis:**\n\n"
        
        for file in files:
            filename = file.get("filename", "unknown")
            content_base64 = file.get("content", "")
            mime_type = file.get("mime_type", "unknown")
            
            print(f"   📄 Processing file: {filename} ({mime_type})")
            
            try:
                # Decode base64 content
                content_bytes = base64.b64decode(content_base64)
                
                # Try to decode as text
                content_text = content_bytes.decode('utf-8', errors='ignore')
                
                # Detect data file types
                if filename.endswith(('.csv', '.json', '.txt', '.log', '.data', '.tsv')):
                    # Data file for analysis
                    processed_content += f"### File: {filename} (Data file)\n```\n{content_text}\n```\n\n"
                    print(f"      ✅ Extracted {len(content_text)} characters of data")
                
                elif filename.endswith(('.xlsx', '.xls')):
                    # Excel file (would need pandas to read properly)
                    processed_content += f"### File: {filename}\n*Excel file detected - {len(content_bytes)} bytes*\n" \
                                       f"*Note: Full Excel analysis requires additional libraries*\n\n"
                    print(f"      ⚠️ Excel file detected - basic info only")
                
                elif filename.endswith(('.pdf')):
                    # PDF (would need PDF parser)
                    processed_content += f"### File: {filename}\n*PDF file detected - {len(content_bytes)} bytes*\n" \
                                       f"*Note: Full PDF analysis requires additional libraries*\n\n"
                    print(f"      ⚠️ PDF detected - basic info only")
                
                else:
                    # Try as text
                    if len(content_text) > 0 and len(content_text) < 50000:
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
        """Execute task - routes to analysis or image generation"""
        
        # Process uploaded files with proper parsing
        file_content = ""
        if files:
            print(f"\n📎 Received {len(files)} file(s) - parsing for analysis...")
            file_content = process_uploaded_files(files)  # Use the new parser!
        
        if self.is_image_task(prompt):
            return await self.generate_image(prompt)
        else:
            # Add file content for analysis
            full_prompt = prompt
            if file_content:
                full_prompt = f"{prompt}\n\n{file_content}"
            
            return await self.execute_analysis_task(full_prompt)
    
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
    
    async def execute_analysis_task(self, prompt: str):
        """Execute analysis/reasoning task using Groq"""
        print(f"\n{'='*60}")
        print(f"🧠 ANALYSIS TASK RECEIVED")
        print(f"{'='*60}")
        print(f"Prompt: {prompt[:200]}...")
        start_time = time.time()
        try:
            if self.api_provider == "openrouter":
                try:
                    response = self.openrouter_client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {
                                "role": "system",
                                "content": """You are an expert analyst specializing in logical reasoning and structured analysis.

CRITICAL RULES:
- Answer the user's question DIRECTLY without meta-commentary
- DO NOT say \"You have asked...\" or \"In the context of...\"
- DO NOT explain what the user wanted or provide an \"Overview\" of their question
- Just provide the actual analysis they're looking for

⚠️ IMPORTANT LIMITATIONS:
- I CANNOT access live data, real-time information, or the internet
- I CANNOT get current sports scores, match statistics, or recent events
- I CANNOT browse websites or access external APIs
- My knowledge is from training data (cutoff: mid-2023)
- If asked about recent events, CLEARLY state: \"I cannot access real-time data. My knowledge is limited to information from mid-2023 and earlier.\"

When analyzing:
- Break down complex problems into clear, manageable parts
- Use structured formatting with clear sections and headings
- Provide pros and cons when comparing options
- Include data-driven insights and evidence-based reasoning
- Give concrete recommendations with clear justification
- Highlight risks and considerations when relevant

When working with uploaded files:
- Analyze the content systematically
- Identify patterns, trends, and key information
Present findings in a clear, structured format

Be thorough but concise. Focus on actionable insights and clear reasoning."""
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    max_tokens=2500,
                    temperature=0.3
                )
                    result = response.choices[0].message.content
                except Exception as e:
                    # If OpenRouter returns a 402 error, fallback to Groq if available
                    if (hasattr(e, 'status_code') and e.status_code == 402) or 'Insufficient credits' in str(e):
                        print("⚠️  OpenRouter credits error, falling back to Groq if available.")
                        if hasattr(self, 'client'):
                            response = self.client.chat.completions.create(
                                model="llama-3.3-70b-versatile",
                                messages=[
                                    {
                                        "role": "system",
                                        "content": """You are an expert analyst specializing in logical reasoning and structured analysis.

CRITICAL RULES:
- Answer the user's question DIRECTLY without meta-commentary
- DO NOT say \"You have asked...\" or \"In the context of...\"
- DO NOT explain what the user wanted or provide an \"Overview\" of their question
- Just provide the actual analysis they're looking for

⚠️ IMPORTANT LIMITATIONS:
- I CANNOT access live data, real-time information, or the internet
- I CANNOT get current sports scores, match statistics, or recent events
- I CANNOT browse websites or access external APIs
- My knowledge is from training data (cutoff: mid-2023)
- If asked about recent events, CLEARLY state: \"I cannot access real-time data. My knowledge is limited to information from mid-2023 and earlier.\"

When analyzing:
- Break down complex problems into clear, manageable parts
- Use structured formatting with clear sections and headings
- Provide pros and cons when comparing options
- Include data-driven insights and evidence-based reasoning
- Give concrete recommendations with clear justification
- Highlight risks and considerations when relevant

When working with uploaded files:
- Analyze the content systematically
- Identify patterns, trends, and key information
Present findings in a clear, structured format

Be thorough but concise. Focus on actionable insights and clear reasoning."""
                                    },
                                    {
                                        "role": "user",
                                        "content": prompt
                                    }
                                ],
                                max_tokens=2500,
                                temperature=0.3
                            )
                            result = response.choices[0].message.content
                        else:
                            raise e
                    else:
                        raise e
            elif self.api_provider == "groq":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": """You are an expert analyst specializing in logical reasoning and structured analysis.

CRITICAL RULES:
- Answer the user's question DIRECTLY without meta-commentary
- DO NOT say \"You have asked...\" or \"In the context of...\"
- DO NOT explain what the user wanted or provide an \"Overview\" of their question
- Just provide the actual analysis they're looking for

⚠️ IMPORTANT LIMITATIONS:
- I CANNOT access live data, real-time information, or the internet
- I CANNOT get current sports scores, match statistics, or recent events
- I CANNOT browse websites or access external APIs
- My knowledge is from training data (cutoff: mid-2023)
- If asked about recent events, CLEARLY state: \"I cannot access real-time data. My knowledge is limited to information from mid-2023 and earlier.\"

When analyzing:
- Break down complex problems into clear, manageable parts
- Use structured formatting with clear sections and headings
- Provide pros and cons when comparing options
- Include data-driven insights and evidence-based reasoning
- Give concrete recommendations with clear justification
- Highlight risks and considerations when relevant

When working with uploaded files:
- Analyze the content systematically
- Identify patterns, trends, and key information
Present findings in a clear, structured format

Be thorough but concise. Focus on actionable insights and clear reasoning."""
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    max_tokens=2500,
                    temperature=0.3
                )
                result = response.choices[0].message.content
            else:
                raise Exception("No valid API provider initialized.")

            execution_time = time.time() - start_time
            print(f"✅ Analysis completed in {execution_time:.2f}s")
            print(f"Response length: {len(result)} characters\n")
            return {
                "result": result,
                "success": True,
                "execution_time": execution_time,
                "task_type": "analysis"
            }
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"❌ Analysis task failed: {e}\n")
            return {
                "result": f"Error: {str(e)}",
                "success": False,
                "execution_time": execution_time,
                "task_type": "analysis"
            }


if __name__ == "__main__":
    worker = AnalysisWorker()
    worker.start()