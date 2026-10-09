#!/usr/bin/env python3
"""Primeiro passe de Unova sobre uma cópia local de pokefirered-expansion.

NÃO transforma sozinho a base num jogo final. Mantém os arquivos originais
em *.unova-backup, preserva níveis/taxas e produz relatório de substituições.
Uso: python3 tools/apply_unova.py --game-dir ../firered-base
"""
import argparse
import hashlib
import json
import re
import shutil
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data" / "unova_species.json"

# Linhas de famílias: cada coluna à esquerda equivale à coluna à direita.
# Mapeamento inicial, sujeito à revisão individual de balanceamento.
FAMILIES = """
BULBASAUR IVYSAUR VENUSAUR : SNIVY SERVINE SERPERIOR
CHARMANDER CHARMELEON CHARIZARD : TEPIG PIGNITE EMBOAR
SQUIRTLE WARTORTLE BLASTOISE : OSHAWOTT DEWOTT SAMUROTT
CATERPIE METAPOD BUTTERFREE : SEWADDLE SWADLOON LEAVANNY
WEEDLE KAKUNA BEEDRILL : VENIPEDE WHIRLIPEDE SCOLIPEDE
PIDGEY PIDGEOTTO PIDGEOT : PIDOVE TRANQUILL UNFEZANT
RATTATA RATICATE : PATRAT WATCHOG
SPEAROW FEAROW : RUFFLET BRAVIARY
EKANS ARBOK : SANDILE KROKOROK
PIKACHU RAICHU : BLITZLE ZEBSTRIKA
SANDSHREW SANDSLASH : DRILBUR EXCADRILL
NIDORAN_F NIDORINA NIDOQUEEN : VULLABY MANDIBUZZ MANDIBUZZ
NIDORAN_M NIDORINO NIDOKING : SCRAGGY SCRAFTY KROOKODILE
CLEFAIRY CLEFABLE : MINCCINO CINCCINO
VULPIX NINETALES : PANSEAR SIMISEAR
JIGGLYPUFF WIGGLYTUFF : MUNNA MUSHARNA
ZUBAT GOLBAT CROBAT : WOOBAT SWOOBAT SWOOBAT
ODDISH GLOOM VILEPLUME : PETILIL LILLIGANT LILLIGANT
BELLOSSOM : LILLIGANT
PARAS PARASECT : FOONGUS AMOONGUSS
VENONAT VENOMOTH : JOLTIK GALVANTULA
DIGLETT DUGTRIO : DRILBUR EXCADRILL
MEOWTH PERSIAN : PURRLOIN LIEPARD
PSYDUCK GOLDUCK : DUCKLETT SWANNA
MANKEY PRIMEAPE : TIMBURR GURDURR
GROWLITHE ARCANINE : LILLIPUP STOUTLAND
POLIWAG POLIWHIRL POLIWRATH : TYMPOLE PALPITOAD SEISMITOAD
POLITOED : SEISMITOAD
ABRA KADABRA ALAKAZAM : GOTHITA GOTHORITA GOTHITELLE
MACHOP MACHOKE MACHAMP : TIMBURR GURDURR CONKELDURR
BELLSPROUT WEEPINBELL VICTREEBEL : PANSAGE SIMISAGE SIMISAGE
TENTACOOL TENTACRUEL : FRILLISH JELLICENT
GEODUDE GRAVELER GOLEM : ROGGENROLA BOLDORE GIGALITH
PONYTA RAPIDASH : BLITZLE ZEBSTRIKA
SLOWPOKE SLOWBRO SLOWKING : MUNNA MUSHARNA MUSHARNA
MAGNEMITE MAGNETON MAGNEZONE : KLINK KLANG KLINKLANG
FARFETCHD : DUCKLETT
DODUO DODRIO : PIDOVE UNFEZANT
SEEL DEWGONG : CUBCHOO BEARTIC
GRIMER MUK : TRUBBISH GARBODOR
SHELLDER CLOYSTER : DWEBBLE CRUSTLE
GASTLY HAUNTER GENGAR : LITWICK LAMPENT CHANDELURE
ONIX STEELIX : DWEBBLE CRUSTLE
DROWZEE HYPNO : MUNNA MUSHARNA
KRABBY KINGLER : DWEBBLE CRUSTLE
VOLTORB ELECTRODE : JOLTIK GALVANTULA
EXEGGCUTE EXEGGUTOR : COTTONEE WHIMSICOTT
CUBONE MAROWAK : SANDILE KROKOROK
HITMONLEE HITMONCHAN HITMONTOP : SAWK THROH SAWK
LICKITUNG LICKILICKY : AUDINO AUDINO
KOFFING WEEZING : TRUBBISH GARBODOR
RHYHORN RHYDON RHYPERIOR : ROGGENROLA BOLDORE GIGALITH
CHANSEY BLISSEY : AUDINO AUDINO
TANGELA TANGROWTH : FERROSEED FERROTHORN
KANGASKHAN : BOUFFALANT
HORSEA SEADRA KINGDRA : TYNAMO EELEKTRIK EELEKTROSS
GOLDEEN SEAKING : ALOMOMOLA ALOMOMOLA
STARYU STARMIE : FRILLISH JELLICENT
MR_MIME : ELGYEM
SCYTHER SCIZOR : DURANT DURANT
JYNX : GOTHITELLE
ELECTABUZZ ELECTIVIRE : EELEKTRIK EELEKTROSS
MAGMAR MAGMORTAR : DARUMAKA DARMANITAN
PINSIR : DURANT
TAUROS : BOUFFALANT
MAGIKARP GYARADOS : TYMPOLE SEISMITOAD
LAPRAS : CARRACOSTA
DITTO : AUDINO
EEVEE VAPOREON JOLTEON FLAREON : DEERLING SAWSBUCK SIMISEAR
ESPEON UMBREON LEAFEON GLACEON SYLVEON : GOTHORITA LIEPARD LEAVANNY BEARTIC WHIMSICOTT
PORYGON PORYGON2 PORYGON_Z : KLINK KLANG KLINKLANG
OMANYTE OMASTAR : TIRTOUGA CARRACOSTA
KABUTO KABUTOPS : ARCHEN ARCHEOPS
AERODACTYL : ARCHEOPS
SNORLAX : STOUTLAND
ARTICUNO ZAPDOS MOLTRES : CRYOGONAL THUNDURUS_INCARNATE RESHIRAM
DRATINI DRAGONAIR DRAGONITE : AXEW FRAXURE HAXORUS
MEWTWO MEW : KYUREM VICTINI
CHIKORITA BAYLEEF MEGANIUM : SNIVY SERVINE SERPERIOR
CYNDAQUIL QUILAVA TYPHLOSION : TEPIG PIGNITE EMBOAR
TOTODILE CROCONAW FERALIGATR : OSHAWOTT DEWOTT SAMUROTT
HOOTHOOT NOCTOWL : PIDOVE UNFEZANT
SENTRET FURRET : PATRAT WATCHOG
SPINARAK ARIADOS : JOLTIK GALVANTULA
CHINCHOU LANTURN : TYNAMO EELEKTROSS
MAREEP FLAAFFY AMPHAROS : BLITZLE ZEBSTRIKA ZEBSTRIKA
MARILL AZUMARILL : TYMPOLE SEISMITOAD
WOOPER QUAGSIRE : TYMPOLE SEISMITOAD
MURKROW HONCHKROW : VULLABY MANDIBUZZ
MISDREAVUS MISMAGIUS : LITWICK CHANDELURE
PINECO FORRETRESS : FERROSEED FERROTHORN
GLIGAR GLISCOR : ARON ARCHEOPS
SNUBBULL GRANBULL : LILLIPUP STOUTLAND
QWILFISH : STUNFISK
SNEASEL WEAVILE : PAWNIARD BISHARP
TEDDIURSA URSARING : CUBCHOO BEARTIC
SLUGMA MAGCARGO : DARUMAKA DARMANITAN
SWINUB PILOSWINE MAMOSWINE : CUBCHOO BEARTIC BEARTIC
CORSOLA : TIRTOUGA
REMORAID OCTILLERY : BASCULIN JELLICENT
DELIBIRD : DUCKLETT
MANTINE : SWANNA
SKARMORY : SKARMORY
HOUNDOUR HOUNDOOM : PURRLOIN LIEPARD
PHANPY DONPHAN : DRILBUR EXCADRILL
SMOOCHUM ELEKID MAGBY : GOTHITA TYNAMO PANSEAR
LARVITAR PUPITAR TYRANITAR : DEINO ZWEILOUS HYDREIGON
TREECKO GROVYLE SCEPTILE : SNIVY SERVINE SERPERIOR
TORCHIC COMBUSKEN BLAZIKEN : TEPIG PIGNITE EMBOAR
MUDKIP MARSHTOMP SWAMPERT : OSHAWOTT DEWOTT SAMUROTT
POOCHYENA MIGHTYENA : PURRLOIN LIEPARD
ZIGZAGOON LINOONE : PATRAT WATCHOG
WURMPLE SILCOON BEAUTIFLY : SEWADDLE SWADLOON LEAVANNY
CASCOON DUSTOX : WHIRLIPEDE SCOLIPEDE
LOTAD LOMBRE LUDICOLO : TYMPOLE PALPITOAD SEISMITOAD
SEEDOT NUZLEAF SHIFTRY : PANSAGE SIMISAGE SIMISAGE
TAILLOW SWELLOW : PIDOVE UNFEZANT
WINGULL PELIPPER : DUCKLETT SWANNA
RALTS KIRLIA GARDEVOIR : GOTHITA GOTHORITA GOTHITELLE
SURSKIT MASQUERAIN : JOLTIK GALVANTULA
SHROOMISH BRELOOM : FOONGUS AMOONGUSS
SLAKOTH VIGOROTH SLAKING : LILLIPUP HERDIER STOUTLAND
NINCADA NINJASK SHEDINJA : VENIPEDE SCOLIPEDE SHEDINJA
WHISMUR LOUDRED EXPLOUD : TIMBURR GURDURR CONKELDURR
MAKUHITA HARIYAMA : TIMBURR CONKELDURR
AZURILL : TYMPOLE
NOSEPASS PROBOPASS : ROGGENROLA GIGALITH
SKITTY DELCATTY : PURRLOIN LIEPARD
SABLEYE MAWILE : SCRAGGY PAWNIARD
ARON LAIRON AGGRON : KLINK KLANG KLINKLANG
MEDITITE MEDICHAM : MIENFOO MIENSHAO
ELECTRIKE MANECTRIC : BLITZLE ZEBSTRIKA
PLUSLE MINUN : EMOLGA EMOLGA
VOLBEAT ILLUMISE : JOLTIK JOLTIK
ROSELIA ROSERADE : PETILIL LILLIGANT
GULPIN SWALOT : TRUBBISH GARBODOR
CARVANHA SHARPEDO : BASCULIN JELLICENT
WAILMER WAILORD : FRILLISH JELLICENT
NUMEL CAMERUPT : DARUMAKA DARMANITAN
TORKOAL : HEATMOR
SPOINK GRUMPIG : MUNNA MUSHARNA
SPINDA : SPINDA
TRAPINCH VIBRAVA FLYGON : SANDILE KROKOROK KROOKODILE
CACNEA CACTURNE : MARACTUS MARACTUS
SWABLU ALTARIA : PIDOVE UNFEZANT
ZANGOOSE SEVIPER : ZANGOOSE SCRAGGY
LUNATONE SOLROCK : SOLOSIS DUOSION
BARBOACH WHISCASH : TYMPOLE SEISMITOAD
CORPHISH CRAWDAUNT : DWEBBLE CRUSTLE
BALTOY CLAYDOL : GOLETT GOLURK
LILEEP CRADILY : FERROSEED FERROTHORN
ANORITH ARMALDO : ARCHEN ARCHEOPS
FEEBAS MILOTIC : FRILLISH JELLICENT
CASTFORM : CASTFORM
KECLEON : KECLEON
SHUPPET BANETTE : YAMASK COFAGRIGUS
DUSKULL DUSCLOPS DUSKNOIR : YAMASK COFAGRIGUS COFAGRIGUS
TROPIUS : SAWSBUCK
CHIMECHO CHINGLING : ELGYEM ELGYEM
ABSOL : ABSOL
WYNAUT WOBBUFFET : ELGYEM BEHEEYEM
SNORUNT GLALIE FROSLASS : CUBCHOO BEARTIC CRYOGONAL
SPHEAL SEALEO WALREIN : CUBCHOO BEARTIC BEARTIC
CLAMPERL HUNTAIL GOREBYSS : TIRTOUGA CARRACOSTA JELLICENT
RELICANTH : CARRACOSTA
LUVDISC : ALOMOMOLA
BAGON SHELGON SALAMENCE : AXEW FRAXURE HAXORUS
BELDUM METANG METAGROSS : KLINK KLANG KLINKLANG
REGIROCK REGICE REGISTEEL : TERRAKION CRYOGONAL COBALION
LATIAS LATIOS : RESHIRAM ZEKROM
KYOGRE GROUDON RAYQUAZA : KYUREM LANDORUS_INCARNATE ZEKROM
JIRACHI DEOXYS : VICTINI GENESECT
""".strip()

