#!/usr/bin/env python3
"""Checagem dos HMs de FireRed no elenco Unova da base expandida.

Não substitui jogar a campanha nem garante disponibilidade antecipada de HM.
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HMS = ("CUT", "FLASH", "FLY", "SURF", "STRENGTH", "ROCK_SMASH", "WATERFALL")
STARTERS = ("SNIVY", "TEPIG", "OSHAWOTT")

FORM_NAMES = {
    "BASCULIN_RED_STRIPED": "Basculin",
    "DARMANITAN_STANDARD": "Darmanitan",
    "DEERLING_SPRING": "Deerling",
    "SAWSBUCK_SPRING": "Sawsbuck",
    "TORNADUS_INCARNATE": "Tornadus",
    "THUNDURUS_INCARNATE": "Thundurus",
    "LANDORUS_INCARNATE": "Landorus",
    "KELDEO_ORDINARY": "Keldeo",
    "MELOETTA_ARIA": "Meloetta",
}


def validate(game_dir):
    learnsets = (game_dir / "src/data/pokemon/teachable_learnsets.h").read_text(encoding="utf8")
    species = json.loads((ROOT / "data/unova_species.json").read_text())["species"]
    tables = {
        m.group(1).lower(): set(re.findall(r"\bMOVE_([A-Z0-9_]+)\b", m.group(2)))
        for m in re.finditer(
            r"static const u16 s([A-Za-z0-9]+)TeachableLearnset\[\]\s*=\s*\{(.*?)\};",
            learnsets, re.DOTALL)
    }
    missing = []
    mon_moves = {}
    for item in species:
        key = item["symbol"].removeprefix("SPECIES_")
        filename = FORM_NAMES.get(key, key.title().replace("_", ""))
        moves = tables.get(filename.lower())
        if moves is None:
            missing.append(key)
            continue
        mon_moves[key] = moves
    counts = {hm: sum(hm in moves for moves in mon_moves.values()) for hm in HMS}
    starter_coverage = {hm: [s for s in STARTERS if hm in mon_moves.get(s, set())] for hm in HMS}
    required_early = {
        "CUT": ["SNIVY", "OSHAWOTT"],
        "FLASH": ["SNIVY"],
        "SURF": ["OSHAWOTT"],
        "STRENGTH": ["TEPIG"],
        "ROCK_SMASH": ["TEPIG", "OSHAWOTT"],
        "WATERFALL": ["OSHAWOTT"],
    }
    errors = [f"Sem learnset: {missing}" ] if missing else []
    for hm, count in counts.items():
        if count == 0:
            errors.append(f"Nenhum Pokémon de Unova aprende {hm}")
    for hm, mons in required_early.items():
        if not any(hm in mon_moves.get(s, set()) for s in mons):
            errors.append(f"Starter obrigatório sem HM {hm}: {mons}")
    return {"ok": not errors, "errors": errors, "learnsets_found": len(mon_moves),
            "hm_compatible_species": counts,
            "starter_hm_coverage": starter_coverage,
            "note": "Compatibilidade estática apenas; testar itens e rotas em emulador."}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--game-dir", type=Path, required=True)
    args = p.parse_args()
    result = validate(args.game_dir)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result["ok"] else 1)
