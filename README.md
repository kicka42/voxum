# Voxum

Modular agent-based CLI that turns meeting recordings into actionable summaries.

## Setup

```bash
pip install -e .
```

Requires **ffmpeg** installed on your system.

## Configuration

Create a `.env` file:

```env
GOOGLE_DRIVE_FOLDER_ID=your_folder_id
GOOGLE_CLIENT_SECRETS_PATH=client_secrets.json
RESEND_API_KEY=your_resend_key
EMAIL_TO=you@example.com
EMAIL_FROM=voxum@yourdomain.com

# Optional
TRANSCRIPTION_MODEL=groq/whisper-large-v3-turbo
SUMMARIZATION_MODEL=gpt-4o-mini
SUMMARY_LANGUAGE=en
POLL_INTERVAL_SECONDS=60
```

Set LLM API keys as needed (e.g., `GROQ_API_KEY`, `OPENAI_API_KEY`).

## Usage

```bash
# Authenticate with Google Drive
voxum auth

# Process a local file
voxum process recording.mp3

# Watch Drive folder for new files
voxum watch
```

## How It Works

1. Audio file detected in Google Drive folder
2. Transcribed via Whisper (Groq/OpenAI)
3. Summarized via LLM (participants, key points, action items)
4. Summary uploaded to Drive + emailed to you
