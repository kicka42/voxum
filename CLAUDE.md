# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build and Run Commands

```bash
# Install (editable mode for development)
pip install -e .

# Run CLI commands
voxum auth              # OAuth with Google Drive
voxum config            # Show current configuration
voxum process <file>    # Process a local audio file
voxum watch             # Start Drive folder watcher

# Enable verbose logging
voxum -v <command>
```

## Architecture

Voxum is a voice meeting summarizer CLI that processes audio files through a three-stage agent pipeline.

### Pipeline Flow

```
Audio File → TranscriberAgent → SummarizerAgent → DeliveryAgent → (Drive + Email)
```

The `Orchestrator` (`voxum/orchestrator.py`) coordinates the pipeline, calling each agent in sequence and handling errors at each stage.

### Agent Pattern

All agents inherit from `BaseAgent` (`voxum/agents/base.py`), which provides:
- Generic `AgentResult[OutputT]` return type with success/error handling
- Automatic logging via `self.logger`
- Prompt loading from `voxum/prompts/` directory via `load_prompt(name)`

Each agent defines typed `Input` and `Output` dataclasses and implements `_process()`.

### Tools Layer

Tools in `voxum/tools/` are stateless utility modules:
- `drive.py` - Google Drive API (auth, list, download, upload, processed tracking)
- `email.py` - Resend API for sending summaries
- `transcription.py` - LiteLLM wrapper for Whisper transcription

### Configuration

Config loaded from environment variables via `voxum/config.py`. Use `get_config()` singleton accessor. Required vars: `GOOGLE_DRIVE_FOLDER_ID`, `RESEND_API_KEY`, `EMAIL_TO`, `EMAIL_FROM`. LLM API keys: Set provider-specific keys (e.g., `OPENAI_API_KEY`, `GEMINI_API_KEY`) - LiteLLM auto-detects these.

### State Files

Stored in `~/.voxum/`:
- `token.json` - Google OAuth credentials
- `processed.json` - IDs of already-processed Drive files

### Watcher

`voxum/watcher.py` uses APScheduler to poll Google Drive at configurable intervals. Filters for audio MIME types and skips already-processed files.
