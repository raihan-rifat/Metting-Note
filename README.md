# Meeting Note (Windows Desktop App)

A simple Windows-friendly note-taking desktop app with a built-in ChatGPT agent.

## Features
- Create, open, and save meeting notes (`.md` / `.txt`)
- Chat panel connected to OpenAI Chat Completions API
- Adjustable model and agent instruction prompt
- One-click insert of latest AI response into your notes

## Requirements
- Windows 10/11
- Python 3.10+
- An OpenAI API key (for agent chat)

## Setup
```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

Set your API key:
```powershell
setx OPENAI_API_KEY "your_api_key_here"
```
Then restart your terminal so the variable is available.

## Run
```powershell
python app.py
```

Or double-click:
- `run_windows.bat`

## How to use
1. Write notes in the left panel.
2. Use the right panel to talk with ChatGPT.
3. Click **Insert Answer into Notes** to paste the latest assistant response.
4. Save notes to `.md` or `.txt`.

## Packaging as a standalone `.exe` (optional)
```powershell
pip install pyinstaller
pyinstaller --onefile --windowed app.py --name MeetingNote
```
Your executable will be in `dist\MeetingNote.exe`.
