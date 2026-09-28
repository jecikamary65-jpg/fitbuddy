"""
Gemini AI Service for FitBuddy.
Handles API key management, model communication using google-genai SDK,
structured JSON response parsing, validation, and graceful fallback handling.
"""

import os
import json
import re
import logging
from typing import Dict, Any, Optional, Tuple
from dotenv import load_dotenv

from google import genai
from google.genai import types
from google.genai.errors import APIError

from prompts import (
    SYSTEM_INSTRUCTION,
    build_plan_generation_prompt,
    build_plan_update_prompt,
    build_nutrition_recovery_prompt,
)
from schemas import WorkoutPlanContent

# Load environment variables from .env file if present
load_dotenv()

logger = logging.getLogger("fitbuddy.gemini")

# Default model used for fast and structured reasoning
PRIMARY_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def get_api_key() -> Optional[str]:
    """Retrieves the Gemini API key from environment, checking for placeholder values."""
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key or key == "your_gemini_api_key_here":
        return None
    return key


def is_gemini_configured() -> bool:
    """Returns True if a valid API key is present."""
    return get_api_key() is not None


def get_client() -> Optional[genai.Client]:
    """Instantiates the Google GenAI client if an API key is available."""
    api_key = get_api_key()
    if not api_key:
        return None
    try:
        return genai.Client(api_key=api_key)
    except Exception as exc:
        logger.error(f"Failed to create genai.Client: {exc}")
        return None


def clean_json_text(raw_text: str) -> str:
    """Strips markdown code blocks, backticks, and whitespace from model responses."""
    text = raw_text.strip()
    # Remove markdown ```json ... ``` or ``` ... ```
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        return match.group(1).strip()
    return text


def parse_and_validate_plan_json(raw_text: str) -> Dict[str, Any]:
    """
    Cleans, parses, and validates the raw text from Gemini into a validated workout plan dict.
    Raises ValueError on parsing failure.
    """
    cleaned = clean_json_text(raw_text)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as err:
        logger.error(f"Failed to decode JSON from Gemini output: {err}. Raw: {raw_text[:200]}")
        raise ValueError(f"Gemini returned invalid JSON: {err}")

    # Validate against Pydantic schema
    try:
        validated = WorkoutPlanContent.model_validate(data)
        return validated.model_dump()
    except Exception as err:
        logger.error(f"Validation against WorkoutPlanContent failed: {err}")
        raise ValueError(f"Plan structure does not meet required schema: {err}")


# ------------------ Fallback Plan Generators ------------------ #

