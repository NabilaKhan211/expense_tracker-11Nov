"""
Personal Expense & Budget Tracker
---------------------------------
A command-line application to record daily expenses, organise them into
categories, set monthly budgets and generate spending summaries.

Concepts practised: functions, collections (list/dict/set), file handling
(JSON + CSV), datetime operations, exception handling, data processing.
"""

import csv
import json
import os
from collections import defaultdict
from datetime import date, datetime

DATA_FILE = os.path.join("data", "expenses.json")
DATE_FORMAT = "%Y-%m-%d"
DEFAULT_CATEGORIES = ["Food", "Transport", "Rent", "Utilities",
                      "Entertainment", "Health", "Shopping", "Education", "Other"]


# --------------------------------------------------------------------------
# Validation helpers
# --------------------------------------------------------------------------
def validate_amount(value):
    """Return a positive float rounded to 2 decimals or raise ValueError."""
    try:
        amount = float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        raise ValueError("Amount must be a number (e.g. 250 or 99.50).")
    if amount != amount or amount in (float("inf"), float("-inf")):
        raise ValueError("Amount must be a finite number.")
    if amount <= 0:
        raise ValueError("Amount must be greater than zero.")
    return round(amount, 2)


def validate_date(value):
    """Return a date string in YYYY-MM-DD format; empty input means today."""
    value = (value or "").strip()
    if not value:
        return date.today().strftime(DATE_FORMAT)
    try:
        parsed = datetime.strptime(value, DATE_FORMAT)
    except ValueError:
        raise ValueError("Date must be in YYYY-MM-DD format (e.g. 2026-11-11).")
    return parsed.strftime(DATE_FORMAT)


def validate_month(value):
    """Return a month string in YYYY-MM format; empty input means this month."""
    value = (value or "").strip()
    if not value:
        return date.today().strftime("%Y-%m")
    try:
        parsed = datetime.strptime(value, "%Y-%m")
    except ValueError:
        raise ValueError("Month must be in YYYY-MM format (e.g. 2026-11).")
    return parsed.strftime("%Y-%m")


def validate_category(value, data):
    """Match a category case-insensitively against the known categories."""
    value = (value or "").strip()
    if not value:
        raise ValueError("Category cannot be empty.")
    for cat in data["categories"]:
        if cat.lower() == value.lower():
            return cat
    raise ValueError(f"Unknown category '{value}'. Available: "
                     f"{', '.join(data['categories'])}")


# --------------------------------------------------------------------------
# Storage (JSON) and export/import (CSV)
# --------------------------------------------------------------------------
def new_data():
    return {"next_id": 1, "categories": list(DEFAULT_CATEGORIES),
            "expenses": [], "budgets": {}}


def load_data(path=DATA_FILE):
    """Load data from JSON. Missing file -> fresh data. Corrupt file -> backup."""
    if not os.path.exists(path):
        return new_data()
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for key, default in new_data().items():
            data.setdefault(key, default)
        return data
    except (json.JSONDecodeError, OSError) as err:
        backup = path + ".corrupt"
        try:
            os.replace(path, backup)
            print(f"[!] Could not read {path} ({err}). Saved copy as {backup}.")
        except OSError:
            print(f"[!] Could not read {path} ({err}). Starting fresh.")
        return new_data()


def save_data(data, path=DATA_FILE):
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)  # atomic write avoids half-written files


CSV_FIELDS = ["id", "date", "amount", "category", "description"]


