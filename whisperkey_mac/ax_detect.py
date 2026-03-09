"""AX cursor detection module for WhisperKey macOS.

Provides:
- is_cursor_in_text_field(): returns True if the currently focused macOS UI element
  is a text input field (AXTextField, AXTextArea, AXComboBox, AXSearchField).

Thread-safe: AXUIElement APIs are safe to call from non-main threads.
Failure-safe: any exception or AX error returns False (DET-02 safe-degradation).

IMPORTANT: macOS requires Accessibility permission (System Settings -> Privacy & Security ->
Accessibility) for this to return True. If permission is denied, kAXErrorAPIDisabled (-25211)
is returned and this function returns False, falling back to the clipboard path. This is
correct per DET-02 — no crash, just clipboard-path degradation.

NOTE: kAXSearchFieldRole does NOT exist as an importable constant in PyObjC 12.1.
The package exports kAXSearchFieldSubrole with the same value 'AXSearchField'.
The string literal 'AXSearchField' is used directly in _TEXT_INPUT_ROLES instead.
"""
from ApplicationServices import (
    AXUIElementCreateSystemWide,
    AXUIElementCopyAttributeValue,
    kAXFocusedUIElementAttribute,  # 'AXFocusedUIElement'
    kAXRoleAttribute,              # 'AXRole'
    kAXTextFieldRole,              # 'AXTextField'
    kAXTextAreaRole,               # 'AXTextArea'
    kAXComboBoxRole,               # 'AXComboBox'
    kAXErrorSuccess,               # 0
    # NOTE: kAXSearchFieldRole does NOT exist — verified ImportError in .venv Python 3.12 + PyObjC 12.1
    # kAXSearchFieldSubrole == 'AXSearchField'; use string literal directly
)

_TEXT_INPUT_ROLES: frozenset[str] = frozenset({
    kAXTextFieldRole,   # 'AXTextField'
    kAXTextAreaRole,    # 'AXTextArea'
    kAXComboBoxRole,    # 'AXComboBox'
    "AXSearchField",    # kAXSearchFieldRole doesn't exist; kAXSearchFieldSubrole == 'AXSearchField'
})


def is_cursor_in_text_field() -> bool:
    """Return True if the currently focused macOS UI element is a text input field.

    Thread-safe: AXUIElement APIs are designed for non-main-thread use.
    Failure-safe: any exception or AX error returns False (DET-02 safe-degradation).

    Returns:
        True if focused element role is AXTextField, AXTextArea, AXComboBox, or AXSearchField.
        False on any error, permission denial, exception, or non-text role.
    """
    try:
        system_wide = AXUIElementCreateSystemWide()
        # Third arg must be None (PyObjC out-parameter bridge); returns (err_code, value_or_None)
        err, focused = AXUIElementCopyAttributeValue(
            system_wide, kAXFocusedUIElementAttribute, None
        )
        if err != kAXErrorSuccess or focused is None:
            return False  # no focused element, permission denied, or API disabled
        err2, role = AXUIElementCopyAttributeValue(focused, kAXRoleAttribute, None)
        if err2 != kAXErrorSuccess or role is None:
            return False
        return role in _TEXT_INPUT_ROLES
    except Exception:
        return False  # DET-02: any failure -> clipboard path (safe degradation)
