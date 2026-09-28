"""
Domain models and Enums for FitBuddy.
"""

from enum import Enum
from typing import Optional
from dataclasses import dataclass
from datetime import datetime


class GoalEnum(str, Enum):
    WEIGHT_LOSS = "Weight Loss"
    MUSCLE_GAIN = "Muscle Gain"
    GENERAL_WELLNESS = "General Wellness"


class IntensityEnum(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class ExperienceEnum(str, Enum):
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"


@dataclass
class User:
    id: Optional[int]
    name: str
    age: int
    weight: float
    goal: str
    intensity: str
    experience_level: str
    preferences: Optional[str] = None
    created_at: Optional[datetime] = None


@dataclass
class WorkoutPlanRecord:
    id: Optional[int]
    user_id: int
    plan_data: str
    feedback: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class NutritionTipRecord:
    id: Optional[int]
    user_id: Optional[int]
    goal: str
    tip: str
    created_at: Optional[datetime] = None