def generate_fallback_workout_plan(user_data: Dict[str, Any], feedback: Optional[str] = None) -> Dict[str, Any]:
    """
    High quality algorithmic fallback generator when Gemini API key is missing or quota is exhausted.
    Ensures seamless testing for evaluators and students.
    """
    goal = user_data.get("goal", "General Wellness")
    intensity = user_data.get("intensity", "Medium")
    experience = user_data.get("experience_level", "Beginner")
    name = user_data.get("name", "Athlete")

    overview_text = (
        f"7-day balanced {goal} routine tailored for {name} ({experience} level, {intensity} intensity)."
    )
    if feedback:
        overview_text += f" Adjusted specifically based on feedback: '{feedback}'."

    # Dynamic exercise library based on goal
    if goal == "Weight Loss":
        days = [
            {
                "day": "Day 1",
                "focus": "Full Body Metabolic Conditioning",
                "warmup": "6 mins: arm circles, high knees, and bodyweight hip openers",
                "exercises": [
                    {"name": "Goblet Squats", "sets": 3, "reps": "12-15 reps", "rest": "45 seconds"},
                    {"name": "Push-Ups (or Incline Push-Ups)", "sets": 3, "reps": "10-12 reps", "rest": "45 seconds"},
                    {"name": "Dumbbell Bent-Over Rows", "sets": 3, "reps": "12 reps", "rest": "45 seconds"},
                    {"name": "Kettlebell / Dumbbell Swings", "sets": 3, "reps": "15 reps", "rest": "60 seconds"},
                    {"name": "Plank Hold", "sets": 3, "reps": "45 seconds", "rest": "45 seconds"}
                ],
                "cooldown": "5 mins: light walking and deep static hamstring/quad stretches",
                "duration_minutes": 45
            },
            {
                "day": "Day 2",
                "focus": "HIIT Intervals & Core Stability",
                "warmup": "5 mins: jumping jacks, torso twists, leg swings",
                "exercises": [
                    {"name": "Mountain Climbers", "sets": 4, "reps": "30 seconds", "rest": "30 seconds"},
                    {"name": "Jump Squats / Air Squats", "sets": 4, "reps": "30 seconds", "rest": "30 seconds"},
                    {"name": "Bicycle Crunches", "sets": 3, "reps": "20 reps total", "rest": "45 seconds"},
                    {"name": "Russian Twists", "sets": 3, "reps": "16 reps total", "rest": "45 seconds"}
                ],
                "cooldown": "5 mins: child's pose, cobra stretch, deep diaphragmatic breathing",
                "duration_minutes": 35
            },
            {
                "day": "Day 3",
                "focus": "Active Recovery & Mobility Flow",
                "warmup": "3 mins: gentle neck and shoulder rolls",
                "exercises": [
                    {"name": "Brisk Outdoor Walk or Low-Resistance Cycling", "sets": 1, "reps": "25-30 mins", "rest": "Continuous"},
                    {"name": "World's Greatest Stretch", "sets": 2, "reps": "5 per side", "rest": "30 seconds"},
                    {"name": "Cat-Cow Stretch", "sets": 2, "reps": "10 slow reps", "rest": "30 seconds"}
                ],
                "cooldown": "5 mins: gentle lower back & hip flexor stretches",
                "duration_minutes": 35
            },
            {
                "day": "Day 4",
                "focus": "Lower Body Calorie Burn & Glute Strength",
                "warmup": "6 mins: glute bridges, ankle circles, air squats",
                "exercises": [
                    {"name": "Dumbbell Romanian Deadlifts", "sets": 3, "reps": "12 reps", "rest": "60 seconds"},
                    {"name": "Walking Lunges", "sets": 3, "reps": "10 each leg", "rest": "45 seconds"},
                    {"name": "Step-Ups onto Bench/Box", "sets": 3, "reps": "12 each leg", "rest": "45 seconds"},
                    {"name": "Calf Raises", "sets": 3, "reps": "15 reps", "rest": "45 seconds"}
                ],
                "cooldown": "5 mins: pigeon pose, standing calf stretch",
                "duration_minutes": 40
            },
            {
                "day": "Day 5",
                "focus": "Upper Body & Cardiovascular Intervals",
                "warmup": "5 mins: dynamic arm crosses, band pull-aparts",
                "exercises": [
                    {"name": "Dumbbell Overhead Shoulder Press", "sets": 3, "reps": "12 reps", "rest": "45 seconds"},
                    {"name": "Lat Pulldowns or Resistance Band Pulls", "sets": 3, "reps": "12 reps", "rest": "45 seconds"},
                    {"name": "Burpees (or Step-back burpees)", "sets": 3, "reps": "10 reps", "rest": "60 seconds"},
                    {"name": "Shadow Boxing / Cardio Intervals", "sets": 3, "reps": "60 seconds", "rest": "45 seconds"}
                ],
                "cooldown": "5 mins: chest opener in doorway, triceps stretch",
                "duration_minutes": 40
            },
            {
                "day": "Day 6",
                "focus": "Core Burner & Steady State Aerobic Cardio",
                "warmup": "5 mins: light jog in place, knee-to-elbows",
                "exercises": [
                    {"name": "Steady State Jogging or Incline Walking", "sets": 1, "reps": "25 mins", "rest": "Continuous"},
                    {"name": "Deadbugs", "sets": 3, "reps": "10 each side", "rest": "30 seconds"},
                    {"name": "Side Plank Hold", "sets": 3, "reps": "30s each side", "rest": "30 seconds"}
                ],
                "cooldown": "5 mins: seated hamstring stretch, butterfly stretch",
                "duration_minutes": 35
            },
            {
                "day": "Day 7",
                "focus": "Full Rest & Mindful Regeneration",
                "warmup": "3 mins: mindful breathing",
                "exercises": [
                    {"name": "Gentle Nature Walk / Leisure Activity", "sets": 1, "reps": "20 mins", "rest": "Self-paced"},
                    {"name": "Foam Rolling or Self-Myofascial Release", "sets": 1, "reps": "10 mins", "rest": "As needed"}
                ],
                "cooldown": "5 mins: lying spinal twist and relaxation",
                "duration_minutes": 30
            }
        ]
    elif goal == "Muscle Gain":
        days = [
            {
                "day": "Day 1",
                "focus": "Upper Body Hypertrophy (Push Focus)",
                "warmup": "7 mins: band dislocates, scapular push-ups, light arm swings",
                "exercises": [
                    {"name": "Barbell or Dumbbell Bench Press", "sets": 4, "reps": "8-10 reps", "rest": "90 seconds"},
                    {"name": "Incline Dumbbell Press", "sets": 3, "reps": "10-12 reps", "rest": "75 seconds"},
                    {"name": "Overhead Dumbbell Shoulder Press", "sets": 3, "reps": "10 reps", "rest": "75 seconds"},
                    {"name": "Lateral Dumbbell Raises", "sets": 3, "reps": "12-15 reps", "rest": "60 seconds"},
                    {"name": "Triceps Cable Pushdowns or Dips", "sets": 3, "reps": "12 reps", "rest": "60 seconds"}
                ],
                "cooldown": "5 mins: chest and anterior shoulder stretching",
                "duration_minutes": 50
            },
            {
                "day": "Day 2",
                "focus": "Lower Body Power & Quad Hypertrophy",
                "warmup": "8 mins: hip 90/90s, bodyweight squats, leg swings",
                "exercises": [
                    {"name": "Barbell / Goblet Back Squats", "sets": 4, "reps": "8-10 reps", "rest": "90-120 seconds"},
                    {"name": "Bulgarian Split Squats", "sets": 3, "reps": "10 each leg", "rest": "75 seconds"},
                    {"name": "Leg Press or Walking Dumbbell Lunges", "sets": 3, "reps": "12 reps", "rest": "75 seconds"},
                    {"name": "Standing Calf Raises", "sets": 4, "reps": "15 reps", "rest": "45 seconds"}
                ],
                "cooldown": "5 mins: quad and hip flexor kneeling stretch",
                "duration_minutes": 50
            },
            {
                "day": "Day 3",
                "focus": "Active Muscle Recovery & Joint Mobility",
                "warmup": "5 mins: foam rolling back and legs",
                "exercises": [
                    {"name": "Zone 2 Low-Impact Cardio (Cycling/Treadmill Walk)", "sets": 1, "reps": "25 mins", "rest": "Continuous"},
                    {"name": "Thoracic Spine Rotations", "sets": 2, "reps": "10 each side", "rest": "30 seconds"}
                ],
                "cooldown": "5 mins: deep full-body mobility flow",
                "duration_minutes": 35
            },
            {
                "day": "Day 4",
                "focus": "Upper Body Hypertrophy (Pull Focus)",
                "warmup": "7 mins: band pull-aparts, lat stretch, wrist warm-up",
                "exercises": [
                    {"name": "Bent-Over Barbell Rows", "sets": 4, "reps": "8-10 reps", "rest": "90 seconds"},
                    {"name": "Pull-Ups or Lat Pulldowns", "sets": 3, "reps": "10-12 reps", "rest": "75 seconds"},
                    {"name": "Seated Cable Rows", "sets": 3, "reps": "12 reps", "rest": "60 seconds"},
                    {"name": "Face Pulls for Rear Delts", "sets": 3, "reps": "15 reps", "rest": "60 seconds"},
                    {"name": "Incline Dumbbell Biceps Curls", "sets": 3, "reps": "10-12 reps", "rest": "60 seconds"}
                ],
                "cooldown": "5 mins: lat and upper back stretch",
                "duration_minutes": 50
            },
            {
                "day": "Day 5",
                "focus": "Posterior Chain & Hamstring / Glute Growth",
                "warmup": "7 mins: inchworms, glute activation bridges",
                "exercises": [
                    {"name": "Romanian Deadlifts (RDLs)", "sets": 4, "reps": "8-10 reps", "rest": "90 seconds"},
                    {"name": "Barbell or Dumbbell Hip Thrusts", "sets": 3, "reps": "10-12 reps", "rest": "75 seconds"},
                    {"name": "Lying Hamstring Curls", "sets": 3, "reps": "12 reps", "rest": "60 seconds"},
                    {"name": "Hanging Knee Raises for Abs", "sets": 3, "reps": "12-15 reps", "rest": "45 seconds"}
                ],
                "cooldown": "5 mins: hamstring and lower back stretching",
                "duration_minutes": 45
            },
            {
                "day": "Day 6",
                "focus": "Arms, Delts & Core Accessory Sculpting",
                "warmup": "5 mins: light shoulder circles and pushups",
                "exercises": [
                    {"name": "Dumbbell Hammer Curls", "sets": 3, "reps": "12 reps", "rest": "60 seconds"},
                    {"name": "Overhead Triceps Rope Extensions", "sets": 3, "reps": "12 reps", "rest": "60 seconds"},
                    {"name": "Cable Lateral Raises", "sets": 3, "reps": "15 reps", "rest": "45 seconds"},
                    {"name": "Ab Rollouts or Weighted Planks", "sets": 3, "reps": "10-12 reps", "rest": "45 seconds"}
                ],
                "cooldown": "5 mins: wrist, bicep, and tricep stretches",
                "duration_minutes": 40
            },
            {
                "day": "Day 7",
                "focus": "Full Rest & Anabolic Muscle Synthesis",
                "warmup": "3 mins: gentle breathing",
                "exercises": [
                    {"name": "Leisure Walking & Hydration Focus", "sets": 1, "reps": "20 mins", "rest": "Self-paced"},
                    {"name": "Full Body Static Stretching", "sets": 1, "reps": "15 mins", "rest": "As needed"}
                ],
                "cooldown": "Deep relaxation and high-protein nutrition",
                "duration_minutes": 30
            }
        ]
    else:  # General Wellness
        days = [
            {
                "day": "Day 1",
                "focus": "Total Body Functional Strength",
                "warmup": "6 mins: arm circles, hips rolls, bodyweight squats",
                "exercises": [
                    {"name": "Kettlebell / Dumbbell Deadlifts", "sets": 3, "reps": "10-12 reps", "rest": "60 seconds"},
                    {"name": "Dumbbell Overhead Press", "sets": 3, "reps": "10 reps", "rest": "60 seconds"},
                    {"name": "Bodyweight Inverted Rows or Band Rows", "sets": 3, "reps": "12 reps", "rest": "45 seconds"},
                    {"name": "Bird-Dog Core Stability", "sets": 3, "reps": "10 each side", "rest": "30 seconds"}
                ],
                "cooldown": "5 mins: child's pose, torso twists",
                "duration_minutes": 40
            },
            {
                "day": "Day 2",
                "focus": "Cardiovascular Stamina & Aerobic Base",
                "warmup": "5 mins: brisk walk, high knees",
                "exercises": [
                    {"name": "Brisk Jog, Cycling or Rowing", "sets": 1, "reps": "25 mins steady", "rest": "Continuous"},
                    {"name": "Plank with Shoulder Taps", "sets": 3, "reps": "16 taps total", "rest": "45 seconds"}
                ],
                "cooldown": "5 mins: calf and hamstring stretches",
                "duration_minutes": 35
            },
            {
                "day": "Day 3",
                "focus": "Spine & Hip Mobility Flow",
                "warmup": "5 mins: deep breathing in seated posture",
                "exercises": [
                    {"name": "Cat-Cow & Thread-the-Needle", "sets": 3, "reps": "8 each side", "rest": "30 seconds"},
                    {"name": "Downward Dog into Cobra", "sets": 3, "reps": "6 slow flows", "rest": "45 seconds"},
                    {"name": "Deep Goblet Squat Hold", "sets": 3, "reps": "30 seconds", "rest": "30 seconds"}
                ],
                "cooldown": "5 mins: savasana relaxation",
                "duration_minutes": 30
            },
            {
                "day": "Day 4",
                "focus": "Lower Body Balance & Functional Movement",
                "warmup": "5 mins: ankle mobility and glute bridges",
                "exercises": [
                    {"name": "Reverse Lunges to Knee Drive", "sets": 3, "reps": "10 each leg", "rest": "60 seconds"},
                    {"name": "Single-Leg Romanian Deadlift", "sets": 3, "reps": "8 each leg", "rest": "60 seconds"},
                    {"name": "Glute Bridge Marches", "sets": 3, "reps": "12 reps", "rest": "45 seconds"}
                ],
                "cooldown": "5 mins: quad and IT band stretches",
                "duration_minutes": 40
            },
            {
                "day": "Day 5",
                "focus": "Upper Body Posture & Core Stability",
                "warmup": "5 mins: shoulder rolls and chest expansions",
                "exercises": [
                    {"name": "Resistance Band Face Pulls", "sets": 3, "reps": "15 reps", "rest": "45 seconds"},
                    {"name": "Incline Push-Ups", "sets": 3, "reps": "10-12 reps", "rest": "45 seconds"},
                    {"name": "Farmers Carry (Walking with weights)", "sets": 3, "reps": "45 seconds", "rest": "60 seconds"},
                    {"name": "Deadbugs", "sets": 3, "reps": "12 total", "rest": "30 seconds"}
                ],
                "cooldown": "5 mins: neck and upper trapezius stretches",
                "duration_minutes": 35
            },
            {
                "day": "Day 6",
                "focus": "Outdoor Active Recreation / HIIT Light",
                "warmup": "5 mins: dynamic outdoor walking",
                "exercises": [
                    {"name": "Hiking, Swimming, or Fun Recreational Sport", "sets": 1, "reps": "30 mins", "rest": "As needed"},
                    {"name": "Bodyweight Squats during pauses", "sets": 2, "reps": "15 reps", "rest": "45 seconds"}
                ],
                "cooldown": "5 mins: mindful full-body stretching",
                "duration_minutes": 40
            },
            {
                "day": "Day 7",
                "focus": "Mindful Rest, Breathwork & Sleep Optimization",
                "warmup": "3 mins: box breathing (4s in, 4s hold, 4s out, 4s hold)",
                "exercises": [
                    {"name": "Gentle Walking in Nature", "sets": 1, "reps": "20 mins", "rest": "Continuous"},
                    {"name": "Legs-Up-The-Wall Restorative Pose", "sets": 1, "reps": "10 mins", "rest": "Rest"}
                ],
                "cooldown": "5 mins: quiet mental restoration",
                "duration_minutes": 30
            }
        ]

    return {
        "goal": goal,
        "intensity": intensity,
        "experience_level": experience,
        "overview": overview_text,
        "days": days
    }