# Corrige pares acima caso o equivalente não exista em Unova.
OVERRIDES = {
    "GLIGAR": "ARCHEN", "SKARMORY": "DURANT", "SHEDINJA": "COFAGRIGUS",
    "SPINDA": "AUDINO", "ZANGOOSE": "MIENFOO", "CASTFORM": "DEERLING",
    "KECLEON": "SCRAGGY", "ABSOL": "BISHARP",
}
DEFAULT_POOLS = {
    "land": ("PATRAT", "LILLIPUP", "PIDOVE", "PURRLOIN", "AUDINO", "MINCCINO",
             "DEERLING", "BLITZLE", "SCRAGGY", "SANDILE", "MIENFOO"),
    "forest": ("SEWADDLE", "VENIPEDE", "JOLTIK", "COTTONEE", "PETILIL",
               "FOONGUS", "KARRABLAST", "SHELMET", "EMOLGA"),
    "cave": ("ROGGENROLA", "WOOBAT", "DRILBUR", "DWEBBLE", "FERROSEED",
             "KLINK", "AXEW", "GOLETT", "DEINO"),
    "water": ("TYMPOLE", "DUCKLETT", "FRILLISH", "BASCULIN", "ALOMOMOLA",
              "TIRTOUGA", "STUNFISK"),
    "elite": ("PAWNIARD", "BISHARP", "MIENFOO", "MIENSHAO", "AXEW", "FRAXURE",
              "HAXORUS", "SOLOSIS", "DUOSION", "REUNICLUS", "DEINO", "ZWEILOUS"),
}
GYM_PARTIES = {
    "TRAINER_LEADER_BROCK": ["ROGGENROLA", "DWEBBLE"],
    "TRAINER_LEADER_MISTY": ["TYMPOLE", "DUCKLETT"],
    "TRAINER_LEADER_LT_SURGE": ["EMOLGA", "BLITZLE", "ZEBSTRIKA"],
    "TRAINER_LEADER_ERIKA": ["SWADLOON", "COTTONEE", "LILLIGANT"],
    "TRAINER_LEADER_KOGA": ["WHIRLIPEDE", "TRUBBISH", "SCOLIPEDE", "GARBODOR"],
    "TRAINER_LEADER_SABRINA": ["GOTHORITA", "DUOSION", "ELGYEM", "GOTHITELLE"],
    "TRAINER_LEADER_BLAINE": ["PANSEAR", "DARUMAKA", "LAMPENT", "DARMANITAN"],
    "TRAINER_LEADER_GIOVANNI": ["KROKOROK", "EXCADRILL", "KROOKODILE", "GOLURK", "KROOKODILE"],
}

