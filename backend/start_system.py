"""
Start E.V.E. System — Master (port 8001) + All Workers
Run: python start_system.py
"""

import subprocess
import time
import sys
import os
import socket
import requests
from pathlib import Path
from dotenv import load_dotenv

# ─────────────────────────────────────────────────────────────
# ALWAYS LOAD ROOT .env (single source of truth)
# ─────────────────────────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parent
ENV_PATH = ROOT_DIR / ".env"

load_dotenv(ENV_PATH)

# ensure all subprocesses inherit the same env
ENV = os.environ.copy()

# ─────────────────────────────────────────────────────────────
# move working directory to backend root
# ─────────────────────────────────────────────────────────────
os.chdir(ROOT_DIR)

print("=" * 70)
print("🚀 STARTING E.V.E. SYSTEM")
print("=" * 70)

# ─────────────────────────────────────────────────────────────
# read master config FROM ROOT ENV
# ─────────────────────────────────────────────────────────────
master_host = os.getenv("MASTER_HOST", "localhost")
master_port = int(os.getenv("MASTER_PORT", 8001))

print(f"\n📡 Master will bind to: http://{master_host}:{master_port}")

# ─────────────────────────────────────────────────────────────
# check port availability
# ─────────────────────────────────────────────────────────────
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    if s.connect_ex(("localhost", master_port)) == 0:
        print(f"\n⚠️  Port {master_port} already in use")
        print(f"Check: http://localhost:{master_port}/health")
        sys.exit(0)

# ─────────────────────────────────────────────────────────────
# windows console fix
# ─────────────────────────────────────────────────────────────
kwargs = {}
if sys.platform == "win32":
    kwargs["creationflags"] = subprocess.CREATE_NEW_CONSOLE


# ─────────────────────────────────────────────────────────────
# START MASTER
# ─────────────────────────────────────────────────────────────
print("\n1️⃣ Starting Master Controller...")

master_script = ROOT_DIR / "master_controller" / "master_controller.py"

if not master_script.exists():
    print(f"❌ Missing: {master_script}")
    sys.exit(1)

master_process = subprocess.Popen(
    [sys.executable, str(master_script)],
    cwd=str(master_script.parent),
    env=ENV,
    **kwargs,
)

print(f"   Master PID: {master_process.pid}")


# ─────────────────────────────────────────────────────────────
# wait for health
# ─────────────────────────────────────────────────────────────
def wait_for_master(host, port, timeout=60):

    url = f"http://{host}:{port}/health"
    start = time.time()

    print(f"   Polling: {url}")

    while time.time() - start < timeout:
        try:
            r = requests.get(url, timeout=2)
            if r.status_code == 200:
                if r.json().get("status") == "ok":
                    print(f"\n   ✅ Master healthy ({int(time.time()-start)}s)")
                    return True
        except:
            pass

        print(f"   Waiting... {int(time.time()-start)}s", end="\r")
        time.sleep(2)

    print("\n❌ Master failed to start")
    return False


if not wait_for_master(master_host, master_port):
    master_process.terminate()
    sys.exit(1)

time.sleep(3)


# ─────────────────────────────────────────────────────────────
# START WORKERS
# ─────────────────────────────────────────────────────────────
print("\n2️⃣ Starting Workers...")

workers = [
    ("Coding Worker", "workers/coding_worker.py"),
    ("Documentation Worker", "workers/doc_worker.py"),
    ("Analysis Worker", "workers/analysis_worker.py"),
]

worker_processes = []

for name, rel in workers:

    script = ROOT_DIR / rel

    if not script.exists():
        print(f"⚠️ Missing worker: {script}")
        continue

    print(f"   Starting {name}...")

    p = subprocess.Popen(
        [sys.executable, str(script)],
        cwd=str(ROOT_DIR),
        env=ENV,
        **kwargs,
    )

    worker_processes.append(p)
    time.sleep(4)


# ─────────────────────────────────────────────────────────────
# FINAL STATUS
# ─────────────────────────────────────────────────────────────
time.sleep(5)

print("\n" + "=" * 70)
print("✅ E.V.E. SYSTEM RUNNING")
print("=" * 70)

print(f"\nMaster : http://localhost:{master_port}")
print(f"Health : http://localhost:{master_port}/health")
print(f"Workers: http://localhost:{master_port}/list_workers")

print("\nBackend : http://localhost:8000")
print("Frontend: http://localhost:5173")

print("\nPress Ctrl+C to stop")

# ─────────────────────────────────────────────────────────────
# shutdown
# ─────────────────────────────────────────────────────────────
try:
    master_process.wait()

except KeyboardInterrupt:

    print("\n🛑 Stopping services...")

    master_process.terminate()

    for p in worker_processes:
        p.terminate()

    print("✅ Stopped")
