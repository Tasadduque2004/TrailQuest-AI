# TrailQuest AI 🌿
**Less scrolling. More exploring.**

TrailQuest AI is a local-first outdoor quest companion designed to encourage people to take short breaks from screens and notice the world around them.

Choose an activity, set the time you have, and get a small, practical outdoor quest. Complete its tasks to earn Trail Points, then put your phone away and enjoy being outside.

## What it does

- Offers four activities: Nature Walk, Birdwatching, Photography Hunt, and Gardening.
- Lets you choose a duration, energy level, and optional interests.
- Shows task checkboxes, completion progress, and safety reminders.
- Awards 25 Trail Points for each completed quest.
- Saves Trail Points in the current browser using `localStorage`.
- Works with a built-in mission library when local AI is unavailable.
- Can connect to a locally running Ollama model for AI-generated missions.

## Current AI status

**The built-in mission mode works without Ollama.** If Ollama is not installed or running, the app uses its built-in mission library and displays a note explaining that fallback mode is active.

Actual local-model generation has not been verified as part of this setup. Do not describe the current demo as using live AI generation unless the header reports that local AI is ready and the mission source confirms the model.

## Run on Windows

1. Install Python 3.10 or later from <https://www.python.org/downloads/>.
2. Extract this project ZIP to a writable folder.
3. Double-click `start.bat`.
4. Wait for the app to start, then open <http://127.0.0.1:5000> in your browser.

The first run may need an internet connection to install Flask. Keep the terminal window open while using the app. To stop the server, close that terminal window.

## Optional: enable local AI with Ollama

This is optional; skip it if you want to avoid a large model download for now.

1. Install Ollama from <https://ollama.com/download/windows>.
2. Open PowerShell and run:

   ```powershell
   ollama pull qwen2.5:3b
   ```

3. Ensure Ollama is running, then restart TrailQuest AI.
4. Confirm the header says `Local AI ready · qwen2.5:3b`, and check that the mission source names the local model.

Model downloads need internet and disk space. After setup, inference can run locally. To use another supported Ollama model, set `OLLAMA_MODEL` before launching the app and download that model first.

## Project structure

- `app.py` — Flask routes, Ollama connection, and built-in fallback missions.
- `templates/index.html` — page structure.
- `static/style.css` — responsive design.
- `static/app.js` — activity selection, quest display, progress, completion, and saved points.
- `start.bat` — Windows launcher.
- `SUBMISSION_POST.md` — editable challenge announcement draft.

## Demo checklist

- [ ] Start the app with `start.bat`.
- [ ] Generate a Nature Walk quest.
- [ ] Select Birdwatching or another activity and generate a different quest.
- [ ] Check all tasks and complete the quest.
- [ ] Confirm Trail Points increase by 25.
- [ ] Refresh the page and restart the browser; confirm points remain saved.
- [ ] If Ollama is configured, verify local AI status and the mission source. Otherwise, clearly show the built-in fallback mode.

## Limitations

- Trail Points are saved in this browser on this device; they are not synced between devices or browsers.
- Clearing browser site data may remove saved points.
- The app does not provide GPS tracking, live maps, live weather, verified nearby trails, or emergency services.
- Outdoor suggestions are general prompts. Always use local judgement, respect access rules, and avoid unsafe conditions.

## Privacy

The app does not require an account or a hosted AI API key. Trail Points are stored in browser local storage. When Ollama is configured, prompts are sent to the Ollama service running on your own computer.

## Open source

This project is released under the MIT License. See `LICENSE`.
