# Voxum

Voxum is a modular agent-based CLI tool that turns meeting recordings into actionable summaries.

## What it does

Drop an audio file into a Google Drive folder (or process locally), and Voxum will:

1. **Transcribe** the audio using Whisper (via Groq or OpenAI)
2. **Summarize** the transcript with an LLM — extracting participants, key points, and action items
3. **Deliver** the summary to your inbox and save it alongside the original file in Drive

## Modes

- **Watch mode**: Runs as a background service, polling Google Drive for new audio files
- **Manual mode**: Process a single local file via `voxum process <file>`

Record your meetings, get summaries in your inbox — no manual effort required.