LAB_FILE = "data/maps/PalletTown_ProfessorOaksLab/scripts.inc"
WILD_FILE = "src/data/wild_encounters.json"
TRAINERS_FILE = "src/data/trainers.party"
MON_PATTERN = re.compile(r"(?m)^(?P<name>[A-Za-z][^\r\n:]*)\n(?=Level: \d+\b)")
HEADER_PATTERN = re.compile(r"(?m)^=== (?P<name>TRAINER_[A-Z0-9_]+) ===\s*$")


def normalized(value):
    return re.sub(r"[^A-Z0-9]", "", value.upper())


def get_catalog():
    data = json.loads(CATALOG.read_text(encoding="utf-8"))["species"]
    by_name = {normalized(m["symbol"].removeprefix("SPECIES_")): m["symbol"].removeprefix("SPECIES_") for m in data}
    ids = {m["national_id"] for m in data}
    if ids != set(range(494, 650)):
        raise ValueError("Catálogo incompleto: esperados 156 Pokémon #494–649")
    return by_name


def get_replacements(available):
    mapping = {}
    for row in FAMILIES.splitlines():
        old, new = (part.split() for part in row.split(" : "))
        if len(old) != len(new):
            raise ValueError(f"Família com tamanhos diferentes: {row}")
        for source, target in zip(old, new):
            mapping[normalized(source)] = target
    mapping.update({normalized(a): b for a, b in OVERRIDES.items()})
    invalid = {k: v for k, v in mapping.items() if normalized(v) not in available}
    if invalid:
        raise ValueError(f"Destinos inválidos (fora de Unova): {invalid}")
    return mapping


