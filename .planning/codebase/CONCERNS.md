# Codebase Concerns

**Analysis Date:** 2026-03-09

## Tech Debt

**Orphaned package name (project renamed):**
- Issue: The project directory is named `vibemouse-mac` but the package is `whisperkey-mac` / `whisperkey_mac`. Two stale egg-info directories exist: `whisperkey_mac.egg-info/` and `whisperkey_mac.egg-info/` alongside an older `whisperkey_mac.egg-info/`. There is also a `whisperkey_mac.egg-info/` alongside `whisperkey_mac.egg-info/` directory (the old `whisperkey_mac` one is still present at root).
- Files: `vibemouse_mac.egg-info/` (entire directory), `whisperkey_mac.egg-info/` (entire directory)
- Impact: Confusing install state; `pip install -e .` could leave stale metadata; `pip show vibemouse-mac` and `pip show whisperkey-mac` may both appear to be installed
- Fix approach: Delete `vibemouse_mac.egg-info/` entirely. Confirm only `whisperkey_mac.egg-info/` remains and matches `pyproject.toml` name `whisperkey-mac`.

**Legacy config fields never used:**
- Issue: `AppConfig` contains four fields (`record_button`, `enter_button`, `enter_mode`, `record_hotkey`, `enter_hotkey`) marked `# ── Legacy ──`. They are serialized into every `config.json` via `to_dict()` but no code path in the active codebase reads `record_button`, `enter_button`, `record_hotkey`, or `enter_hotkey` for any functional purpose.
- Files: `whisperkey_mac/config.py` (lines 47-51), `whisperkey_mac/output.py` (reads `enter_mode` only)
- Impact: Every saved config grows with dead keys; any future rename/remove will silently corrupt configs that loaded them; `MouseListener` in `mouse_listener.py` is defined but never instantiated anywhere in `main.py`.
- Fix approach: Remove legacy fields from `AppConfig` or migrate them behind a migration shim in `load_config()`. Remove or wire up `MouseListener` — it is currently dead code.

**`MouseListener` is unreachable dead code:**
- Issue: `whisperkey_mac/mouse_listener.py` defines a fully functional `MouseListener` class but `main.py` never imports or instantiates it. The `App` class only sets up `HotkeyListener`.
- Files: `whisperkey_mac/mouse_listener.py`, `whisperkey_mac/main.py`
- Impact: Mouse-button functionality is silently unavailable; the code carries maintenance cost for nothing; new contributors may assume it is wired.
- Fix approach: Either wire `MouseListener` into `App.__init__()` alongside `HotkeyListener`, or delete `mouse_listener.py` and the legacy `record_button`/`enter_button` config fields.

**Silent config load failure swallows all errors:**
- Issue: In `load_config()`, the entire JSON parse + field assignment block is wrapped in a bare `except Exception: pass`.
- Files: `whisperkey_mac/config.py` (lines 69-79)
- Impact: Any corrupt or partially written `~/.config/whisperkey/config.json` silently falls back to defaults with no user warning. Users will be confused when their saved settings disappear.
- Fix approach: At minimum log a warning to stderr; ideally surface a structured error message and prompt the user to run `whisperkey setup` again.

**No dependency version pinning (lockfile absent):**
- Issue: `pyproject.toml` specifies only minimum versions (`>=`) with no upper bounds and no `requirements.lock` / `pip.lock`. The `.venv` at runtime pins actual versions, but nothing is committed.
- Files: `pyproject.toml`
- Impact: `pip install -e .` on a fresh machine may pull in a breaking major version of `faster-whisper`, `pynput`, or `numpy` at any future date.
- Fix approach: Generate and commit a `requirements.lock` (via `pip freeze > requirements.lock`) or add it to the GitHub Actions / install docs. Consider adding upper bounds for the most volatile deps (`faster-whisper<2.0`, `pynput<2.0`).

**`enter_mode` default is `"enter"` but it is a legacy field:**
- Issue: `AppConfig.enter_mode` defaults to `"enter"` and is read by `TextOutput.send_enter()`. However `on_enter` callback is wired only from `HotkeyListener`'s `on_enter` parameter in `App.__init__()`, which is never triggered — `HotkeyListener` has no mechanism to fire `on_enter` from any keyboard event. The `detect()` and `send_enter()` code exists but is unreachable.
- Files: `whisperkey_mac/main.py` (line 29), `whisperkey_mac/keyboard_listener.py`, `whisperkey_mac/output.py` (lines 41-71)
- Impact: The Enter-sending feature is silently non-functional for keyboard hotkeys.
- Fix approach: Either remove `on_enter` from `HotkeyListener` and `App`, or implement the key binding that triggers it.

## Known Bugs

