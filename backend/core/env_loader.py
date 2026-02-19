from pathlib import Path
from dotenv import load_dotenv

# go to project root (backend folder)
ROOT_DIR = Path(__file__).resolve().parent.parent

env_path = ROOT_DIR / ".env"

load_dotenv(env_path)
