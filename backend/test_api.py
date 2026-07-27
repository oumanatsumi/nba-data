"""Test API startup and routes"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

from app.main import app

print("=== API Routes ===")
for route in app.routes:
    if hasattr(route, 'path') and hasattr(route, 'methods'):
        methods = ', '.join(sorted(route.methods - {'HEAD', 'OPTIONS'}))
        if methods:
            print(f"  {methods:10s} {route.path}")

print("\n=== Testing DB connection ===")
from app.core.database import sync_engine
with sync_engine.connect() as conn:
    result = conn.execute(__import__('sqlalchemy').text("SELECT COUNT(*) FROM players")).scalar()
    print(f"  Players in DB: {result:,}")

print("\n✅ API ready to start!")
print("Run: E:\\Env\\Miniconda\\envs\\nba-data\\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
print("Docs: http://localhost:8000/docs")
