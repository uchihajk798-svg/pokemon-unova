"""Transforma a Pokédex regional Kanto do FireRed em Pokédex Unova #001–156.

Conserva números nacionais reais #494–649, sprites e dados que a base
expandida já oferece. NÃO modifica o enum nacional, saves ou ROMs.
"""
import json
import re
import shutil
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
CATALOG = BASE / "data" / "unova_species.json"

POKEMON_C = "src/pokemon.c"
DEX_CONST = "include/constants/pokedex.h"
DEX_SCREEN = "src/pokedex_screen.c"


def patch_constants(text):
    before = "#define KANTO_DEX_COUNT KANTO_DEX_MEW"
    after = "#define KANTO_DEX_COUNT 156 // Regional Unova dex count"
    if before in text:
        return text.replace(before, after, 1)
    if after in text:
        return text
    raise ValueError("KANTO_DEX_COUNT não encontrado em include/constants/pokedex.h")


def patch_pokemon(text, species):
    rx = re.compile(
        r"static const enum NationalDexOrder sKantoToNationalOrder\[KANTO_DEX_COUNT\] =\s*\{\s*.*?^\};",
        re.MULTILINE | re.DOTALL,
    )
    entries = [sp["symbol"].replace("SPECIES_", "NATIONAL_DEX_", 1) for sp in species]
    # Formas-padrão da base têm nomes de espécie diferentes do enum NATIONAL_DEX.
    replacements = {
        "NATIONAL_DEX_BASCULIN_RED_STRIPED": "NATIONAL_DEX_BASCULIN",
        "NATIONAL_DEX_DARMANITAN_STANDARD": "NATIONAL_DEX_DARMANITAN",
        "NATIONAL_DEX_DEERLING_SPRING": "NATIONAL_DEX_DEERLING",
        "NATIONAL_DEX_SAWSBUCK_SPRING": "NATIONAL_DEX_SAWSBUCK",
        "NATIONAL_DEX_TORNADUS_INCARNATE": "NATIONAL_DEX_TORNADUS",
        "NATIONAL_DEX_THUNDURUS_INCARNATE": "NATIONAL_DEX_THUNDURUS",
        "NATIONAL_DEX_LANDORUS_INCARNATE": "NATIONAL_DEX_LANDORUS",
        "NATIONAL_DEX_KELDEO_ORDINARY": "NATIONAL_DEX_KELDEO",
        "NATIONAL_DEX_MELOETTA_ARIA": "NATIONAL_DEX_MELOETTA",
    }
    entries = [replacements.get(x, x) for x in entries]
    if len(entries) != 156 or len(set(entries)) != 156:
        raise ValueError("A Pokédex Unova não contém 156 entradas distintas.")
    initializer = ("static const enum NationalDexOrder sKantoToNationalOrder[KANTO_DEX_COUNT] =\n"
                   "{\n    " + ",\n    ".join(entries) + "\n};")
    if not rx.search(text):
        raise ValueError("Array sKantoToNationalOrder não encontrado")
    text, count = rx.subn(initializer, text, count=1)
    if count != 1:
        raise ValueError("Array não alterado exatamente uma vez")
    original_guard = "if (KANTO_DEX_START <= kantoNum && kantoNum < KANTO_DEX_END)"
    new_guard = "if (KANTO_DEX_START <= kantoNum && kantoNum < KANTO_DEX_START + KANTO_DEX_COUNT)"
    if original_guard in text:
        text = text.replace(original_guard, new_guard)
    if new_guard not in text:
        raise ValueError("Limite do índice regional não encontrado")
    return text


def patch_screen(text):
    # O contador regional de visto/capturado deve cobrir todas as 156 espécies.
    text = text.replace("i < KANTO_DEX_END", "i < KANTO_DEX_START + KANTO_DEX_COUNT")
    return text


def apply_regional_pokedex(game_dir, dry_run=False):
    species = json.loads(CATALOG.read_text(encoding="utf-8"))["species"]
    if [s["national_id"] for s in species] != list(range(494, 650)):
        raise ValueError("Ordem nacional incompleta")
    tasks = ((DEX_CONST, patch_constants),
             (POKEMON_C, lambda text: patch_pokemon(text, species)),
             (DEX_SCREEN, patch_screen))
    results = {}
    for relative, transform in tasks:
        path = game_dir / relative
        if not path.is_file():
            raise FileNotFoundError(f"Pokédex: arquivo ausente {relative}")
        original = path.read_text(encoding="utf-8")
        updated = transform(original)
        if updated == original:
            results[relative] = "unchanged"
        else:
            results[relative] = "modified"
            if not dry_run:
                backup = path.with_name(path.name + ".unova-backup")
                if not backup.exists():
                    shutil.copy2(path, backup)
                path.write_text(updated, encoding="utf-8")
    return {"regional_entries": 156, "scope": "Kanto regional Pokédex reassigned to Unova, not National Dex",
            "files": results}
