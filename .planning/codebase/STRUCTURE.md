# Codebase Structure

**Analysis Date:** 2026-03-09

## Directory Layout

```
20260302__python__vibemouse-mac/
├── whisperkey_mac/             # Main source package
│   ├── __init__.py             # Empty package marker
│   ├── main.py                 # App class, main() entry point, detect() utility
│   ├── config.py               # AppConfig dataclass, load/save/config_exists
│   ├── audio.py                # AudioRecorder, AudioRecording dataclass
│   ├── transcriber.py          # Transcriber (faster-whisper wrapper)
│   ├── output.py               # TextOutput (clipboard + AppleScript paste)
│   ├── keyboard_listener.py    # HotkeyListener, key name ↔ pynput mapping
│   ├── mouse_listener.py       # MouseListener (side button detection, legacy)
│   ├── setup_wizard.py         # Interactive 5-step first-run wizard
│   ├── help_cmd.py             # Diagnostics checker (whisperkey help)
│   ├── i18n.py                 # Bilingual string table + t() helper
│   └── __pycache__/            # Python bytecode cache (auto-generated)
├── build/                      # setuptools build artifacts (generated)
│   └── lib/whisperkey_mac/     # Mirror of source at build time
├── whisperkey_mac.egg-info/    # Installed package metadata (generated)
├── vibemouse_mac.egg-info/     # Legacy package name metadata (generated)
├── .planning/                  # GSD planning documents
│   └── codebase/               # Codebase analysis docs
├── .venv/                      # Local virtualenv (not committed)
├── pyproject.toml              # Package config, dependencies, entry points
├── start.sh                    # Shell launcher (validates .venv, execs main)
├── WhisperKey.command          # macOS Finder double-click launcher
├── CONTEXT.md                  # Project context / notes
├── README.md                   # English documentation
├── README.zh.md                # Chinese documentation
├── LICENSE                     # License file
└── .gitignore                  # Git ignore rules
```

## Directory Purposes

**`whisperkey_mac/` (primary source):**
- Purpose: All application code; installed as a Python package
- Contains: 10 Python modules covering the full feature set
- Key files: `main.py` (entry), `config.py` (settings), `audio.py`, `transcriber.py`, `output.py`

**`build/` (generated):**
- Purpose: setuptools build output; exact mirror of `whisperkey_mac/`
- Contains: Copies of source files from last `pip install -e .` or build run
- Generated: Yes — do not edit here
- Committed: No (should be in `.gitignore`)

**`whisperkey_mac.egg-info/` and `vibemouse_mac.egg-info/` (generated):**
- Purpose: pip/setuptools package metadata
- Contains: `PKG-INFO`, `SOURCES.txt`, `entry_points.txt`, `requires.txt`
- Generated: Yes — created by `pip install -e .`
- Committed: No (typically excluded)
- Note: Two egg-info directories exist because the package was renamed from `vibemouse_mac` to `whisperkey_mac`; both reflect this historical rename

**`.venv/` (local virtualenv):**
- Purpose: Isolated Python 3.12 environment with all dependencies
- Contains: `python`, `whisperkey` console script, all installed packages
- Generated: Yes (`python3.12 -m venv .venv && pip install -e .`)
- Committed: No

**`.planning/codebase/`:**
- Purpose: GSD codebase analysis documents
- Contains: ARCHITECTURE.md, STRUCTURE.md, and other analysis docs

## Key File Locations

**Entry Points:**
- `whisperkey_mac/main.py`: `main()` function — CLI dispatch and App startup
- `start.sh`: Shell launcher with `.venv` validation
- `WhisperKey.command`: macOS Finder double-click launcher

**Configuration:**
- `pyproject.toml`: Package name, version, dependencies, `[project.scripts]` console entry
- `whisperkey_mac/config.py`: Runtime config dataclass + JSON persistence at `~/.config/whisperkey/config.json`

