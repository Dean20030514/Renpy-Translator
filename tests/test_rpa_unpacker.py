#!/usr/bin/env python3
"""Tests for tools.rpa_unpacker — RPA-3.0 and RPA-2.0 archive handling."""

import io
import os
import pickle
import sys
import tempfile
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.rpa_unpacker import (
    CorruptedArchive,
    RPAError,
    UnsupportedVersion,
    list_rpa,
    unpack_rpa,
    unpack_all_rpa_in_dir,
)


# ---------------------------------------------------------------------------
# Helpers: build synthetic RPA archives
# ---------------------------------------------------------------------------

def _build_rpa3(files: dict[str, bytes], key: int = 0xDEADBEEF) -> bytes:
    """Build a minimal RPA-3.0 archive in memory.

    Args:
        files: mapping of {filename: content_bytes}
        key: XOR obfuscation key

    Returns:
        Complete archive bytes.
    """
    buf = io.BytesIO()

    # Reserve space for the header line (will be overwritten)
    header_placeholder = b"RPA-3.0 0000000000000000 0000000000000000\n"
    buf.write(header_placeholder)

    # Write file data and build index
    index: dict[bytes, list[tuple[int, int, bytes]]] = {}
    for name, data in files.items():
        offset = buf.tell()
        buf.write(data)
        length = len(data)
        # XOR obfuscate offset and length
        index[name.encode("utf-8")] = [(offset ^ key, length ^ key, b"")]

    # Write the index
    index_offset = buf.tell()
    pickled = pickle.dumps(index, protocol=2)
    compressed = zlib.compress(pickled)
    buf.write(compressed)

    # Go back and write the real header
    header = f"RPA-3.0 {index_offset:016x} {key:016x}\n".encode("ascii")
    buf.seek(0)
    buf.write(header)

    return buf.getvalue()


def _build_rpa2(files: dict[str, bytes]) -> bytes:
    """Build a minimal RPA-2.0 archive in memory."""
    buf = io.BytesIO()

    header_placeholder = b"RPA-2.0 0000000000000000\n"
    buf.write(header_placeholder)

    index: dict[bytes, list[tuple[int, int, bytes]]] = {}
    for name, data in files.items():
        offset = buf.tell()
        buf.write(data)
        length = len(data)
        # RPA-2.0: no XOR
        index[name.encode("utf-8")] = [(offset, length, b"")]

    index_offset = buf.tell()
    pickled = pickle.dumps(index, protocol=2)
    compressed = zlib.compress(pickled)
    buf.write(compressed)

    header = f"RPA-2.0 {index_offset:016x}\n".encode("ascii")
    buf.seek(0)
    buf.write(header)

    return buf.getvalue()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_rpa3_list():
    """RPA-3.0: list files."""
    archive_data = _build_rpa3({
        "script.rpy": b'label start:\n    "Hello"\n',
        "screens.rpy": b'screen main_menu():\n    pass\n',
        "images/bg.png": b"\x89PNG\r\n\x1a\n" + b"\x00" * 16,
    })

    with tempfile.NamedTemporaryFile(suffix=".rpa", delete=False) as f:
        f.write(archive_data)
        tmp = Path(f.name)

    try:
        files = list_rpa(tmp)
        assert len(files) == 3
        assert "script.rpy" in files
        assert "screens.rpy" in files
        assert "images/bg.png" in files
        print("[OK] test_rpa3_list")
    finally:
        tmp.unlink()


def test_rpa3_extract():
    """RPA-3.0: extract files and verify content."""
    content_rpy = b'label start:\n    mc "Hello world"\n'
    content_rpyc = b"\x00RPYC_FAKE_COMPILED_DATA\x00"

    archive_data = _build_rpa3({
        "script.rpy": content_rpy,
        "compiled.rpyc": content_rpyc,
    })

    with tempfile.NamedTemporaryFile(suffix=".rpa", delete=False) as f:
        f.write(archive_data)
        tmp = Path(f.name)

    with tempfile.TemporaryDirectory() as outdir:
        outdir = Path(outdir)
        try:
            extracted = unpack_rpa(tmp, outdir)
            assert len(extracted) == 2

            # Verify content integrity
            assert (outdir / "script.rpy").read_bytes() == content_rpy
            assert (outdir / "compiled.rpyc").read_bytes() == content_rpyc
            print("[OK] test_rpa3_extract")
        finally:
            tmp.unlink()


