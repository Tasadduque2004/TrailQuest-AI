
from flask import Flask, render_template, request, jsonify
import os
import json
import urllib.request
import urllib.error

app = Flask(__name__)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/free")

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

    base_minutes, remainder = divmod(minutes, len(chosen))
    task_list = []

    for index, task in enumerate(chosen):
        task_minutes = base_minutes + (1 if index < remainder else 0)
        task_list.append({
            "title": task[0],
            "description": task[1],
            "minutes": task_minutes
        })

    article = "An" if difficulty.lower().startswith(
        ("easy", "adventurous")
    ) else "A"

    return {
        "title": f"{activity}: Your {minutes}-Minute Field Quest",
        "intro": (
            f"{article} {difficulty.lower()} outdoor reset built around "
            f"{interests or 'noticing the world around you'}. "
            "Keep your phone away between tasks."
        ),
        "tasks": task_list,
        "safety": (
            "Choose a familiar, permitted place, stay aware of traffic and "
            "weather, tell someone where you are going, and never approach "
            "wildlife or enter unsafe areas."
        ),
        "source": "built-in mission library"
    }


def create_ai_mission(activity, minutes, difficulty, interests):
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY is not configured.")

    prompt = f"""
Create a safe, practical outdoor mission for less screen time.

Activity: {activity}
Available time: {minutes} minutes
Difficulty: {difficulty}
Interests: {interests or 'nature and mindful observation'}

Return ONLY valid JSON with these keys:
title, intro, tasks, safety.

tasks must contain 3 to 5 objects.
Each task must have title, description, and minutes (integer).
Task minutes must be positive and add up to exactly {minutes}.
Keep tasks realistic, accessible, and specific.
No unsafe climbing, touching wildlife, eating wild plants,
trespassing, or requiring special equipment.
Encourage the person to put their phone away after reading.
"""

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You create safe outdoor quests. "
                    "Return only a valid JSON object, with no markdown."
                )
            },
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }

    req = urllib.request.Request(
        OPENROUTER_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://trailquest-ai.onrender.com",
            "X-Title": "TrailQuest AI"
        },
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=45) as response:
        api_result = json.loads(response.read().decode("utf-8"))

    content = api_result["choices"][0]["message"]["content"]

    if isinstance(content, list):
        content = "".join(
            part.get("text", "")
            for part in content
            if isinstance(part, dict)
        )

    content = content.strip()

    if content.startswith("```"):
        content = content.split("\n", 1)[-1]
        if content.endswith("```"):
            content = content[:-3].strip()
        if content.startswith("json"):
            content = content[4:].strip()

    mission = json.loads(content)

    if not isinstance(mission, dict):
        raise ValueError("AI response is not a JSON object.")

    for key in ("title", "intro", "safety", "tasks"):
        if key not in mission:
            raise ValueError(f"Missing field: {key}")

    tasks = mission["tasks"]

    if not isinstance(tasks, list) or not 3 <= len(tasks) <= 5:
        raise ValueError("AI returned an invalid number of tasks.")

    total_minutes = 0

    for task in tasks:
        if not isinstance(task, dict):
            raise ValueError("Invalid task format.")

        if not all(key in task for key in ("title", "description", "minutes")):
            raise ValueError("A task is missing required fields.")

        if not isinstance(task["title"], str) or not isinstance(
            task["description"], str
        ):
            raise ValueError("Invalid task text.")

        task_minutes = task["minutes"]

        if (
            not isinstance(task_minutes, int)
            or isinstance(task_minutes, bool)
            or task_minutes < 1
        ):
            raise ValueError("Invalid task duration.")

        total_minutes += task_minutes

    if total_minutes != minutes:
        raise ValueError("Task durations do not match the selected time.")

    mission["source"] = "OpenRouter AI"
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
        result = create_ai_mission(
            activity, minutes, difficulty, interests
        )
    except (
        urllib.error.URLError,
        urllib.error.HTTPError,
        TimeoutError,
        ValueError,
        json.JSONDecodeError,
        KeyError,
        IndexError,
        TypeError,
        OSError
    ) as error:
        app.logger.warning(
            "AI mission generation failed: %s", str(error)[:250]
        )
        result = fallback_mission(
            activity, minutes, difficulty, interests
        )
        result["note"] = (
            "AI generation was unavailable, so a built-in mission "
            "was used. Check the Render logs for details."
        )

    return jsonify(result)


@app.route("/api/health")
def health():
    return jsonify({
        "openrouter_configured": bool(OPENROUTER_API_KEY),
        "model": OPENROUTER_MODEL,
        "fallback_available": True
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
