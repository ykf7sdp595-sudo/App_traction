"""Vérifications indépendantes de l'interface : python -m unittest -v."""

from pathlib import Path
import unittest

from readers import ImportErrorDetail, column_values, read_measurement


class ReaderTests(unittest.TestCase):
    def test_reference_exports(self):
        folder = Path(__file__).parent
        cases = [("Crimp tensile - cosse_1.TRA", 941, 1, 65.37660217285),
                 ("Force insertion  retention contact.CSV", 478, 1, 0.3055521249771),
                 ("Data_260602_155441.txt", 6797, 2, 173.65)]
        for name, count, force_column, maximum in cases:
            with self.subTest(name=name):
                data = read_measurement((folder / name).read_bytes())
                self.assertEqual(len(data.rows), count)
                self.assertAlmostEqual(max(r[force_column] for r in data.rows), maximum)

    def test_txt_keeps_both_groups_and_time_origin(self):
        data = read_measurement((Path(__file__).parent / "Data_260602_155441.txt").read_bytes())
        self.assertEqual(len(data.headers), 6)
        self.assertEqual(data.rows[0][0], 3.839)
        self.assertEqual(data.rows[-1][0], 10.635)
        self.assertEqual(min(r[1] for r in data.rows), -2.067)

    def test_units_and_acquisition_order(self):
        data = read_measurement(b"Allongement;Force standard\n0;1\n2;2\n1;-3\n")
        self.assertEqual(column_values(data, 0, "displacement", "mm"), [0, 2, 1])
        self.assertEqual(column_values(data, 1, "force", "kN"), [1000, 2000, -3000])

    def test_invalid_files_are_not_silently_truncated(self):
        for content in (b"", b"unknown", b"Allongement;Force standard\n", b"Allongement;Force standard\n1;NaN", b"Allongement;Force standard\n0;1\n2;\n3;4", b"1;2;3\t4;5;6\n7;8\t9;10;11;12"):
            with self.subTest(content=content), self.assertRaises(ImportErrorDetail):
                read_measurement(content)

    def test_decimal_comma_and_bom(self):
        source = "Allongement;Force standard\n0,5;1,5e+01\n"
        for encoding in ("utf-8-sig", "utf-16", "cp1252"):
            self.assertEqual(read_measurement(source.encode(encoding)).rows, ((0.5, 15.0),))


if __name__ == "__main__":
    unittest.main()
