from flask import Flask, render_template, request, jsonify
import os, json, urllib.request, urllib.error

app = Flask(__name__)
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")

MISSIONS = {
    "Nature Walk": [
        ("Notice five different shades of green", "Look at leaves, grass, moss, or shrubs without picking anything.", 10),
        ("Find a tiny detail", "Observe a leaf pattern, seed, bark texture, or small insect from a respectful distance.", 10),
        ("Pause and listen", "Stand safely for one minute and identify three sounds around you.", 5),
        ("Walk mindfully", "Walk at a comfortable pace and notice how the ground and air feel.", 15),
        ("Leave the place better", "If safe, pick up one piece of litter using protection; skip anything sharp or hazardous.", 5),
    ],
    "Birdwatching": [
        ("Listen before looking", "Pause quietly and notice bird calls. Do not play calls to attract birds.", 5),
        ("Observe a bird's movement", "From a distance, watch how a bird walks, hops, flies, or searches for food.", 10),
        ("Notice colours and shapes", "Record a bird's visible colours and approximate size without disturbing it.", 10),
        ("Look for a safe perch", "Observe where birds rest, keeping away from nests and young birds.", 10),
        ("Respect wildlife", "Keep your distance, never feed wild birds, and leave nests undisturbed.", 5),
    ],
    "Photography Hunt": [
        ("Frame a natural pattern", "Find repeating lines or shapes in leaves, branches, stones, or clouds.", 10),
        ("Capture a texture", "Photograph bark, grass, soil, or a fallen leaf without damaging it.", 10),
        ("Try a new angle", "Take a photo from a safe angle while staying on the path.", 10),
        ("Find a natural colour palette", "Spot three colours in the landscape and remember or photograph them.", 10),
        ("One photo, no scrolling", "Take one photo you like, then put the phone away and enjoy the scene.", 5),
    ],
    "Gardening": [
        ("Inspect the soil", "Touch a small patch of soil and notice whether it feels dry or moist.", 5),
        ("Check one plant", "Look for new growth, damaged leaves, or signs of pests without harming insects.", 10),
        ("Water thoughtfully", "Water only if the plant needs it and follow its usual care instructions.", 10),
        ("Clear a small area", "Remove harmless weeds only if you can identify them confidently.", 10),
        ("Notice a pollinator", "Watch for bees or butterflies from a respectful distance; do not touch them.", 5),
    ],
}

def fallback_mission(activity, minutes, difficulty, interests):
    tasks = MISSIONS.get(activity, MISSIONS["Nature Walk"])
    count = 3 if minutes <= 15 else 4 if minutes <= 30 else 5
    chosen = tasks[:count]
    if difficulty == "Easy":
        chosen = chosen[:max(3, count - 1)]

    # Make the displayed task times add up to the time the user selected.
    # Distribute any remainder across the first tasks (e.g. 10 minutes / 3 tasks = 4, 3, 3).
    base_minutes, remainder = divmod(minutes, len(chosen))
    task_list = []
    for index, task in enumerate(chosen):
        task_minutes = base_minutes + (1 if index < remainder else 0)
        task_list.append({"title": task[0], "description": task[1], "minutes": task_minutes})

    article = "An" if difficulty.lower().startswith(("easy", "adventurous")) else "A"
    return {
        "title": f"{activity}: Your {minutes}-Minute Field Quest",
        "intro": f"{article} {difficulty.lower()} outdoor reset built around {interests or 'noticing the world around you'}. Keep your phone away between tasks.",
        "tasks": task_list,
        "safety": "Choose a familiar, permitted place, stay aware of traffic and weather, tell someone where you are going, and never approach wildlife or enter unsafe areas.",
        "source": "built-in mission library"
    }

def create_ai_mission(activity, minutes, difficulty, interests):
    prompt = f"""Create a safe, practical outdoor mission for a person who wants less screen time.
Activity: {activity}
Available time: {minutes} minutes
Difficulty: {difficulty}
Interests: {interests or 'nature and mindful observation'}
Return ONLY valid JSON with keys title, intro, tasks, safety.
tasks must be an array of 3 to 5 objects with title, description, minutes (integer).
Keep tasks realistic, accessible, and specific. No unsafe climbing, touching wildlife, eating wild plants, trespassing, or requiring special equipment.
Encourage the person to put their phone away after reading. Total task minutes should be close to the available time."""
    payload = json.dumps({"model": OLLAMA_MODEL, "prompt": prompt, "stream": False, "format": "json",
                          "options": {"temperature": 0.7}})
    req = urllib.request.Request(OLLAMA_URL, data=payload.encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=90) as response:
        result = json.loads(response.read().decode())
    mission = json.loads(result.get("response", "{}"))
    if not isinstance(mission.get("tasks"), list) or not mission["tasks"]:
        raise ValueError("The model did not return a valid mission.")
    mission["source"] = f"local open-weight model: {OLLAMA_MODEL}"
    return mission

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/mission", methods=["POST"])
def mission():
    data = request.get_json(silent=True) or {}
    activity = data.get("activity", "Nature Walk")
    if activity not in MISSIONS:
        activity = "Nature Walk"
    try:
        minutes = int(data.get("minutes", 20))
    except (TypeError, ValueError):
        minutes = 20
    minutes = max(10, min(60, minutes))
    difficulty = data.get("difficulty", "Easy")
    if difficulty not in ("Easy", "Moderate", "Adventurous"):
        difficulty = "Easy"
    interests = str(data.get("interests", ""))[:180].strip()
    try:
        result = create_ai_mission(activity, minutes, difficulty, interests)
    except (urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError, KeyError, OSError):
        result = fallback_mission(activity, minutes, difficulty, interests)
        result["note"] = "Local model unavailable, so a built-in mission was used. Install and start Ollama to enable AI-generated missions."
    return jsonify(result)

@app.route("/api/health")
def health():
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags")
        with urllib.request.urlopen(req, timeout=2) as response:
            data = json.loads(response.read().decode())
        models = [m.get("name", "") for m in data.get("models", [])]
        return jsonify({"ollama": True, "model": OLLAMA_MODEL, "available_models": models})
    except Exception:
        return jsonify({"ollama": False, "model": OLLAMA_MODEL, "available_models": []})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