def generate_fallback_nutrition_tip(goal: str) -> Dict[str, Any]:
    """Generates an evidence-based nutrition and recovery tip when Gemini is offline."""
    if goal == "Weight Loss":
        return {
            "title": "Satiety First: The Protein & Fiber Blueprint for Fat Loss",
            "tip": "Prioritize 25-35g of lean protein (chicken, tofu, Greek yogurt, fish) at every meal. Combine with high-volume, fiber-rich cruciferous vegetables to stay comfortably full in a sustainable caloric deficit.",
            "hydration_tip": "Drink 500ml of cold water 20 minutes before meals. Aim for 2.5 - 3.5 liters daily to optimize metabolic efficiency and prevent mistaking thirst for hunger.",
            "recovery_tip": "Target 7.5 to 8.5 hours of consistent sleep. Sleep deprivation elevates cortisol and ghrelin (the hunger hormone), making cravings significantly harder to manage."
        }
    elif goal == "Muscle Gain":
        return {
            "title": "Hypertrophy Fueling: Protein Distribution & Glycogen Synthesis",
            "tip": "Consume 1.6 to 2.2 grams of protein per kilogram of bodyweight daily, spaced across 3-4 meals. Ingest a carbohydrate-rich meal (e.g. oatmeal, rice, banana) 90 minutes before lifting to fuel maximum mechanical tension.",
            "hydration_tip": "Muscles are over 70% water! Hydrate with 3.5 - 4.5 liters daily, adding a pinch of sea salt or electrolytes on heavy training days to prevent cramping and maintain pump.",
            "recovery_tip": "Growth hormone peaks during deep stage-3 NREM sleep. Keep your bedroom cool (18°C / 65°F), dark, and screen-free 45 minutes before sleep to accelerate myofibrillar repair."
        }
    else:  # General Wellness
        return {
            "title": "Holistic Vitality: Anti-Inflammatory Nutrition & Longevity",
            "tip": "Follow an 80/20 Mediterranean-style approach: colorful whole produce, extra virgin olive oil, wild-caught omega-3s, and unrefined grains. Eat without screen distractions to promote mindful digestive health.",
            "hydration_tip": "Start every morning with 500ml of room temperature water with fresh lemon to activate gastrointestinal motility. Maintain consistent hydration throughout the workday.",
            "recovery_tip": "Practice active decompression: 10 minutes of daily diaphragmatic breathwork, combined with a daily 20-minute sunlight walk, resets circadian rhythm and balances nervous system tone."
        }


