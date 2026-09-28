"""
Prompt engineering templates and builders for FitBuddy Gemini integration.
Enforces strict JSON schema generation, safe fitness protocols, and tailored personalization.
"""

from typing import Dict, Any, Optional

SYSTEM_INSTRUCTION = """You are FitBuddy, an elite certified fitness trainer, strength & conditioning coach, and sports nutrition specialist.
Your mission is to generate highly effective, personalized, evidence-based 7-day workout plans and practical recovery advice.

Core Principles:
1. Safety First: Always program adequate warm-ups, proper cool-downs, and sensible volume. If a user is a Beginner, focus on fundamental movement patterns with safe progression.
2. Personalization: Strictly tailor the exercise selection, volume, and split to the user's age, weight, fitness goal, workout intensity, experience level, and individual preferences.
3. Realistic & Practical: For rest days, program 'Active Recovery & Mobility' with gentle stretching or walking rather than leaving days blank.
4. Medical Safety Boundary: Do NOT prescribe medical treatments, diagnose injuries, or provide therapeutic medical advice. Keep advice educational, positive, and lifestyle-oriented.
5. Strict JSON Output: You MUST respond ONLY with a single valid JSON object adhering precisely to the specified schema. Do not include markdown codeblocks or conversational commentary outside the JSON.
"""


def build_plan_generation_prompt(user_data: Dict[str, Any]) -> str:
    """
    Builds the structured prompt for Scenario 1: Generating a 7-day workout plan.
    """
    name = user_data.get("name", "Athlete")
    age = user_data.get("age", 25)
    weight = user_data.get("weight", 70)
    goal = user_data.get("goal", "General Wellness")
    intensity = user_data.get("intensity", "Medium")
    experience = user_data.get("experience_level", "Beginner")
    preferences = user_data.get("preferences") or "Standard gym or home equipment, balanced exercises"

    prompt = f"""Generate a personalized 7-Day Workout Plan for {name} with the following profile:
- Name: {name}
- Age: {age} years old
- Weight: {weight} kg
- Primary Fitness Goal: {goal}
- Target Workout Intensity: {intensity}
- Experience Level: {experience}
- Special Preferences / Equipment / Notes: {preferences}

Guidelines for this specific profile:
- Fitness Goal '{goal}': 
  * If Weight Loss: Focus on metabolic conditioning, compound movements, HIIT/LISS cardio intervals, and high-energy full body or upper/lower splits.
  * If Muscle Gain: Focus on hypertrophy principles, progressive overload, structured push/pull/legs or upper/lower splits, optimal set/rep ranges (8-12 reps), and adequate rest.
  * If General Wellness: Deliver a well-rounded balance of functional strength, cardiovascular fitness, core stability, and joint mobility.
- Intensity '{intensity}' & Experience '{experience}':
  * Low / Beginner: Safe exercise variations, higher reps/lower load, 30-40 min sessions, 2-3 recovery days.
  * Medium / Intermediate: Moderate to high volume, 40-50 min sessions, 1-2 active recovery days.
  * High / Advanced: Challenging supersets, heavy compounds, athletic conditioning, 50-60 min sessions.
- Always include for every day:
  1. day: e.g. "Day 1", "Day 2", ... "Day 7"
  2. focus: e.g. "Push (Chest, Shoulders & Triceps)", "Lower Body & Core", "Active Recovery & Mobility"
  3. warmup: 5-8 minute dynamic mobility routine
  4. exercises: list of 4-6 exercises with 'name', 'sets' (number), 'reps' (e.g. '10-12 reps' or '45 secs'), 'rest' (e.g. '60 seconds')
  5. cooldown: 5 minute static stretching / breathing
  6. duration_minutes: integer representing total minutes

Return ONLY valid JSON matching this exact structure:
{{
  "goal": "{goal}",
  "intensity": "{intensity}",
  "experience_level": "{experience}",
  "overview": "A concise 2-sentence encouraging summary of the 7-day split strategy.",
  "days": [
    {{
      "day": "Day 1",
      "focus": "Full Body Functional Strength",
      "warmup": "5 mins of arm circles, leg swings, and bodyweight squats",
      "exercises": [
        {{
          "name": "Goblet Squats",
          "sets": 3,
          "reps": "12 reps",
          "rest": "60 seconds"
        }}
      ],
      "cooldown": "5 mins hamstring and quad stretches",
      "duration_minutes": 45
    }}
  ]
}}
"""
    return prompt