def choose(source, context, available, mapping):
    key = normalized(source.removeprefix("SPECIES_"))
    if key in available:
        return available[key], False
    if key in mapping:
        return available[normalized(mapping[key])], False
    pool = DEFAULT_POOLS[context]
    num = int(hashlib.sha256(f"{context}:{key}".encode()).hexdigest()[:8], 16)
    result = pool[num % len(pool)]
    return available[normalized(result)], True


def habitat(map_name, encounter_kind):
    if encounter_kind in {"water_mons", "fishing_mons"}:
        return "water"
    if any(term in map_name for term in ("CAVE", "TUNNEL", "MT_MOON", "ROCK", "VICTORY_ROAD", "CERULEAN_CAVE")):
        return "cave"
    if any(term in map_name for term in ("FOREST", "BERRY", "SAFARI")):
        return "forest"
    return "land"


def patch_lab(text):
    choices = {"BULBASAUR": "SNIVY", "CHARMANDER": "TEPIG", "SQUIRTLE": "OSHAWOTT"}
    changed = Counter()
    for old, new in choices.items():
        before = f"SPECIES_{old}"
        count = text.count(before)
        text = text.replace(before, f"SPECIES_{new}")
        changed[old] += count
    if sum(changed.values()) not in (0, 6):
        raise ValueError(f"Laboratório inesperado: {dict(changed)}")
    return text, dict(changed), 0