**Transcriber `language` config field may conflict with env var:**
- Symptoms: If `WHISPERKEY_LANGUAGE` is set as an env var and `config.json` also has `transcribe_language != "auto"`, the env var wins but `transcribe_language` (the human-readable label) is never updated. The ready message will display the wrong language label.
- Files: `whisperkey_mac/config.py` (lines 81-101)
- Trigger: Set `WHISPERKEY_LANGUAGE=en` env var while `config.json` has `transcribe_language: "zh"`. The banner prints "语言: zh" but Whisper transcribes English.
- Workaround: None currently.

**`_check_input_monitoring()` monkey-patches `sys.stderr.write` unsafely:**
- Symptoms: If the function raises unexpectedly mid-intercept (e.g. pynput import failure), `sys.stderr.write` may be left replaced with the `intercept` closure even after the `finally` block.
- Files: `whisperkey_mac/help_cmd.py` (lines 54-86)
- Trigger: Import-level error in pynput during `whisperkey help`.
- Workaround: The `finally` block does restore it, but if the assignment itself raises an exception the restoration is skipped.

**`_on_press` race condition in `HotkeyListener`:**
- Symptoms: `timer` variable referenced in the `if mode == "idle": timer.start()` branch (line 142) is assigned inside a `with self._lock` block, but the `timer.start()` call happens outside the lock with a local copy. If another thread calls `stop()` between the lock release and `timer.start()`, the already-cancelled timer is started anyway, leading to a phantom `_start_hold_recording` call.
- Files: `whisperkey_mac/keyboard_listener.py` (lines 136-142)
- Trigger: Very fast press/release of hold key coinciding with app shutdown.
- Workaround: Low probability in normal use.

## Security Considerations

**AppleScript execution with user-controlled text (indirect):**
- Risk: `TextOutput._paste_clipboard()` calls `osascript` via `subprocess.run` with a fixed AppleScript string. The transcribed text itself goes only via `pyperclip.copy()` (clipboard), not into the AppleScript string — so there is no shell injection from transcription output. Risk is low.
- Files: `whisperkey_mac/output.py` (lines 52-58)
- Current mitigation: The AppleScript payload is a hardcoded literal, not constructed from user input.
- Recommendations: No action needed for current implementation. If the AppleScript string is ever templated with transcription results, sanitization would be required.

**Config file written as world-readable JSON:**
- Risk: `~/.config/whisperkey/config.json` is created by `save_config()` with default `open()` permissions (typically `0o644`), readable by all local users. The config holds no secrets currently, but any future addition of API keys or tokens would leak them.
- Files: `whisperkey_mac/config.py` (line 108)
- Current mitigation: No secrets stored today.
- Recommendations: Set file mode to `0o600` when writing config: `CONFIG_PATH.write_text(...); CONFIG_PATH.chmod(0o600)`.

## Performance Bottlenecks

**Model load blocks startup preload thread on first install:**
- Problem: `WhisperModel(...)` downloads the model from HuggingFace on first use, inside the preload thread. The download can take minutes for `large-v3-turbo` (~1.5 GB). During this time, hotkey callbacks are registered and may be triggered, but transcription attempts will block on `self._lock` inside `_ensure_loaded()`.
- Files: `whisperkey_mac/transcriber.py` (lines 41-56), `whisperkey_mac/main.py` (line 38)
- Cause: `faster_whisper.WhisperModel` calls HuggingFace Hub download transparently on first instantiation.
- Improvement path: Print a clear "Downloading model, this may take several minutes..." message before entering the `WhisperModel(...)` call. The preload thread is already daemon=True so it does not block shutdown.

**`_paste_clipboard()` adds a fixed 50ms sleep after every paste:**
- Problem: Every transcription incurs a mandatory `time.sleep(0.05)` regardless of app response speed.
- Files: `whisperkey_mac/output.py` (line 59)
- Cause: Guard against the receiving app not yet processing the Cmd+V event.
- Improvement path: Low priority. 50ms is imperceptible to users. Only worth revisiting if paste reliability issues appear.

**Memory grows unbounded for very long recordings:**
- Problem: `AudioRecorder._frames` accumulates raw `float32` numpy chunks for the entire recording duration with no cap. At 16000 Hz mono float32, a 10-minute recording would accumulate ~37 MB in memory before `np.concatenate` allocates another ~37 MB copy.
- Files: `whisperkey_mac/audio.py` (lines 25, 98)
- Cause: Append-only list of numpy arrays; no maximum duration enforced.
- Improvement path: Add a `max_duration_s` config field (e.g. 120s default) and stop recording automatically when exceeded.

## Fragile Areas

**`setup_wizard._python_app_path()` heuristic often returns the wrong path:**
- Files: `whisperkey_mac/setup_wizard.py` (lines 75-82)
- Why fragile: The function walks `sys.executable`'s parent chain looking for a directory ending in `.app`. In a typical `.venv` install, `sys.executable` is `.venv/bin/python` — no `.app` bundle exists in the parent chain. The function falls back to returning `sys.executable` (the raw binary path), which is not what macOS Privacy settings expects. The user is shown a venv binary path instead of a `Python.app` bundle, making the permission instructions confusing.
- Safe modification: Only change the path-resolution logic; the rest of `_step_permissions()` is stable.
- Test coverage: None.