def build_plan_update_prompt(user_data: Dict[str, Any], existing_plan: Dict[str, Any], feedback: str) -> str:
    """
    Builds the structured prompt for Scenario 2: Updating an existing plan using user feedback.
    """
    name = user_data.get("name", "Athlete")
    goal = user_data.get("goal", "General Wellness")
    intensity = user_data.get("intensity", "Medium")
    experience = user_data.get("experience_level", "Beginner")
    preferences = user_data.get("preferences", "None")

    prompt = f"""You are modifying an existing 7-Day Workout Plan for {name} based on their direct feedback.

USER PROFILE:
- Name: {name}
- Age: {user_data.get('age', 25)}
- Weight: {user_data.get('weight', 70)} kg
- Goal: {goal}
- Intensity: {intensity}
- Experience: {experience}
- Original Preferences: {preferences}

USER'S FEEDBACK / REQUESTED CHANGE:
\"{feedback}\"

CURRENT PLAN SUMMARY:
{existing_plan.get('overview', 'Existing 7-day split')}

CRITICAL INSTRUCTIONS:
- DO NOT just append this feedback to the old plan.
- Re-architect the 7-day schedule intelligently to solve their request:
  * If they ask for "more cardio": replace or augment strength days with HIIT, metabolic circuits, or dedicated cardio sessions.
  * If they ask for "more rest days" or "too tired": convert 1 or 2 high-intensity days into Active Recovery & Mobility or full Rest.
  * If they ask for "less time" (e.g. 30 minutes): streamline exercises, use supersets, and adjust duration_minutes to match their time limit.
  * If they ask to "focus more on legs" or "focus on core": increase volume for that target muscle group while maintaining balanced weekly recovery.
  * If they report joint pain or injury constraint: substitute high-impact exercises with low-impact joint-friendly alternatives.
- Keep the user's primary goal ({goal}) in mind.

Respond ONLY with valid JSON following the exact same schema:
{{
  "goal": "{goal}",
  "intensity": "{intensity}",
  "experience_level": "{experience}",
  "overview": "Explanation of how the plan was adjusted to honor the user's feedback: '{feedback}'.",
  "days": [
    {{
      "day": "Day 1",
      "focus": "...",
      "warmup": "...",
      "exercises": [
        {{
          "name": "...",
          "sets": 3,
          "reps": "...",
          "rest": "..."
        }}
      ],
      "cooldown": "...",
      "duration_minutes": 45
    }}
  ]
}}
"""
    return prompt


def build_nutrition_recovery_prompt(goal: str, user_data: Optional[Dict[str, Any]] = None) -> str:
    """
    Builds the prompt for Scenario 3: Nutrition & Recovery Tip based on goal.
    """
    user_context = ""
    if user_data:
        user_context = f"Athlete Context: Age {user_data.get('age')}, Weight {user_data.get('weight')} kg, Intensity: {user_data.get('intensity')}."

    prompt = f"""Provide a highly actionable, evidence-based Nutrition and Recovery guide tailored specifically for the fitness goal: '{goal}'.
{user_context}

Goal-specific guidance criteria:
- Weight Loss: Sustainable calorie deficit management, high satiety foods (fiber, lean protein), hydration timing, and managing sleep for hunger hormones.
- Muscle Gain: Optimal protein distribution (1.6-2.2g/kg), pre/post-workout carbohydrate timing, creatine/hydration support, and muscle repair sleep architecture.
- General Wellness: Mediterranean-style nutrient density, anti-inflammatory whole foods, consistent daily hydration, stress reduction, and restorative sleep hygiene.

Safety Constraint:
- DO NOT prescribe medication or medical disease treatments.
- Focus on practical, daily athletic lifestyle habits.

Return ONLY a valid JSON object with this exact structure:
{{
  "title": "Inspiring catchy headline for {goal} nutrition/recovery",
  "tip": "2-3 clear, practical bullet points or concise sentences detailing actionable nutritional advice.",
  "hydration_tip": "Specific daily water/electrolyte hydration guideline.",
  "recovery_tip": "Targeted recovery practice (e.g. sleep duration, active mobility, contrast showers, or deload technique)."
}}
"""
    return prompt
