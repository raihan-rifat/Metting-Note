@echo off
setlocal

if "%OPENAI_API_KEY%"=="" (
  echo [INFO] OPENAI_API_KEY is not set. ChatGPT calls will fail until you set it.
)

python app.py
