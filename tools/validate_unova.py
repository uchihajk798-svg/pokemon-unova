#!/usr/bin/env python3
"""Confere substituições de espécies em uma base já modificada, sem ROM."""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from apply_unova import LAB_FILE, TRAINERS_FILE, WILD_FILE, MON_PATTERN, get_catalog, normalized
from complete_encounters import is_firered


def validate(game_dir):
    catalog = get_catalog()
    errors = []
    counts = Counter()

    lab = (game_dir / LAB_FILE).read_text(encoding="utf-8")
    for species in ("BULBASAUR", "CHARMANDER", "SQUIRTLE"):
        if f"SPECIES_{species}" in lab:
            errors.append(f"Inicial original ainda presente no laboratório: {species}")
    for species in ("SNIVY", "TEPIG", "OSHAWOTT"):
        if f"SPECIES_{species}" not in lab:
            errors.append(f"Inicial de Unova ausente: {species}")

    groups = json.loads((game_dir / WILD_FILE).read_text(encoding="utf-8"))["wild_encounter_groups"]
    seen_wild = set()
    for group in groups:
        for event in group["encounters"]:
            if not is_firered(event):
                continue
            for field, value in event.items():
                if field.endswith("_mons") and isinstance(value, dict):
                    for mon in value.get("mons", []):
                        symbol = mon["species"]
                        name = normalized(symbol.removeprefix("SPECIES_"))
                        counts["encounter_slots"] += 1
                        if not symbol.startswith("SPECIES_") or name not in catalog:
                            errors.append(f"Encontro inválido: {event['map']} / {symbol}")
                        else:
                            seen_wild.add(name)

    text = (game_dir / TRAINERS_FILE).read_text(encoding="utf-8")
    seen_trainers = set()
    for match in MON_PATTERN.finditer(text):
        name = match.group("name")
        key = normalized(name)
        counts["trainer_party_entries"] += 1
        if key not in catalog:
            errors.append(f"Treinador com Pokémon fora de Unova: {name}")
        else:
            seen_trainers.add(key)
    missing_wild = sorted(set(catalog) - seen_wild)
    if missing_wild:
        errors.append(f"Faltam espécies selvagens em FireRed: {len(missing_wild)}; "
                      + ", ".join(missing_wild[:20]))
    if not counts["encounter_slots"] or not counts["trainer_party_entries"]:
        errors.append("Dados de encontros ou equipes estão vazios")

    return {
        "ok": not errors,
        "errors": errors[:50],
        "error_count": len(errors),
        "encounter_slots": counts["encounter_slots"],
        "trainer_party_entries": counts["trainer_party_entries"],
        "unique_species_in_wild": len(seen_wild),
        "missing_species_wild": missing_wild,
        "unique_species_in_trainers": len(seen_trainers),
        "unique_species_overall": len(seen_wild | seen_trainers),
        "catalog_size": len(catalog),
        "notice": "Validação apenas de referências de espécies; não prova compilação, acessibilidade, movimentos nem progresso completo.",
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--game-dir", type=Path, required=True)
    args = p.parse_args()
    report = validate(args.game_dir.resolve())
    print(json.dumps(report, indent=2, ensure_ascii=False))
    sys.exit(0 if report["ok"] else 1)


if __name__ == "__main__":
    main()
