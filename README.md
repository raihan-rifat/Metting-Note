# Meeting Note (Web App)

A browser-based note-taking web app with a built-in ChatGPT meeting agent.

## Features
- Write and manage meeting notes in the browser
- Open local `.md` / `.txt` files into the editor
- Download notes as a markdown file
- ChatGPT side panel with configurable model + system prompt
- Optional notes-as-context toggle for smarter responses
- One-click insert of latest AI response into notes

## Requirements
- Python 3.10+
- An OpenAI API key (for agent chat)

## Setup
```bash
python -m venv .venv
source .venv/bin/activate   # Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Set your API key:
```bash
# Linux/macOS
export OPENAI_API_KEY="your_api_key_here"

# Windows PowerShell
setx OPENAI_API_KEY "your_api_key_here"
```

## Run
```bash
python app.py
```
Then open:
- `http://localhost:8000`

## Windows quick start
- Double-click `run_windows.bat`

## How to use
1. Write notes on the left side.
2. Ask the ChatGPT agent questions on the right side.
3. Click **Insert answer into notes** to paste the latest response into your note.
4. Click **Download .md** to save your note.

## API behavior
- The server calls OpenAI Chat Completions at `POST /chat`.
- `OPENAI_API_KEY` must be available in the server environment.
