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


def test_find_method_by_signature_disambiguates_same_count_overloads():
    bridge = MonoBridge.__new__(MonoBridge)
    bridge.exports = {
        "mono_class_get_methods": 0x100,
        "mono_method_get_name": 0x200,
        "mono_method_signature": 0x300,
        "mono_signature_get_param_count": 0x400,
        "mono_signature_get_params": 0x500,
        "mono_type_get_type": 0x600,
    }
    bridge.executor = MagicMock()
    bridge.executor.scratch_base = 0x10000
    bridge.pm = MagicMock()
    bridge._read_utf8_c_string = MagicMock(return_value="GetSpawnable")

    methods = iter([0xA000, 0xB000])

    def call(func, *args):
        if func == 0x100:
            return next(methods)
        if func == 0x200:
            return {0xA000: 0xA100, 0xB000: 0xB100}[args[0]]
        if func == 0x300:
            return {0xA000: 0xA200, 0xB000: 0xB200}[args[0]]
        if func == 0x400:
            return 1
        if func == 0x500:
            return {0xA200: 0xA300, 0xB200: 0xB300}[args[0]]
        if func == 0x600:
            return {0xA300: 0x0E, 0xB300: MonoBridge.MONO_TYPE_U1}[args[0]]
        raise AssertionError((func, args))

    bridge.executor.call.side_effect = call

    assert bridge.find_method_by_signature(
        0x9000, "GetSpawnable", (MonoBridge.MONO_TYPE_U1,)
    ) == 0xB000
    assert bridge.pm.write_ulonglong.call_count == 3


def test_managed_object_gc_handle_is_pinned_and_released():
    bridge = MonoBridge.__new__(MonoBridge)
    bridge.exports = {
        "mono_gchandle_new": 0x700,
        "mono_gchandle_free": 0x800,
    }
    bridge.executor = MagicMock()
    bridge.executor.call.side_effect = [0x123, 0]

    assert bridge.pin_object(0xCAFE) == 0x123
    bridge.free_gchandle(0x123)
    assert bridge.executor.call.call_args_list == [
        ((0x700, 0xCAFE, 1),),
        ((0x800, 0x123),),
    ]
