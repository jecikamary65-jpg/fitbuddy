"""
FitBuddy – AI Fitness Plan Generator
FastAPI Backend Application.
Provides REST API endpoints and Jinja2 frontend rendering.
"""

import os
import json
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from database import (
    init_db,
    create_user,
    get_user_by_id,
    save_workout_plan,
    update_workout_plan as db_update_workout_plan,
    get_latest_plan_by_user,
    save_nutrition_tip,
    get_recent_tips_by_user,
    get_db_connection,
)
from schemas import (
    PlanGenerateRequest,
    PlanUpdateRequest,
    NutritionTipRequest,
    PlanResponse,
    NutritionTipResponse,
    ErrorResponse,
)
import gemini_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("fitbuddy.app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes the database on startup and performs clean shutdown."""
    logger.info("Starting FitBuddy Application...")
    try:
        init_db()
    except Exception as exc:
        logger.warning(f"Startup database initialization notice: {exc}")
    yield
    logger.info("Shutting down FitBuddy Application.")


app = FastAPI(
    title="FitBuddy – AI Fitness Plan Generator",
    description="Intelligent 7-day personalized workout plan & nutrition assistant powered by Google Gemini Models and SQLite.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Vercel Serverless Path Normalization Middleware
from starlette.middleware.base import BaseHTTPMiddleware

class VercelPathMiddleware(BaseHTTPMiddleware):
    """
    Normalizes ASGI request paths when Vercel serverless rewrites route requests
    to /api/index.py while passing the original client path in x-invoke-path header.
    """
    async def dispatch(self, request: Request, call_next):
        # 1. Read original path passed by Vercel edge router
        invoke_path = request.headers.get("x-invoke-path")
        if invoke_path:
            clean = invoke_path.split("?")[0]
            if clean:
                request.scope["path"] = clean
                return await call_next(request)

        # 2. Check x-matched-path if invoke-path is absent
        matched_path = request.headers.get("x-matched-path")
        if matched_path and not matched_path.startswith("/api/index"):
            clean = matched_path.split("?")[0]
            if clean:
                request.scope["path"] = clean
                return await call_next(request)

        # 3. Fallback: strip /api/index prefixes from path
        path = request.scope.get("path", "")
        for prefix in ["/api/index.py", "/api/index"]:
            if path.startswith(prefix):
                new_path = path[len(prefix):] or "/"
                request.scope["path"] = new_path
                break
        else:
            if path in ["/api", "/api/"]:
                request.scope["path"] = "/"

        return await call_next(request)


app.add_middleware(VercelPathMiddleware)


# Static files and Templates resolution for local and Vercel serverless runtimes
def locate_directory(name: str) -> str:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(current_dir, name),
        os.path.join(current_dir, "api", name),
        os.path.join(os.getcwd(), name),
        os.path.join(os.getcwd(), "api", name),
        os.path.join("/var/task", name),
        os.path.join("/var/task", "api", name),
    ]
    for p in candidates:
        if os.path.exists(p) and os.path.isdir(p):
            return p
    fallback = os.path.join(current_dir, name)
    os.makedirs(fallback, exist_ok=True)
    return fallback


static_dir = locate_directory("static")
templates_dir = locate_directory("templates")

app.mount("/static", StaticFiles(directory=static_dir), name="static")
try:
    app.mount("/api/static", StaticFiles(directory=static_dir), name="api_static")
except Exception:
    pass

templates = Jinja2Templates(directory=templates_dir)


# ------------------ Exception Handlers ------------------ #

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Formats Pydantic validation errors into clean, friendly error messages."""
    error_messages = []
    for err in exc.errors():
        field = " -> ".join([str(loc) for loc in err.get("loc", []) if loc != "body"])
        msg = err.get("msg", "Invalid value")
        error_messages.append(f"{field}: {msg}" if field else msg)

    friendly_text = " | ".join(error_messages)
    logger.warning(f"Validation failure on {request.url.path}: {friendly_text}")
    return JSONResponse(
        status_code=422,
        content={"status": "error", "message": f"Input validation failed: {friendly_text}", "details": exc.errors()},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Returns structured JSON for HTTPExceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "message": exc.detail},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catches unhandled errors gracefully without revealing sensitive internals."""
    logger.exception(f"Unhandled server error at {request.url.path}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"status": "error", "message": f"An unexpected error occurred: {str(exc)}"},
    )


# ------------------ Frontend Route ------------------ #

@app.get("/", response_class=HTMLResponse)
@app.get("/api", response_class=HTMLResponse)
@app.get("/api/index", response_class=HTMLResponse)
@app.get("/api/index.py", response_class=HTMLResponse)
async def index_page(request: Request):
    """Renders the main FitBuddy web interface."""
    gemini_ready = gemini_service.is_gemini_configured()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "gemini_ready": gemini_ready,
            "title": "FitBuddy – AI Fitness Plan Generator"
        }
    )