def test_rpa3_extract_scripts_only():
    """RPA-3.0: filter by extension."""
    archive_data = _build_rpa3({
        "script.rpy": b"label start:\n",
        "compiled.rpyc": b"\x00RPYC\x00",
        "images/bg.png": b"\x89PNG",
        "audio/bgm.ogg": b"OggS",
    })

    with tempfile.NamedTemporaryFile(suffix=".rpa", delete=False) as f:
        f.write(archive_data)
        tmp = Path(f.name)

    with tempfile.TemporaryDirectory() as outdir:
        outdir = Path(outdir)
        try:
            extracted = unpack_rpa(
                tmp, outdir, filter_ext=(".rpy", ".rpyc"),
            )
            assert len(extracted) == 2
            extracted_names = {p.name for p in extracted}
            assert "script.rpy" in extracted_names
            assert "compiled.rpyc" in extracted_names
            assert not (outdir / "images" / "bg.png").exists()
            print("[OK] test_rpa3_extract_scripts_only")
        finally:
            tmp.unlink()


def test_rpa3_no_overwrite():
    """RPA-3.0: skip existing files when force=False."""
    archive_data = _build_rpa3({"script.rpy": b"new content"})

    with tempfile.NamedTemporaryFile(suffix=".rpa", delete=False) as f:
        f.write(archive_data)
        tmp = Path(f.name)

    with tempfile.TemporaryDirectory() as outdir:
        outdir = Path(outdir)
        # Pre-create the file
        (outdir / "script.rpy").write_bytes(b"old content")
        try:
            extracted = unpack_rpa(tmp, outdir, force=False)
            assert len(extracted) == 0
            assert (outdir / "script.rpy").read_bytes() == b"old content"
            print("[OK] test_rpa3_no_overwrite")
        finally:
            tmp.unlink()


def test_rpa3_force_overwrite():
    """RPA-3.0: overwrite existing files when force=True."""
    archive_data = _build_rpa3({"script.rpy": b"new content"})

    with tempfile.NamedTemporaryFile(suffix=".rpa", delete=False) as f:
        f.write(archive_data)
        tmp = Path(f.name)

    with tempfile.TemporaryDirectory() as outdir:
        outdir = Path(outdir)
        (outdir / "script.rpy").write_bytes(b"old content")
        try:
            extracted = unpack_rpa(tmp, outdir, force=True)
            assert len(extracted) == 1
            assert (outdir / "script.rpy").read_bytes() == b"new content"
            print("[OK] test_rpa3_force_overwrite")
        finally:
            tmp.unlink()


def test_rpa2_extract():
    """RPA-2.0: extract files (no XOR key)."""
    content = b'label start:\n    "RPA-2.0 test"\n'
    archive_data = _build_rpa2({"script.rpy": content})

    with tempfile.NamedTemporaryFile(suffix=".rpa", delete=False) as f:
        f.write(archive_data)
        tmp = Path(f.name)

    with tempfile.TemporaryDirectory() as outdir:
        outdir = Path(outdir)
        try:
            extracted = unpack_rpa(tmp, outdir)
            assert len(extracted) == 1
            assert (outdir / "script.rpy").read_bytes() == content
            print("[OK] test_rpa2_extract")
        finally:
            tmp.unlink()


def test_rpa3_different_keys():
    """RPA-3.0: works with different XOR keys."""
    content = b"test data with key variation"
    for key in [0, 1, 0xFFFFFFFF, 0x12345678, 0xCAFEBABE]:
        archive_data = _build_rpa3({"test.rpy": content}, key=key)
        with tempfile.NamedTemporaryFile(suffix=".rpa", delete=False) as f:
            f.write(archive_data)
            tmp = Path(f.name)
        with tempfile.TemporaryDirectory() as outdir:
            try:
                extracted = unpack_rpa(tmp, Path(outdir))
                assert len(extracted) == 1
                assert (Path(outdir) / "test.rpy").read_bytes() == content
            finally:
                tmp.unlink()
    print("[OK] test_rpa3_different_keys")


def test_rpa3_prefix_bytes():
    """RPA-3.0: handle prefix bytes in index entries."""
    prefix = b"\xAB\xCD"
    real_data = b"the actual file data"

    # Build archive manually with prefix
    buf = io.BytesIO()
    key = 0x42
    header_placeholder = b"RPA-3.0 0000000000000000 0000000000000000\n"
    buf.write(header_placeholder)

    # Write only the non-prefix part
    offset = buf.tell()
    buf.write(real_data)
    length = len(real_data)

    index = {
        b"file.rpy": [(offset ^ key, length ^ key, prefix)],
    }
    index_offset = buf.tell()
    buf.write(zlib.compress(pickle.dumps(index, protocol=2)))

    header = f"RPA-3.0 {index_offset:016x} {key:016x}\n".encode("ascii")
    buf.seek(0)
    buf.write(header)

    with tempfile.NamedTemporaryFile(suffix=".rpa", delete=False) as f:
        f.write(buf.getvalue())
        tmp = Path(f.name)

    with tempfile.TemporaryDirectory() as outdir:
        try:
            extracted = unpack_rpa(tmp, Path(outdir))
            assert len(extracted) == 1
            # Content should be prefix + real_data
            assert (Path(outdir) / "file.rpy").read_bytes() == prefix + real_data
            print("[OK] test_rpa3_prefix_bytes")
        finally:
            tmp.unlink()


