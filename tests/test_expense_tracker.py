import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import expense_tracker as et


def sample():
    d = et.new_data()
    et.add_expense(d, "2026-11-01", "250", "food", "Groceries")
    et.add_expense(d, "2026-11-01", "60.50", "Transport", "Auto fare")
    et.add_expense(d, "2026-11-05", "1200", "Shopping", "Shoes")
    et.add_expense(d, "2026-10-20", "300", "Food", "Dinner out")
    return d


class ValidationTests(unittest.TestCase):
    def test_amount_valid(self):
        self.assertEqual(et.validate_amount("1,250.456"), 1250.46)

    def test_amount_invalid(self):
        for bad in ["abc", "-5", "0", "", None, "nan", "inf"]:
            with self.assertRaises(ValueError):
                et.validate_amount(bad)

    def test_date(self):
        self.assertEqual(et.validate_date("2026-02-03"), "2026-02-03")
        for bad in ["2026-13-01", "03/02/2026", "2026-02-30"]:
            with self.assertRaises(ValueError):
                et.validate_date(bad)

    def test_month(self):
        self.assertEqual(et.validate_month("2026-11"), "2026-11")
        with self.assertRaises(ValueError):
            et.validate_month("11-2026")

    def test_category_case_insensitive_and_unknown(self):
        d = et.new_data()
        self.assertEqual(et.validate_category("fOOd", d), "Food")
        with self.assertRaises(ValueError):
            et.validate_category("Gambling", d)


class CrudTests(unittest.TestCase):
    def test_add_assigns_incrementing_ids(self):
        d = sample()
        self.assertEqual([e["id"] for e in d["expenses"]], [1, 2, 3, 4])

    def test_edit_partial_and_atomic(self):
        d = sample()
        et.edit_expense(d, 1, amount="275")
        self.assertEqual(et.find_expense(d, 1)["amount"], 275.0)
        with self.assertRaises(ValueError):
            et.edit_expense(d, 1, amount="500", category="Nope")
        self.assertEqual(et.find_expense(d, 1)["amount"], 275.0)  # unchanged

    def test_delete(self):
        d = sample()
        et.delete_expense(d, 2)
        self.assertEqual(len(d["expenses"]), 3)
        with self.assertRaises(KeyError):
            et.find_expense(d, 2)

    def test_category_add_delete_rules(self):
        d = sample()
        self.assertEqual(et.add_category(d, "pets"), "Pets")
        with self.assertRaises(ValueError):
            et.add_category(d, "PETS")
        with self.assertRaises(ValueError):
            et.delete_category(d, "Food")  # in use
        et.delete_category(d, "Pets")


class SearchTests(unittest.TestCase):
    def test_filters(self):
        d = sample()
        self.assertEqual(len(et.search_expenses(d, keyword="groc")), 1)
        self.assertEqual(len(et.search_expenses(d, category="food")), 2)
        self.assertEqual(len(et.search_expenses(d, start="2026-11-01", end="2026-11-01")), 2)
        self.assertEqual(len(et.search_expenses(d, min_amount="250", max_amount="400")), 2)
        self.assertEqual(len(et.search_expenses(d)), 4)


class SummaryTests(unittest.TestCase):
    def test_totals(self):
        d = sample()
        self.assertEqual(et.daily_total(d, "2026-11-01"), 310.5)
        self.assertEqual(et.monthly_total(d, "2026-11"), 1510.5)
        self.assertEqual(et.category_totals(d, "2026-11"),
                         {"Shopping": 1200.0, "Food": 250.0, "Transport": 60.5})
        self.assertEqual(list(et.daily_breakdown(d, "2026-11")), ["2026-11-01", "2026-11-05"])

    def test_budget_status(self):
        d = sample()
        et.set_budget(d, "2026-11", "2000")
        et.set_budget(d, "2026-11", "200", "Food")
        st = et.budget_status(d, "2026-11")
        self.assertEqual(st["remaining"], 489.5)
        self.assertEqual(st["percent"], 75.5)
        self.assertEqual(st["categories"][0]["percent"], 125.0)
        self.assertEqual(et.budget_alert(125.0), "OVER BUDGET")
        self.assertEqual(et.budget_alert(85), "Warning: 80%+ used")
        self.assertEqual(et.budget_alert(10), "On track")

    def test_no_budget(self):
        st = et.budget_status(sample(), "2026-11")
        self.assertIsNone(st["percent"])


class StorageTests(unittest.TestCase):
    def test_json_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "x", "e.json")
            d = sample()
            et.save_data(d, p)
            self.assertEqual(et.load_data(p), d)

    def test_missing_file(self):
        self.assertEqual(et.load_data("/nonexistent/e.json"), et.new_data())

    def test_corrupt_file_is_backed_up(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "e.json")
            with open(p, "w") as f:
                f.write("{not json")
            self.assertEqual(et.load_data(p), et.new_data())
            self.assertTrue(os.path.exists(p + ".corrupt"))

    def test_csv_roundtrip_and_bad_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "e.csv")
            d = sample()
            et.export_csv(d, p)
            n, errs = et.import_csv(et.new_data(), p)
            self.assertEqual((n, errs), (4, []))
            with open(p, "a") as f:
                f.write("9,not-a-date,10,Food,bad\n9,2026-11-02,-4,Food,bad\n")
            n, errs = et.import_csv(et.new_data(), p)
            self.assertEqual((n, len(errs)), (4, 2))


if __name__ == "__main__":
    unittest.main()