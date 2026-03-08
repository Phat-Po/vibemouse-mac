# Architecture

**Analysis Date:** 2026-03-09

## Pattern Overview

**Overall:** Event-driven pipeline with a central App coordinator

**Key Characteristics:**
- Single-process, multi-threaded macOS desktop tool
- Input events (keyboard/mouse) trigger a linear audio → transcription → text injection pipeline
- All components are wired together in `App.__init__()` via callback injection
- Config is loaded once at startup and passed to every component as a shared `AppConfig` dataclass
- No persistent state beyond the config file; all runtime state lives in component instances

## Layers

**Input Layer:**
- Purpose: Detect user gestures and fire callbacks
- Location: `whisperkey_mac/keyboard_listener.py`, `whisperkey_mac/mouse_listener.py`
- Contains: `HotkeyListener` (keyboard), `MouseListener` (mouse side buttons)
- Depends on: `pynput`, `AppConfig` (for hotkey specs)
- Used by: `App` (callbacks wired in `__init__`)

**Audio Layer:**
- Purpose: Capture microphone audio during recording window
- Location: `whisperkey_mac/audio.py`
- Contains: `AudioRecorder`, `AudioRecording` dataclass
- Depends on: `sounddevice`, `soundfile`, `numpy`, `AppConfig`
- Used by: `App._start_recording()`, `App._stop_and_transcribe()`

**Transcription Layer:**
- Purpose: Convert audio file to text using Whisper
- Location: `whisperkey_mac/transcriber.py`
- Contains: `Transcriber` (lazy-loads WhisperModel on first use)
- Depends on: `faster-whisper`, `opencc` (Traditional→Simplified Chinese conversion), `AppConfig`
- Used by: `App._transcribe_and_inject()` (runs in daemon thread)

**Output Layer:**
- Purpose: Inject transcribed text into the active application
- Location: `whisperkey_mac/output.py`
- Contains: `TextOutput`
- Depends on: `pyperclip`, `pynput.keyboard.Controller`, `osascript` (AppleScript via subprocess)
- Used by: `App._transcribe_and_inject()`

**Configuration Layer:**
- Purpose: Load, validate, save, and expose all settings as a typed dataclass
- Location: `whisperkey_mac/config.py`
- Contains: `AppConfig` dataclass, `load_config()`, `save_config()`, `config_exists()`
- Depends on: stdlib only (`json`, `os`, `dataclasses`, `pathlib`)
- Used by: All layers

**Application Coordinator:**
- Purpose: Wire all layers together, manage lifecycle, handle OS signals
- Location: `whisperkey_mac/main.py`
- Contains: `App` class, `main()` entry point, `detect()` utility
- Depends on: All other layers
- Used by: CLI entry point (`whisperkey` console script)

**Setup & Support:**
- Purpose: First-run interactive wizard, diagnostics, i18n, help command
- Location: `whisperkey_mac/setup_wizard.py`, `whisperkey_mac/help_cmd.py`, `whisperkey_mac/i18n.py`
- Contains: Step-by-step TUI wizard, system health checks, bilingual string table
- Depends on: `rich` (optional), `AppConfig`, `pynput`, `ApplicationServices` (macOS framework)

## Data Flow

**Hold-to-talk recording flow:**

1. User holds the configured key (`alt_r` by default)
2. `HotkeyListener._on_press()` sets a `threading.Timer` for 150ms debounce
3. Timer fires → `App._start_recording()` → `AudioRecorder.start()` opens `sounddevice.InputStream`
4. Audio frames buffered in `AudioRecorder._frames` list via stream callback
5. User releases key → `HotkeyListener._on_release()` → `App._stop_and_transcribe()`
6. `AudioRecorder.stop_and_save()` concatenates frames, writes WAV to temp dir, returns `AudioRecording`
7. `App` spawns daemon thread → `App._transcribe_and_inject(recording)`
8. `Transcriber.transcribe(path)` runs `faster-whisper` with VAD filter, converts Traditional→Simplified Chinese
9. `TextOutput.inject(text)` copies to clipboard via `pyperclip`, pastes via AppleScript `osascript`
10. Temp WAV file deleted via `recording.path.unlink()`

**Hands-free toggle flow:**