def test_unsupported_version():
    """Detect and reject unsupported RPA versions."""
    data = b"RPA-4.0 0000000000000000 0000000000000000\n"
    with tempfile.NamedTemporaryFile(suffix=".rpa", delete=False) as f:
        f.write(data)
        tmp = Path(f.name)

    try:
        try:
            list_rpa(tmp)
            assert False, "Should have raised UnsupportedVersion"
        except UnsupportedVersion as exc:
            assert "RPA-4.0" in str(exc)
            print(f"[OK] test_unsupported_version: {exc}")
    finally:
        tmp.unlink()


def test_invalid_file():
    """Reject non-RPA files."""
    with tempfile.NamedTemporaryFile(suffix=".rpa", delete=False) as f:
        f.write(b"This is not an RPA archive\n")
        tmp = Path(f.name)

    try:
        try:
            list_rpa(tmp)
            assert False, "Should have raised UnsupportedVersion"
        except UnsupportedVersion:
            print("[OK] test_invalid_file")
    finally:
        tmp.unlink()


def test_corrupted_index():
    """Detect corrupted index data."""
    # Write valid header pointing to garbage index
    data = b"RPA-3.0 0000000000000030 0000000000000000\n"
    data += b"\x00" * (0x30 - len(data))  # pad to offset 0x30
    data += b"THIS IS NOT VALID ZLIB DATA"

    with tempfile.NamedTemporaryFile(suffix=".rpa", delete=False) as f:
        f.write(data)
        tmp = Path(f.name)

    try:
        try:
            list_rpa(tmp)
            assert False, "Should have raised CorruptedArchive"
        except CorruptedArchive as exc:
            assert "zlib" in str(exc).lower() or "解压" in str(exc)
            print(f"[OK] test_corrupted_index: {exc}")
    finally:
        tmp.unlink()


def test_unpack_all_rpa_in_dir():
    """unpack_all_rpa_in_dir: scan and extract multiple archives."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        game_dir = tmpdir / "game"
        game_dir.mkdir()

        # Create two archives
        rpa1 = _build_rpa3({"scripts/main.rpy": b"label start:\n"})
        rpa2 = _build_rpa3({"scripts/chapter1.rpy": b"label ch1:\n"})
        (game_dir / "archive1.rpa").write_bytes(rpa1)
        (game_dir / "archive2.rpa").write_bytes(rpa2)

        extracted = unpack_all_rpa_in_dir(game_dir)
        assert len(extracted) == 2
        assert (game_dir / "scripts" / "main.rpy").exists()
        assert (game_dir / "scripts" / "chapter1.rpy").exists()
        print("[OK] test_unpack_all_rpa_in_dir")


def test_nested_directory_structure():
    """RPA-3.0: preserve nested directory structure."""
    archive_data = _build_rpa3({
        "tl/english/script.rpy": b"# English\n",
        "tl/chinese/script.rpy": b"# Chinese\n",
        "game/screens.rpy": b"screen main:\n",
    })

    with tempfile.NamedTemporaryFile(suffix=".rpa", delete=False) as f:
        f.write(archive_data)
        tmp = Path(f.name)

    with tempfile.TemporaryDirectory() as outdir:
        outdir = Path(outdir)
        try:
            extracted = unpack_rpa(tmp, outdir)
            assert len(extracted) == 3
            assert (outdir / "tl" / "english" / "script.rpy").read_bytes() == b"# English\n"
            assert (outdir / "tl" / "chinese" / "script.rpy").read_bytes() == b"# Chinese\n"
            assert (outdir / "game" / "screens.rpy").read_bytes() == b"screen main:\n"
            print("[OK] test_nested_directory_structure")
        finally:
            tmp.unlink()


def test_empty_archive():
    """RPA-3.0: handle archive with no files."""
    archive_data = _build_rpa3({})

    with tempfile.NamedTemporaryFile(suffix=".rpa", delete=False) as f:
        f.write(archive_data)
        tmp = Path(f.name)

    with tempfile.TemporaryDirectory() as outdir:
        try:
            files = list_rpa(tmp)
            assert files == []
            extracted = unpack_rpa(tmp, Path(outdir))
            assert extracted == []
            print("[OK] test_empty_archive")
        finally:
            tmp.unlink()


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    test_rpa3_list()
    test_rpa3_extract()
    test_rpa3_extract_scripts_only()
    test_rpa3_no_overwrite()
    test_rpa3_force_overwrite()
    test_rpa2_extract()
    test_rpa3_different_keys()
    test_rpa3_prefix_bytes()
    test_unsupported_version()
    test_invalid_file()
    test_corrupted_index()
    test_unpack_all_rpa_in_dir()
    test_nested_directory_structure()
    test_empty_archive()
    print("\n=== 全部 RPA 解包测试通过 ===")
