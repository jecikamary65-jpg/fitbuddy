# FitBuddy – AI Fitness Plan Generator 🏋️‍♂️

> **An intelligent, web-based AI fitness assistant that generates personalized 7-day workout splits and nutrition/recovery advice powered by Google Gemini Models, FastAPI, and SQLite.**

---

## 📖 Project Overview

**FitBuddy** is an end-to-end fitness application designed for lifters, runners, and wellness enthusiasts of all levels. Using Google's Gemini models and structured prompt engineering, FitBuddy analyzes an athlete's physical profile, fitness goals, workout intensity, and training constraints to deliver a comprehensive, actionable 7-day workout plan.

Unlike static fitness templates, FitBuddy features an **interactive feedback loop** where users can iteratively refine their routine (e.g., adding cardio, shortening sessions to 30 minutes, or reducing impact on sensitive joints) without losing their primary preferences.

---

## 🌟 Key Features

### 1. Scenario 1 – Personalized 7-Day Workout Split Generation
- **Athlete Profiling**: Collects name, age (validated 14–100), weight in kg (validated 30–300 kg), fitness goal, workout intensity, experience level, and optional custom constraints.
- **Dynamic 7-Day Architecture**: Automatically programs every day of the week with:
  - Daily workout focus (e.g. Upper Body Hypertrophy, Active Mobility & Core, Push Strength).
  - Dynamic warm-up routine with specific movements.
  - Exercise prescription with exact sets, reps/duration, and rest intervals.
  - Cool-down and post-workout mobility protocols.
  - Estimated session duration in minutes.
- **SQLite Persistence**: Automatically saves user profiles to the `users` table and generated plans to `workout_plans`.

### 2. Scenario 2 – Intelligent Plan Modification via Feedback
- **Conversational Refinement**: Users can supply freeform or chip-assisted feedback:
  - *"Add more cardio."*
  - *"I only have 30 minutes available."*
  - *"I have knee pain, please substitute high-impact movements."*
  - *"Add an extra rest day."*
- **Reconstruction Engine**: Rather than merely appending text, FitBuddy prompts Gemini to intelligently rebuild the 7-day schedule to fulfill the user's feedback while preserving their primary goal and preferences.
- **History & Versioning**: Updates the record in SQLite with a timestamp and user feedback log.

### 3. Scenario 3 – Targeted Nutrition & Recovery Advice
- **Goal-Aligned Guidance**:
  - **Weight Loss**: Sustainable calorie deficit, protein/fiber satiety, hydration timing, and sleep regulation for hunger hormones.
  - **Muscle Gain**: Daily protein distribution (1.6–2.2g/kg), carbohydrate timing, electrolyte hydration, and deep sleep architecture.
  - **General Wellness**: Anti-inflammatory nutrient density, hydration habits, stress mitigation, and restorative routines.
- **Safe & Practical**: Actionable daily athletic lifestyle habits without medical diagnoses or prescriptions.

