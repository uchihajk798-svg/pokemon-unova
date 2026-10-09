/* BPS1: SourceRead, TargetRead, SourceCopy e TargetCopy.
 * Implementado localmente: nunca faz upload da ROM ou patch.
 * Referência: especificação BPS da comunidade ROM hacking.
 */
const MAGIC = [66, 80, 83, 49];
const table = new Uint32Array(256);
for (let i = 0; i < 256; i++) {
  let c = i;
  for (let k = 0; k < 8; k++) c = (c & 1) ? (0xEDB88320 ^ (c >>> 1)) : (c >>> 1);
  table[i] = c >>> 0;
}

export function crc32(bytes) {
  let result = 0xFFFFFFFF;
  for (let i = 0; i < bytes.length; i++) {
    result = table[(result ^ bytes[i]) & 255] ^ (result >>> 8);
  }
  return (result ^ 0xFFFFFFFF) >>> 0;
}

function u32(bytes, i) {
  if (i < 0 || i + 4 > bytes.length) throw Error("Checksum BPS truncado.");
  return (bytes[i] | (bytes[i + 1] << 8) | (bytes[i + 2] << 16) | (bytes[i + 3] << 24)) >>> 0;
}

function byteArray(value) {
  if (value instanceof Uint8Array) return value;
  if (value instanceof ArrayBuffer) return new Uint8Array(value);
  throw new TypeError("Esperado um ArrayBuffer ou Uint8Array.");
}

export function applyBps(sourceInput, patchInput, maxOutputBytes = 64 * 1024 * 1024) {
  const source = byteArray(sourceInput);
  const patch = byteArray(patchInput);
  if (patch.length < 16 || MAGIC.some((c, i) => patch[i] !== c)) {
    throw Error("Arquivo inválido: esperado patch BPS1.");
  }
  const footer = patch.length - 12;
  if (crc32(patch.subarray(0, patch.length - 4)) !== u32(patch, patch.length - 4)) {
    throw Error("Patch danificado (checksum CRC32 incorreto).");
  }
  let offset = 4;
  function varint() {
    let value = 0, factor = 1;
    for (;;) {
      if (offset >= footer) throw Error("Dados BPS truncados.");
      const byte = patch[offset++];
      value += (byte & 0x7F) * factor;
      if (!Number.isSafeInteger(value)) throw Error("Número BPS muito grande.");
      if (byte & 0x80) return value;
      factor *= 128;
      value += factor;
      if (!Number.isSafeInteger(value)) throw Error("Número BPS muito grande.");
    }
  }
  function signed() {
    const n = varint();
    const distance = Math.floor(n / 2);
    return n % 2 ? -distance : distance;
  }
  const sourceSize = varint();
  const outputSize = varint();
  const metadataSize = varint();
  if (sourceSize !== source.byteLength || u32(patch, footer) !== crc32(source)) {
    throw Error("ROM base incorreta para esse BPS. Confira a versão exata e o checksum exigidos pelo patch.");
  }
  if (outputSize > maxOutputBytes) throw Error("O jogo modificado excede o limite seguro de tamanho.");
  if (offset + metadataSize > footer) throw Error("Metadados BPS inválidos.");
  offset += metadataSize;
  const output = new Uint8Array(outputSize);
  let position = 0, sourceRelative = 0, targetRelative = 0;
  while (offset < footer) {
    const instruction = varint();
    const action = instruction % 4;
    const length = Math.floor(instruction / 4) + 1;
    if (position + length > outputSize) throw Error("O patch excede o tamanho final da ROM.");
    switch (action) {
      case 0: // SourceRead
        if (position + length > source.length) throw Error("Leitura fora da ROM de origem.");
        output.set(source.subarray(position, position + length), position);
        break;
      case 1: // TargetRead
        if (offset + length > footer) throw Error("Dados inseridos estão truncados.");
        output.set(patch.subarray(offset, offset + length), position);
        offset += length;
        break;
      case 2: // SourceCopy
        sourceRelative += signed();
        if (sourceRelative < 0 || sourceRelative + length > source.length) {
          throw Error("Cópia fora da ROM original.");
        }
        output.set(source.subarray(sourceRelative, sourceRelative + length), position);
        sourceRelative += length;
        break;
      case 3: // TargetCopy (pode se sobrepor ao que já foi escrito)
        targetRelative += signed();
        if (targetRelative < 0 || targetRelative >= position) {
          throw Error("Cópia inválida do resultado parcial.");
        }
        for (let i = 0; i < length; i++) {
          output[position + i] = output[targetRelative + i];
        }
        targetRelative += length;
        break;
      default:
        throw Error("Comando BPS desconhecido.");
    }
    position += length;
  }
  if (position !== outputSize || crc32(output) !== u32(patch, footer + 4)) {
    throw Error("O arquivo modificado falhou na checagem de integridade.");
  }
  return output;
}
