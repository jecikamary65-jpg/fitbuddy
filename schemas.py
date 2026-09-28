"""
Pydantic schemas for request validation and response serialization.
"""

from typing import List, Optional, Any, Union
from pydantic import BaseModel, Field, field_validator
from models import GoalEnum, IntensityEnum, ExperienceEnum


class Exercise(BaseModel):
    name: str = Field(..., description="Exercise name, e.g., 'Goblet Squats'")
    sets: Union[int, str] = Field(..., description="Number of sets, e.g., 3 or '3'")
    reps: str = Field(..., description="Target repetitions or interval duration, e.g., '10-12 reps' or '45s'")
    rest: str = Field(..., description="Rest interval between sets, e.g., '60 seconds'")


class WorkoutDay(BaseModel):
    day: str = Field(..., description="Day label, e.g., 'Day 1' or 'Day 1 - Monday'")
    focus: str = Field(..., description="Muscle group or workout focus, e.g., 'Lower Body Hypertrophy' or 'Active Recovery'")
    warmup: str = Field(..., description="Dynamic warmup routine instructions, e.g., '5 min leg swings, bodyweight squats'")
    exercises: List[Exercise] = Field(default_factory=list, description="List of planned exercises")
    cooldown: str = Field(..., description="Cool-down and mobility instructions, e.g., '5 min hamstring & quad stretches'")
    duration_minutes: int = Field(..., ge=10, le=180, description="Estimated total workout duration in minutes")


class WorkoutPlanContent(BaseModel):
    goal: str = Field(..., description="Primary fitness goal")
    intensity: str = Field(..., description="Workout intensity level")
    experience_level: Optional[str] = Field(None, description="User's training experience level")
    overview: Optional[str] = Field(None, description="Short summary and strategy for the 7-day split")
    days: List[WorkoutDay] = Field(..., description="7 daily workout breakdowns")

    @field_validator("days")
    @classmethod
    def validate_days_count(cls, v):
        if len(v) < 1:
            raise ValueError("Workout plan must contain at least 1 day of scheduled activities.")
        return v


# ------------------ Request Schemas ------------------ #

class PlanGenerateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="User's name")
    age: int = Field(..., ge=14, le=100, description="User's age (14 to 100)")
    weight: float = Field(..., ge=30.0, le=300.0, description="User's weight in kilograms (30kg to 300kg)")
    goal: GoalEnum = Field(..., description="Target fitness goal")
    intensity: IntensityEnum = Field(..., description="Desired workout intensity")
    experience_level: ExperienceEnum = Field(..., description="Current training experience level")
    preferences: Optional[str] = Field(
        None,
        max_length=500,
        description="Optional preferences like 'Home workout only', 'No jumping', 'Have dumbbells'",
    )


class PlanUpdateRequest(BaseModel):
    user_id: int = Field(..., ge=1, description="ID of the user requesting the plan modification")
    feedback: str = Field(
        ...,
        min_length=3,
        max_length=1000,
        description="User feedback, e.g., 'Add more cardio', 'I have only 30 minutes per day', 'More rest days'",
    )


class NutritionTipRequest(BaseModel):
    user_id: Optional[int] = Field(None, description="Optional user ID for personalized context")
    goal: GoalEnum = Field(..., description="Fitness goal for the tip")


# ------------------ Response Schemas ------------------ #

class PlanResponse(BaseModel):
    status: str = "success"
    plan_id: int
    user_id: int
    user_name: str
    is_updated: bool = False
    feedback: Optional[str] = None
    plan: WorkoutPlanContent
    created_at: str
    updated_at: str
    model_source: str = "Gemini AI"


class NutritionTipResponse(BaseModel):
    status: str = "success"
    id: int
    user_id: Optional[int] = None
    goal: str
    title: str
    tip: str
    hydration_tip: Optional[str] = None
    recovery_tip: Optional[str] = None
    model_source: str = "Gemini AI"


class ErrorResponse(BaseModel):
    status: str = "error"
    message: str
    details: Optional[Any] = None