**Core Logic:**
- `whisperkey_mac/audio.py`: Microphone capture
- `whisperkey_mac/transcriber.py`: Whisper model wrapper
- `whisperkey_mac/output.py`: Text injection via clipboard + AppleScript
- `whisperkey_mac/keyboard_listener.py`: Hold-to-talk + hands-free hotkey logic

**User-Facing Strings:**
- `whisperkey_mac/i18n.py`: All zh/en strings; the only file to touch for copy changes

**Wizard & Diagnostics:**
- `whisperkey_mac/setup_wizard.py`: First-run interactive setup
- `whisperkey_mac/help_cmd.py`: `whisperkey help` system health checker

## Naming Conventions

**Files:**
- `snake_case.py` for all Python source files
- Descriptive single-word or compound names matching the class they contain (e.g., `audio.py` → `AudioRecorder`, `transcriber.py` → `Transcriber`)

**Classes:**
- `PascalCase` (e.g., `AudioRecorder`, `HotkeyListener`, `TextOutput`, `AppConfig`)

**Functions and Methods:**
- `snake_case` for public methods: `start()`, `stop_and_save()`, `transcribe()`
- `_snake_case` prefix for private/internal methods: `_callback()`, `_ensure_loaded()`, `_paste_clipboard()`

**Constants:**
- `UPPER_SNAKE_CASE`: `CONFIG_PATH`, `MIN_HOLD_S`, `STRINGS`, `WHISPER_LANGUAGES`, `_KEY_MAP`

**Callbacks:**
- Named `on_<event>` pattern: `on_record_start`, `on_record_stop_transcribe`, `on_enter`, `on_press`, `on_release`

## Where to Add New Code

**New recording trigger (e.g., voice activation, new hotkey type):**
- Add a new listener class in `whisperkey_mac/` (follow `keyboard_listener.py` or `mouse_listener.py` pattern)
- Wire callbacks into `App.__init__()` in `whisperkey_mac/main.py`
- Add config fields for it in `AppConfig` in `whisperkey_mac/config.py`

**New output method (e.g., send to clipboard only, or type character by character):**
- Add method to `TextOutput` in `whisperkey_mac/output.py`
- Expose as config option in `AppConfig`

**New setup wizard step:**
- Add `_step_<name>()` function in `whisperkey_mac/setup_wizard.py`
- Call it in `run_setup()` and pass result into `AppConfig()`
- Add strings to both `zh` and `en` dicts in `whisperkey_mac/i18n.py`

**New user-facing strings:**
- Edit `whisperkey_mac/i18n.py` — add key to both `"zh"` and `"en"` dicts in `STRINGS`
- Access via `t("your_key", lang)` anywhere

**New config option:**
- Add field with default to `AppConfig` dataclass in `whisperkey_mac/config.py`
- Optionally add env var override in `load_config()`
- If user-configurable, add a setup wizard step or allow env var only

**New CLI subcommand (e.g., `whisperkey reset`):**
- Add `elif args[0] == "reset":` branch in `main()` in `whisperkey_mac/main.py`
- Implement in a dedicated module or inline for simple cases

## Special Directories

**`build/`:**
- Purpose: setuptools build artifacts mirroring source
- Generated: Yes
- Committed: No — safe to delete; recreated by `pip install -e .`

**`whisperkey_mac.egg-info/` and `vibemouse_mac.egg-info/`:**
- Purpose: Installed package metadata for pip
- Generated: Yes
- Committed: No — safe to delete; recreated by `pip install -e .`
- Note: `vibemouse_mac.egg-info/` is a legacy artifact from a prior package name; the `vibemouse` console script entry point it defines points to `vibemouse_mac.main:main` which does not exist as a module — only `whisperkey_mac` is the live package name

**`.venv/`:**
- Purpose: Python 3.12 virtualenv with all runtime dependencies
- Generated: Yes (`python3.12 -m venv .venv`)
- Committed: No

**`whisperkey_mac/__pycache__/`:**
- Purpose: Python bytecode cache
- Generated: Yes
- Committed: No

---

*Structure analysis: 2026-03-09*