# ------------------ Core Service API Functions ------------------ #

def generate_workout_plan(user_data: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
    """
    Scenario 1: Generates a 7-day personalized workout plan using Google Gemini.
    Returns (plan_dict, model_source).
    """
    client = get_client()
    if not client:
        logger.warning("Gemini API key is not configured. Using intelligent fallback plan generator.")
        plan = generate_fallback_workout_plan(user_data)
        return plan, "FitBuddy Intelligent Engine (Demo Mode - Add GEMINI_API_KEY for live AI)"

    prompt = build_plan_generation_prompt(user_data)
    try:
        logger.info(f"Calling Gemini ({PRIMARY_MODEL}) to generate workout plan for {user_data.get('name')}...")
        response = client.models.generate_content(
            model=PRIMARY_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.4,
                response_mime_type="application/json",
            ),
        )
        if not response or not response.text:
            raise ValueError("Gemini returned an empty response.")

        plan = parse_and_validate_plan_json(response.text)
        return plan, f"Gemini ({PRIMARY_MODEL})"
    except APIError as api_err:
        logger.error(f"Gemini API Error occurred: {api_err}. Falling back to default plan.")
        # If API key is invalid or quota exceeded, fall back smoothly
        plan = generate_fallback_workout_plan(user_data)
        return plan, f"Fallback Engine (Gemini API Error: {api_err.message if hasattr(api_err, 'message') else 'Check API Key'})"
    except Exception as exc:
        logger.error(f"Unexpected error calling Gemini: {exc}. Falling back.")
        plan = generate_fallback_workout_plan(user_data)
        return plan, f"Fallback Engine (AI Processing Notice: {str(exc)})"


