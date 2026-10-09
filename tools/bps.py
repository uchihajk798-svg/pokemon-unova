#!/usr/bin/env python3
"""Criar/verificar patches BPS sem distribuir ROMs GBA.

Suporta BPS1 (SourceRead/TargetRead); sem compressão interna.
Formato: https://www.romhacking.net/documents/746/
"""
import argparse
import struct
import zlib
from pathlib import Path

MAGIC = b"BPS1"


def pack_varint(value):
    if value < 0:
        raise ValueError("Inteiro negativo")
    out = bytearray()
    while True:
        x = value & 0x7F
        value >>= 7
        if value == 0:
            out.append(x | 0x80)
            return bytes(out)
        out.append(x)
        value -= 1


def unpack_varint(data, offset):
    result = 0
    shift = 1
    while True:
        if offset >= len(data):
            raise ValueError("BPS truncado")
        x = data[offset]
        offset += 1
        result += (x & 0x7F) * shift
        if x & 0x80:
            return result, offset
        shift <<= 7
        result += shift


def crc(data):
    return struct.pack("<I", zlib.crc32(data) & 0xFFFFFFFF)


def make_patch(source, target, metadata=b"Pokemon Unova patch; apply to the matching clean build"):
    """Preserva sequências iguais, guarda só segmentos alterados."""
    out = bytearray(MAGIC)
    for n in (len(source), len(target), len(metadata)):
        out.extend(pack_varint(n))
    out.extend(metadata)
    i = 0
    n = len(target)
    while i < n:
        if i < len(source) and source[i] == target[i]:
            start = i
            while i < n and i < len(source) and source[i] == target[i]:
                i += 1
            out.extend(pack_varint(((i - start - 1) << 2) | 0))  # SourceRead
        else:
            start = i
            while i < n:
                # At least 4 equal bytes ahead to justify switching to SourceRead.
                if (i + 4 <= n and i + 4 <= len(source)
                        and source[i:i + 4] == target[i:i + 4]):
                    break
                i += 1
            out.extend(pack_varint(((i - start - 1) << 2) | 1))  # TargetRead
            out.extend(target[start:i])
    out.extend(crc(source))
    out.extend(crc(target))
    out.extend(crc(out))
    return bytes(out)


def apply_patch(source, patch):
    if patch[:4] != MAGIC or len(patch) < 16:
        raise ValueError("Arquivo não é um patch BPS1")
    if patch[-4:] != crc(patch[:-4]):
        raise ValueError("CRC do patch BPS inválido")
    offset = 4
    source_size, offset = unpack_varint(patch, offset)
    target_size, offset = unpack_varint(patch, offset)
    metadata_size, offset = unpack_varint(patch, offset)
    if len(source) != source_size or patch[-12:-8] != crc(source):
        raise ValueError("ROM base não corresponde ao BPS")
    offset += metadata_size
    if offset > len(patch) - 12:
        raise ValueError("Metadados BPS truncados")
    target = bytearray()
    while offset < len(patch) - 12:
        command, offset = unpack_varint(patch, offset)
        length = (command >> 2) + 1
        action = command & 3
        if len(target) + length > target_size:
            raise ValueError("BPS excede o tamanho alvo")
        if action == 0:
            start = len(target)
            if start + length > len(source):
                raise ValueError("SourceRead fora da ROM")
            target.extend(source[start:start + length])
        elif action == 1:
            if offset + length > len(patch) - 12:
                raise ValueError("TargetRead fora do patch")
            target.extend(patch[offset:offset + length])
            offset += length
        else:
            raise ValueError("Este verificador suporta apenas SourceRead/TargetRead")
    if len(target) != target_size or crc(target) != patch[-8:-4]:
        raise ValueError("O resultado do patch não passou no CRC")
    return bytes(target)


def main():
    p = argparse.ArgumentParser(description="Gerar/validar patch BPS sem publicar ROM")
    sub = p.add_subparsers(dest="command", required=True)
    make = sub.add_parser("create")
    make.add_argument("--base", type=Path, required=True)
    make.add_argument("--modified", type=Path, required=True)
    make.add_argument("--output", type=Path, required=True)
    verify = sub.add_parser("verify")
    verify.add_argument("--base", type=Path, required=True)
    verify.add_argument("--patch", type=Path, required=True)
    args = p.parse_args()
    if args.command == "create":
        source, target = args.base.read_bytes(), args.modified.read_bytes()
        payload = make_patch(source, target)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(payload)
        if apply_patch(source, payload) != target:
            raise RuntimeError("Patch gerado falhou na autoverificação")
        print(f"Patch BPS gerado e verificado: {args.output} ({len(payload)} bytes)")
    else:
        source, patch = args.base.read_bytes(), args.patch.read_bytes()
        print(f"Patch íntegro: {len(apply_patch(source, patch))} bytes no resultado")


if __name__ == "__main__":
    main()
