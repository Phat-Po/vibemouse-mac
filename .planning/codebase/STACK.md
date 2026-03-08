# Technology Stack

**Analysis Date:** 2026-03-09

## Languages

**Primary:**
- Python 3.12 - All application code in `whisperkey_mac/`

**Secondary:**
- Bash - Launcher script `start.sh` and `WhisperKey.command`

## Runtime

**Environment:**
- CPython 3.12.10 (Homebrew: `/opt/homebrew/Cellar/python@3.12/3.12.10_1`)
- Minimum required: Python 3.10+ (declared in `pyproject.toml`)

**Package Manager:**
- pip via setuptools
- Virtual environment: `.venv/` (created with `python3.12 -m venv .venv`)
- Lockfile: Not present — only version lower-bounds in `pyproject.toml`

## Frameworks

**Core:**
- None — pure Python stdlib + third-party packages, no web or app framework

**Build/Dev:**
- setuptools >= 68 — build backend declared in `pyproject.toml`
- wheel — packaging

**CLI Entry Point:**
- `whisperkey` command registered via `[project.scripts]` → `whisperkey_mac.main:main`

## Key Dependencies

**Critical:**
- `faster-whisper >= 1.0` (installed: 1.2.1) — local on-device speech-to-text via CTranslate2 runtime; downloads Whisper models from HuggingFace on first run
- `ctranslate2 4.7.1` — inference engine used internally by faster-whisper
- `onnxruntime 1.24.3` — used by faster-whisper for VAD (voice activity detection)
- `pynput >= 1.7` (installed: 1.8.1) — keyboard and mouse event listener; requires macOS Input Monitoring permission
- `sounddevice >= 0.4` (installed: 0.5.5) — real-time audio capture from microphone via PortAudio
- `soundfile >= 0.12` (installed: 0.13.1) — writes captured audio to WAV files for Whisper input
- `numpy >= 1.24` (installed: 2.4.2) — audio buffer concatenation in `whisperkey_mac/audio.py`

**Infrastructure:**
- `pyperclip >= 1.8` (installed: 1.11.0) — clipboard write; used in `whisperkey_mac/output.py` to copy transcribed text before pasting
- `opencc-python-reimplemented >= 0.1` (installed: 0.1.7) — Traditional → Simplified Chinese conversion in `whisperkey_mac/transcriber.py`
- `rich >= 13.0` (installed: 14.3.3) — optional terminal UI for setup wizard and help command; gracefully degrades if unavailable

**macOS System (implicit):**
- `ApplicationServices` framework — accessed via pyobjc in `whisperkey_mac/help_cmd.py` to check `AXIsProcessTrusted()` (Accessibility permission status)
- `osascript` (AppleScript) — invoked via `subprocess` in `whisperkey_mac/output.py` to send Cmd+V keystrokes through System Events

## Configuration

**Environment:**
- All config via `~/.config/whisperkey/config.json` (written by setup wizard, path hardcoded in `whisperkey_mac/config.py` as `CONFIG_PATH`)
- Env var overrides supported at runtime (checked in `whisperkey_mac/config.py:load_config()`):
  - `WHISPERKEY_MODEL` — Whisper model size (base / small / large-v3-turbo)
  - `WHISPERKEY_COMPUTE_TYPE` — CTranslate2 compute type (default: int8)
  - `WHISPERKEY_DEVICE` — cpu or cuda (default: cpu)
  - `WHISPERKEY_LANGUAGE` — ISO language code or empty for auto-detect
  - `WHISPERKEY_SAMPLE_RATE` — audio sample rate (default: 16000)
  - `WHISPERKEY_TEMP_DIR` — temp directory for WAV files
  - `WHISPERKEY_MIN_DURATION` — minimum recording duration in seconds
  - `WHISPERKEY_AUTO_PASTE` — "1" to enable auto-paste

**Build:**
- `pyproject.toml` — single build config file, no setup.cfg or setup.py
- Editable install: `.venv/bin/python -m pip install -e .`

## Platform Requirements

**Development:**
- macOS only (hard requirement — uses macOS-specific APIs: AppleScript, AXIsProcessTrusted, macOS Input Monitoring, macOS Accessibility permissions)
- Python 3.10+
- PortAudio system library (required by sounddevice)
- Microphone hardware

**Production:**
- Runs as a persistent foreground process (no daemon/service infrastructure built in)
- Models cached at `~/.cache/huggingface/hub/models--Systran--faster-whisper-*/`
- No server, no deployment target — local macOS desktop tool only

---

*Stack analysis: 2026-03-09*
