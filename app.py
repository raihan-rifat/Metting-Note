import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_SYSTEM_PROMPT = (
    "You are a helpful meeting assistant. Summarize notes, extract action items, and keep responses concise."
)

HTML = """
<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <title>Meeting Note Web App</title>
  <style>
    :root { font-family: Segoe UI, Arial, sans-serif; }
    body { margin: 0; background: #f3f4f6; color: #111827; }
    .container { max-width: 1300px; margin: 20px auto; padding: 0 12px; }
    .grid { display: grid; grid-template-columns: 3fr 2fr; gap: 14px; }
    .card { background: #fff; border: 1px solid #d1d5db; border-radius: 10px; padding: 12px; }
    h2 { margin: 0 0 12px 0; }
    .toolbar, .row { display: flex; gap: 8px; margin-bottom: 10px; align-items: center; flex-wrap: wrap; }
    input[type=text], textarea { width: 100%; border: 1px solid #9ca3af; border-radius: 6px; padding: 8px; box-sizing: border-box; }
    textarea { min-height: 520px; resize: vertical; font-family: Consolas, monospace; }
    .chat-log { height: 420px; overflow: auto; border: 1px solid #d1d5db; border-radius: 6px; padding: 8px; background: #fafafa; }
    .msg { white-space: pre-wrap; margin: 8px 0; padding: 8px; border-radius: 8px; }
    .me { background: #e5e7eb; }
    .bot { background: #dbeafe; }
    .err { background: #fee2e2; color: #7f1d1d; }
    button { border: 1px solid #6b7280; background: #fff; border-radius: 6px; padding: 7px 10px; cursor: pointer; }
    button.primary { background: #2563eb; color: #fff; border-color: #1d4ed8; }
    .status { font-size: 13px; color: #374151; }
    @media (max-width: 980px) { .grid { grid-template-columns: 1fr; } textarea { min-height: 280px; } }
  </style>
</head>
<body>
  <div class=\"container\">
    <div class=\"grid\">
      <section class=\"card\">
        <h2>Notes</h2>
        <div class=\"toolbar\">
          <button onclick=\"newNote()\">New</button>
          <button onclick=\"downloadNote()\">Download .md</button>
          <label for=\"upload\" style=\"cursor:pointer;border:1px solid #6b7280;border-radius:6px;padding:7px 10px;\">Open file</label>
          <input id=\"upload\" type=\"file\" accept=\".md,.txt\" style=\"display:none\" onchange=\"openFile(event)\" />
          <span class=\"status\" id=\"noteStatus\">Unsaved note</span>
        </div>
        <textarea id=\"notes\" placeholder=\"Write your meeting notes here...\"></textarea>
      </section>

      <section class=\"card\">
        <h2>ChatGPT Agent</h2>
        <div class=\"row\">
          <label style=\"min-width:62px\">Model</label>
          <input id=\"model\" type=\"text\" value=\"gpt-4o-mini\" />
        </div>
        <div class=\"row\">
          <label style=\"min-width:62px\">Prompt</label>
          <input id=\"system\" type=\"text\" value=\"You are a helpful meeting assistant. Summarize notes, extract action items, and keep responses concise.\" />
        </div>
        <div class=\"row\">
          <label><input id=\"includeNotes\" type=\"checkbox\" checked /> Include current notes as context</label>
        </div>

        <div id=\"chatLog\" class=\"chat-log\"></div>

        <div class=\"row\" style=\"margin-top:10px\">
          <input id=\"chatInput\" type=\"text\" placeholder=\"Ask the meeting agent...\" onkeydown=\"if(event.key==='Enter'){sendMessage()}\" />
          <button id=\"sendBtn\" class=\"primary\" onclick=\"sendMessage()\">Send</button>
        </div>
        <div class=\"row\">
          <button onclick=\"insertLastReply()\">Insert answer into notes</button>
          <button onclick=\"clearChat()\">Clear chat</button>
          <span class=\"status\" id=\"chatStatus\">Ready. Set OPENAI_API_KEY on server.</span>
        </div>
      </section>
    </div>
  </div>

<script>
  const chatHistory = [];
  let lastAssistantReply = "";

  function setStatus(id, text){ document.getElementById(id).textContent = text; }
  function addChat(sender, content, kind){
    const log = document.getElementById('chatLog');
    const div = document.createElement('div');
    div.className = `msg ${kind}`;
    div.textContent = `${sender}:\n${content}`;
    log.appendChild(div);
    log.scrollTop = log.scrollHeight;
  }
  function newNote(){ if (document.getElementById('notes').value && !confirm('Discard current note?')) return; document.getElementById('notes').value = ''; setStatus('noteStatus', 'Unsaved note'); }
  function downloadNote(){
    const text = document.getElementById('notes').value || '';
    const blob = new Blob([text], {type:'text/markdown;charset=utf-8'});
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'meeting-note.md'; a.click(); URL.revokeObjectURL(a.href);
    setStatus('noteStatus', 'Downloaded meeting-note.md');
  }
  function openFile(event){
    const f = event.target.files[0]; if (!f) return;
    const r = new FileReader(); r.onload = () => { document.getElementById('notes').value = r.result; setStatus('noteStatus', `Opened: ${f.name}`); }; r.readAsText(f);
  }
  async function sendMessage(){
    const input = document.getElementById('chatInput'); const userText = input.value.trim(); if (!userText) return;
    input.value = ''; chatHistory.push({ role: 'user', content: userText }); addChat('You', userText, 'me');
    const payload = { model: document.getElementById('model').value.trim() || 'gpt-4o-mini', system_prompt: document.getElementById('system').value.trim(), include_notes: document.getElementById('includeNotes').checked, notes: document.getElementById('notes').value, history: chatHistory };
    const btn = document.getElementById('sendBtn'); btn.disabled = true; setStatus('chatStatus', 'Thinking...');
    try {
      const res = await fetch('/chat', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload) });
      const data = await res.json(); if (!res.ok) throw new Error(data.error || 'Unknown error');
      chatHistory.push({ role: 'assistant', content: data.reply }); lastAssistantReply = data.reply; addChat('Agent', data.reply, 'bot'); setStatus('chatStatus', 'Ready');
    } catch (err) { addChat('Error', String(err), 'err'); setStatus('chatStatus', 'Request failed'); }
    finally { btn.disabled = false; }
  }
  function clearChat(){ chatHistory.length = 0; lastAssistantReply = ''; document.getElementById('chatLog').innerHTML = ''; setStatus('chatStatus', 'Ready'); }
  function insertLastReply(){ if (!lastAssistantReply) { alert('Ask the agent first, then insert the reply.'); return; } const notes = document.getElementById('notes'); notes.value += `\n\n---\nAgent suggestion:\n${lastAssistantReply}\n`; setStatus('noteStatus', 'Agent reply inserted into notes'); }
</script>
</body>
</html>
"""


