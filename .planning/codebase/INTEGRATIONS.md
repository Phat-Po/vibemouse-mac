# External Integrations

**Analysis Date:** 2026-03-09

## APIs & External Services

**AI / Machine Learning:**
- HuggingFace Hub (implicit, via faster-whisper) — model weight downloads only
  - SDK/Client: `faster-whisper` library auto-downloads on first `WhisperModel()` instantiation
  - Auth: None required for public Systran models
  - Models used: `Systran/faster-whisper-base`, `Systran/faster-whisper-small`, `Systran/faster-whisper-large-v3-turbo`
  - Network required: First run only; subsequent runs use local cache at `~/.cache/huggingface/hub/`
  - Called from: `whisperkey_mac/transcriber.py:_ensure_loaded()`

**macOS System APIs (local, no network):**
- AppleScript / System Events — invoked via `osascript` subprocess in `whisperkey_mac/output.py:_paste_clipboard()` to trigger Cmd+V in frontmost application
- ApplicationServices framework (`AXIsProcessTrusted`) — checked in `whisperkey_mac/help_cmd.py:_check_accessibility()` to verify Accessibility permission status
- macOS Privacy & Security settings — `subprocess.run(["open", "x-apple.systempreferences:..."])` in `whisperkey_mac/setup_wizard.py:_step_permissions()` to open Input Monitoring and Accessibility preference panes

## Data Storage

**Databases:**
- None

**File Storage:**
- Local filesystem only
  - Config: `~/.config/whisperkey/config.json` — JSON, read/written by `whisperkey_mac/config.py`
  - Temp audio: `<system_tmpdir>/whisperkey_mac/rec_<uuid>.wav` — created in `whisperkey_mac/audio.py`, deleted immediately after transcription in `whisperkey_mac/main.py:_transcribe_and_inject()`
  - Model cache: `~/.cache/huggingface/hub/` — managed by faster-whisper/HuggingFace Hub library

**Caching:**
- None (beyond HuggingFace model cache managed by the faster-whisper library)

## Authentication & Identity

**Auth Provider:**
- None — local tool with no user accounts or remote authentication

## Monitoring & Observability

**Error Tracking:**
- None — errors printed to stdout/stderr only

**Logs:**
- All output via `print()` to stdout, prefixed with `[whisperkey]`
- No structured logging, no log files, no log rotation

## CI/CD & Deployment

**Hosting:**
- No server hosting — local macOS desktop application only

**CI Pipeline:**
- Not detected (no `.github/`, no CI config files)

**Distribution:**
- Installable Python package via `pip install -e .` from local clone
- `WhisperKey.command` — double-clickable macOS Terminal launcher in project root
- `start.sh` — bash launcher that invokes `.venv/bin/python -m whisperkey_mac.main`

## Environment Configuration

**Required env vars:**
- None required — all configuration uses `~/.config/whisperkey/config.json` with hardcoded defaults
- Optional overrides: `WHISPERKEY_MODEL`, `WHISPERKEY_COMPUTE_TYPE`, `WHISPERKEY_DEVICE`, `WHISPERKEY_LANGUAGE`, `WHISPERKEY_SAMPLE_RATE`, `WHISPERKEY_TEMP_DIR`, `WHISPERKEY_MIN_DURATION`, `WHISPERKEY_AUTO_PASTE`

**Secrets location:**
- No secrets used anywhere in this project

## Webhooks & Callbacks

**Incoming:**
- None

**Outgoing:**
- None

---

*Integration audit: 2026-03-09*