### 4. Enterprise-Ready Architecture & Aesthetics
- **Modern Dark UI**: Glassmorphism cards, glowing status badges, responsive grid layout, micro-animations, and accessible typography using *Plus Jakarta Sans*.
- **Offline / Demo Mode**: Built-in intelligent algorithmic fallback generator so students, teachers, and reviewers can test all 3 scenarios and SQLite storage even before configuring a Gemini API key.
- **Utility Actions**: One-click **Copy to Clipboard**, **Print / Save as PDF** with dedicated print styles, and **Download JSON** export.

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Backend Framework** | [FastAPI](https://fastapi.tiangolo.com/) (Python 3.10+) |
| **ASGI Server** | [Uvicorn](https://www.uvicorn.org/) |
| **Generative AI** | [Google GenAI SDK](https://github.com/google-gemini/generative-ai-python) (`google-genai` / Gemini 2.5 Flash) |
| **Validation** | [Pydantic v2](https://docs.pydantic.dev/) |
| **Database** | [SQLite3](https://www.sqlite.org/) with WAL journaling & foreign keys |
| **Templating** | [Jinja2](https://palletsprojects.com/p/jinja/) |
| **Frontend** | Vanilla HTML5, Modern CSS3 (Variables, Flexbox/Grid, Glassmorphism), Vanilla JavaScript (ES6+ Fetch API) |
| **Icons & Typography** | FontAwesome 6, Google Fonts (*Plus Jakarta Sans*) |

---

## 🏛️ System Architecture

```text
               +---------------------------------------+
               |        Athlete / Web Browser          |
               |  (HTML5 / CSS3 / Vanilla JavaScript)  |
               +-------------------+-------------------+
                                   |
                   REST API Requests / Fetch Calls
                                   |
                                   v
               +---------------------------------------+
               |            FastAPI Backend            |
               | (Route Handlers, CORS, Static Files)  |
               +-------------------+-------------------+
                                   |
                 Pydantic Validation (schemas.py)
                                   |
                    +--------------+--------------+
                    |                             |
                    v                             v
     +------------------------------+  +--------------------------+
     |      Gemini AI Service       |  |     SQLite Database      |
     |      (gemini_service.py)     |  |      (database.py)       |
     |                              |  |                          |
     | - System Prompt Engineering  |  | - users                  |
     | - Structured JSON Output     |  | - workout_plans          |
     | - Fallback Algorithmic Engine|  | - nutrition_tips         |
     +--------------+---------------+  +--------------------------+
                    |
                    v
     +------------------------------+
     |   Google Gemini 2.5 Models   |
     |      (Google GenAI API)      |
     +------------------------------+
```

---

## 📁 Project Structure

```text
fitbuddy/
├── app.py                  # Main FastAPI application, routes & lifespan handler
├── database.py             # SQLite connection management & parameterized CRUD
├── models.py               # Domain models, dataclasses, and enum definitions
├── schemas.py              # Pydantic v2 validation models for requests and responses
├── gemini_service.py       # Google GenAI client, prompt execution & fallback engine
├── prompts.py              # System prompt & structured prompt templates for Scenarios 1-3
├── test_app.py             # Comprehensive test suite covering all scenarios & validation
├── requirements.txt        # Python dependency manifest
├── .env.example            # Environment variables template
├── .gitignore              # Git ignore rules for virtualenvs, keys, and SQLite DBs
├── README.md               # Complete project documentation
├── static/
│   ├── style.css           # Modern dark-mode stylesheet with responsive grid & print rules
│   └── script.js           # Client-side controller (Fetch API, DOM manipulation, toasts)
└── templates/
    └── index.html          # Semantic Jinja2 template with forms, cards, and modal
```

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.10+** (Tested on Python 3.12)
- **pip** package manager
- Free **Google Gemini API Key** (from [Google AI Studio](https://aistudio.google.com/))

---

### Step 1: Clone or Navigate to the Project

```bash
cd fitbuddy
```

---

### Step 2: Set Up Virtual Environment (Recommended)

#### On Windows (PowerShell):
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

#### On macOS / Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

---

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

---

### Step 4: Configure Environment Variables

Copy the `.env.example` file to create your `.env` file:

```bash
cp .env.example .env
```

Open `.env` in any text editor and paste your Gemini API key:

```ini
GEMINI_API_KEY=AIzaSyYourGeminiApiKeyHere
HOST=127.0.0.1
PORT=8000
```

> 💡 **Note on Demo Mode:** If you do not have a Gemini API key yet, you can still run the entire application! FitBuddy includes an intelligent fallback generator that builds structured 7-day splits and nutrition guides, allowing immediate evaluation of UI and database flows.

---

### Step 5: Run the Application

Start the FastAPI application using Uvicorn:

```bash
uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

---

### Step 6: Open in Your Browser

Open your browser and navigate to:
```
http://127.0.0.1:8000
```

Interactive Swagger API documentation is also available at:
```
http://127.0.0.1:8000/docs
```

---

## 🧪 Running Automated Tests

A complete automated unit and integration test suite is included in `test_app.py`. It tests:
1. `GET /` (Jinja2 HTML rendering)
2. `GET /api/status` (Health check & database connectivity)
3. `POST /generate-plan` (Scenario 1 generation & schema validation)
4. `POST /update-plan` (Scenario 2 feedback-based update)
5. `GET /plan/{user_id}` (Database retrieval)
6. `POST /nutrition-tip` (Scenario 3 nutrition & recovery generation)
7. Input boundary and validation error handling (HTTP 422)

Execute the test suite with:

```bash
python test_app.py
```

---

## 📡 REST API Documentation

### 1. `GET /api/status`
Returns application health, database connectivity, and Gemini AI state.

**Example Response:**
```json
{
  "status": "healthy",
  "gemini_api_configured": true,
  "active_model": "gemini-2.5-flash",
  "database_connected": true,
  "stats": {
    "total_users": 14,
    "total_plans": 14
  }
}
```

---

### 2. `POST /generate-plan` (Scenario 1)
Generates and persists a personalized 7-day workout plan.

**Request Body:**
```json
{
  "name": "Sarah Connor",
  "age": 29,
  "weight": 64.5,
  "goal": "Weight Loss",
  "intensity": "High",
  "experience_level": "Intermediate",
  "preferences": "Dumbbells and resistance bands, 45 min max"
}
```

**Response Body (Excerpt):**
```json
{
  "status": "success",
  "plan_id": 1,
  "user_id": 1,
  "user_name": "Sarah Connor",
  "is_updated": false,
  "feedback": null,
  "plan": {
    "goal": "Weight Loss",
    "intensity": "High",
    "experience_level": "Intermediate",
    "overview": "Metabolic conditioning and progressive resistance split.",
    "days": [
      {
        "day": "Day 1",
        "focus": "Full Body Metabolic Conditioning",
        "warmup": "6 mins dynamic hip openers, arm swings, high knees",
        "exercises": [
          {
            "name": "Goblet Squats",
            "sets": 3,
            "reps": "12-15 reps",
            "rest": "45 seconds"
          }
        ],
        "cooldown": "5 mins static stretching",
        "duration_minutes": 45
      }
    ]
  },
  "created_at": "2026-09-28 14:16:05",
  "updated_at": "2026-09-28 14:16:05",
  "model_source": "Gemini (gemini-2.5-flash)"
}
```

---

### 3. `POST /update-plan` (Scenario 2)
Reconstructs an existing plan incorporating user feedback.

**Request Body:**
```json
{
  "user_id": 1,
  "feedback": "I have knee pain, please substitute high-impact jumps with low-impact alternatives."
}
```

**Response Body:**
```json
{
  "status": "success",
  "plan_id": 1,
  "user_id": 1,
  "user_name": "Sarah Connor",
  "is_updated": true,
  "feedback": "I have knee pain, please substitute high-impact jumps with low-impact alternatives.",
  "plan": { ... },
  "model_source": "Gemini (gemini-2.5-flash)"
}
```

---

### 4. `POST /nutrition-tip` (Scenario 3)
Generates practical, goal-tailored nutrition and recovery recommendations.

**Request Body:**
```json
{
  "user_id": 1,
  "goal": "Weight Loss"
}
```

**Response Body:**
```json
{
  "status": "success",
  "id": 1,
  "user_id": 1,
  "goal": "Weight Loss",
  "title": "Satiety First: The Protein & Fiber Blueprint for Fat Loss",
  "tip": "Prioritize 25-35g of lean protein at every meal combined with high-volume, fiber-rich vegetables to stay comfortably full in a sustainable caloric deficit.",
  "hydration_tip": "Drink 500ml of cold water 20 minutes before meals. Aim for 2.5 - 3.5 liters daily.",
  "recovery_tip": "Target 7.5 to 8.5 hours of consistent sleep to optimize cortisol and ghrelin levels.",
  "model_source": "Gemini (gemini-2.5-flash)"
}
```

---

## 📱 Screenshots & UI Tour

| State | Preview |
|---|---|
| **Athlete Input Form** | Sleek dark card with live character count, intensity segmented pill control, and input validation |
| **7-Day Workout Split** | Responsive grid of daily workout cards featuring dynamic warm-ups, exercise badges (sets, reps, rest), and cool-downs |
| **Scenario 2 Feedback Loop** | Quick suggestion chips (`🏃 Add more cardio`, `⏱️ 30-min time cap`, `🛌 Extra rest day`) + textarea |
| **Scenario 3 Nutrition Card** | 3-column breakdown of Diet Strategy, Hydration Target, and Sleep/Recovery protocols |
| **Print / PDF Output** | Dedicated clean black-and-white print styles for exporting workout splits to physical paper or PDF |

---

## 🛢️ SQLite Database Schema

FitBuddy uses clean abstraction in `database.py`. No raw SQL is written inside route handlers.

```sql
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    age INTEGER NOT NULL,
    weight REAL NOT NULL,
    goal TEXT NOT NULL,
    intensity TEXT NOT NULL,
    experience_level TEXT NOT NULL,
    preferences TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS workout_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    plan_data TEXT NOT NULL,
    feedback TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS nutrition_tips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    goal TEXT NOT NULL,
    tip TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);
```

---

## 🌐 Deployment Guidance

### ⚡ Deploying on Vercel (Frontend & Backend Together)

FitBuddy is pre-configured for **Vercel** serverless deployment with:
- [`api/index.py`](api/index.py): Vercel Python serverless entrypoint
- [`vercel.json`](vercel.json): Edge rewrite configuration routing all requests and static assets
- [`database.py`](database.py): Auto-detects serverless environments and initializes SQLite in `/tmp/fitbuddy.db`

#### Method A: 1-Click Import from GitHub (Recommended)
1. Push your repository to GitHub:
   ```bash
   git push -u origin main
   ```
2. Log in to [Vercel](https://vercel.com/) and click **"Add New..." -> "Project"**.
3. Select your repository (`fitbuddy` or `jecikamary65-jpg/fitbuddy`).
4. In the **Environment Variables** section, add:
   - Key: `GEMINI_API_KEY`
   - Value: `AIzaSyYourActualKeyHere`
5. Click **Deploy**. Vercel will install dependencies from `requirements.txt` and launch your live application with a global `*.vercel.app` URL!

#### Method B: Deploying via Vercel CLI
```bash
# Run Vercel CLI from the fitbuddy directory
npx vercel

# When deploying to production:
npx vercel --prod
```

---

### Deploying to Render / Railway / Cloud Run

1. **Procfile** (for PaaS hosts like Render or Railway):
   ```text
   web: uvicorn app:app --host 0.0.0.0 --port $PORT
   ```

2. **Dockerfile** (for containerized deployments on Google Cloud Run):
   ```dockerfile
   FROM python:3.12-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   COPY . .
   EXPOSE 8000
   CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
   ```

3. **Set Environment Variables on Host**:
   - `GEMINI_API_KEY`: Your Google AI Studio API key
   - `PORT`: Set automatically by cloud provider

---

## 📦 Pushing to GitHub

To publish this project to GitHub:

```bash
# 1. Initialize git
git init

# 2. Add files (.gitignore ensures .env and *.db are not committed)
git add .

# 3. Commit initial release
git commit -m "Initial commit: FitBuddy AI Fitness Plan Generator"

# 4. Set main branch and remote
git branch -M main
git remote add origin https://github.com/your-username/fitbuddy.git

# 5. Push to GitHub
git push -u origin main
```

---

## ⚠️ Health & Safety Disclaimer

> **FitBuddy provides general fitness, exercise programming, and wellness information and is not a substitute for professional medical advice, clinical diagnosis, or medical treatment. Always consult a qualified physician or healthcare provider before beginning any new exercise regimen or nutrition protocol, particularly if you have pre-existing medical conditions, cardiovascular concerns, pregnancy, or joint/musculoskeletal injuries.**