**`_detect_combo_keys()` event logic is ambiguous:**
- Files: `whisperkey_mac/setup_wizard.py` (lines 248-286)
- Why fragile: The `event.set()` is triggered both when `len(held) >= 2` AND when all keys are released (`not held and max_combo`). The `event.wait(timeout=15)` returns on whichever fires first. If only one key is detected before timeout, `max_combo` will have only one entry and will be used silently as the hands-free combo — which will then never trigger (requires 2 keys). The fallback message does not fire because `max_combo` is non-empty.
- Safe modification: Add validation that `len(max_combo) >= 2` before accepting; otherwise print an error and retry.
- Test coverage: None.

**`transcriber.py` uses `assert` in production path:**
- Files: `whisperkey_mac/transcriber.py` (line 23)
- Why fragile: `assert self._model is not None` will raise `AssertionError` (not a user-friendly error) if Python is run with `-O` (optimize flag strips asserts). Though unlikely with a `.venv` setup, it is an anti-pattern for runtime guards.
- Safe modification: Replace with an explicit `if self._model is None: raise RuntimeError(...)`.
- Test coverage: None.

**`key_name_to_pynput()` silently falls back to `alt_r` on unrecognized key:**
- Files: `whisperkey_mac/keyboard_listener.py` (line 66)
- Why fragile: If a user's `config.json` contains a key name not in `_KEY_MAP` (e.g. `"f20"` or a typo like `"alt_right"`), `key_name_to_pynput()` returns `None` and the expression `... or keyboard.Key.alt_r` silently uses Right Option. No warning is emitted.
- Safe modification: Log a warning when the fallback fires: `print(f"[whisperkey] Unknown key '{hold_key}', defaulting to alt_r")`.
- Test coverage: None.

## Scaling Limits

**Single-threaded transcription serialized by lock:**
- Current capacity: One transcription job at a time (enforced by `self._transcribe_lock` in `main.py`).
- Limit: If the user holds the key again before the previous transcription finishes, the new job queues behind the lock. For `large-v3-turbo` on CPU this can be 10-30 seconds.
- Scaling path: Not a real concern for a personal tool; the lock prevents audio/text ordering issues.

## Dependencies at Risk

**`opencc-python-reimplemented` is an unofficial reimplementation:**
- Risk: The package `opencc-python-reimplemented` is not the official `opencc` Python binding. It is maintained by a single contributor, has no guaranteed update cadence, and may produce incorrect Traditional→Simplified conversions for edge cases.
- Impact: Transcribed Traditional Chinese text may not be fully converted, causing unexpected output.
- Migration plan: Switch to `opencc-python` (the official binding) or `hanziconv`; both are more widely maintained. Verify conversion accuracy for Cantonese (`yue`) input.

**No upper-bound pins on `faster-whisper`:**
- Risk: `faster-whisper>=1.0` will install any future `2.x` release that may break the `WhisperModel` constructor signature or `transcribe()` return shape.
- Impact: Silent breakage after `pip install --upgrade`.
- Migration plan: Pin `faster-whisper>=1.0,<2.0` in `pyproject.toml` until the v2 API is validated.

## Missing Critical Features

**No logging to file — all output is print() to stdout:**
- Problem: There is no persistent log. If `whisperkey` is run as a background service (via `WhisperKey.command` launcher), stdout is discarded. Transcription errors, model load failures, and "recording too short" events are invisible.
- Blocks: Debugging production issues for non-terminal users.

**No maximum recording duration guard:**
- Problem: A user who holds the hotkey and walks away accumulates audio indefinitely with no auto-stop.
- Blocks: Predictable memory usage; avoidance of very slow transcription on multi-minute audio.

**`whisperkey_mac.egg-info/` and `vibemouse_mac.egg-info/` both committed as stale artifacts:**
- Problem: Both egg-info directories are present on disk (though `.gitignore` lists `*.egg-info/`). If the `.gitignore` rule was added after initial `pip install -e .`, these directories may already be tracked in git history.
- Blocks: Clean installs from a fresh clone may behave differently than the current working tree.

## Test Coverage Gaps

**No tests exist anywhere in the project:**
- What's not tested: All modules — `audio.py`, `config.py`, `transcriber.py`, `keyboard_listener.py`, `output.py`, `setup_wizard.py`, `help_cmd.py`, `mouse_listener.py`
- Files: Entire `whisperkey_mac/` package
- Risk: Any refactor can silently break recording state machine, config parsing, key resolution, or text injection without detection.
- Priority: High for `config.py` (load/save roundtrip), `keyboard_listener.py` (state machine), `audio.py` (stop_and_save logic). Low for `setup_wizard.py` (interactive terminal).

---

*Concerns audit: 2026-03-09*
