"""Testes rápidos, gratuitos e sem ROM, de integridade da ferramenta."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from apply_unova import (  # noqa: E402
    LAB_FILE, TRAINERS_FILE, WILD_FILE, apply,
    get_catalog, get_replacements, patch_lab, patch_trainers, patch_wild
)


class UnovaTests(unittest.TestCase):
    def setUp(self):
        self.available = get_catalog()
        self.mapping = get_replacements(self.available)

    def test_catalog_has_every_gen5_species(self):
        self.assertEqual(len(self.available), 156)
        self.assertEqual(self.available["SNIVY"], "SNIVY")
        self.assertIn("GENESECT", self.available)
        self.assertIn("DARMANITANSTANDARD", self.available)

    def test_starter_event_and_rival(self):
        lab = (
            "setvar PLAYER_STARTER_SPECIES, SPECIES_BULBASAUR\n"
            "setvar RIVAL_STARTER_SPECIES, SPECIES_CHARMANDER\n"
            "setvar PLAYER_STARTER_SPECIES, SPECIES_SQUIRTLE\n"
            "setvar RIVAL_STARTER_SPECIES, SPECIES_BULBASAUR\n"
            "setvar PLAYER_STARTER_SPECIES, SPECIES_CHARMANDER\n"
            "setvar RIVAL_STARTER_SPECIES, SPECIES_SQUIRTLE\n"
        )
        updated, changed, fallback = patch_lab(lab)
        self.assertEqual(sum(changed.values()), 6)
        self.assertIn("SPECIES_SNIVY", updated)
        self.assertIn("SPECIES_TEPIG", updated)
        self.assertIn("SPECIES_OSHAWOTT", updated)
        self.assertNotIn("SPECIES_BULBASAUR", updated)
        self.assertEqual(fallback, 0)
        self.assertEqual(patch_lab(updated)[0], updated)

    def test_encounter_rates_and_levels_preserved(self):
        encounters = {
            "wild_encounter_groups": [{
                "label": "gWildMonHeaders", "encounters": [{
                    "map": "MAP_ROUTE1", "base_label": "sRoute1_FireRed",
                    "land_mons": {
                        "encounter_rate": 21,
                        "mons": [
                            {"min_level": 2, "max_level": 4, "species": "SPECIES_PIDGEY"},
                            {"min_level": 3, "max_level": 5, "species": "SPECIES_RATTATA"},
                            {"min_level": 4, "max_level": 7, "species": "SPECIES_HOOTHOOT"},
                        ],
                    },
                }, {
                    "map": "MAP_SEAFOAM_ISLANDS", "base_label": "sSeafoam_FireRed",
                    "water_mons": {"encounter_rate": 15, "mons": [
                        {"min_level": 20, "max_level": 32, "species": "SPECIES_PSYDUCK"}
                    ]},
                }],
            }],
        }
        result, count, fallback = patch_wild(json.dumps(encounters), self.available, self.mapping)
        parsed = json.loads(result)
        self.assertEqual(sum(count.values()), 4)
        self.assertEqual(fallback, 0)
        route = parsed["wild_encounter_groups"][0]["encounters"][0]["land_mons"]
        self.assertEqual(route["encounter_rate"], 21)
        self.assertEqual([(m["min_level"], m["max_level"]) for m in route["mons"]],
                         [(2, 4), (3, 5), (4, 7)])
        for event in parsed["wild_encounter_groups"][0]["encounters"]:
            for field, config in event.items():
                if field.endswith("_mons"):
                    for mon in config["mons"]:
                        self.assertIn(mon["species"][8:].replace("_", ""), self.available)
        self.assertEqual(patch_wild(result, self.available, self.mapping)[0], result)

    def test_trainers_and_leader_team(self):
        raw = (
            "=== TRAINER_YOUNGSTER_1 ===\nName: JOE\nClass: Youngster\n\n"
            "Rattata\nLevel: 5\nIVs: 0 HP\n\n"
            "=== TRAINER_LEADER_BROCK ===\nName: BROCK\nClass: Leader\n\n"
            "Geodude\nLevel: 12\nIVs: 0 HP\n\n"
            "Onix\nLevel: 14\nIVs: 0 HP\n"
        )
        result, count, fallback = patch_trainers(raw, self.available, self.mapping)
        self.assertEqual(sum(count.values()), 3)
        self.assertEqual(fallback, 0)
        self.assertIn("PATRAT\nLevel: 5", result)
        self.assertIn("ROGGENROLA\nLevel: 12", result)
        self.assertIn("DWEBBLE\nLevel: 14", result)
        self.assertEqual(patch_trainers(result, self.available, self.mapping)[0], result)

    def test_apply_backup_and_idempotency(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            for relative, contents in [
                (LAB_FILE, "setvar PLAYER_STARTER_SPECIES, SPECIES_BULBASAUR\n" +
                 "setvar RIVAL_STARTER_SPECIES, SPECIES_CHARMANDER\n" +
                 "setvar PLAYER_STARTER_SPECIES, SPECIES_SQUIRTLE\n" +
                 "setvar RIVAL_STARTER_SPECIES, SPECIES_BULBASAUR\n" +
                 "setvar PLAYER_STARTER_SPECIES, SPECIES_CHARMANDER\n" +
                 "setvar RIVAL_STARTER_SPECIES, SPECIES_SQUIRTLE\n"),
                (WILD_FILE, json.dumps({"wild_encounter_groups": [{
                    "label": "x", "encounters": [{"map": "MAP_ROUTE1", "land_mons": {
                        "encounter_rate": 20, "mons": [
                            {"min_level": 2, "max_level": 4, "species": "SPECIES_PIDGEY"}
                        ]}}]}]})),
                (TRAINERS_FILE, "=== TRAINER_YOUNGSTER_1 ===\nName: Joe\n\n"
                 "Rattata\nLevel: 4\nIVs: 0 HP\n"),
            ]:
                path = d / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(contents, encoding="utf-8")
            dry = apply(d, dry_run=True)
            self.assertTrue(dry["dry_run"])
            self.assertIn("SPECIES_BULBASAUR", (d / LAB_FILE).read_text())
            result = apply(d)
            self.assertEqual(len(result["results"]), 3)
            for relative in (LAB_FILE, WILD_FILE, TRAINERS_FILE):
                path = d / relative
                self.assertTrue(path.with_name(path.name + ".unova-backup").exists())
            snapshot = [(d / p).read_text() for p in (LAB_FILE, WILD_FILE, TRAINERS_FILE)]
            apply(d)
            self.assertEqual(snapshot, [(d / p).read_text()
                                        for p in (LAB_FILE, WILD_FILE, TRAINERS_FILE)])


if __name__ == "__main__":
    unittest.main()