def export_csv(data, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for e in data["expenses"]:
            writer.writerow({k: e[k] for k in CSV_FIELDS})
    return len(data["expenses"])


def import_csv(data, path):
    """Import expenses from CSV (columns: date, amount, category, description).
    Invalid rows are skipped and reported. Returns (imported, errors)."""
    imported, errors = 0, []
    with open(path, newline="", encoding="utf-8") as f:
        for line_no, row in enumerate(csv.DictReader(f), start=2):
            try:
                if row.get("category", "").strip().lower() not in \
                        [c.lower() for c in data["categories"]]:
                    add_category(data, row.get("category", ""))
                add_expense(data, row.get("date"), row.get("amount"),
                            row.get("category"), row.get("description", ""))
                imported += 1
            except ValueError as err:
                errors.append(f"line {line_no}: {err}")
    return imported, errors


# --------------------------------------------------------------------------
# Category management
# --------------------------------------------------------------------------
def add_category(data, name):
    name = (name or "").strip().title()
    if not name:
        raise ValueError("Category name cannot be empty.")
    if name.lower() in [c.lower() for c in data["categories"]]:
        raise ValueError(f"Category '{name}' already exists.")
    data["categories"].append(name)
    return name


def delete_category(data, name):
    name = validate_category(name, data)
    if any(e["category"] == name for e in data["expenses"]):
        raise ValueError(f"'{name}' is used by existing expenses; "
                         "re-categorise or delete them first.")
    data["categories"].remove(name)
    return name


# --------------------------------------------------------------------------
# Expense CRUD
# --------------------------------------------------------------------------
def add_expense(data, date_str, amount, category, description=""):
    expense = {
        "id": data["next_id"],
        "date": validate_date(date_str),
        "amount": validate_amount(amount),
        "category": validate_category(category, data),
        "description": (description or "").strip(),
    }
    data["next_id"] += 1
    data["expenses"].append(expense)
    return expense


def find_expense(data, expense_id):
    for e in data["expenses"]:
        if e["id"] == expense_id:
            return e
    raise KeyError(f"No expense found with ID {expense_id}.")


def edit_expense(data, expense_id, date_str=None, amount=None,
                 category=None, description=None):
    """Update only the fields that are provided (not None / not blank)."""
    expense = find_expense(data, expense_id)
    # validate everything first so a bad value changes nothing
    new_date = validate_date(date_str) if date_str else expense["date"]
    new_amount = validate_amount(amount) if amount not in (None, "") else expense["amount"]
    new_cat = validate_category(category, data) if category else expense["category"]
    expense.update(date=new_date, amount=new_amount, category=new_cat)
    if description is not None and description != "":
        expense["description"] = description.strip()
    return expense


def delete_expense(data, expense_id):
    expense = find_expense(data, expense_id)
    data["expenses"].remove(expense)
    return expense


def sorted_expenses(expenses):
    return sorted(expenses, key=lambda e: (e["date"], e["id"]))


# --------------------------------------------------------------------------
# Search and filtering
# --------------------------------------------------------------------------
def search_expenses(data, keyword=None, category=None, start=None, end=None,
                    min_amount=None, max_amount=None):
    """Filter expenses; every criterion left as None/blank is ignored."""
    results = data["expenses"]
    if keyword:
        kw = keyword.lower()
        results = [e for e in results
                   if kw in e["description"].lower() or kw in e["category"].lower()]
    if category:
        cat = validate_category(category, data)
        results = [e for e in results if e["category"] == cat]
    if start:
        s = validate_date(start)
        results = [e for e in results if e["date"] >= s]
    if end:
        en = validate_date(end)
        results = [e for e in results if e["date"] <= en]
    if min_amount not in (None, ""):
        lo = validate_amount(min_amount)
        results = [e for e in results if e["amount"] >= lo]
    if max_amount not in (None, ""):
        hi = validate_amount(max_amount)
        results = [e for e in results if e["amount"] <= hi]
    return sorted_expenses(results)


# --------------------------------------------------------------------------
# Totals and summaries
# --------------------------------------------------------------------------
def daily_total(data, day):
    day = validate_date(day)
    return round(sum(e["amount"] for e in data["expenses"] if e["date"] == day), 2)


def monthly_total(data, month):
    month = validate_month(month)
    return round(sum(e["amount"] for e in data["expenses"]
                     if e["date"].startswith(month)), 2)


def category_totals(data, month=None):
    """Return {category: total}, optionally restricted to one YYYY-MM month."""
    totals = defaultdict(float)
    for e in data["expenses"]:
        if month is None or e["date"].startswith(month):
            totals[e["category"]] += e["amount"]
    return {k: round(v, 2) for k, v in
            sorted(totals.items(), key=lambda kv: kv[1], reverse=True)}


def daily_breakdown(data, month):
    totals = defaultdict(float)
    for e in data["expenses"]:
        if e["date"].startswith(month):
            totals[e["date"]] += e["amount"]
    return {k: round(v, 2) for k, v in sorted(totals.items())}


# --------------------------------------------------------------------------
# Budgets
# --------------------------------------------------------------------------
def set_budget(data, month, amount, category=None):
    """Set an overall monthly budget, or a per-category one if category given."""
    month = validate_month(month)
    amount = validate_amount(amount)
    entry = data["budgets"].setdefault(month, {"overall": None, "categories": {}})
    if category:
        entry["categories"][validate_category(category, data)] = amount
    else:
        entry["overall"] = amount
    return entry


def budget_status(data, month):
    """Compare spending with budgets for a month. Returns a dict."""
    month = validate_month(month)
    entry = data["budgets"].get(month, {"overall": None, "categories": {}})
    spent = monthly_total(data, month)
    status = {"month": month, "spent": spent, "overall": entry["overall"],
              "remaining": None, "percent": None, "categories": []}
    if entry["overall"]:
        status["remaining"] = round(entry["overall"] - spent, 2)
        status["percent"] = round(spent / entry["overall"] * 100, 1)
    cat_spent = category_totals(data, month)
    for cat, limit in entry["categories"].items():
        s = cat_spent.get(cat, 0.0)
        status["categories"].append({
            "category": cat, "budget": limit, "spent": s,
            "remaining": round(limit - s, 2),
            "percent": round(s / limit * 100, 1)})
    return status


def budget_alert(percent):
    if percent is None:
        return ""
    if percent > 100:
        return "OVER BUDGET"
    if percent >= 80:
        return "Warning: 80%+ used"
    return "On track"


# --------------------------------------------------------------------------
# Display helpers
# --------------------------------------------------------------------------
def print_expenses(expenses):
    if not expenses:
        print("  (no expenses found)")
        return
    print(f"  {'ID':<5}{'Date':<12}{'Category':<15}{'Amount':>10}  Description")
    print("  " + "-" * 62)
    for e in expenses:
        print(f"  {e['id']:<5}{e['date']:<12}{e['category']:<15}"
              f"{e['amount']:>10.2f}  {e['description']}")
    print("  " + "-" * 62)
    print(f"  {'Total':<32}{sum(e['amount'] for e in expenses):>10.2f}"
          f"   ({len(expenses)} records)")


def print_bar(label, value, maximum, width=30):
    filled = int(round(value / maximum * width)) if maximum else 0
    print(f"  {label:<15}{value:>10.2f}  {'#' * filled}")


def print_summary(data, month):
    month = validate_month(month)
    total = monthly_total(data, month)
    print(f"\n=== Spending summary for {month} ===")
    print(f"  Total spent: {total:.2f}")
    cats = category_totals(data, month)
    if not cats:
        print("  No expenses recorded for this month.")
        return
    print("\n  By category:")
    top = max(cats.values())
    for cat, amt in cats.items():
        print_bar(cat, amt, top)
    days = daily_breakdown(data, month)
    print(f"\n  Days with spending: {len(days)}   "
          f"Average per active day: {total / len(days):.2f}")
    worst = max(days, key=days.get)
    print(f"  Highest-spending day: {worst} ({days[worst]:.2f})")
    st = budget_status(data, month)
    if st["overall"]:
        print(f"\n  Budget: {st['overall']:.2f}   Remaining: {st['remaining']:.2f}"
              f"   Used: {st['percent']}%  -> {budget_alert(st['percent'])}")
    for c in st["categories"]:
        print(f"    {c['category']:<14} {c['spent']:>9.2f} / {c['budget']:<9.2f}"
              f" ({c['percent']}%) {budget_alert(c['percent'])}")


# --------------------------------------------------------------------------
# Interactive menu
# --------------------------------------------------------------------------
def ask(prompt):
    return input(prompt).strip()


def ask_int(prompt):
    try:
        return int(ask(prompt))
    except ValueError:
        raise ValueError("Please enter a whole number.")


def menu_add(data):
    print(f"Categories: {', '.join(data['categories'])}")
    e = add_expense(data, ask("Date (YYYY-MM-DD, blank = today): "),
                    ask("Amount: "), ask("Category: "), ask("Description: "))
    print(f"Added expense #{e['id']}: {e['amount']:.2f} on {e['date']} [{e['category']}]")
    # live budget feedback
    st = budget_status(data, e["date"][:7])
    if st["percent"] is not None and st["percent"] >= 80:
        print(f"  ! {budget_alert(st['percent'])} for {st['month']} ({st['percent']}% used)")


def menu_edit(data):
    eid = ask_int("Expense ID to edit: ")
    cur = find_expense(data, eid)
    print(f"Current: {cur}")
    print("Leave a field blank to keep it unchanged.")
    edit_expense(data, eid, ask("New date: "), ask("New amount: "),
                 ask("New category: "), ask("New description: "))
    print("Expense updated.")


def menu_delete(data):
    eid = ask_int("Expense ID to delete: ")
    e = find_expense(data, eid)
    if ask(f"Delete '{e['description'] or e['category']}' ({e['amount']:.2f})? [y/N]: ").lower() == "y":
        delete_expense(data, eid)
        print("Expense deleted.")
    else:
        print("Cancelled.")


def menu_view(data):
    print_expenses(sorted_expenses(data["expenses"]))


def menu_search(data):
    print("Leave any filter blank to skip it.")
    res = search_expenses(data, ask("Keyword: "), ask("Category: "),
                          ask("From date: "), ask("To date: "),
                          ask("Min amount: "), ask("Max amount: "))
    print_expenses(res)


def menu_categories(data):
    print(f"Categories: {', '.join(data['categories'])}")
    action = ask("[a]dd, [d]elete, or Enter to go back: ").lower()
    if action == "a":
        print(f"Added category '{add_category(data, ask('Name: '))}'.")
    elif action == "d":
        print(f"Deleted category '{delete_category(data, ask('Name: '))}'.")


def menu_budget(data):
    month = validate_month(ask("Month (YYYY-MM, blank = this month): "))
    cat = ask("Category (blank = overall budget): ")
    set_budget(data, month, ask("Budget amount: "), cat or None)
    print("Budget saved.")


def menu_summary(data):
    month = ask("Month (YYYY-MM, blank = this month): ")
    print_summary(data, month)
    day = ask("\nDaily total for a date (YYYY-MM-DD, blank to skip): ")
    if day:
        print(f"  Total for {validate_date(day)}: {daily_total(data, day):.2f}")


def menu_export(data):
    path = ask("CSV file to export to [expenses_export.csv]: ") or "expenses_export.csv"
    print(f"Exported {export_csv(data, path)} expenses to {path}.")


def menu_import(data):
    path = ask("CSV file to import: ")
    imported, errors = import_csv(data, path)
    print(f"Imported {imported} expenses.")
    for err in errors:
        print("  skipped", err)


MENU = [
    ("Add expense", menu_add), ("Edit expense", menu_edit),
    ("Delete expense", menu_delete), ("View all expenses", menu_view),
    ("Search / filter expenses", menu_search),
    ("Manage categories", menu_categories), ("Set monthly budget", menu_budget),
    ("Spending summary & budget status", menu_summary),
    ("Export to CSV", menu_export), ("Import from CSV", menu_import),
]


def main():
    data = load_data()
    print("=" * 46)
    print("   PERSONAL EXPENSE & BUDGET TRACKER")
    print("=" * 46)
    while True:
        print("\nMenu")
        for i, (label, _) in enumerate(MENU, start=1):
            print(f"  {i:>2}. {label}")
        print("   0. Save & exit")
        choice = ask("Choose an option: ")
        if choice == "0":
            save_data(data)
            print("Data saved. Goodbye!")
            break
        if not choice.isdigit() or not 1 <= int(choice) <= len(MENU):
            print("Invalid choice, please pick a number from the menu.")
            continue
        try:
            MENU[int(choice) - 1][1](data)
            save_data(data)  # auto-save after every action
        except (ValueError, KeyError, OSError) as err:
            print(f"Error: {err.args[0] if isinstance(err, KeyError) else err}")
        except (KeyboardInterrupt, EOFError):
            print("\nAction cancelled.")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nInterrupted. Goodbye!")