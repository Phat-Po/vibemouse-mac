# Testing Patterns

**Analysis Date:** 2026-03-09

## Test Framework

**Runner:** Not configured

**Status:** No test files, no test directories, and no test framework configuration exist in this project. The following were checked and are absent:
- No `tests/` or `test/` directory
- No `test_*.py` or `*_test.py` files
- No `pytest.ini`, `setup.cfg [tool:pytest]`, or `[tool.pytest.ini_options]` in `pyproject.toml`
- No `unittest` usage in any source file

**Run Commands:**
```bash
# No test commands configured
# pytest is not installed in the .venv
```

## Test File Organization

**Location:** Not established

**Naming:** Not established

## Test Structure

No tests exist. However, based on the codebase structure, the natural test boundaries would be:

- `whisperkey_mac/config.py` — `load_config()`, `save_config()`, `config_exists()` are pure functions testable without hardware
- `whisperkey_mac/i18n.py` — `t()` function is a pure function, fully testable
- `whisperkey_mac/keyboard_listener.py` — `key_name_to_pynput()`, `pynput_key_to_name()` are pure functions
- `whisperkey_mac/audio.py` — `AudioRecorder` requires `sounddevice` hardware mocking
- `whisperkey_mac/transcriber.py` — `Transcriber` requires `WhisperModel` mocking
- `whisperkey_mac/output.py` — `TextOutput.inject()` requires `subprocess` and `pyperclip` mocking

## Mocking

**Framework:** Not established (no `unittest.mock` or `pytest-mock` usage found)

**What would need mocking for hardware-dependent modules:**
- `sounddevice.InputStream` — audio capture in `whisperkey_mac/audio.py`
- `faster_whisper.WhisperModel` — ML model in `whisperkey_mac/transcriber.py`
- `subprocess.run` — AppleScript calls in `whisperkey_mac/output.py` and `whisperkey_mac/help_cmd.py`
- `pyperclip.copy` — clipboard in `whisperkey_mac/output.py`
- `pynput.keyboard.Listener` — system input monitoring in `whisperkey_mac/keyboard_listener.py`

## Fixtures and Factories

**Test Data:** Not established

**Config fixture pattern (would be natural):**
```python
# Suggested pattern based on AppConfig dataclass in whisperkey_mac/config.py
import pytest
from whisperkey_mac.config import AppConfig

@pytest.fixture
def default_config():
    return AppConfig()

@pytest.fixture
def zh_config():
    return AppConfig(ui_language="zh", transcribe_language="zh", language="zh")
```

## Coverage

**Requirements:** None enforced

**View Coverage:**
```bash
# Not configured — would require: pip install pytest pytest-cov
# pytest --cov=whisperkey_mac --cov-report=term-missing
```

## Test Types

**Unit Tests:** None present

**Integration Tests:** None present

**E2E Tests:** Not used

## Notes for Adding Tests

When introducing tests to this project:

1. Install test dependencies and add to `pyproject.toml`:
   ```toml
   [project.optional-dependencies]
   dev = ["pytest>=8.0", "pytest-cov"]
   ```

2. Create `tests/` directory at project root (sibling of `whisperkey_mac/`)

3. Start with pure-function unit tests — no mocking needed:
   - `tests/test_i18n.py` — test `t()` key lookups, fallback behavior, `{placeholder}` formatting
   - `tests/test_config.py` — test `load_config()` with tmp config file, env var overrides
   - `tests/test_keyboard_listener.py` — test `key_name_to_pynput()` and `pynput_key_to_name()` round-trips

4. Add `pytest.ini` or `[tool.pytest.ini_options]` section to `pyproject.toml`:
   ```toml
   [tool.pytest.ini_options]
   testpaths = ["tests"]
   ```

5. Hardware-dependent classes (`AudioRecorder`, `Transcriber`, `TextOutput`) require `unittest.mock.patch` or `pytest-mock` to mock at the boundary (`sd.InputStream`, `WhisperModel`, `subprocess.run`).

---

*Testing analysis: 2026-03-09*
