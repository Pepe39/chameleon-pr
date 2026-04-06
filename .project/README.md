# Code Review Labeler — Extension + API

Bridges the annotation platform (`annotation-platform-henna.vercel.app`) to the
local `/run` Claude pipeline.

## Layout

```
.project/
├── extension/   # Chrome MV3 sidepanel
└── api/         # Flask bridge that invokes `claude -p "/run {id}"`
```

## Setup

### 1. API

```bash
cd .project/api
pip install -r requirements.txt
python app.py            # serves http://localhost:5002
```

Requires the `claude` CLI to be on `PATH`.

### 2. Extension

1. Open `chrome://extensions`, enable **Developer mode**.
2. **Load unpacked** -> select `.project/extension/`.
3. Pin the action; clicking it opens the side panel.

## Usage

1. Open a task at `https://annotation-platform-henna.vercel.app/tasks/<id>`.
2. The side panel auto-scrapes the 10 input variables. Verify nothing is `(empty)`.
3. Click **Run /run pipeline**. The API writes `tasks/{date}/{id}/inputs.md`
   and triggers Claude in the background.
4. When deliverables are ready, click **Fill Deliverables** to populate the
   four axes back into the platform.

## Notes

- Scraping uses heuristics (label text + data attributes). If the platform DOM
  differs, refine `scrapeTaskPage` in `extension/background.js`.
- The fill routine clicks radios by visible label and writes textareas. The
  context table autodetect looks for a table containing `diff_line` + `file_path`.
- Deliverable parsing lives in `api/app.py` (`parse_*` functions) and matches
  the platform copy-paste format already documented in the `/run` skill.
