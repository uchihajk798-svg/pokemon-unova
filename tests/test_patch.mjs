import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { crc32, applyBps } from "../docs/app/patch.mjs";

function variable(number) {
  const out = [];
  for (;;) {
    const x = number & 127;
    number = Math.floor(number / 128);
    if (!number) return [...out, x | 128];
    out.push(x);
    number--;
  }
}
function little32(number) {
  return [number & 255, (number >>> 8) & 255, (number >>> 16) & 255, (number >>> 24) & 255];
}
function patch(source, target, instructions, metadata = []) {
  const content = [
    66, 80, 83, 49,
    ...variable(source.length),
    ...variable(target.length),
    ...variable(metadata.length),
    ...metadata,
    ...instructions,
    ...little32(crc32(source)), ...little32(crc32(target))
  ];
  return Uint8Array.from([...content, ...little32(crc32(content))]);
}
const encodeInstruction = (length, action) => variable((length - 1) * 4 + action);

test("BPS SourceRead preserva dados e varint grande", () => {
  const source = Uint8Array.from({ length: 500 }, (_, i) => i % 256);
  const bps = patch(source, source, encodeInstruction(500, 0));
  assert.deepEqual(applyBps(source, bps), source);
});
test("BPS TargetRead produz novos bytes", () => {
  const original = Uint8Array.from([1, 2, 3, 4]);
  const target = Uint8Array.from([5, 7, 9]);
  const instructions = [...encodeInstruction(3, 1), ...target];
  assert.deepEqual(applyBps(original, patch(original, target, instructions)), target);
});
test("BPS SourceCopy usa offset relativo", () => {
  const original = Uint8Array.from([1, 2, 3, 4, 5, 6]);
  const target = Uint8Array.from([3, 4, 5]);
  const instructions = [...encodeInstruction(3, 2), ...variable(4)]; // offset +2
  assert.deepEqual(applyBps(original, patch(original, target, instructions)), target);
});
test("BPS TargetCopy suporta repetição com sobreposição", () => {
  const original = new Uint8Array(1);
  const target = new Uint8Array(9).fill(90);
  const commands = [...encodeInstruction(1, 1), 90, ...encodeInstruction(8, 3), ...variable(0)];
  assert.deepEqual(applyBps(original, patch(original, target, commands)), target);
});
test("BPS aplica arquivo com metadados", () => {
  const source = Uint8Array.from([0]);
  const target = Uint8Array.from([8]);
  assert.deepEqual(applyBps(source, patch(source, target, [...encodeInstruction(1, 1), 8], [97, 98])), target);
});
test("BPS rejeita ROM base diferente", () => {
  const source = Uint8Array.from([1]);
  const target = Uint8Array.from([2]);
  const data = patch(source, target, [...encodeInstruction(1, 1), 2]);
  assert.throws(() => applyBps(Uint8Array.from([3]), data), /ROM base incorreta/);
});
test("BPS rejeita patch com CRC danificado", () => {
  const source = Uint8Array.from([1]);
  const target = Uint8Array.from([2]);
  const data = patch(source, target, [...encodeInstruction(1, 1), 2]);
  data[4] ^= 1;
  assert.throws(() => applyBps(source, data), /danificado/);
});
test("PWA contém os arquivos e configurações para GBA", () => {
  const manifest = JSON.parse(readFileSync("docs/app/manifest.webmanifest", "utf8"));
  const html = readFileSync("docs/app/index.html", "utf8");
  const player = readFileSync("docs/app/player.html", "utf8");
  assert.equal(manifest.display, "standalone");
  assert.ok(manifest.icons.length);
  assert.match(html, /main\.mjs/);
  assert.match(html, /manifest\.webmanifest/);
  assert.match(player, /EJS_core="gba"/);
  assert.match(player, /cdn\.emulatorjs\.org/);
});
