"""Verificação BPS com alterações no início, meio, fim, tamanho e CRC."""
import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from bps import apply_patch, make_patch, pack_varint, unpack_varint


class TestBPS(unittest.TestCase):
    def test_varint_roundtrip(self):
        for n in (0, 1, 127, 128, 255, 256, 1024, 16384, 2**32 - 1):
            data = pack_varint(n)
            result, end = unpack_varint(data, 0)
            self.assertEqual(result, n)
            self.assertEqual(end, len(data))

    def test_diff_roundtrip(self):
        fixtures = [
            (b"", b""),
            (b"", b"test target"),
            (b"abc123", b"abc123"),
            (b"abc123", b"Abc123"),
            (b"abc123", b"abc124"),
            (b"abcdefghij", b"abcdWXYZij"),
            (b"long source content", b"small"),
            (b"abc" * 400, b"abc" * 399 + b"XYz"),
            (bytes(range(256)) * 10, bytes(range(255, -1, -1)) * 10),
        ]
        rng = random.Random(2026)
        for _ in range(15):
            a = bytes(rng.randrange(256) for _ in range(rng.randrange(0, 1024)))
            b = bytes(rng.randrange(256) for _ in range(rng.randrange(0, 1024)))
            fixtures.append((a, b))
        for base, modified in fixtures:
            with self.subTest(base=len(base), modified=len(modified)):
                patch = make_patch(base, modified)
                self.assertEqual(apply_patch(base, patch), modified)

    def test_invalid_source_rejected(self):
        patch = make_patch(b"original", b"modified")
        with self.assertRaisesRegex(ValueError, "ROM base"):
            apply_patch(b"wrong", patch)

    def test_invalid_patch_crc_rejected(self):
        patch = bytearray(make_patch(b"original", b"modified"))
        patch[-1] ^= 1
        with self.assertRaisesRegex(ValueError, "CRC do patch"):
            apply_patch(b"original", patch)


if __name__ == "__main__":
    unittest.main()
