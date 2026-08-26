"""Mono runtime bridge for interacting with Unity's MonoBleedingEdge runtime."""

import os
import struct
from typing import Dict, Optional, Sequence, Tuple
import pefile
import pymem
import pymem.process

from .remote import RemoteExecutor


class MonoBridge:
    """Dissects and interacts with Unity Mono runtime inside the target process."""

    # MonoTypeEnum values from Mono's metadata API.  Keeping the byte type here
    # avoids confusing one-parameter overloads such as GetSpawnable(string)
    # and GetSpawnable(byte).
    MONO_TYPE_U1 = 0x05

    def __init__(self, pm: pymem.Pymem, mono_module_name: str = "mono-2.0-bdwgc.dll"):
        self.pm = pm
        self.mono_module_name = mono_module_name
        self.mono_module = pymem.process.module_from_name(pm.process_handle, mono_module_name)
        if not self.mono_module:
            raise RuntimeError(f"Could not find {mono_module_name} in target process.")

        self.module_base = self.mono_module.lpBaseOfDll
        self.executor = RemoteExecutor(pm)
        self.exports: Dict[str, int] = {}
        self._load_exports()

        # Cache root domain and configure remote executor auto-attachment
        self.root_domain: Optional[int] = None
        self.images: Dict[str, int] = {}
        self.classes: Dict[Tuple[str, str, str], int] = {}
        self._initialize_mono()

    def _load_exports(self) -> None:
        """Parses exports from the local Mono DLL to compute remote virtual addresses."""
        mono_path = None
        candidates = [
            r"D:\SteamLibrary\steamapps\common\How to Fish\How to Fish\MonoBleedingEdge\EmbedRuntime\mono-2.0-bdwgc.dll",
        ]
        for c in candidates:
            if os.path.exists(c):
                mono_path = c
                break

        if mono_path and os.path.exists(mono_path):
            pe = pefile.PE(mono_path)
            if hasattr(pe, "DIRECTORY_ENTRY_EXPORT"):
                for exp in pe.DIRECTORY_ENTRY_EXPORT.symbols:
                    if exp.name:
                        name = exp.name.decode("utf-8")
                        self.exports[name] = self.module_base + exp.address
        else:
            self._load_exports_from_memory()

    def _load_exports_from_memory(self) -> None:
        """Parses PE export directory directly from remote module memory."""
        e_lfanew = self.pm.read_int(self.module_base + 0x3C)
        nt_headers = self.module_base + e_lfanew
        export_rva = self.pm.read_uint(nt_headers + 0x88)
        if not export_rva:
            return

        export_dir = self.module_base + export_rva
        num_names = self.pm.read_uint(export_dir + 0x18)
        funcs_rva = self.pm.read_uint(export_dir + 0x1C)
        names_rva = self.pm.read_uint(export_dir + 0x20)
        ordinals_rva = self.pm.read_uint(export_dir + 0x24)

        names_table = self.module_base + names_rva
        ordinals_table = self.module_base + ordinals_rva
        funcs_table = self.module_base + funcs_rva

        for i in range(num_names):
            name_rva = self.pm.read_uint(names_table + i * 4)
            name_addr = self.module_base + name_rva
            raw_name = bytearray()
            offset = 0
            while True:
                b = self.pm.read_bytes(name_addr + offset, 1)
                if b == b"\x00" or offset > 128:
                    break
                raw_name.extend(b)
                offset += 1
            name = raw_name.decode("utf-8", errors="ignore")

            ordinal = self.pm.read_ushort(ordinals_table + i * 2)
            func_rva = self.pm.read_uint(funcs_table + ordinal * 4)
            self.exports[name] = self.module_base + func_rva

    def get_export(self, name: str) -> int:
        """Returns the virtual address of an exported Mono function."""
        addr = self.exports.get(name)
        if not addr:
            raise KeyError(f"Export {name} not found in Mono runtime.")
        return addr

    def _initialize_mono(self) -> None:
        """Initializes Mono domain context and configures executor TLS attach."""
        get_domain_fn = self.get_export("mono_get_root_domain")
        self.root_domain = self.executor.call(get_domain_fn)
        if not self.root_domain:
            raise RuntimeError("Failed to get Mono root domain.")

        attach_fn = self.get_export("mono_thread_attach")
        self.executor.set_mono_attach(self.root_domain, attach_fn)
        self.executor.call(attach_fn, self.root_domain)

    def find_image(self, assembly_name: str = "Assembly-CSharp") -> int:
        """Finds the MonoImage pointer for a loaded assembly."""
        if assembly_name in self.images:
            return self.images[assembly_name]

        # 1. First try mono_image_loaded (works for already loaded images like Assembly-CSharp)
        if "mono_image_loaded" in self.exports:
            image_loaded_fn = self.get_export("mono_image_loaded")
            str_addr = self.executor.write_string(0x1000, assembly_name)
            image_ptr = self.executor.call(image_loaded_fn, str_addr)
            if not image_ptr:
                str_addr = self.executor.write_string(0x1000, f"{assembly_name}.dll")
                image_ptr = self.executor.call(image_loaded_fn, str_addr)
            if image_ptr:
                self.images[assembly_name] = image_ptr
                return image_ptr

        # 2. Fallback to mono_domain_assembly_open
        dom_open_fn = self.get_export("mono_domain_assembly_open")
        get_image_fn = self.get_export("mono_assembly_get_image")

        str_addr = self.executor.write_string(0x1000, assembly_name)
        assembly_ptr = self.executor.call(dom_open_fn, self.root_domain, str_addr)
        if not assembly_ptr:
            str_addr = self.executor.write_string(0x1000, f"{assembly_name}.dll")
            assembly_ptr = self.executor.call(dom_open_fn, self.root_domain, str_addr)

        if not assembly_ptr:
            raise RuntimeError(f"Could not find or open assembly '{assembly_name}'")

        image_ptr = self.executor.call(get_image_fn, assembly_ptr)
        if not image_ptr:
            raise RuntimeError(f"Could not get image from assembly '{assembly_name}'")

        self.images[assembly_name] = image_ptr
        return image_ptr

    def find_class(self, assembly_name: str, class_name: str, namespace: str = "") -> int:
        """Finds a MonoClass pointer in the specified assembly image."""
        key = (assembly_name, namespace, class_name)
        if key in self.classes:
            return self.classes[key]

        image_ptr = self.find_image(assembly_name)
        class_from_name_fn = self.get_export("mono_class_from_name")

        ns_addr = self.executor.write_string(0x1100, namespace)
        name_addr = self.executor.write_string(0x1200, class_name)

        class_ptr = self.executor.call(class_from_name_fn, image_ptr, ns_addr, name_addr)
        if not class_ptr:
            raise RuntimeError(f"Class '{namespace}.{class_name}' not found in {assembly_name}")

        self.classes[key] = class_ptr
        return class_ptr

    def find_method(self, class_ptr: int, method_name: str, param_count: int = -1) -> int:
        """Finds a MonoMethod pointer on a class."""
        get_method_fn = self.get_export("mono_class_get_method_from_name")
        name_addr = self.executor.write_string(0x1300, method_name)

        method_ptr = self.executor.call(get_method_fn, class_ptr, name_addr, param_count)
        if not method_ptr:
            raise RuntimeError(f"Method '{method_name}' (params: {param_count}) not found on class 0x{class_ptr:X}")

        return method_ptr

    def _read_utf8_c_string(self, address: int, max_bytes: int = 512) -> str:
        """Reads a bounded null-terminated UTF-8 string from the target."""
        if not address:
            return ""
        if max_bytes <= 0:
            raise ValueError("max_bytes must be greater than zero.")

        raw = bytearray()
        for offset in range(max_bytes):
            value = self.pm.read_bytes(address + offset, 1)
            if value == b"\x00":
                return raw.decode("utf-8", errors="replace")
            raw.extend(value)
        raise ValueError(
            f"Remote UTF-8 string at 0x{address:X} exceeds {max_bytes} bytes."
        )

    def find_method_by_signature(
        self,
        class_ptr: int,
        method_name: str,
        param_type_codes: Sequence[int],
    ) -> int:
        """Finds a Mono method by name and exact ``MonoTypeEnum`` parameters.

        ``mono_class_get_method_from_name`` only distinguishes overloads by
        parameter count.  This iterator additionally inspects every parameter
        type so same-count overloads cannot be selected accidentally.
        """
        if not self.executor.scratch_base:
            raise RuntimeError("Scratch buffer is not allocated.")

        expected_types = tuple(int(code) for code in param_type_codes)
        get_methods_fn = self.get_export("mono_class_get_methods")
        get_name_fn = self.get_export("mono_method_get_name")
        get_signature_fn = self.get_export("mono_method_signature")
        get_param_count_fn = self.get_export("mono_signature_get_param_count")
        get_params_fn = self.get_export("mono_signature_get_params")
        get_type_fn = self.get_export("mono_type_get_type")

        method_iter_addr = self.executor.scratch_base + 0x1600
        param_iter_addr = self.executor.scratch_base + 0x1608
        self.pm.write_ulonglong(method_iter_addr, 0)

        while True:
            method_ptr = self.executor.call(
                get_methods_fn, class_ptr, method_iter_addr
            )
            if not method_ptr:
                break

            name_ptr = self.executor.call(get_name_fn, method_ptr)
            if self._read_utf8_c_string(name_ptr) != method_name:
                continue

            signature_ptr = self.executor.call(get_signature_fn, method_ptr)
            if not signature_ptr:
                continue
            param_count = int(
                self.executor.call(get_param_count_fn, signature_ptr)
            )
            if param_count != len(expected_types):
                continue

            self.pm.write_ulonglong(param_iter_addr, 0)
            actual_types = []
            for _ in range(param_count):
                type_ptr = self.executor.call(
                    get_params_fn, signature_ptr, param_iter_addr
                )
                if not type_ptr:
                    actual_types = []
                    break
                actual_types.append(int(self.executor.call(get_type_fn, type_ptr)))

            if tuple(actual_types) == expected_types:
                return method_ptr

        signature = ", ".join(f"0x{code:02X}" for code in expected_types)
        raise RuntimeError(
            f"Method '{method_name}' (types: [{signature}]) not found "
            f"on class 0x{class_ptr:X}"
        )

    def compile_method(self, method_ptr: int) -> int:
        """JIT compiles a Mono method and returns its native code entry point."""
        compile_fn = self.get_export("mono_compile_method")
        native_code_ptr = self.executor.call(compile_fn, method_ptr)
        if not native_code_ptr:
            raise RuntimeError(f"Failed to JIT compile method 0x{method_ptr:X}")
        return native_code_ptr

    def get_static_field_data_addr(self, class_ptr: int) -> int:
        """Returns the base address of static field data for a class."""
        vtable_fn = self.get_export("mono_class_vtable")
        static_data_fn = self.get_export("mono_vtable_get_static_field_data")

        vtable = self.executor.call(vtable_fn, self.root_domain, class_ptr)
        if not vtable:
            raise RuntimeError(f"Failed to get vtable for class 0x{class_ptr:X}")

        static_data = self.executor.call(static_data_fn, vtable)
        if not static_data:
            raise RuntimeError(f"Failed to get static field data for vtable 0x{vtable:X}")

        return static_data

    def get_field_offset(self, class_ptr: int, field_name: str) -> int:
        """Returns the memory offset of a field in a class."""
        get_field_fn = self.get_export("mono_class_get_field_from_name")
        get_offset_fn = self.get_export("mono_field_get_offset")

        name_addr = self.executor.write_string(0x1400, field_name)
        field_ptr = self.executor.call(get_field_fn, class_ptr, name_addr)
        if not field_ptr:
            raise RuntimeError(f"Field '{field_name}' not found on class 0x{class_ptr:X}")

        offset = self.executor.call(get_offset_fn, field_ptr)
        return offset

    def create_string(self, text: str, scratch_offset: int = 0x1800) -> int:
        """Creates a managed ``System.String`` in the target Mono domain.

        ``mono_string_new`` expects UTF-8 input and returns a managed object
        owned by Mono's GC.  The remote call still goes through
        :class:`RemoteExecutor`, so the worker thread is attached to Mono TLS
        before entering the runtime.
        """
        if not isinstance(text, str):
            raise TypeError("Mono strings can only be created from str values.")
        if not self.root_domain:
            raise RuntimeError("Mono root domain is not initialized.")

        utf8_addr = self.executor.write_string(scratch_offset, text)
        string_ptr = self.executor.call(
            self.get_export("mono_string_new"), self.root_domain, utf8_addr
        )
        if not string_ptr:
            raise RuntimeError("mono_string_new returned a null string pointer.")
        return string_ptr

    def pin_object(self, object_ptr: int) -> int:
        """Pins a managed object until :meth:`free_gchandle` is called."""
        if not object_ptr:
            raise ValueError("Cannot pin a null managed object pointer.")
        handle = self.executor.call(
            self.get_export("mono_gchandle_new"), object_ptr, 1
        )
        if not handle:
            raise RuntimeError("mono_gchandle_new returned an invalid handle.")
        return int(handle)

    def free_gchandle(self, handle: int) -> None:
        """Releases a managed GC handle created by :meth:`pin_object`."""
        if handle:
            self.executor.call(self.get_export("mono_gchandle_free"), handle)

    def read_string(self, string_ptr: int, max_chars: int = 4096) -> str:
        """Reads a managed Mono string using its UTF-16 character buffer."""
        if not string_ptr:
            return ""
        if max_chars <= 0:
            raise ValueError("max_chars must be greater than zero.")

        length = self.executor.call(self.get_export("mono_string_length"), string_ptr)
        if length > max_chars:
            raise ValueError(
                f"Managed string length {length} exceeds safety limit {max_chars}."
            )
        if length == 0:
            return ""

        chars_ptr = self.executor.call(self.get_export("mono_string_chars"), string_ptr)
        if not chars_ptr:
            raise RuntimeError("mono_string_chars returned a null character pointer.")

        raw = self.pm.read_bytes(chars_ptr, int(length) * 2)
        return raw.decode("utf-16-le", errors="replace")

    def close(self) -> None:
        """Cleans up remote allocations."""
        self.executor.close()