1. User presses both `handsfree_keys` simultaneously (`alt_r + cmd_r` by default)
2. `HotkeyListener` detects all keys in `_handsfree_pkeys` are in `_held_keys`
3. If `_mode == "idle"` → switches to `"handsfree"`, fires `on_record_start`
4. Same combo pressed again → switches to `"idle"`, fires `on_record_stop_transcribe`
5. Transcription and injection follow same path as hold-to-talk (steps 6–10 above)

**First-run / setup flow:**

1. `main()` calls `config_exists()` → if missing and running in TTY, launches `setup_wizard.run_setup()`
2. Wizard collects: UI language, transcription language, model size, hotkeys, permissions
3. `save_config(AppConfig(...))` writes `~/.config/whisperkey/config.json`
4. `App().run()` starts immediately after setup

**State Management:**
- `HotkeyListener._mode` tracks recording state: `"idle"` | `"hold_recording"` | `"handsfree"`
- `AudioRecorder._recording` bool tracks whether microphone stream is open
- `Transcriber._model` is `None` until first use (lazy-loaded with double-checked locking)
- All state mutations are guarded by `threading.Lock` instances

## Key Abstractions

**AppConfig:**
- Purpose: Single source of truth for all settings; passed by reference to every component
- Location: `whisperkey_mac/config.py`
- Pattern: Frozen-in-practice Python `dataclass`; loaded from `~/.config/whisperkey/config.json` with env var overrides

**AudioRecording:**
- Purpose: Transient transfer object from recorder to transcriber
- Location: `whisperkey_mac/audio.py`
- Pattern: `@dataclass` with `path: Path` and `duration_s: float`; path is deleted after transcription

**HotkeyListener (callback injection):**
- Purpose: Decouple input detection from business logic
- Location: `whisperkey_mac/keyboard_listener.py`
- Pattern: Callbacks (`on_record_start`, `on_record_stop_transcribe`, `on_enter`) injected at construction; listener knows nothing about audio or output

## Entry Points

**CLI — `main()`:**
- Location: `whisperkey_mac/main.py:144`
- Triggers: `whisperkey` console script (registered in `pyproject.toml`), or `python -m whisperkey_mac.main`
- Responsibilities: Argument dispatch (`setup`, `help`, `detect`), first-run detection, construct and run `App`

**Shell launcher — `start.sh`:**
- Location: `start.sh`
- Triggers: Direct shell execution (e.g., double-click `.command` file)
- Responsibilities: Validate `.venv` exists, exec `whisperkey_mac.main` with env var model override

**macOS launcher — `WhisperKey.command`:**
- Location: `WhisperKey.command`
- Triggers: Finder double-click
- Responsibilities: Open Terminal and launch via `start.sh`

**Diagnostic — `detect()`:**
- Location: `whisperkey_mac/main.py:124`
- Triggers: `whisperkey detect`
- Responsibilities: Print raw pynput button values for mouse button discovery

## Error Handling

**Strategy:** Print-and-continue; exceptions in transcription are caught and logged, execution resumes

**Patterns:**
- `Transcriber.transcribe()` errors caught in `App._transcribe_and_inject()` with `try/except Exception as exc` → prints error, returns
- `TextOutput._paste_clipboard()` failure is silent; method returns `"clipboard"` instead of `"pasted"` so user can manually paste
- `AudioRecorder` short recordings (<`min_duration_s`) return `None` — caller checks before spawning transcription thread
- Config load failures are silently swallowed (`except Exception: pass`) — defaults applied
- `load_config()` env var overrides applied after JSON load for resilience

## Cross-Cutting Concerns

**Logging:** `print()` statements with `[whisperkey]` prefix; no structured logging framework

**Validation:** Input validation in setup wizard only (user choices); no runtime schema validation on config JSON

**Authentication:** None — local macOS tool, no network auth

**i18n:** All user-facing strings in `whisperkey_mac/i18n.py` `STRINGS` dict; accessed via `t(key, lang)` helper; bilingual (zh/en)

**Threading:** All audio callbacks run on `sounddevice` callback thread; transcription runs on daemon threads; all shared state protected by `threading.Lock`; main thread blocks on `stop_event.wait()`

**macOS Permissions:** Requires Input Monitoring + Accessibility entitlements; `help_cmd.py` provides runtime diagnostics for both

---

*Architecture analysis: 2026-03-09*
