import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from patch_pokedex import patch_constants, patch_pokemon, patch_screen, apply_regional_pokedex, CATALOG


class UnovaPokedexTest(unittest.TestCase):
    def setUp(self):
        self.catalog = json.loads(CATALOG.read_text(encoding="utf-8"))["species"]

    def test_156_regional_entries_in_correct_order(self):
        source = """const int beginning = 0;
static const enum NationalDexOrder sKantoToNationalOrder[KANTO_DEX_COUNT] =
{
    KANTO_TO_NATIONAL(BULBASAUR),
    KANTO_TO_NATIONAL(MEW),
};
enum NationalDexOrder KantoToNationalDexNum(enum KantoDexOrder kantoNum)
{
    if (KANTO_DEX_START <= kantoNum && kantoNum < KANTO_DEX_END)
        return sKantoToNationalOrder[kantoNum - KANTO_DEX_START];
    return NATIONAL_DEX_NONE;
}
"""
        changed = patch_pokemon(source, self.catalog)
        self.assertEqual(changed.count("NATIONAL_DEX_VICTINI"), 1)
        self.assertIn("NATIONAL_DEX_SNIVY", changed)
        self.assertIn("NATIONAL_DEX_GENESECT", changed)
        self.assertNotIn("KANTO_TO_NATIONAL(BULBASAUR)", changed)
        self.assertIn("kantoNum < KANTO_DEX_START + KANTO_DEX_COUNT", changed)
        self.assertEqual(patch_pokemon(changed, self.catalog), changed)

    def test_count_and_screen(self):
        source = "#define KANTO_DEX_COUNT KANTO_DEX_MEW\n"
        updated = patch_constants(source)
        self.assertIn("KANTO_DEX_COUNT 156", updated)
        self.assertEqual(patch_constants(updated), updated)
        self.assertEqual(patch_screen("for (i = KANTO_DEX_START; i < KANTO_DEX_END; i++)"),
                         "for (i = KANTO_DEX_START; i < KANTO_DEX_START + KANTO_DEX_COUNT; i++)")

    def test_files_are_modified_with_backups(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            fixtures = {
                "include/constants/pokedex.h": "#define KANTO_DEX_COUNT KANTO_DEX_MEW\n",
                "src/pokemon.c": ("static const enum NationalDexOrder sKantoToNationalOrder[KANTO_DEX_COUNT] =\n"
                                  "{\n KANTO_TO_NATIONAL(BULBASAUR),\n};\n"
                                  "if (KANTO_DEX_START <= kantoNum && kantoNum < KANTO_DEX_END)"),
                "src/pokedex_screen.c": "for (i = KANTO_DEX_START; i < KANTO_DEX_END; i++)",
            }
            for relative, content in fixtures.items():
                file = folder / relative
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_text(content)
            report = apply_regional_pokedex(folder)
            self.assertEqual(report["regional_entries"], 156)
            self.assertEqual(list(report["files"].values()), ["modified"] * 3)
            for relative in fixtures:
                p = folder / relative
                self.assertTrue(p.with_name(p.name + ".unova-backup").is_file())
            self.assertTrue(all(x == "unchanged" for x in apply_regional_pokedex(folder)["files"].values()))


if __name__ == "__main__":
    unittest.main()
