"""Garantir a obtenção de todos os Pokémon de Unova por encontros selvagens.

Passagem de cobertura: não altera contagem de slots/taxas de encontro;
usa os slots mais raros, respeita habitat e exige locais tardios para
lendários. A disponibilidade via grama/caverna/pesca NÃO equivale a um
evento lendário com batalha estática (etapa posterior).
"""
import json
from collections import Counter
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data" / "unova_habitats.json"


def is_firered(event):
    return not event.get("base_label", "").endswith("_LeafGreen")


def habitat(map_name, field):
    if field in {"water_mons", "fishing_mons"}:
        return "water"
    if any(term in map_name for term in (
        "CAVE", "TUNNEL", "MT_MOON", "ROCK", "VICTORY_ROAD",
        "MANSION", "RUIN", "DIGLETTS", "CERULEAN_CAVE",
    )):
        return "cave"
    if any(term in map_name for term in ("FOREST", "BERRY", "SAFARI", "PATTERN_BUSH")):
        return "forest"
    return "land"


def is_endgame(name):
    return any(term in name for term in (
        "CERULEAN_CAVE", "VICTORY_ROAD", "ONE_ISLAND", "TWO_ISLAND",
        "THREE_ISLAND", "FOUR_ISLAND", "FIVE_ISLAND", "SIX_ISLAND",
        "SEVEN_ISLAND", "NAVEL_ROCK", "BIRTH_ISLAND", "TREASURE_BEACH",
        "POWER_PLANT", "SEAFOAM_ISLANDS", "POKEMON_MANSION", "ROUTE23",
    ))


def guarantee_full_coverage(wild):
    catalog = json.loads(DATA.read_text(encoding="utf-8"))["species"]
    required = {"SPECIES_" + item["symbol"].removeprefix("SPECIES_") for item in catalog}
    freq = Counter()
    candidates = []
    for group in wild["wild_encounter_groups"]:
        weights = {f["type"]: f.get("encounter_rates", []) for f in group.get("fields", [])}
        for e in group.get("encounters", []):
            if not is_firered(e):
                continue
            for field, config in e.items():
                if not field.endswith("_mons") or not isinstance(config, dict):
                    continue
                slot_list = config.get("mons", [])
                for ix, mon in enumerate(slot_list):
                    freq[mon["species"]] += 1
                    field_weights = weights.get(field, [])
                    weight = field_weights[ix] if ix < len(field_weights) else 50
                    candidates.append({
                        "event": e, "mons": slot_list, "ix": ix,
                        "slot": mon, "map": e["map"], "field": field,
                        "weight": weight, "habitat": habitat(e["map"], field),
                        "level": mon["min_level"],
                    })

    missing = [x for x in catalog if x["symbol"] not in freq]
    assigned = []
    used_maps = set()
    for item in sorted(missing, key=lambda p: (not p["special"], -p["stage"], p["national_id"])):
        symbol = item["symbol"]
        eligible = []
        for serial, candidate in enumerate(candidates):
            current = candidate["slot"]["species"]
            if current == symbol or (current in required and freq[current] <= 1):
                continue
            stage = item["stage"]
            level = candidate["level"]
            if stage >= 2 and level < 30:
                continue
            if stage == 1 and level < 15:
                continue
            if item["special"] and not is_endgame(candidate["map"]):
                continue
            if item["special"] and level < 30:
                continue
            score = 0
            score += 100 if candidate["habitat"] == item["habitat"] else 0
            score += 90 if candidate["weight"] <= 1 else 60 if candidate["weight"] <= 5 else 0
            score += 40 if candidate["map"] not in used_maps else 0
            if stage == 0:
                score += 15 if level <= 26 else 0
            if stage >= 2:
                score += 15 if level >= 37 else 0
            if item["special"]:
                score += 20 if candidate["weight"] <= 1 else 0
                score += 15 if any(x in candidate["map"] for x in ("CERULEAN_CAVE", "SEVEN_ISLAND", "VICTORY_ROAD")) else 0
            score += min(freq[current], 30)
            # deterministic ordering, prefer later slots for lower encounter probability
            eligible.append((score, candidate["map"], candidate["event"].get("base_label", ""),
                             candidate["ix"], serial, candidate))
        if not eligible:
            raise ValueError(f"Não foi encontrado habitat/slot compatível para {symbol}")
        _, _, _, _, _, chosen = max(eligible, key=lambda e: e[:5])
        prior = chosen["slot"]["species"]
        chosen["slot"]["species"] = symbol
        freq[prior] -= 1
        freq[symbol] += 1
        used_maps.add(chosen["map"])
        assigned.append({
            "species": symbol,
            "map": chosen["map"],
            "encounter": chosen["field"],
            "level": [chosen["slot"]["min_level"], chosen["slot"]["max_level"]],
            "slot_weight": chosen["weight"],
        })
    remaining = sorted(required - {name for name, n in freq.items() if n > 0})
    if remaining:
        raise ValueError(f"Pokémon sem encontro FireRed: {remaining}")
    return {"available_in_firered": len(required), "new_placements": len(assigned),
            "placements": assigned,
            "warning": "Cobertura do código dos encontros, não prova acesso a todas as áreas ou qualidade de balanceamento."}