# ------------------ API Endpoints ------------------ #

@app.get("/api/status")
async def system_status():
    """Returns application health, database connectivity, and Gemini AI status."""
    is_gemini = gemini_service.is_gemini_configured()
    db_ok = False
    stats = {}
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM workout_plans")
            plan_count = cursor.fetchone()[0]
            stats = {"total_users": user_count, "total_plans": plan_count}
            db_ok = True
    except Exception as exc:
        logger.error(f"Status check DB error: {exc}")

    return {
        "status": "healthy" if db_ok else "degraded",
        "gemini_api_configured": is_gemini,
        "active_model": gemini_service.PRIMARY_MODEL if is_gemini else "Fallback Engine (Set GEMINI_API_KEY for live AI)",
        "database_connected": db_ok,
        "stats": stats,
    }


@app.post("/generate-plan", response_model=PlanResponse)
@app.post("/api/generate-plan", response_model=PlanResponse)
async def generate_plan(payload: PlanGenerateRequest):
    """
    Scenario 1:
    1. Validates input
    2. Saves user profile in SQLite
    3. Calls Gemini AI service to synthesize 7-day personalized workout plan
    4. Persists the generated plan in SQLite
    5. Returns the structured plan for UI rendering
    """
    logger.info(f"Generating plan for user: {payload.name}, Goal: {payload.goal.value}, Intensity: {payload.intensity.value}")

    # Step 1: Save User to SQLite
    try:
        user_id = create_user(
            name=payload.name,
            age=payload.age,
            weight=payload.weight,
            goal=payload.goal.value,
            intensity=payload.intensity.value,
            experience_level=payload.experience_level.value,
            preferences=payload.preferences,
        )
    except Exception as db_err:
        logger.error(f"Failed to save user in database: {db_err}")
        raise HTTPException(status_code=500, detail="Database failure while saving user profile.")

    # Step 2: Call Gemini AI Service
    user_dict = {
        "id": user_id,
        "name": payload.name,
        "age": payload.age,
        "weight": payload.weight,
        "goal": payload.goal.value,
        "intensity": payload.intensity.value,
        "experience_level": payload.experience_level.value,
        "preferences": payload.preferences,
    }

    try:
        plan_content, model_source = gemini_service.generate_workout_plan(user_dict)
    except Exception as gen_err:
        logger.error(f"Plan generation failed: {gen_err}")
        raise HTTPException(status_code=500, detail=f"Failed to generate workout plan: {str(gen_err)}")

    # Step 3: Save generated plan to SQLite
    try:
        plan_id = save_workout_plan(user_id=user_id, plan_data=plan_content, feedback=None)
    except Exception as db_err:
        logger.error(f"Failed to save workout plan: {db_err}")
        raise HTTPException(status_code=500, detail="Database failure while persisting workout plan.")

    # Step 4: Fetch freshly saved record details
    saved_plan = get_latest_plan_by_user(user_id)
    created_at = saved_plan.get("created_at", "") if saved_plan else ""
    updated_at = saved_plan.get("updated_at", "") if saved_plan else ""

    return PlanResponse(
        status="success",
        plan_id=plan_id,
        user_id=user_id,
        user_name=payload.name,
        is_updated=False,
        feedback=None,
        plan=plan_content,
        created_at=str(created_at),
        updated_at=str(updated_at),
        model_source=model_source,
    )


