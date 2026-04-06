---
description: Boot the local stack for the code-review extension. Starts the Flask API on :5002 in background, installs Python deps if missing, verifies /status, and reports the log path. Use when the user says /init, "arranca todo", "boot", "start the api/server/stack".
user_invocable: true
---

# /init - Boot the local code-review stack

Starts everything the Chrome extension needs to talk to the labeling pipeline.

## What it does

1. Check if the API is already up: `curl -s -m 2 http://localhost:5002/status`
   - If `{"ok": true}` is returned, report "API already running" and stop. Do NOT start a second instance.
2. Ensure Python deps are installed (idempotent):
   ```
   python3 -c "import flask, flask_cors" 2>/dev/null || pip3 install -q flask flask-cors
   ```
3. Make the log dir: `mkdir -p .project/logs`
4. Launch the Flask API in background from the repo root:
   ```
   cd .project/api && nohup python3 app.py > ../logs/api.log 2>&1 &
   ```
   Use the Bash tool with `run_in_background: false` but with `nohup ... &` so it detaches; do NOT use `run_in_background: true` (we want it to survive past the Claude session).
5. Wait ~2s, then verify with `curl -s -m 3 http://localhost:5002/status`. Expect `{"ok": true}`.
6. Report:
   - API URL: http://localhost:5002
   - Log file: `.project/logs/api.log`
   - PID (from `lsof -iTCP:5002 -sTCP:LISTEN -t`)
   - Reminder: open the Chrome side panel and confirm the API status dot is green.

## Failure handling

- If port 5002 is taken by something else, report it with `lsof -iTCP:5002 -sTCP:LISTEN` and ask the user before killing.
- If `curl` still fails after launch, tail `.project/logs/api.log` (last 30 lines) and show it.

## Out of scope

Do not start the Chrome extension itself (it's a browser extension, not a server). Do not run any task pipeline (`/run`). This skill only brings the API up.
