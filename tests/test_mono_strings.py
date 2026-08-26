"""Tests for bounded remote and managed Mono string helpers."""

from unittest.mock import MagicMock

import pytest

from howtofish_cheat.mono.bridge import MonoBridge
from howtofish_cheat.mono.remote import RemoteExecutor


def test_remote_write_string_enforces_scratch_bounds():
    executor = RemoteExecutor.__new__(RemoteExecutor)
    executor.pm = MagicMock()
    executor.scratch_base = 0x1000
    executor.scratch_size = 8

    assert executor.write_string(2, "abc") == 0x1002
    executor.pm.write_bytes.assert_called_once_with(0x1002, b"abc\x00", 4)

    with pytest.raises(ValueError):
        executor.write_string(6, "abc")


def test_create_managed_string_uses_root_domain_and_utf8_buffer():
    bridge = MonoBridge.__new__(MonoBridge)
    bridge.root_domain = 0x1111
    bridge.exports = {"mono_string_new": 0x2222}
    bridge.executor = MagicMock()
    bridge.executor.write_string.return_value = 0x3333
    bridge.executor.call.return_value = 0x4444

    assert bridge.create_string("鲨鱼") == 0x4444
    bridge.executor.write_string.assert_called_once_with(0x1800, "鲨鱼")
    bridge.executor.call.assert_called_once_with(0x2222, 0x1111, 0x3333)


def test_read_managed_string_decodes_utf16_and_checks_limit():
    bridge = MonoBridge.__new__(MonoBridge)
    bridge.exports = {
        "mono_string_length": 0x100,
        "mono_string_chars": 0x200,
    }
    bridge.executor = MagicMock()
    bridge.pm = MagicMock()
    encoded = "测试鱼".encode("utf-16-le")

    def call(func, *args):
        if func == 0x100:
            return 3
        if func == 0x200:
            return 0x5000
        raise AssertionError(func)

    bridge.executor.call.side_effect = call
    bridge.pm.read_bytes.return_value = encoded
    assert bridge.read_string(0x1234) == "测试鱼"
    bridge.pm.read_bytes.assert_called_once_with(0x5000, 6)

    with pytest.raises(ValueError):
        bridge.read_string(0x1234, max_chars=2)