def build_messages(system_prompt: str, include_notes: bool, notes: str, history: list[dict[str, str]]) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt or DEFAULT_SYSTEM_PROMPT}]
    if include_notes and notes.strip():
        messages.append(
            {
                "role": "system",
                "content": (
                    "Current working meeting notes from the user. Use as context but do not repeat verbatim unless asked:\n"
                    f"{notes.strip()}"
                ),
            }
        )
    messages.extend(history)
    return messages


def call_openai(api_key: str, model: str, messages: list[dict[str, str]]) -> str:
    req = Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps({"model": model or DEFAULT_MODEL, "messages": messages, "temperature": 0.3}).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except HTTPError as exc:
        raise RuntimeError(f"API error {exc.code}: {exc.read().decode('utf-8', 'ignore')}") from exc
    except URLError as exc:
        raise RuntimeError(f"Network error: {exc.reason}") from exc

    try:
        return body["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"Unexpected API response: {body}") from exc


class Handler(BaseHTTPRequestHandler):
    def _write_json(self, status_code: int, payload: dict[str, str]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path != "/":
            self.send_response(404)
            self.end_headers()
            return
        body = HTML.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/chat":
            self.send_response(404)
            self.end_headers()
            return

        content_length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(content_length)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            self._write_json(400, {"error": "Invalid JSON body"})
            return

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            self._write_json(400, {"error": "OPENAI_API_KEY is not set on the server."})
            return

        history = payload.get("history", [])
        if not isinstance(history, list):
            self._write_json(400, {"error": "history must be a list"})
            return

        messages = build_messages(
            system_prompt=str(payload.get("system_prompt", DEFAULT_SYSTEM_PROMPT)),
            include_notes=bool(payload.get("include_notes", True)),
            notes=str(payload.get("notes", "")),
            history=history,
        )

        try:
            reply = call_openai(api_key=api_key, model=str(payload.get("model", DEFAULT_MODEL)), messages=messages)
        except Exception as exc:  # noqa: BLE001
            self._write_json(500, {"error": str(exc)})
            return

        self._write_json(200, {"reply": reply})


def main() -> None:
    port = int(os.getenv("PORT", "8000"))
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"Meeting Note Web App running on http://localhost:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
