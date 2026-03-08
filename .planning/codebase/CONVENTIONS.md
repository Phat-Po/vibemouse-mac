# Coding Conventions

**Analysis Date:** 2026-03-09

## Naming Patterns

**Files:**
- `snake_case.py` for all modules: `audio.py`, `keyboard_listener.py`, `setup_wizard.py`, `help_cmd.py`
- One module per responsibility; named after its primary class or feature

**Classes:**
- `PascalCase`: `AppConfig`, `AudioRecorder`, `AudioRecording`, `HotkeyListener`, `TextOutput`, `Transcriber`, `App`
- Data classes use `@dataclass` decorator (see `AppConfig` in `whisperkey_mac/config.py`, `AudioRecording` in `whisperkey_mac/audio.py`)

**Functions:**
- `snake_case` for all functions and methods
- Module-level private helpers prefixed with single underscore: `_step_language()`, `_ask()`, `_model_cached()`, `_python_app_path()` in `whisperkey_mac/setup_wizard.py`
- Instance private methods prefixed with `_`: `_on_press()`, `_start_hold_recording()`, `_callback()`, `_paste_clipboard()`

**Variables:**
- `snake_case` for local variables and instance attributes
- Instance attributes always prefixed with `_` to signal private: `self._config`, `self._lock`, `self._frames`, `self._model`
- Module-level constants in `UPPER_SNAKE_CASE`: `CONFIG_PATH`, `MIN_HOLD_S`, `_KEY_MAP`, `STRINGS`, `WHISPER_LANGUAGES`
- Single-letter variables avoided except for tight loops (`k`, `v`, `i` in list comprehensions)

**Types/Type Hints:**
- `PascalCase` for all types; `str | None` union style (PEP 604, not `Optional[str]`)
- Return types always annotated on public and private methods
- Parameter types always annotated
- `from __future__ import annotations` at top of every file — enables postponed evaluation for forward references

## Code Style

**Formatting:**
- No formatter config file found (no `.prettierrc`, `ruff.toml`, or `[tool.ruff]` in `pyproject.toml`)
- Code follows PEP 8 style manually: 4-space indent, blank lines between methods
- Line length: generally kept under 100 characters; long f-strings split with backslash continuation or parentheses
- Trailing newline at end of files

**Linting:**
- No linting config detected (no `.flake8`, `mypy.ini`, `pylintrc`)
- Type annotations are present throughout but not enforced by a CI tool

## Import Organization

**Order (observed throughout all files):**
1. `from __future__ import annotations` — always first
2. Standard library imports (alphabetical within group): `import json`, `import os`, `import subprocess`, `import sys`, `import threading`, `import time`
3. Third-party imports: `import numpy as np`, `import sounddevice as sd`, `from faster_whisper import WhisperModel`, `from pynput import keyboard`
4. Local package imports: `from whisperkey_mac.config import AppConfig`, `from whisperkey_mac.i18n import t`

**Conditional imports:**
- Optional dependencies wrapped in `try/except ImportError` blocks, with a boolean flag set:
  ```python
  try:
      from rich.console import Console
      from rich.panel import Panel
      _rich = True
  except ImportError:
      _rich = False
  ```
  Pattern used in `whisperkey_mac/setup_wizard.py` and `whisperkey_mac/help_cmd.py`

- Late imports inside functions when used rarely or to avoid circular deps:
  ```python
  def main() -> None:
      if args and args[0] == "setup":
          from whisperkey_mac.setup_wizard import run_setup
  ```
  Pattern used in `whisperkey_mac/main.py`

**Path Aliases:**
- None. All imports use full package path: `from whisperkey_mac.config import ...`

## Error Handling

**Patterns:**
- Exception swallowing with `except Exception: pass` is used when failure is non-fatal and a fallback is implicit:
  ```python
  # whisperkey_mac/config.py
  try:
      data = json.loads(CONFIG_PATH.read_text())
      ...
  except Exception:
      pass
  ```
- Named exception binding used when error message matters:
  ```python
  except Exception as exc:
      print(f"[whisperkey] {t('transcribe_error', lang)}: {exc}")
      return
  ```
- `finally` used for guaranteed cleanup (temp file deletion in `whisperkey_mac/main.py`):
  ```python
  finally:
      try:
          recording.path.unlink(missing_ok=True)
      except Exception:
          pass
  ```
- `subprocess.run(..., check=True)` used where failure should raise (e.g., AppleScript paste in `whisperkey_mac/output.py`)
- `subprocess.run(..., check=False)` used for best-effort operations like opening System Preferences
- Early returns used extensively to reduce nesting: `if not self._recording: return`
- `assert` used only once for type narrowing after `Optional` guarantee (`assert self._model is not None` in `whisperkey_mac/transcriber.py`)

**Return value signaling:**
- Methods that may produce no result return `None` (not raise): `stop_and_save() -> AudioRecording | None`
- String status codes used for output results: `"pasted"`, `"clipboard"`, `"empty"` in `whisperkey_mac/output.py`

## Logging

**Framework:** `print()` — no logging library used

**Patterns:**
- All runtime messages prefixed with `[whisperkey]` for easy filtering in terminal output
- All user-facing strings go through the `t()` i18n function from `whisperkey_mac/i18n.py`
- Format: `print(f"[whisperkey] {t('key', lang)}")`
- Debug-style prints (recording state, model load) go to stdout, not stderr
- No structured logging, no log levels

## Comments

**When to Comment:**
- Section dividers using `# ── Label ───...` style (Unicode box-drawing) to separate logical groups within a file
- Inline comments for non-obvious decisions: thread-safety rationale, why AppleScript is used over pynput, etc.
- Docstrings used selectively on public and "step" functions; single-line `"""` preferred for simple descriptions
- Multi-line docstrings with "Returns:" annotation for functions returning multiple values:
  ```python
  def _step_transcribe_language(lang: str) -> tuple[str, str | None]:
      """
      Step 2: Transcription language.
      Returns (transcribe_language, whisper_language).
      """
  ```

## Function Design

**Size:** Small and focused. No function exceeds ~50 lines. Setup wizard step functions average 15–25 lines.

**Parameters:**
- Config passed as `AppConfig` dataclass — no kwargs unpacking
- Callback functions typed with `Callable[[], None]` from `collections.abc`
- Thread callbacks receive typed parameters matching library signatures

**Return Values:**
- Tuple returns used for multi-value returns: `tuple[str, str | None]`, `tuple[bool, str]`
- `None` used as explicit "no result" signal
- No use of exceptions for flow control

## Module Design

**Exports:**
- No `__all__` declarations in any module
- Public API implied by absence of underscore prefix
- `whisperkey_mac/__init__.py` is empty — no re-exports at package level

**Barrel Files:**
- Not used. Callers import directly from the specific module:
  `from whisperkey_mac.config import load_config, config_exists`

**Thread safety:**
- All mutable shared state protected by `threading.Lock()` with `with self._lock:` blocks
- Double-checked locking pattern used in `Transcriber._ensure_loaded()` for lazy model initialization

---

*Convention analysis: 2026-03-09*
