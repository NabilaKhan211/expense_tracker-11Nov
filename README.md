# Personal Expense & Budget Tracker

A command-line Python application to record daily expenses, organise them into categories, set monthly budgets and generate spending summaries. Built as **Day 3 project** of the Veda Technology Python internship.

## Features

| Deliverable | What it does |
|---|---|
| Expense tracking | Add, edit, delete and view expenses (each with ID, date, amount, category, description) |
| Category management | 9 built-in categories; add custom ones; deleting a category in use is blocked |
| Monthly budgets | Set an overall budget and/or per-category budgets for any month |
| Budget alerts | Live warning at 80% used and **OVER BUDGET** alert beyond 100% |
| Spending summary | Monthly total, category-wise totals with bar chart, daily totals, average per active day, highest-spending day |
| Data storage | Persistent **JSON** storage (auto-save after each action, atomic writes) plus **CSV export/import** |
| Search & filtering | Combine keyword, category, date range and amount range |
| Validation | Amount (positive number), date (`YYYY-MM-DD`), month (`YYYY-MM`) and category checks with friendly messages |

## Python concepts used

- **Functions** - one focused function per operation (`add_expense`, `edit_expense`, `delete_expense`, `search_expenses`, `budget_status`, ...)
- **Collections** - lists of expense dicts, dict for budgets, `defaultdict` for totals, sorting with key functions
- **File handling** - JSON persistence, CSV reading/writing, atomic save via temp file, corrupt-file backup
- **datetime** - `datetime.strptime` validation, default-to-today, month/day grouping
- **Exception handling** - `ValueError` for invalid input, `KeyError` for missing IDs, `JSONDecodeError`/`OSError` for file problems, `KeyboardInterrupt`/`EOFError` handled gracefully
- **Data processing** - aggregation by day / month / category, budget percentage and remaining calculations

## Project structure

```
expense-tracker/
├── expense_tracker.py          # main application (logic + CLI menu)
├── sample_data.py              # loads demo data for a quick try-out
├── tests/test_expense_tracker.py   # 17 unit tests
├── data/                       # expenses.json is created here at runtime
├── docs/
│   ├── sample_output.txt       # captured demo session
│   └── Project_Report.pdf      # project report
├── README.md
└── .gitignore
```

## Getting started

Requires **Python 3.8+**. No third-party packages needed.

```bash
git clone https://github.com/<your-username>/expense-tracker.git
cd expense-tracker

python sample_data.py      # optional: load demo data
python expense_tracker.py  # start the app
```

## Usage

```
 1. Add expense                      6. Manage categories
 2. Edit expense                     7. Set monthly budget
 3. Delete expense                   8. Spending summary & budget status
 4. View all expenses                9. Export to CSV
 5. Search / filter expenses        10. Import from CSV
 0. Save & exit
```

- Leave **date** blank when adding to use today's date.
- When editing, leave a field blank to keep its current value.
- For a per-category budget, enter the category name in option 7; leave it blank for the overall budget.
- CSV import needs columns `date, amount, category, description`; invalid rows are skipped and reported.

### Sample output (summary for 2026-11)

```
=== Spending summary for 2026-11 ===
  Total spent: 9919.00

  By category:
  Rent              6500.00  ##############################
  Shopping          1200.00  ######
  Food               800.00  ####
  ...
  Budget: 12000.00   Remaining: 2081.00   Used: 82.7%  -> Warning: 80%+ used
    Food              800.00 / 1500.00   (53.3%) On track
    Shopping         1200.00 / 1000.00   (120.0%) OVER BUDGET
```

See `docs/sample_output.txt` for the full session.

## Data format (`data/expenses.json`)

```json
{
  "next_id": 3,
  "categories": ["Food", "Transport", "..."],
  "expenses": [
    {"id": 1, "date": "2026-11-01", "amount": 320.0, "category": "Food", "description": "Groceries"}
  ],
  "budgets": {
    "2026-11": {"overall": 12000.0, "categories": {"Food": 1500.0}}
  }
}
```

## Running the tests

```bash
python -m unittest discover -s tests -v
```

The 17 tests cover validation, CRUD, search filters, totals, budget status/alerts, JSON round-trip, corrupt-file recovery and CSV import/export.

## Design decisions

- **Logic separated from I/O** - core functions take and return plain data, so they are unit-testable without typing into the menu.
- **Validate before mutate** - `edit_expense` checks every new value first, so a bad value never leaves an expense half-edited.
- **Atomic saves** - data is written to a temp file and then renamed, so a crash can't corrupt the data file.
- **Dates as ISO strings** - `YYYY-MM-DD` sorts correctly as text, which keeps filtering and month grouping simple.

## Possible improvements

Recurring expenses, charts with matplotlib, multi-user profiles, currency selection, and a GUI or web front-end.

## Author

**Nabila Khan** - Python Intern, Veda Technology