@app.post("/update-plan", response_model=PlanResponse)
@app.post("/api/update-plan", response_model=PlanResponse)
async def update_plan(payload: PlanUpdateRequest):
    """
    Scenario 2:
    1. Validates user_id and feedback
    2. Retrieves existing user profile and active workout plan from SQLite
    3. Prompts Gemini to intelligently re-architect the 7-day plan incorporating the feedback
    4. Persists the updated plan into SQLite
    5. Returns the updated plan
    """
    logger.info(f"Updating plan for user_id={payload.user_id} with feedback: '{payload.feedback}'")

    # Step 1: Retrieve user profile
    user = get_user_by_id(payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User with ID {payload.user_id} was not found.")

    # Step 2: Retrieve existing plan
    existing_plan_record = get_latest_plan_by_user(payload.user_id)
    if not existing_plan_record:
        raise HTTPException(status_code=404, detail="No existing workout plan found for this user to update.")

    existing_plan_data = existing_plan_record.get("plan_data", {})

    # Step 3: Call Gemini AI Service to regenerate the plan with feedback
    try:
        updated_plan_content, model_source = gemini_service.update_workout_plan(
            user_data=user,
            existing_plan=existing_plan_data,
            feedback=payload.feedback,
        )
    except Exception as err:
        logger.error(f"Plan update regeneration failed: {err}")
        raise HTTPException(status_code=500, detail=f"Failed to update workout plan: {str(err)}")

    # Step 4: Save or update plan in SQLite
    plan_id = existing_plan_record.get("id")
    try:
        db_update_workout_plan(plan_id=plan_id, plan_data=updated_plan_content, feedback=payload.feedback)
    except Exception as db_err:
        logger.error(f"Failed to persist updated plan: {db_err}")
        raise HTTPException(status_code=500, detail="Database failure while updating workout plan.")

    # Step 5: Fetch fresh record
    refreshed_record = get_latest_plan_by_user(payload.user_id)

    return PlanResponse(
        status="success",
        plan_id=plan_id,
        user_id=payload.user_id,
        user_name=user.get("name", "Athlete"),
        is_updated=True,
        feedback=payload.feedback,
        plan=updated_plan_content,
        created_at=str(refreshed_record.get("created_at", "")),
        updated_at=str(refreshed_record.get("updated_at", "")),
        model_source=model_source,
    )


@app.get("/plan/{user_id}", response_model=PlanResponse)
@app.get("/api/plan/{user_id}", response_model=PlanResponse)
async def get_user_plan(user_id: int):
    """Retrieves the latest 7-day workout plan for the given user ID."""
    plan_record = get_latest_plan_by_user(user_id)
    if not plan_record:
        raise HTTPException(status_code=404, detail=f"No workout plan found for user ID {user_id}")

    return PlanResponse(
        status="success",
        plan_id=plan_record["id"],
        user_id=user_id,
        user_name=plan_record.get("user_name", "Athlete"),
        is_updated=bool(plan_record.get("feedback")),
        feedback=plan_record.get("feedback"),
        plan=plan_record["plan_data"],
        created_at=str(plan_record.get("created_at", "")),
        updated_at=str(plan_record.get("updated_at", "")),
        model_source="FitBuddy Saved Record",
    )


@app.post("/nutrition-tip", response_model=NutritionTipResponse)
@app.post("/api/nutrition-tip", response_model=NutritionTipResponse)
async def get_nutrition_tip(payload: NutritionTipRequest):
    """
    Scenario 3:
    Generates a personalized, practical nutrition and recovery guide based on the user's fitness goal.
    Saves the tip in SQLite and returns the response.
    """
    logger.info(f"Generating nutrition tip for goal: {payload.goal.value}")

    user_data = None
    if payload.user_id:
        user_data = get_user_by_id(payload.user_id)

    try:
        tip_dict, model_source = gemini_service.generate_nutrition_tip(
            goal=payload.goal.value,
            user_data=user_data,
        )
    except Exception as err:
        logger.error(f"Nutrition tip generation failed: {err}")
        raise HTTPException(status_code=500, detail=f"Failed to generate nutrition tip: {str(err)}")

    # Save to SQLite
    tip_text = json.dumps(tip_dict, ensure_ascii=False)
    tip_id = save_nutrition_tip(user_id=payload.user_id, goal=payload.goal.value, tip=tip_text)

    return NutritionTipResponse(
        status="success",
        id=tip_id,
        user_id=payload.user_id,
        goal=payload.goal.value,
        title=tip_dict.get("title", f"Nutrition Guide for {payload.goal.value}"),
        tip=tip_dict.get("tip", ""),
        hydration_tip=tip_dict.get("hydration_tip"),
        recovery_tip=tip_dict.get("recovery_tip"),
        model_source=model_source,
    )


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app:app", host=host, port=port, reload=True)
