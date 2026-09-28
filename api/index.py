"""
Vercel Serverless Function entrypoint for FitBuddy FastAPI application.
Exposes the ASGI app instance for Vercel's Python runtime.
"""

import sys
import os
import traceback

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

for p in [PROJECT_ROOT, CURRENT_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from app import app
except Exception as err:
    tb = traceback.format_exc()
    print(f"FATAL: Error importing app in api/index.py:\n{tb}", file=sys.stderr)
    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse

    app = FastAPI()

    @app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE"])
    async def vercel_diagnostic(full_path: str):
        return HTMLResponse(
            f"<html><body style='font-family:sans-serif;padding:2rem;background:#090d16;color:#f8fafc;'>"
            f"<h2 style='color:#ef4444;'>FitBuddy Serverless Startup Diagnostic</h2>"
            f"<p>An exception occurred while loading modules on Vercel:</p>"
            f"<pre style='background:#1e293b;padding:1rem;border-radius:8px;color:#38bdf8;overflow:auto;'>{tb}</pre>"
            f"</body></html>",
            status_code=500,
        )
