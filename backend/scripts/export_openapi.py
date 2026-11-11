"""Write the API's OpenAPI schema to a file (used to generate the frontend's TypeScript types).

Usage (from the repository root):
    python backend/scripts/export_openapi.py frontend/openapi.json
"""
import json
import os
import sys
import tempfile

# Importing the app needs a database URL; schema generation never touches it.
os.environ.setdefault("DATABASE_URL", f"sqlite:///{tempfile.gettempdir()}/acedra-openapi.db")
os.environ.setdefault("AUTO_CREATE_SCHEMA", "false")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app

target = sys.argv[1] if len(sys.argv) > 1 else "openapi.json"
with open(target, "w", encoding="utf-8") as fh:
    json.dump(app.openapi(), fh, indent=1, sort_keys=True)
print(f"OpenAPI schema written to {target}")
