let selectedActivity = "Nature Walk";
let currentMission = null;
const $ = (id) => document.getElementById(id);

function getTrailPoints() {
  const saved = Number.parseInt(localStorage.getItem("trailPoints") || "0", 10);
  return Number.isFinite(saved) && saved >= 0 ? saved : 0;
}

function updateTrailPointsDisplay() {
  $("trailPointsDisplay").textContent = String(getTrailPoints());
}

// Show the saved score immediately whenever the page opens or refreshes.
updateTrailPointsDisplay();

document.querySelectorAll(".activity").forEach(button => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".activity").forEach(b => b.classList.remove("selected"));
    button.classList.add("selected");
    selectedActivity = button.dataset.activity;
  });
});

async function checkHealth() {
  try {
    const response = await fetch("/api/health");
    const data = await response.json();
    $("statusDot").className = "dot " + (data.ollama ? "online" : "offline");
    $("statusText").textContent = data.ollama ? `Local AI ready · ${data.model}` : "Offline quest mode ready";
  } catch {
    $("statusDot").className = "dot offline";
    $("statusText").textContent = "Offline quest mode ready";
  }
}
checkHealth();

$("generate").addEventListener("click", async () => {
  const button = $("generate");
  button.disabled = true;
  button.innerHTML = "Preparing your quest… <span>✳</span>";
  try {
    const response = await fetch("/api/mission", {
      method: "POST", headers: {"Content-Type":"application/json"},
      body: JSON.stringify({
        activity: selectedActivity,
        minutes: $("minutes").value,
        difficulty: $("difficulty").value,
        interests: $("interests").value
      })
    });
    if (!response.ok) throw new Error("Could not create quest");
    currentMission = await response.json();
    renderMission(currentMission);
  } catch (error) {
    alert("Could not reach the local app. Please restart it using start.bat.");
  } finally {
    button.disabled = false;
    button.innerHTML = 'Create my outdoor quest <span>↗</span>';
  }
});

function renderMission(mission) {
  $("questTitle").textContent = mission.title || "Your outdoor quest";
  $("questIntro").textContent = mission.intro || "Your next adventure starts just outside.";
  $("questTime").textContent = `${$("minutes").value} MINUTES`;
  $("safetyText").textContent = mission.safety || "Stay aware of your surroundings and choose a safe, permitted place.";
  $("sourceNote").textContent = "Quest engine: " + (mission.source || "local quest generator") + (mission.note ? " · " + mission.note : "");
  $("completed").classList.add("hidden");
  const list = $("taskList");
  list.innerHTML = "";
  mission.tasks.forEach((task, index) => {
    const row = document.createElement("label");
    row.className = "task";
    const check = document.createElement("input");
    check.type = "checkbox";
    check.addEventListener("change", () => {
      row.classList.toggle("done", check.checked);
      updateProgress();
    });
    const content = document.createElement("div");
    content.className = "task-content";
    const title = document.createElement("h3");
    title.textContent = `${String(index + 1).padStart(2, "0")} / ${task.title}`;
    const description = document.createElement("p");
    description.textContent = task.description;
    content.append(title, description);
    const meta = document.createElement("span");
    meta.className = "task-meta";
    meta.textContent = `${task.minutes || 5} MIN`;
    row.append(check, content, meta);
    list.append(row);
  });
  $("questSection").classList.remove("hidden");
  updateProgress();
  $("questSection").scrollIntoView({behavior:"smooth", block:"start"});
}

function updateProgress() {
  const checks = [...$("taskList").querySelectorAll('input[type="checkbox"]')];
  const done = checks.filter(c => c.checked).length;
  const percent = checks.length ? Math.round(done / checks.length * 100) : 0;
  $("progressLabel").textContent = `${done} of ${checks.length} complete`;
  $("progressPercent").textContent = `${percent}%`;
  $("progressBar").style.width = `${percent}%`;
  $("finish").disabled = checks.length === 0 || done !== checks.length;
}

$("finish").addEventListener("click", () => {
  $("completed").classList.remove("hidden");
  $("finish").textContent = "Quest completed ✓";
  $("finish").disabled = true;
  const total = getTrailPoints() + 25;
  localStorage.setItem("trailPoints", String(total));
  updateTrailPointsDisplay();
  $("completed").querySelector("p").textContent = `You earned 25 Trail Points. Total: ${total}. Your score is saved on this browser. Now keep enjoying the outdoors—no need to stay on this screen.`;
});
$("newQuest").addEventListener("click", () => {
  $("questSection").classList.add("hidden");
  window.scrollTo({top:0,behavior:"smooth"});
  $("finish").textContent = "Complete my quest ✓";
});
