@echo off
setlocal

if "%OPENAI_API_KEY%"=="" (
  echo [INFO] OPENAI_API_KEY is not set. ChatGPT will not work until you set it.
)

python app.py
