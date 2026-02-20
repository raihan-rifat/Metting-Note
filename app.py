import json
import os
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

import requests


class NoteChatApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Meeting Note + ChatGPT Agent")
        self.root.geometry("1200x720")

        self.notes_file: Path | None = None
        self.chat_history: list[dict[str, str]] = []

        self._build_ui()

    def _build_ui(self) -> None:
        main_frame = ttk.Frame(self.root, padding=12)
        main_frame.pack(fill=tk.BOTH, expand=True)

        splitter = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        splitter.pack(fill=tk.BOTH, expand=True)

        notes_panel = ttk.Frame(splitter)
        chat_panel = ttk.Frame(splitter)
        splitter.add(notes_panel, weight=3)
        splitter.add(chat_panel, weight=2)

        # Notes panel
        ttk.Label(notes_panel, text="Notes", font=("Segoe UI", 14, "bold")).pack(anchor="w")
        notes_toolbar = ttk.Frame(notes_panel)
        notes_toolbar.pack(fill=tk.X, pady=8)

        ttk.Button(notes_toolbar, text="New", command=self.new_note).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(notes_toolbar, text="Open", command=self.open_note).pack(side=tk.LEFT, padx=4)
        ttk.Button(notes_toolbar, text="Save", command=self.save_note).pack(side=tk.LEFT, padx=4)
        ttk.Button(notes_toolbar, text="Save As", command=self.save_note_as).pack(side=tk.LEFT, padx=4)

        self.note_status = tk.StringVar(value="Unsaved note")
        ttk.Label(notes_toolbar, textvariable=self.note_status).pack(side=tk.RIGHT)

        self.notes_text = ScrolledText(notes_panel, wrap=tk.WORD, font=("Consolas", 11), undo=True)
        self.notes_text.pack(fill=tk.BOTH, expand=True)

        # Chat panel
        ttk.Label(chat_panel, text="ChatGPT Agent", font=("Segoe UI", 14, "bold")).pack(anchor="w")

        config_frame = ttk.Frame(chat_panel)
        config_frame.pack(fill=tk.X, pady=8)

        ttk.Label(config_frame, text="Model:").grid(row=0, column=0, sticky="w")
        self.model_var = tk.StringVar(value="gpt-4o-mini")
        ttk.Entry(config_frame, textvariable=self.model_var).grid(row=0, column=1, sticky="ew", padx=6)

        ttk.Label(config_frame, text="Agent instructions:").grid(row=1, column=0, sticky="nw", pady=(8, 0))
        self.system_var = tk.StringVar(
            value="You are a concise assistant helping write, summarize, and improve meeting notes."
        )
        ttk.Entry(config_frame, textvariable=self.system_var).grid(
            row=1, column=1, sticky="ew", padx=6, pady=(8, 0)
        )
        config_frame.columnconfigure(1, weight=1)

        self.chat_output = ScrolledText(chat_panel, wrap=tk.WORD, height=22, state=tk.DISABLED, font=("Segoe UI", 10))
        self.chat_output.pack(fill=tk.BOTH, expand=True)

        input_frame = ttk.Frame(chat_panel)
        input_frame.pack(fill=tk.X, pady=(8, 0))

        self.chat_input = ttk.Entry(input_frame)
        self.chat_input.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.chat_input.bind("<Return>", lambda _event: self.send_message())

        ttk.Button(input_frame, text="Send", command=self.send_message).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(input_frame, text="Insert Answer into Notes", command=self.insert_last_reply_into_notes).pack(
            side=tk.LEFT, padx=(6, 0)
        )

        self.chat_status = tk.StringVar(value="Ready. Set OPENAI_API_KEY to enable ChatGPT.")
        ttk.Label(chat_panel, textvariable=self.chat_status).pack(anchor="w", pady=(6, 0))

    # Notes actions
    def new_note(self) -> None:
        if self.notes_text.edit_modified() and not self._confirm_discard_changes():
            return
        self.notes_text.delete("1.0", tk.END)
        self.notes_file = None
        self.note_status.set("Unsaved note")
        self.notes_text.edit_modified(False)

    def open_note(self) -> None:
        if self.notes_text.edit_modified() and not self._confirm_discard_changes():
            return
        path = filedialog.askopenfilename(
            title="Open note",
            filetypes=[("Text files", "*.txt *.md"), ("All files", "*.*")],
        )
        if not path:
            return
        content = Path(path).read_text(encoding="utf-8")
        self.notes_text.delete("1.0", tk.END)
        self.notes_text.insert("1.0", content)
        self.notes_file = Path(path)
        self.note_status.set(f"Opened: {self.notes_file.name}")
        self.notes_text.edit_modified(False)

    def save_note(self) -> None:
        if not self.notes_file:
            self.save_note_as()
            return
        self.notes_file.write_text(self.notes_text.get("1.0", tk.END).rstrip() + "\n", encoding="utf-8")
        self.note_status.set(f"Saved: {self.notes_file.name} ({datetime.now():%H:%M:%S})")
        self.notes_text.edit_modified(False)

    def save_note_as(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Save note as",
            defaultextension=".md",
            filetypes=[("Markdown", "*.md"), ("Text", "*.txt"), ("All files", "*.*")],
        )
        if not path:
            return
        self.notes_file = Path(path)
        self.save_note()

    def _confirm_discard_changes(self) -> bool:
        return messagebox.askyesno("Unsaved changes", "You have unsaved changes. Discard them?")

    # Chat actions
    def send_message(self) -> None:
        user_text = self.chat_input.get().strip()
        if not user_text:
            return

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            messagebox.showerror("Missing API key", "Set OPENAI_API_KEY in your environment.")
            return

        self.chat_input.delete(0, tk.END)
        self.chat_history.append({"role": "user", "content": user_text})
        self._append_chat("You", user_text)
        self.chat_status.set("Thinking...")
        self.root.update_idletasks()

        try:
            assistant_text = self._call_openai(api_key)
        except Exception as exc:  # noqa: BLE001
            self.chat_status.set("Request failed")
            self._append_chat("Error", str(exc))
            return

        self.chat_history.append({"role": "assistant", "content": assistant_text})
        self._append_chat("Agent", assistant_text)
        self.chat_status.set("Ready")

    def _call_openai(self, api_key: str) -> str:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        messages = [{"role": "system", "content": self.system_var.get().strip()}] + self.chat_history
        payload = {
            "model": self.model_var.get().strip() or "gpt-4o-mini",
            "messages": messages,
            "temperature": 0.5,
        }

        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=60)
        if response.status_code != 200:
            raise RuntimeError(f"API error {response.status_code}: {response.text}")

        body = response.json()
        try:
            return body["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(f"Unexpected API response: {body}") from exc

    def _append_chat(self, sender: str, content: str) -> None:
        self.chat_output.configure(state=tk.NORMAL)
        self.chat_output.insert(tk.END, f"\n{sender}:\n{content}\n")
        self.chat_output.configure(state=tk.DISABLED)
        self.chat_output.see(tk.END)

    def insert_last_reply_into_notes(self) -> None:
        for item in reversed(self.chat_history):
            if item["role"] == "assistant":
                self.notes_text.insert(tk.END, f"\n\n---\nAgent suggestion:\n{item['content']}\n")
                self.note_status.set("Agent reply inserted into notes")
                return
        messagebox.showinfo("No assistant reply", "Ask ChatGPT first, then insert the answer.")


def main() -> None:
    root = tk.Tk()
    app = NoteChatApp(root)
    root.protocol("WM_DELETE_WINDOW", root.destroy)
    root.mainloop()


if __name__ == "__main__":
    main()