def patch_wild(text, available, mapping):
    wild = json.loads(text)
    changed = Counter()
    fallback = 0
    for group in wild["wild_encounter_groups"]:
        for event in group["encounters"]:
            for field, value in event.items():
                if not field.endswith("_mons") or not isinstance(value, dict):
                    continue
                for mon in value.get("mons", []):
                    old = mon["species"]
                    new, guessed = choose(old, habitat(event["map"], field), available, mapping)
                    mon["species"] = "SPECIES_" + new
                    if old != mon["species"]:
                        changed[old] += 1
                    fallback += int(guessed)
    return json.dumps(wild, indent=2, ensure_ascii=False) + "\n", dict(changed), fallback


def patch_trainers(text, available, mapping):
    changed = Counter()
    fallback = 0
    lines = list(HEADER_PATTERN.finditer(text))
    if not lines:
        raise ValueError("Formato de trainers.party não reconhecido")
    output = [text[:lines[0].start()]]
    for i, found in enumerate(lines):
        end = lines[i + 1].start() if i + 1 < len(lines) else len(text)
        part = text[found.start():end]
        trainer = found.group("name")
        leader_party = GYM_PARTIES.get(trainer)
        index = 0

        def replace_mon(match):
            nonlocal index, fallback
            name = match.group("name")
            if leader_party is not None and index < len(leader_party):
                new, guessed = available[normalized(leader_party[index])], False
            else:
                context = "elite" if any(word in trainer for word in ("ELITE_FOUR", "CHAMPION", "RIVAL")) else "land"
                new, guessed = choose(name, context, available, mapping)
            index += 1
            fallback += int(guessed)
            if normalized(name) != normalized(new):
                changed[name] += 1
            return new + "\n"

        output.append(MON_PATTERN.sub(replace_mon, part))
    return "".join(output), dict(changed), fallback


def apply(game_dir, dry_run=False):
    available = get_catalog()
    mapping = get_replacements(available)
    transformations = (
        (LAB_FILE, lambda text: patch_lab(text)),
        (WILD_FILE, lambda text: patch_wild(text, available, mapping)),
        (TRAINERS_FILE, lambda text: patch_trainers(text, available, mapping)),
    )
    results = []
    for relative, patch in transformations:
        path = game_dir / relative
        if not path.is_file():
            raise FileNotFoundError(f"Arquivo ausente: {path}; use a base pokefirered-expansion compatível")
        original = path.read_text(encoding="utf-8")
        patched, replacements, fallback = patch(original)
        results.append({
            "file": relative,
            "changed_occurrences": sum(replacements.values()),
            "fallback_occurrences": fallback,
            "before_sha256": hashlib.sha256(original.encode()).hexdigest(),
            "after_sha256": hashlib.sha256(patched.encode()).hexdigest(),
        })
        if not dry_run and original != patched:
            backup = path.with_name(path.name + ".unova-backup")
            if not backup.exists():
                shutil.copy2(path, backup)
            path.write_text(patched, encoding="utf-8")
    return {"dry_run": dry_run, "base": str(game_dir), "results": results,
            "notice": "Passagem inicial apenas; sem garantia de build, sprites, movesets ou campanha completa."}


def main():
    p = argparse.ArgumentParser(description="Aplicar a primeira passagem de Unova numa base de FireRed expandida")
    p.add_argument("--game-dir", type=Path, required=True, help="Pasta local de pokefirered-expansion")
    p.add_argument("--dry-run", action="store_true", help="Mostrar alterações sem gravar")
    p.add_argument("--report", type=Path, help="Salvar relatório JSON (opcional)")
    args = p.parse_args()
    report = apply(args.game_dir.resolve(), dry_run=args.dry_run)
    data = json.dumps(report, indent=2, ensure_ascii=False)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(data + "\n", encoding="utf-8")
    print(data)


if __name__ == "__main__":
    main()
