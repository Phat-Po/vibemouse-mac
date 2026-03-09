"""Unit tests for whisperkey_mac.overlay — OVL-01, OVL-02, OVL-03 structural checks
and RST-01 through RST-04 state machine tests.

Tests verify NSPanel flags, position, transparency, dispatch_to_main wiring,
and OverlayStateMachine state transitions with mocked NSPanel.
No app.run() is called — panel is created and inspected directly.
"""
import unittest.mock

import pytest
from AppKit import (
    NSApplicationActivationPolicyAccessory,
    NSApplication,
    NSFloatingWindowLevel,
    NSWindowCollectionBehaviorCanJoinAllSpaces,
    NSWindowCollectionBehaviorStationary,
    NSWindowCollectionBehaviorFullScreenAuxiliary,
    NSScreen,
)

from whisperkey_mac.overlay import OverlayPanel, OverlayState, OverlayStateMachine, dispatch_to_main


@pytest.fixture(scope="module")
def panel():
    """Create an OverlayPanel instance once per module and return its underlying NSPanel."""
    overlay = OverlayPanel.create()
    return overlay._panel


def test_panel_flags(panel):
    """OVL-01: Verify all NSPanel structural flags are set correctly."""
    assert panel.isOpaque() is False, "Panel must not be opaque"
    assert panel.hasShadow() is False, "Panel must have no shadow"
    assert panel.ignoresMouseEvents() is True, "Panel must be click-through"
    assert panel.level() == NSFloatingWindowLevel, (
        f"Panel level must be NSFloatingWindowLevel ({NSFloatingWindowLevel}), got {panel.level()}"
    )
    assert panel.styleMask() & 128 == 128, (
        f"Style mask must have NSWindowStyleMaskNonactivatingPanel (128) bit set, got {panel.styleMask()}"
    )


def test_panel_position(panel):
    """OVL-02: Verify panel frame is at bottom-center of main screen with correct dimensions."""
    frame = panel.frame()
    screen = NSScreen.mainScreen()
    screen_width = screen.frame().size.width

    assert frame.size.width == 280.0, f"Panel width must be 280, got {frame.size.width}"
    assert frame.size.height == 56.0, f"Panel height must be 56, got {frame.size.height}"
    assert frame.origin.y == 40.0, f"Panel y must be 40.0 (bottom margin), got {frame.origin.y}"

    expected_x = (screen_width - 280) / 2
    assert abs(frame.origin.x - expected_x) <= 1.0, (
        f"Panel x must be within 1px of {expected_x} (centered), got {frame.origin.x}"
    )


def test_panel_invisible(panel):
    """OVL-02: Verify panel is fully invisible (alpha=0.0) in Phase 1."""
    assert panel.alphaValue() == 0.0, f"Panel alphaValue must be 0.0, got {panel.alphaValue()}"


def test_activation_policy():
    """OVL-03: Verify NSApplication activation policy is Accessory (no Dock icon, no focus steal)."""
    app = NSApplication.sharedApplication()
    policy = app.activationPolicy()
    assert policy == NSApplicationActivationPolicyAccessory, (
        f"Activation policy must be NSApplicationActivationPolicyAccessory (1), got {policy}"
    )


def test_collection_behavior(panel):
    """OVL-03: Verify panel collection behavior includes all three required flags."""
    behavior = panel.collectionBehavior()

    assert behavior & NSWindowCollectionBehaviorCanJoinAllSpaces != 0, (
        "NSWindowCollectionBehaviorCanJoinAllSpaces (1) must be set"
    )
    assert behavior & NSWindowCollectionBehaviorStationary != 0, (
        "NSWindowCollectionBehaviorStationary (16) must be set"
    )
    assert behavior & NSWindowCollectionBehaviorFullScreenAuxiliary != 0, (
        "NSWindowCollectionBehaviorFullScreenAuxiliary (256) must be set"
    )


def test_dispatch_to_main():
    """Verify dispatch_to_main() wraps callAfter() correctly without calling app.run()."""
    sentinel = object()
    arg1 = "test_arg"

    # Patch the name as it lives in overlay.py after `from PyObjCTools.AppHelper import callAfter`
    with unittest.mock.patch("whisperkey_mac.overlay.callAfter") as mock_call_after:
        dispatch_to_main(sentinel, arg1)
        mock_call_after.assert_called_once_with(sentinel, arg1)


