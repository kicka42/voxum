# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Voxum is a voice meeting summarizer CLI. It watches a Google Drive folder for audio files, transcribes them, generates summaries, and delivers results via email.

## Commands

```bash
# Install (development mode)
pip install -e .

# Run CLI commands
voxum version              # Show version
voxum auth                 # OAuth flow for Google Drive
voxum config               # Show current configuration
voxum process <file>       # Process a local audio file
voxum watch                # Start background watcher (polls Drive folder)

# Verbose mode (any command)
voxum -v <command>
```

## Architecture

### Pipeline Flow
```
Audio File → TranscriberAgent → SummarizerAgent → DeliveryAgent → Email + Drive
```

The `Orchestrator` (`voxum/orchestrator.py`) coordinates the three-stage pipeline.

### Agent Pattern
All agents inherit from `BaseAgent` (`voxum/agents/base.py`):
- Generic typed interface: `BaseAgent[InputT, OutputT]`
- Override `_process()` method for implementation
- `process()` wraps with error handling and returns `AgentResult`
- Prompts loaded from `voxum/prompts/*.txt` via `load_prompt()`

### Agents
- `TranscriberAgent`: Audio → text using LiteLLM transcription API
- `SummarizerAgent`: Transcript → structured summary using LiteLLM completion
- `DeliveryAgent`: Uploads summary to Drive, sends email via Resend

### Tools
- `voxum/tools/drive.py`: Google Drive API (OAuth, list/download/upload files, processed tracking)
- `voxum/tools/email.py`: Resend email sending
- `voxum/tools/transcription.py`: LiteLLM transcription with auto-compression (ffmpeg) for files >24MB

### Configuration
Environment variables loaded from `.env` via `voxum/config.py`:

Required:
- `GOOGLE_DRIVE_FOLDER_ID`
- `RESEND_API_KEY`
- `EMAIL_TO`
- `EMAIL_FROM`

Optional (with defaults):
- `GOOGLE_CLIENT_SECRETS_PATH` (default: `client_secrets.json`)
- `TRANSCRIPTION_MODEL` (default: `groq/whisper-large-v3-turbo`)
- `SUMMARIZATION_MODEL` (default: `gpt-4o-mini`)
- `SUMMARY_LANGUAGE` (default: `en`)
- `POLL_INTERVAL_SECONDS` (default: `60`)
- `VOXUM_STATE_DIR` (default: `~/.voxum`)
- `TRANSCRIPTION_MAX_FILE_SIZE_MB` (default: `24`)
- `TRANSCRIPTION_AUDIO_BITRATE` (default: `40k`)

LLM API keys (e.g., `OPENAI_API_KEY`, `GROQ_API_KEY`) are read by LiteLLM from environment.

### State Storage
Stored in `VOXUM_STATE_DIR` (default: `~/.voxum`):
- `token.json`: Google OAuth credentials
- `processed.json`: Tracking of processed file IDs

## External Dependencies
- **ffmpeg**: Required for audio compression (must be installed on system)
