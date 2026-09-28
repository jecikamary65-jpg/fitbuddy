/**
 * FitBuddy – AI Fitness Plan Generator
 * Frontend Application Controller
 * Handles Scenario 1 (Generation), Scenario 2 (Feedback Update), Scenario 3 (Nutrition Tips),
 * and interactive utility actions (Copy, Print, Export).
 */

document.addEventListener("DOMContentLoaded", () => {
  // Application State
  const state = {
    userId: null,
    planId: null,
    planData: null,
    userName: "",
    userGoal: "Muscle Gain",
    isGenerating: false,
    isUpdating: false,
    quoteInterval: null,
  };

  // Motivational Quotes for Loading Screen
  const loadingQuotes = [
    "\"Analyzing training experience and metabolic requirements...\"",
    "\"Balancing push, pull, and lower body volume splits...\"",
    "\"Programming dynamic warm-ups and injury prevention protocols...\"",
    "\"Structuring progressive overload and optimal rest windows...\"",
    "\"Fine-tuning exercise selection for maximum athletic adaptation...\"",
    "\"Consulting Gemini AI fitness models...\""
  ];

  // DOM Elements
  const workoutForm = document.getElementById("workoutForm");
  const btnGeneratePlan = document.getElementById("btnGeneratePlan");
  const emptyState = document.getElementById("emptyState");
  const loadingState = document.getElementById("loadingState");
  const loadingQuote = document.getElementById("loadingQuote");
  const resultsContainer = document.getElementById("resultsContainer");
  const workoutDaysGrid = document.getElementById("workoutDaysGrid");

  // Summary Elements
  const planUserBadge = document.getElementById("planUserBadge");
  const planGoalBadge = document.getElementById("planGoalBadge");
  const planIntensityBadge = document.getElementById("planIntensityBadge");
  const planSourceBadge = document.getElementById("planSourceBadge");
  const planUpdatedBadge = document.getElementById("planUpdatedBadge");
  const planMainTitle = document.getElementById("planMainTitle");
  const planOverviewText = document.getElementById("planOverviewText");

  // Feedback Elements (Scenario 2)
  const feedbackForm = document.getElementById("feedbackForm");
  const feedbackInput = document.getElementById("feedbackInput");
  const btnUpdatePlan = document.getElementById("btnUpdatePlan");
  const chipButtons = document.querySelectorAll(".chip-btn");

  // Nutrition Elements (Scenario 3)
  const btnGetNutritionTip = document.getElementById("btnGetNutritionTip");
  const nutritionTipDisplay = document.getElementById("nutritionTipDisplay");
  const tipGoalBadge = document.getElementById("tipGoalBadge");
  const tipSourceBadge = document.getElementById("tipSourceBadge");
  const tipTitle = document.getElementById("tipTitle");
  const tipMainText = document.getElementById("tipMainText");
  const tipHydrationText = document.getElementById("tipHydrationText");
  const tipRecoveryText = document.getElementById("tipRecoveryText");

  // Action Buttons
  const btnCopyPlan = document.getElementById("btnCopyPlan");
  const btnPrintPlan = document.getElementById("btnPrintPlan");
  const btnExportJson = document.getElementById("btnExportJson");

  // Status & Modal Elements
  const apiStatusPill = document.getElementById("apiStatusPill");
  const apiStatusText = document.getElementById("apiStatusText");
  const btnApiKeyHelp = document.getElementById("btnApiKeyHelp");
  const apiKeyModal = document.getElementById("apiKeyModal");
  const btnCloseModal = document.getElementById("btnCloseModal");
  const btnDismissModal = document.getElementById("btnDismissModal");
  const toastContainer = document.getElementById("toastContainer");

  // Preferences Char Counter
  const preferencesInput = document.getElementById("preferences");
  const prefCharCount = document.getElementById("prefCharCount");
  if (preferencesInput && prefCharCount) {
    preferencesInput.addEventListener("input", () => {
      prefCharCount.textContent = preferencesInput.value.length;
    });
  }

  // Check initial API status
  checkApiStatus();

  // ------------------ SCENARIO 1: Generate Plan ------------------ //

  workoutForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    // 1. Client-Side Validation
    if (!validateForm()) {
      return;
    }

    const formData = new FormData(workoutForm);
    const payload = {
      name: formData.get("name").trim(),
      age: parseInt(formData.get("age"), 10),
      weight: parseFloat(formData.get("weight")),
      goal: formData.get("goal"),
      intensity: formData.get("intensity"),
      experience_level: formData.get("experience_level"),
      preferences: formData.get("preferences") ? formData.get("preferences").trim() : null,
    };

    // Update state tracking
    state.userName = payload.name;
    state.userGoal = payload.goal;

    // 2. Set UI to Loading State
    setGeneratingState(true);

    try {
      const response = await fetch("/generate-plan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || `Server returned error ${response.status}`);
      }

      // 3. Store in State
      state.userId = data.user_id;
      state.planId = data.plan_id;
      state.planData = data.plan;

      // 4. Render the Plan
      renderPlanOverview(data);
      renderWorkoutDays(data.plan.days);

      // Hide loading, show results
      setGeneratingState(false);
      emptyState.style.display = "none";
      resultsContainer.style.display = "block";

      showToast("7-Day Workout Plan Generated Successfully!", "success");

      // Auto-scroll to results on mobile
      if (window.innerWidth <= 860) {
        resultsContainer.scrollIntoView({ behavior: "smooth" });
      }

    } catch (error) {
      console.error("Plan Generation Error:", error);
      setGeneratingState(false);
      showToast(error.message || "Failed to generate plan. Please try again.", "error");
    }
  });


  // ------------------ SCENARIO 2: Update Plan with Feedback ------------------ //

  // Quick suggestion chips handler
  chipButtons.forEach((chip) => {
    chip.addEventListener("click", () => {
      const text = chip.getAttribute("data-text");
      feedbackInput.value = text;
      feedbackInput.focus();
    });
  });

  feedbackForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    if (!state.userId) {
      showToast("Please generate a workout plan first before submitting feedback.", "error");
      return;
    }

    const feedbackText = feedbackInput.value.trim();
    if (feedbackText.length < 3) {
      showToast("Please enter at least 3 characters of feedback.", "error");
      return;
    }

    setUpdatingState(true);

    try {
      const response = await fetch("/update-plan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: state.userId,
          feedback: feedbackText,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || "Failed to update workout plan.");
      }

      // Update state with new plan
      state.planData = data.plan;

      // Re-render
      renderPlanOverview(data);
      renderWorkoutDays(data.plan.days);

      feedbackInput.value = "";
      setUpdatingState(false);
      showToast("Plan intelligently updated based on your feedback!", "success");

      // Smooth scroll to top of summary
      resultsContainer.scrollIntoView({ behavior: "smooth" });

    } catch (error) {
      console.error("Plan Update Error:", error);
      setUpdatingState(false);
      showToast(error.message || "Could not update plan. Please retry.", "error");
    }
  });


  // ------------------ SCENARIO 3: Nutrition & Recovery Tip ------------------ //

  btnGetNutritionTip.addEventListener("click", async () => {
    const goal = state.userGoal || document.getElementById("goal").value || "General Wellness";

    setNutritionLoading(true);

    try {
      const response = await fetch("/nutrition-tip", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: state.userId || null,
          goal: goal,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || "Failed to retrieve nutrition tip.");
      }

      // Populate Nutrition Display
      tipGoalBadge.textContent = `${data.goal} Nutrition`;
      tipSourceBadge.textContent = data.model_source;
      tipTitle.textContent = data.title || `${data.goal} Guidance`;
      tipMainText.textContent = data.tip || "No nutrition tip provided.";
      tipHydrationText.textContent = data.hydration_tip || "Stay consistently hydrated throughout the day.";
      tipRecoveryText.textContent = data.recovery_tip || "Prioritize 7-9 hours of quality sleep.";

      nutritionTipDisplay.style.display = "block";
      setNutritionLoading(false);
      showToast("Evidence-based Nutrition & Recovery protocol loaded!", "success");

      // Scroll smoothly to nutrition section
      nutritionTipDisplay.scrollIntoView({ behavior: "smooth", block: "nearest" });

    } catch (error) {
      console.error("Nutrition Tip Error:", error);
      setNutritionLoading(false);
      showToast(error.message || "Unable to load nutrition tip.", "error");
    }
  });


  // ------------------ Rendering Helpers ------------------ //

  function renderPlanOverview(data) {
    const plan = data.plan;

    planUserBadge.innerHTML = `<i class="fa-regular fa-user"></i> ${data.user_name || "Athlete"}`;
    planGoalBadge.textContent = plan.goal || state.userGoal;
    planIntensityBadge.textContent = `${plan.intensity} Intensity`;
    planSourceBadge.innerHTML = `<i class="fa-solid fa-microchip"></i> ${data.model_source || "Gemini AI"}`;

    if (data.is_updated) {
      planUpdatedBadge.style.display = "inline-flex";
      planUpdatedBadge.innerHTML = `<i class="fa-solid fa-rotate"></i> Updated via Feedback`;
    } else {
      planUpdatedBadge.style.display = "none";
    }

    planMainTitle.textContent = `${data.user_name}'s 7-Day ${plan.goal} Split`;
    planOverviewText.textContent = plan.overview || "Custom designed 7-day routine tailored to your fitness stats.";
  }

  function renderWorkoutDays(days) {
    workoutDaysGrid.innerHTML = "";

    if (!days || days.length === 0) {
      workoutDaysGrid.innerHTML = `<p class="text-muted">No workout days returned.</p>`;
      return;
    }

    days.forEach((day, index) => {
      const card = document.createElement("div");
      card.className = "day-card";

      // Build exercise list HTML
      let exercisesHtml = "";
      if (day.exercises && day.exercises.length > 0) {
        exercisesHtml = day.exercises.map(ex => `
          <div class="exercise-item">
            <span class="ex-name">${escapeHtml(ex.name)}</span>
            <span class="ex-badge ex-sets">${escapeHtml(String(ex.sets))} Sets</span>
            <span class="ex-badge ex-reps">${escapeHtml(ex.reps)}</span>
            <span class="ex-badge ex-rest"><i class="fa-regular fa-clock"></i> ${escapeHtml(ex.rest)}</span>
          </div>
        `).join("");
      } else {
        exercisesHtml = `<p class="text-muted" style="font-size:0.85rem;">Rest or unstructured active recovery.</p>`;
      }

      card.innerHTML = `
        <div class="day-header">
          <div class="day-title-wrap">
            <span class="day-tag">${escapeHtml(day.day || `Day ${index + 1}`)}</span>
            <h3 class="day-focus">${escapeHtml(day.focus)}</h3>
          </div>
          <span class="day-duration">
            <i class="fa-solid fa-stopwatch"></i> ${day.duration_minutes || 45} mins
          </span>
        </div>

        <div class="routine-box routine-warmup">
          <i class="fa-solid fa-person-running routine-icon"></i>
          <div>
            <span class="routine-label">Warm-up:</span>
            <span>${escapeHtml(day.warmup || "5 min dynamic mobility and light cardio")}</span>
          </div>
        </div>

        <div class="exercise-list">
          ${exercisesHtml}
        </div>

        <div class="routine-box routine-cooldown">
          <i class="fa-solid fa-child-reaching routine-icon"></i>
          <div>
            <span class="routine-label">Cool-down:</span>
            <span>${escapeHtml(day.cooldown || "5 min static stretches and deep breathing")}</span>
          </div>
        </div>
      `;

      workoutDaysGrid.appendChild(card);
    });
  }


  // ------------------ Actions: Copy, Print, Export ------------------ //

  btnCopyPlan.addEventListener("click", () => {
    if (!state.planData) {
      showToast("No active plan to copy.", "error");
      return;
    }

    const text = formatPlanAsPlainText(state.planData, state.userName);
    navigator.clipboard.writeText(text)
      .then(() => showToast("Workout plan copied to clipboard!", "success"))
      .catch(() => showToast("Failed to copy to clipboard.", "error"));
  });

  btnPrintPlan.addEventListener("click", () => {
    if (!state.planData) {
      showToast("No active plan to print.", "error");
      return;
    }
    window.print();
  });

  btnExportJson.addEventListener("click", () => {
    if (!state.planData) {
      showToast("No active plan to export.", "error");
      return;
    }

    const exportObj = {
      athlete: state.userName,
      exported_at: new Date().toISOString(),
      plan: state.planData,
    };

    const blob = new Blob([JSON.stringify(exportObj, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `FitBuddy_${state.userName.replace(/\s+/g, "_")}_Plan.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    showToast("JSON file downloaded!", "info");
  });


  // ------------------ Form Validation ------------------ //

  function validateForm() {
    let isValid = true;

    const nameInput = document.getElementById("name");
    const nameError = document.getElementById("nameError");
    if (!nameInput.value.trim()) {
      nameError.textContent = "Please enter your name.";
      nameError.style.display = "block";
      isValid = false;
    } else {
      nameError.style.display = "none";
    }

    const ageInput = document.getElementById("age");
    const ageError = document.getElementById("ageError");
    const ageVal = parseInt(ageInput.value, 10);
    if (isNaN(ageVal) || ageVal < 14 || ageVal > 100) {
      ageError.textContent = "Age must be between 14 and 100.";
      ageError.style.display = "block";
      isValid = false;
    } else {
      ageError.style.display = "none";
    }

    const weightInput = document.getElementById("weight");
    const weightError = document.getElementById("weightError");
    const weightVal = parseFloat(weightInput.value);
    if (isNaN(weightVal) || weightVal < 30 || weightVal > 300) {
      weightError.textContent = "Weight must be between 30 and 300 kg.";
      weightError.style.display = "block";
      isValid = false;
    } else {
      weightError.style.display = "none";
    }

    return isValid;
  }


  // ------------------ Loading State Controls ------------------ //

  function setGeneratingState(isLoading) {
    state.isGenerating = isLoading;
    btnGeneratePlan.disabled = isLoading;

    const textSpan = btnGeneratePlan.querySelector(".btn-text");
    const spinnerSpan = btnGeneratePlan.querySelector(".btn-spinner");

    if (isLoading) {
      textSpan.style.display = "none";
      spinnerSpan.style.display = "inline-flex";
      emptyState.style.display = "none";
      resultsContainer.style.display = "none";
      loadingState.style.display = "block";

      // Cycle quotes
      let quoteIdx = 0;
      loadingQuote.textContent = loadingQuotes[0];
      state.quoteInterval = setInterval(() => {
        quoteIdx = (quoteIdx + 1) % loadingQuotes.length;
        loadingQuote.textContent = loadingQuotes[quoteIdx];
      }, 2500);

    } else {
      textSpan.style.display = "inline-flex";
      spinnerSpan.style.display = "none";
      loadingState.style.display = "none";
      if (state.quoteInterval) {
        clearInterval(state.quoteInterval);
        state.quoteInterval = null;
      }
    }
  }

  function setUpdatingState(isLoading) {
    state.isUpdating = isLoading;
    btnUpdatePlan.disabled = isLoading;

    const textSpan = btnUpdatePlan.querySelector(".btn-text");
    const spinnerSpan = btnUpdatePlan.querySelector(".btn-spinner");

    if (isLoading) {
      textSpan.style.display = "none";
      spinnerSpan.style.display = "inline-flex";
    } else {
      textSpan.style.display = "inline-flex";
      spinnerSpan.style.display = "none";
    }
  }

  function setNutritionLoading(isLoading) {
    btnGetNutritionTip.disabled = isLoading;
    const textSpan = btnGetNutritionTip.querySelector(".btn-text");
    const spinnerSpan = btnGetNutritionTip.querySelector(".btn-spinner");

    if (isLoading) {
      textSpan.style.display = "none";
      spinnerSpan.style.display = "inline-flex";
    } else {
      textSpan.style.display = "inline-flex";
      spinnerSpan.style.display = "none";
    }
  }


  // ------------------ API Status Check ------------------ //

  async function checkApiStatus() {
    try {
      const res = await fetch("/api/status");
      const statusData = await res.json();

      if (statusData.gemini_api_configured) {
        apiStatusPill.className = "status-pill status-active";
        apiStatusText.textContent = "Gemini 2.5 Active";
      } else {
        apiStatusPill.className = "status-pill status-demo";
        apiStatusText.textContent = "Demo Engine (Add Key)";
      }
    } catch (err) {
      console.warn("Unable to fetch status:", err);
    }
  }


  // ------------------ Modal Controls ------------------ //

  btnApiKeyHelp.addEventListener("click", () => {
    apiKeyModal.style.display = "flex";
  });

  const closeModal = () => { apiKeyModal.style.display = "none"; };
  btnCloseModal.addEventListener("click", closeModal);
  btnDismissModal.addEventListener("click", closeModal);
  apiKeyModal.addEventListener("click", (e) => {
    if (e.target === apiKeyModal) closeModal();
  });


  // ------------------ Toast Notification System ------------------ //

  function showToast(message, type = "info", duration = 4000) {
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;

    let iconClass = "fa-solid fa-circle-info";
    if (type === "success") iconClass = "fa-solid fa-circle-check";
    if (type === "error") iconClass = "fa-solid fa-triangle-exclamation";

    toast.innerHTML = `
      <i class="${iconClass}"></i>
      <span>${escapeHtml(message)}</span>
    `;

    toastContainer.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transform = "translateX(20px)";
      toast.style.transition = "all 0.3s ease";
      setTimeout(() => toast.remove(), 300);
    }, duration);
  }


  // ------------------ Plain Text Format Helper ------------------ //

  function formatPlanAsPlainText(plan, athleteName) {
    let out = `FITBUDDY 7-DAY WORKOUT SPLIT\n`;
    out += `Athlete: ${athleteName}\n`;
    out += `Goal: ${plan.goal} | Intensity: ${plan.intensity}\n`;
    out += `Overview: ${plan.overview || "Personalized 7-day program."}\n`;
    out += `--------------------------------------------------------\n\n`;

    plan.days.forEach((d) => {
      out += `[${d.day}] - ${d.focus} (${d.duration_minutes} mins)\n`;
      out += `Warmup: ${d.warmup}\n`;
      out += `Exercises:\n`;
      d.exercises.forEach((ex, i) => {
        out += `  ${i + 1}. ${ex.name} - ${ex.sets} sets x ${ex.reps} (Rest: ${ex.rest})\n`;
      });
      out += `Cooldown: ${d.cooldown}\n\n`;
    });

    out += `Generated by FitBuddy AI (Gemini Models)`;
    return out;
  }

  function escapeHtml(str) {
    if (typeof str !== "string") return str;
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
});
