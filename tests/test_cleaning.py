import unittest

import pandas as pd

from cleaner.cleaning import clean, profile


def frame():
    return pd.DataFrame(
        {
            "id": ["123456789", "123456789", "12345", "222222222"],
            "name": ["  Sara   Ahmad ", "Sara Ahmad", "Ali", None],
            "phone": ["059 765-4321", "0597654321", "123", "+970599123456"],
            "joined": ["31/12/2025", "31/12/2025", "2026-01-05", "not a date"],
        }
    )


class ProfileTests(unittest.TestCase):
    def test_counts_missing_and_duplicates(self):
        p = profile(frame())
        self.assertEqual(p["rows"], 4)
        self.assertEqual(p["missing_by_column"], {"name": 1})
        self.assertEqual(p["duplicates_by_column"]["id"], 1)


class CleanTests(unittest.TestCase):
    def setUp(self):
        self.out, self.rep = clean(
            frame(), phone_column="phone", id_column="id", date_columns=("joined",)
        )

    def test_whitespace_is_trimmed(self):
        self.assertEqual(self.out.loc[0, "name"], "Sara Ahmad")

    def test_phones_are_normalised_and_invalid_ones_counted(self):
        self.assertEqual(self.out.loc[0, "phone"], "0597654321")
        self.assertEqual(self.out.loc[2, "phone"], "0599123456")
        self.assertEqual(self.out.loc[1, "phone"], "123")  # invalid: kept as-is, but counted
        self.assertEqual(self.rep.invalid_phones, 1)

    def test_invalid_ids_are_counted_but_rows_kept(self):
        self.assertEqual(self.rep.invalid_ids, 1)
        self.assertIn("12345", set(self.out["id"]))

    def test_dates_become_iso_and_bad_dates_become_missing(self):
        self.assertEqual(self.out.loc[0, "joined"], "2025-12-31")
        self.assertEqual(self.out.loc[1, "joined"], "2026-01-05")  # ISO input must not be day/month swapped
        self.assertTrue(pd.isna(self.out.loc[2, "joined"]))

    def test_duplicates_are_removed_after_normalising(self):
        self.assertEqual(self.rep.duplicates_removed, 1)
        self.assertEqual((self.rep.rows_in, self.rep.rows_out), (4, 3))

    def test_input_is_not_modified(self):
        original = frame()
        clean(original, phone_column="phone")
        pd.testing.assert_frame_equal(original, frame())

    def test_can_keep_duplicates(self):
        _, rep = clean(frame(), phone_column="phone", drop_duplicates=False)
        self.assertEqual(rep.duplicates_removed, 0)


if __name__ == "__main__":
    unittest.main()
