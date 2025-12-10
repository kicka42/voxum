# Voxum Tech Stack

| Component | Tech |
|-----------|------|
| Language | Python |
| LLM | LiteLLM |
| Transcription | Gemini API |
| CLI | Typer |
| Google Drive | Google Drive API (watch + storage) |
| Background polling | APScheduler |
| Email | Resend |

## How it works

1. Background service polls Google Drive folder for new audio files
2. Or run `voxum process <file>` manually from terminal
3. Transcribes audio with Gemini API
4. Summarizes transcript with LLM (via LiteLLM)
5. Saves summary as a file next to the audio on Google Drive
6. Sends email via Resend
