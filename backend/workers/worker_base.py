"""
E.V.E. Worker Base - NEW VERSION with Hardware Monitoring & Auto-Registration
- Auto-registers in AI_Agents table
- Sends hardware metrics in heartbeat
- Supports file processing
"""

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
import os
import time
import requests
import psutil
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, List, Dict
from threading import Thread


load_dotenv()

class BaseWorker:
    def __init__(self, worker_id, specialization, port):
        self.worker_id = worker_id
        self.specialization = specialization
        self.port = port
        self.master_host = os.getenv("MASTER_HOST", "localhost")
        self.master_port = os.getenv("MASTER_PORT", "8000")
        self.master_url = f"http://{self.master_host}:{self.master_port}"
        self.is_running = False
        self.agent_id = None  # Will be set after registration
        
        # Create FastAPI app
        self.app = FastAPI(title=f"E.V.E. Worker - {worker_id}")
        
        # Register routes
        self.register_routes()
    
    def get_hardware_stats(self) -> Dict:
        """Get current hardware statistics using psutil"""
        try:
            # CPU usage (percentage)
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Memory usage (percentage)
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Temperature (if available)
            temperature = 0.0
            try:
                temps = psutil.sensors_temperatures()
                if temps:
                    # Get first available temperature sensor
                    for name, entries in temps.items():
                        if entries:
                            temperature = entries[0].current
                            break
            except:
                temperature = 0.0
            
            return {
                "cpu": round(cpu_percent, 2),
                "memory": round(memory_percent, 2),
                "temperature": round(temperature, 2)
            }
        except Exception as e:
            print(f"⚠️  Hardware stats error: {e}")
            return {"cpu": 0.0, "memory": 0.0, "temperature": 0.0}
    
    def register_routes(self):
        """Register FastAPI routes with FILE SUPPORT"""
        
        class TaskRequest(BaseModel):
            prompt: str
            timestamp: Optional[str] = None
            files: Optional[List[Dict]] = None  # File support
        
        @self.app.post("/execute")
        async def execute_endpoint(request: TaskRequest):
            # Pass files to execute_task if they exist
            if hasattr(self, 'execute_task'):
                import inspect
                sig = inspect.signature(self.execute_task)
                if 'files' in sig.parameters:
                    return await self.execute_task(request.prompt, files=request.files)
                else:
                    return await self.execute_task(request.prompt)
            else:
                return {"result": "execute_task not implemented", "success": False}
        
        @self.app.get("/health")
        async def health_endpoint():
            return await self.health_check()
    
    def register_with_master(self, max_retries=5, initial_delay=2):
        """Register this worker with master with retry logic - STORES IN AI_AGENTS TABLE"""
        print(f"🔌 Registering {self.worker_id} with master...")
        print(f"   Master: {self.master_url}")
        print(f"   Specialization: {self.specialization}")
        
        for attempt in range(1, max_retries + 1):
            try:
                # Use localhost since master and workers are on same machine
                my_host = "localhost"
                
                # Get hardware stats for registration
                hw_stats = self.get_hardware_stats()
                
                response = requests.post(
                    f"{self.master_url}/register_agent",  # NEW: Uses AI_Agents registry
                    json={
                        "agent_name": self.worker_id,
                        "capability": self.specialization,
                        "host": my_host,
                        "port": self.port,
                        "hardware_stats": hw_stats
                    },
                    timeout=30  # Increased from 10s to 30s
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.agent_id = data.get('agent_id')
                    print(f"✅ Registered successfully! Agent ID: {self.agent_id}")
                    print(f"   CPU: {hw_stats['cpu']}% | RAM: {hw_stats['memory']}% | Temp: {hw_stats['temperature']}°C")
                    return True
                else:
                    print(f"⚠️ Registration attempt {attempt}/{max_retries} failed: HTTP {response.status_code}")
                    
            except requests.exceptions.Timeout:
                print(f"⚠️ Registration attempt {attempt}/{max_retries} timed out")
            except Exception as e:
                print(f"⚠️ Registration attempt {attempt}/{max_retries} failed: {e}")
            
            # Wait before retry with exponential backoff
            if attempt < max_retries:
                delay = initial_delay * (2 ** (attempt - 1))  # 2, 4, 8, 16 seconds
                print(f"   Retrying in {delay} seconds...")
                time.sleep(delay)
        
        print(f"❌ Failed to register after {max_retries} attempts")
        return False
    
    def send_heartbeat(self):
        """Send heartbeat with hardware metrics every 3 seconds"""
        while self.is_running:
            try:
                hw_stats = self.get_hardware_stats()
                
                response = requests.post(
                    f"{self.master_url}/agent_heartbeat",  # NEW: Updated endpoint
                    json={
                        "agent_name": self.worker_id,
                        "status": "idle",  # Workers report their own status
                        "hardware_stats": hw_stats
                    },
                    timeout=30  # Increased from 15s to 30s
                )
                
                if response.status_code == 200:
                    print(f"💓 Heartbeat | CPU: {hw_stats['cpu']}% | RAM: {hw_stats['memory']}% | Temp: {hw_stats['temperature']}°C")
                else:
                    print(f"⚠️  Heartbeat warning: {response.status_code}")
                    
            except Exception as e:
                print(f"⚠️  Heartbeat failed: {e}")
            
            time.sleep(3)
    
    async def execute_task(self, prompt: str, files: list = None):
        """
        This method should be overridden by specific workers
        Supports FILES!
        """
        raise NotImplementedError("Subclass must implement execute_task")
    
    async def health_check(self):
        """Health check endpoint with hardware stats"""
        hw_stats = self.get_hardware_stats()
        return {
            "status": "healthy",
            "worker_id": self.worker_id,
            "agent_id": self.agent_id,
            "specialization": self.specialization,
            "file_support": True,
            "hardware": hw_stats
        }
    
    def start(self):
        """Start the worker"""
        import uvicorn
        
        print(f"\n{'='*60}")
        print(f"🤖 Starting {self.worker_id}")
        print(f"{'='*60}")
        print(f"Specialization: {self.specialization}")
        print(f"Port: {self.port}")
        print(f"Master: {self.master_url}")
        print(f"File Support: ✅ Enabled")
        print(f"Hardware Monitor: ✅ Enabled (CPU, RAM, Temp)")
        print(f"{'='*60}\n")
        
        # Register with master (stores in AI_Agents table)
        if not self.register_with_master():
            print("❌ Failed to register. Exiting...")
            return
        
        # Start heartbeat thread with hardware monitoring
        self.is_running = True
        heartbeat_thread = Thread(target=self.send_heartbeat, daemon=True)
        heartbeat_thread.start()
        
        print(f"\n✅ {self.worker_id} is now running!")
        print(f"📡 Listening on port {self.port}")
        print(f"💓 Sending heartbeats with hardware stats")
        print(f"📎 Ready to receive files!\n")
        
        # Start FastAPI server
        uvicorn.run(
            self.app,
            host="0.0.0.0",
            port=self.port,
            log_level="info"
        )