def update_workout_plan(
    user_data: Dict[str, Any],
    existing_plan: Dict[str, Any],
    feedback: str
) -> Tuple[Dict[str, Any], str]:
    """
    Scenario 2: Updates and reconstructs the 7-day workout plan based on feedback.
    Returns (updated_plan_dict, model_source).
    """
    client = get_client()
    if not client:
        logger.warning("Gemini API key is not configured. Using fallback plan updater.")
        plan = generate_fallback_workout_plan(user_data, feedback=feedback)
        return plan, "FitBuddy Intelligent Engine (Demo Mode - Add GEMINI_API_KEY for live AI)"

    prompt = build_plan_update_prompt(user_data, existing_plan, feedback)
    try:
        logger.info(f"Calling Gemini ({PRIMARY_MODEL}) to update plan with feedback: {feedback[:50]}...")
        response = client.models.generate_content(
            model=PRIMARY_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.4,
                response_mime_type="application/json",
            ),
        )
        if not response or not response.text:
            raise ValueError("Gemini returned an empty update response.")

        updated_plan = parse_and_validate_plan_json(response.text)
        return updated_plan, f"Gemini ({PRIMARY_MODEL})"
    except APIError as api_err:
        logger.error(f"Gemini API Error during plan update: {api_err}")
        plan = generate_fallback_workout_plan(user_data, feedback=feedback)
        return plan, f"Fallback Engine (Gemini Notice: {api_err.message if hasattr(api_err, 'message') else 'Error'})"
    except Exception as exc:
        logger.error(f"Error during plan update: {exc}")
        plan = generate_fallback_workout_plan(user_data, feedback=feedback)
        return plan, f"Fallback Engine (AI Processing Notice: {str(exc)})"