# ---------------------------------------------------------------------------
# State Machine Tests (RST-01 through RST-04, transition guard)
# ---------------------------------------------------------------------------

@pytest.fixture
def sm():
    """Create an OverlayStateMachine with mocked NSPanel, label, sublabel.

    Patches callLater at the overlay module level so no NSRunLoop is needed.
    Returns (state_machine, mock_panel, mock_label, mock_sublabel).
    """
    mock_panel = unittest.mock.MagicMock()
    mock_label = unittest.mock.MagicMock()
    mock_sublabel = unittest.mock.MagicMock()
    machine = OverlayStateMachine(mock_panel, mock_label, mock_sublabel)
    return machine, mock_panel, mock_label, mock_sublabel


def test_show_recording_transitions_to_recording(sm):
    """RST-01: show_recording() from HIDDEN transitions state to RECORDING."""
    machine, mock_panel, mock_label, mock_sublabel = sm
    assert machine._state == OverlayState.HIDDEN
    with unittest.mock.patch("whisperkey_mac.overlay.callLater"):
        machine.show_recording()
    assert machine._state == OverlayState.RECORDING


def test_show_transcribing_transitions(sm):
    """RST-01: show_transcribing() after show_recording() transitions to TRANSCRIBING."""
    machine, mock_panel, mock_label, mock_sublabel = sm
    with unittest.mock.patch("whisperkey_mac.overlay.callLater"):
        machine.show_recording()
        machine.show_transcribing()
    assert machine._state == OverlayState.TRANSCRIBING


def test_hide_after_paste(sm):
    """RST-01: hide_after_paste() from TRANSCRIBING forces state to HIDDEN and calls orderOut_."""
    machine, mock_panel, mock_label, mock_sublabel = sm
    with unittest.mock.patch("whisperkey_mac.overlay.callLater"):
        machine.show_recording()
        machine.show_transcribing()
        machine.hide_after_paste()
    assert machine._state == OverlayState.HIDDEN
    mock_panel.orderOut_.assert_called()


def test_show_result_sets_label(sm):
    """RST-02: show_result(text) sets the primary label to the transcribed text."""
    machine, mock_panel, mock_label, mock_sublabel = sm
    with unittest.mock.patch("whisperkey_mac.overlay.callLater"):
        machine.show_recording()
        machine.show_transcribing()
        machine.show_result("hello")
    mock_label.setStringValue_.assert_called_with("hello")


def test_show_result_clipboard_hint(sm):
    """RST-03: show_result() sets secondary label to '已复制到剪贴板'."""
    machine, mock_panel, mock_label, mock_sublabel = sm
    with unittest.mock.patch("whisperkey_mac.overlay.callLater"):
        machine.show_recording()
        machine.show_transcribing()
        machine.show_result("hello")
    mock_sublabel.setStringValue_.assert_called_with("已复制到剪贴板")


def test_auto_dismiss_fires(sm):
    """RST-04: _auto_dismiss(gen=current gen) from RESULT state transitions to HIDDEN."""
    machine, mock_panel, mock_label, mock_sublabel = sm
    with unittest.mock.patch("whisperkey_mac.overlay.callLater"):
        machine.show_recording()
        machine.show_transcribing()
        machine.show_result("test")
    assert machine._state == OverlayState.RESULT
    current_gen = machine._dismiss_gen
    machine._auto_dismiss(current_gen)
    assert machine._state == OverlayState.HIDDEN


def test_auto_dismiss_stale_ignored(sm):
    """RST-04: _auto_dismiss(gen=stale) does not change state from RESULT."""
    machine, mock_panel, mock_label, mock_sublabel = sm
    with unittest.mock.patch("whisperkey_mac.overlay.callLater"):
        machine.show_recording()
        machine.show_transcribing()
        machine.show_result("test")
    assert machine._state == OverlayState.RESULT
    stale_gen = machine._dismiss_gen - 1
    machine._auto_dismiss(stale_gen)
    assert machine._state == OverlayState.RESULT


def test_transition_guard_rejects_invalid(sm):
    """Transition guard: calling show_recording() twice keeps state at RECORDING (no corruption)."""
    machine, mock_panel, mock_label, mock_sublabel = sm
    with unittest.mock.patch("whisperkey_mac.overlay.callLater"):
        machine.show_recording()
        assert machine._state == OverlayState.RECORDING
        machine.show_recording()  # second call while RECORDING — should be rejected
    assert machine._state == OverlayState.RECORDING
