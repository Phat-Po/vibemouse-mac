"""Unit tests for whisperkey_mac.ax_detect — DET-01 and DET-02.

All AX API calls are mocked — no real Accessibility permission required.
Tests cover: text input roles (True), non-text roles (False),
AX error codes (False), and exceptions (False).
"""
import unittest.mock

import pytest

from whisperkey_mac.ax_detect import is_cursor_in_text_field


def _make_ax_patch(focused_return, role_return=None):
    """Helper: build side_effect list for AXUIElementCopyAttributeValue mock.

    focused_return: (err_code, element_or_None) for the focused element query
    role_return: (err_code, role_str_or_None) for the role query (None = not called)
    """
    if role_return is None:
        return [focused_return]
    return [focused_return, role_return]


class TestTextInputRoles:
    """DET-01: is_cursor_in_text_field() returns True for all text input roles."""

    @pytest.mark.parametrize("role", ["AXTextField", "AXTextArea", "AXComboBox", "AXSearchField"])
    def test_text_input_roles(self, role):
        """Returns True when focused element has a text input role."""
        mock_element = unittest.mock.MagicMock()
        with (
            unittest.mock.patch("whisperkey_mac.ax_detect.AXUIElementCreateSystemWide") as mock_sw,
            unittest.mock.patch(
                "whisperkey_mac.ax_detect.AXUIElementCopyAttributeValue",
                side_effect=[(0, mock_element), (0, role)],
            ),
        ):
            mock_sw.return_value = unittest.mock.MagicMock()
            result = is_cursor_in_text_field()
        assert result is True, f"Expected True for role {role!r}"


class TestNonTextRoles:
    """DET-01: is_cursor_in_text_field() returns False for non-text roles."""

    @pytest.mark.parametrize("role", ["AXButton", "AXWindow"])
    def test_non_text_roles(self, role):
        """Returns False when focused element has a non-text role."""
        mock_element = unittest.mock.MagicMock()
        with (
            unittest.mock.patch("whisperkey_mac.ax_detect.AXUIElementCreateSystemWide") as mock_sw,
            unittest.mock.patch(
                "whisperkey_mac.ax_detect.AXUIElementCopyAttributeValue",
                side_effect=[(0, mock_element), (0, role)],
            ),
        ):
            mock_sw.return_value = unittest.mock.MagicMock()
            result = is_cursor_in_text_field()
        assert result is False, f"Expected False for role {role!r}"


def test_ax_error_returns_false():
    """DET-02: Returns False when AXUIElementCopyAttributeValue returns non-zero error code for focused element."""
    with (
        unittest.mock.patch("whisperkey_mac.ax_detect.AXUIElementCreateSystemWide") as mock_sw,
        unittest.mock.patch(
            "whisperkey_mac.ax_detect.AXUIElementCopyAttributeValue",
            return_value=(-25211, None),  # kAXErrorAPIDisabled
        ),
    ):
        mock_sw.return_value = unittest.mock.MagicMock()
        result = is_cursor_in_text_field()
    assert result is False


def test_ax_exception_returns_false():
    """DET-02: Returns False when AXUIElementCreateSystemWide raises an exception."""
    with unittest.mock.patch(
        "whisperkey_mac.ax_detect.AXUIElementCreateSystemWide",
        side_effect=RuntimeError("AX not available"),
    ):
        result = is_cursor_in_text_field()
    assert result is False
