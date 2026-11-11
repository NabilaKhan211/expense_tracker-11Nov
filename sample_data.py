"""Generate demo data in data/expenses.json so you can try the app quickly."""
import expense_tracker as et

d = et.new_data()
rows = [
    ("2026-11-01", 6500, "Rent", "November rent share"),
    ("2026-11-01", 320, "Food", "Groceries"),
    ("2026-11-02", 80, "Transport", "Auto + bus"),
    ("2026-11-03", 450, "Utilities", "Electricity bill"),
    ("2026-11-04", 199, "Entertainment", "OTT subscription"),
    ("2026-11-05", 150, "Food", "Lunch with friends"),
    ("2026-11-06", 1200, "Shopping", "Shoes"),
    ("2026-11-07", 90, "Health", "Pharmacy"),
    ("2026-11-08", 540, "Education", "Python course book"),
    ("2026-11-09", 210, "Food", "Weekend dinner"),
    ("2026-11-10", 60, "Transport", "Metro card top-up"),
    ("2026-11-11", 120, "Food", "Cafe"),
    ("2026-10-15", 280, "Food", "Groceries"),
    ("2026-10-22", 700, "Shopping", "Clothes"),
]
for r in rows:
    et.add_expense(d, *r)
et.set_budget(d, "2026-11", 12000)
et.set_budget(d, "2026-11", 1500, "Food")
et.set_budget(d, "2026-11", 1000, "Shopping")
et.save_data(d)
print(f"Wrote {len(d['expenses'])} sample expenses to {et.DATA_FILE}")