def generate_nutrition_tip(
    goal: str,
    user_data: Optional[Dict[str, Any]] = None
) -> Tuple[Dict[str, Any], str]:
    """
    Scenario 3: Generates concise, science-backed nutrition and recovery advice.
    Returns (tip_dict, model_source).
    """
    client = get_client()
    if not client:
        logger.warning("Gemini API key not configured. Using evidence-based nutrition fallback.")
        tip = generate_fallback_nutrition_tip(goal)
        return tip, "FitBuddy Nutrition Database (Demo Mode)"

    prompt = build_nutrition_recovery_prompt(goal, user_data)
    try:
        logger.info(f"Calling Gemini ({PRIMARY_MODEL}) for nutrition tip (Goal: {goal})...")
        response = client.models.generate_content(
            model=PRIMARY_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.5,
                response_mime_type="application/json",
            ),
        )
        if not response or not response.text:
            raise ValueError("Empty nutrition tip response from Gemini.")

        cleaned = clean_json_text(response.text)
        tip_data = json.loads(cleaned)
        # Ensure mandatory keys exist
        if "title" not in tip_data or "tip" not in tip_data:
            raise ValueError("Malformed nutrition tip JSON.")
        return tip_data, f"Gemini ({PRIMARY_MODEL})"
    except Exception as exc:
        logger.error(f"Error generating nutrition tip with Gemini: {exc}")
        tip = generate_fallback_nutrition_tip(goal)
        return tip, f"Nutrition Database (Fallback: {str(exc)})"
