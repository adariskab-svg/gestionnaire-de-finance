"""
💰 Personal Finance Manager
Python project - Everyday life challenges
"""

import json
import os
import sys
from abc import ABC, abstractmethod
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ── Save file ─────────────────────────────────────────────────────────────────
FILE_PATH = "mes_finances.json"

CATEGORIES = [
    "Housing", "Food", "Transport", "Health",
    "Leisure", "Clothing", "Education", "Other"
]


# ── Load / Save ───────────────────────────────────────────────────────────────


def load_data():
    default_data = {
        "transactions": [],
        "users": [],
        "credentials": {
            "username": "admin",
            "password": "admin123",
        },
        "monthly_budget": 0.0,
        "alert_threshold": 75.0,
    }

    if os.path.exists(FILE_PATH):
        try:
            with open(FILE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            return default_data

        if not isinstance(data, dict):
            return default_data

        for key, value in default_data.items():
            data.setdefault(key, value)
        return data

    return default_data


def save_data(data):
    with open(FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ── POO models ───────────────────────────────────────────────────────────────


class Transaction(ABC):
    def __init__(self, description, amount, category, date=None):
        self._description = (description or "No description").strip() or "No description"
        self._category = category
        self._date = date or datetime.now().strftime("%Y-%m-%d")
        self.amount = amount

    @property
    def description(self):
        return self._description

    @property
    def amount(self):
        return self._amount

    @amount.setter
    def amount(self, value):
        value = float(value)
        if value <= 0:
            raise ValueError("Amount must be positive.")
        self._amount = value

    @property
    def category(self):
        return self._category

    @property
    def date(self):
        return self._date

    @property
    @abstractmethod
    
    
    def emoji(self):
        pass

    @property
    @abstractmethod
    def transaction_type(self):
        pass

    @abstractmethod
    def render(self):
        pass

    def to_dict(self):
        return {
            "type": self.transaction_type,
            "description": self.description,
            "amount": self.amount,
            "category": self.category,
            "date": self.date,
        }


class IncomeTransaction(Transaction):
    @property
    def emoji(self):
        return "💵"

    @property
    def transaction_type(self):
        return "income"

    def render(self):
        return f"{self.emoji} [{self.date}] {self.description[:25]:<25} +{self.amount:8.2f} FCFA  ({self.category})"


class ExpenseTransaction(Transaction):
    @property
    def emoji(self):
        return "💸"

    @property
    def transaction_type(self):
        return "expense"

    def render(self):
        return f"{self.emoji} [{self.date}] {self.description[:25]:<25} -{self.amount:8.2f} FCFA  ({self.category})"


class FinanceManager:
    def __init__(self, file_path=FILE_PATH):
        self._file_path = file_path
        self._data = load_data()
        self._transactions = []
        self._users = list(self._data.get("users", []))

    @property
    def transactions(self):
        return list(self._transactions)

    @property
    def users(self):
        return list(self._users)

    @property
    def credentials(self):
        stored_credentials = self._data.get("credentials") or {}
        if not isinstance(stored_credentials, dict):
            stored_credentials = {}
        return {
            "username": str(stored_credentials.get("username", "")).strip(),
            "password": str(stored_credentials.get("password", "")).strip(),
        }

    @property
    def monthly_budget(self):
        return float(self._data.get("monthly_budget", 0.0))

    @monthly_budget.setter
    def monthly_budget(self, value):
        self._data["monthly_budget"] = float(value)
        self.save()

    @property
    def alert_threshold(self):
        return float(self._data.get("alert_threshold", 20.0))

    @alert_threshold.setter
    def alert_threshold(self, value):
        self._data["alert_threshold"] = float(value)
        self.save()

    def load(self):
        self._data = load_data()
        normalized_users = []
        for index, user in enumerate(self._data.get("users", [])):
            if not isinstance(user, dict):
                continue

            normalized_user = dict(user)
            username = str(normalized_user.get("username") or normalized_user.get("name") or "").strip()
            if not username:
                username = f"user_{index + 1}"

            normalized_user["username"] = username
            normalized_user["name"] = str(normalized_user.get("name") or username).strip() or username
            normalized_user["email"] = (normalized_user.get("email") or "").strip() or None
            normalized_user["password"] = str(normalized_user.get("password") or "").strip() or None
            normalized_users.append(normalized_user)

        self._data["users"] = normalized_users
        self._transactions = []
        self._users = list(normalized_users)
        for entry in self._data.get("transactions", []):
            self._transactions.append(self._build_transaction(entry))
        return self._transactions

    def _build_transaction(self, entry):
        tx_type = entry.get("type", "expense")
        transaction_class = IncomeTransaction if tx_type == "income" else ExpenseTransaction
        return transaction_class(
            description=entry["description"],
            amount=entry["amount"],
            category=entry["category"],
            date=entry["date"],
        )

    def save(self):
        self._data["transactions"] = [transaction.to_dict() for transaction in self._transactions]
        self._data["users"] = list(self._users)
        save_data(self._data)

    def add_transaction(self, tx_type, description, amount, category):
        transaction_class = IncomeTransaction if tx_type == "income" else ExpenseTransaction
        transaction = transaction_class(description, amount, category)
        self._transactions.append(transaction)
        self.save()
        return transaction

    def add_user(self, username, password, name=None, email=None):
        cleaned_username = (username or "").strip()
        cleaned_password = (password or "").strip()
        if not cleaned_username:
            raise ValueError("Username is required.")
        if not cleaned_password:
            raise ValueError("Password is required.")

        for existing_user in self._users:
            if str(existing_user.get("username") or "").strip().lower() == cleaned_username.lower():
                raise ValueError("Username already taken.")

        display_name = (name or cleaned_username).strip() or cleaned_username
        user = {
            "username": cleaned_username,
            "password": cleaned_password,
            "name": display_name,
            "email": (email or "").strip() or None,
        }
        self._users.append(user)
        self.save()
        return user

    def update_user(self, index, name=None, email=None):
        if not 0 <= index < len(self._users):
            return None

        user = self._users[index]
        if name is not None:
            cleaned_name = (name or "").strip()
            if not cleaned_name:
                raise ValueError("User name is required.")
            user["name"] = cleaned_name

        if email is not None:
            user["email"] = (email or "").strip() or None

        self.save()
        return user

    def delete_user(self, index):
        if 0 <= index < len(self._users):
            removed = self._users.pop(index)
            self.save()
            return removed
        return None

    def delete_transaction(self, index):
        if 0 <= index < len(self._transactions):
            removed = self._transactions.pop(index)
            self.save()
            return removed
        return None

    def authenticate(self, username, password):
        supplied_username = str(username or "").strip()
        supplied_password = str(password or "").strip()

        stored = self.credentials
        if supplied_username == stored["username"] and supplied_password == stored["password"]:
            return True

        for user in self._users:
            stored_username = str(user.get("username") or "").strip()
            stored_password = str(user.get("password") or "").strip()
            if stored_username == supplied_username and stored_password == supplied_password:
                return True

        return False

    def calculate_monthly_stats(self):
        current_month = datetime.now().strftime("%Y-%m")
        month_transactions = [tx for tx in self._transactions if tx.date.startswith(current_month)]

        total_income = sum(tx.amount for tx in month_transactions if isinstance(tx, IncomeTransaction))
        total_expenses = sum(tx.amount for tx in month_transactions if isinstance(tx, ExpenseTransaction))
        balance = total_income - total_expenses

        categories = {}
        for tx in month_transactions:
            if isinstance(tx, ExpenseTransaction):
                categories[tx.category] = categories.get(tx.category, 0.0) + tx.amount

        return {
            "transactions": month_transactions,
            "total_income": total_income,
            "total_expenses": total_expenses,
            "balance": balance,
            "categories": categories,
        }

    def view_transactions(self):
        print(f"\n  📋  All transactions ({len(self._transactions)} total)")
        line()

        if not self._transactions:
            print("  No transactions recorded.")
            return

        for index, transaction in enumerate(self._transactions, start=1):
            print(f"  {index:3}. {transaction.render()}")
        line()

    def view_users(self):
        print(f"\n  👤  Registered users ({len(self._users)} total)")
        line()

        if not self._users:
            print("  No users registered.")
            return

        for index, user in enumerate(self._users, start=1):
            username = user.get("username") or user.get("name") or "Unknown"
            display_name = user.get("name") or username
            email = user.get("email") or "No email"
            print(f"  {index:3}. {username:<20} | {display_name:<20} | {email}")
        line()

    def search_users(self, query):
        term = (query or "").strip().lower()
        if not term:
            return []

        matches = []
        for index, user in enumerate(self._users, start=1):
            username = (user.get("username") or "").lower()
            name = (user.get("name") or "").lower()
            email = (user.get("email") or "").lower()
            if term in username or term in name or term in email:
                matches.append((index, user))
        return matches

    def monthly_summary(self):
        stats = self.calculate_monthly_stats()
        month_name = datetime.now().strftime("%B %Y")

        print(f"\n  📊  Summary — {month_name}")
        line()
        print(f"  Income        : +{stats['total_income']:10.2f} FCFA")
        print(f"  Expenses      :  {stats['total_expenses']:10.2f} FCFA")
        line("·")
        print(f"  Net balance   : {'+' if stats['balance'] >= 0 else ''}{stats['balance']:10.2f} FCFA  {'✅' if stats['balance'] >= 0 else '⚠️'}")

        if stats["transactions"]:
            print(f"\n  Expenses by category:")
            for category, amount in sorted(stats["categories"].items(), key=lambda item: -item[1]):
                pct_cat = (amount / stats["total_expenses"] * 100) if stats["total_expenses"] > 0 else 0
                print(f"    {category:<15} {amount:8.2f} FCFA  ({pct_cat:.0f}%)")
        line()


class BudgetTracker(FinanceManager):
    def monthly_summary(self):
        stats = self.calculate_monthly_stats()
        month_name = datetime.now().strftime("%B %Y")

        print(f"\n  📊  Summary — {month_name}")
        line()
        print(f"  Income        : +{stats['total_income']:10.2f} FCFA")
        print(f"  Expenses      :  {stats['total_expenses']:10.2f} FCFA")
        line("·")
        print(f"  Net balance   : {'+' if stats['balance'] >= 0 else ''}{stats['balance']:10.2f} FCFA  {'✅' if stats['balance'] >= 0 else '⚠️'}")

        budget = self.monthly_budget
        if budget > 0:
            remaining = budget - stats["total_expenses"]
            pct = (stats["total_expenses"] / budget) * 100
            remaining_pct = max(0.0, (remaining / budget) * 100)
            alert_threshold = self.alert_threshold
            bar = int(pct / 5)
            print(f"\n  Monthly budget : {budget:.2f} FCFA")
            print(f"  Used           : {pct:.1f}%  [{'█'*bar}{'░'*(20-bar)}]")
            print(f"  Remaining      : {remaining:.2f} FCFA  {'✅' if remaining >= 0 else '🚨 Over budget!'}")
            print(f"  Alert threshold: {alert_threshold:.0f}% remaining")
            if remaining_pct <= alert_threshold and remaining >= 0:
                print(f"  🚨 Low budget alert: only {remaining_pct:.1f}% of budget remaining!")

        if stats["transactions"]:
            print(f"\n  Expenses by category:")
            for category, amount in sorted(stats["categories"].items(), key=lambda item: -item[1]):
                pct_cat = (amount / stats["total_expenses"] * 100) if stats["total_expenses"] > 0 else 0
                print(f"    {category:<15} {amount:8.2f} FCFA  ({pct_cat:.0f}%)")
        line()


# ── Display ───────────────────────────────────────────────────────────────────


def line(char="─", n=50):
    print(char * n)


def title(text):
    line()
    print(f"  💰  {text}")
    line()


def main_menu():
    title("PERSONAL FINANCE MANAGER")
    print("  📁  Transactions")
    print("  1. ➕  Add income")
    print("  2. ➖  Add expense")
    print("  3. 📋  View all transactions")
    print("  4. 📊  Monthly summary")
    print("  5. 🎯  Budget settings")
    print("  6. 🗑️   Delete a transaction")
    print()
    print("  👤  Users")
    print("  7. 🆕  Create account")
    print("  8. 📋  View users")
    print("  9. 🔎  Search user")
    print(" 10. ✏️   Edit user")
    print(" 11. 🗑️   Delete user")
    print()
    print(" 12. 🚪  Exit")
    line()


# ── Input helpers ────────────────────────────────────────────────────────────


def enter_amount(prompt):
    while True:
        try:
            amount = float(input(prompt).replace(",", "."))
            if amount <= 0:
                print("  ⚠️  Amount must be positive.")
            else:
                return amount
        except ValueError:
            print("  ⚠️  Please enter a valid number.")


def enter_percentage(prompt):
    while True:
        value = enter_amount(prompt)
        if value <= 100:
            return value
        print("  ⚠️  Please enter a percentage between 0 and 100.")


def choose_category():
    print("\n  Available categories:")
    for i, cat in enumerate(CATEGORIES, 1):
        print(f"    {i}. {cat}")
    while True:
        choice = input("  Your choice (number): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(CATEGORIES):
            return CATEGORIES[int(choice) - 1]
        print("  ⚠️  Invalid choice.")


def register_account(tracker):
    print("\n  🆕  Create a new account")
    try:
        username = input("  Username: ").strip()
        password = input("  Password: ").strip()
        confirm_password = input("  Confirm password: ").strip()
        display_name = input("  Full name (optional): ").strip() or None
        email = input("  Email (optional): ").strip() or None
    except EOFError:
        print("\n  🚫  Account creation interrupted.")
        return False

    if not username:
        print("  ⚠️  Username is required.")
        return False
    if not password:
        print("  ⚠️  Password is required.")
        return False
    if password != confirm_password:
        print("  ⚠️  Passwords do not match.")
        return False

    try:
        tracker.add_user(username, password, name=display_name, email=email)
    except ValueError as exc:
        print(f"  ⚠️  {exc}")
        return False

    print(f"  ✅  Account '{username}' created successfully. You can now log in.")
    return True


def authenticate_user(tracker, attempts=3):
    print("\n  🔐  Login required")
    print("  1. Login")
    print("  2. Create account")
    print("  3. Exit")

    while True:
        choice = input("  Choice: ").strip()

        if choice == "2":
            register_account(tracker)
            print("\n  🔐  Login required")
            print("  1. Login")
            print("  2. Create account")
            print("  3. Exit")
            continue

        if choice == "3":
            print("\n  🚫  Login cancelled. Exiting.")
            return False

        if choice != "1":
            print("  ⚠️  Invalid choice.")
            continue

        for attempt in range(1, attempts + 1):
            try:
                username = input("  Username: ").strip()
                password = input("  Password: ").strip()
            except EOFError:
                print("\n  🚫  Login interrupted. Exiting.")
                return False

            if tracker.authenticate(username, password):
                print("  ✅  Authentication successful.")
                return True

            remaining = attempts - attempt
            print(f"  ⚠️  Invalid credentials. Attempts remaining: {remaining}")

        print("  🚫  Too many failed attempts. Exiting.")
        return False


# ── Features ────────────────────────────────────────────────────────────────


def manage_budget(tracker):
    print(f"\n  🎯  Current monthly budget: {tracker.monthly_budget:.2f} FCFA")
    print(f"  ⚠️  Current low-budget alert: {tracker.alert_threshold:.0f}% remaining")
    line("·")
    print("  1. Change budget")
    print("  2. Change alert threshold")
    print("  3. Back")
    choice = input("  Choice: ").strip()
    if choice == "1":
        new_budget = enter_amount("  New monthly budget (FCFA): ")
        tracker.monthly_budget = new_budget
        print(f"  ✅  Budget set to {new_budget:.2f} FCFA!")
    elif choice == "2":
        new_threshold = enter_percentage("  New alert threshold (%): ")
        tracker.alert_threshold = new_threshold
        print(f"  ✅  Alert threshold set to {new_threshold:.0f}%")


# ── Main program ──────────────────────────────────────────────────────────────


def main():
    tracker = BudgetTracker(FILE_PATH)
    tracker.load()
    tracker.save()

    if not authenticate_user(tracker):
        return

    while True:
        print()
        main_menu()
        choice = input("  Your choice: ").strip()

        if choice == "1":
            description = input("  Description: ").strip() or "No description"
            amount = enter_amount("  Amount (FCFA): ")
            tracker.add_transaction("income", description, amount, "Income")
            print(f"\n  ✅  Income of {amount:.2f} FCFA added!")
        elif choice == "2":
            description = input("  Description: ").strip() or "No description"
            amount = enter_amount("  Amount (FCFA): ")
            category = choose_category()
            tracker.add_transaction("expense", description, amount, category)
            print(f"\n  ✅  Expense of {amount:.2f} FCFA added!")
        elif choice == "3":
            tracker.view_transactions()
        elif choice == "4":
            tracker.monthly_summary()
        elif choice == "5":
            manage_budget(tracker)
        elif choice == "6":
            tracker.view_transactions()
            if not tracker.transactions:
                continue
            tx_index = input("  Number to delete (0 to cancel): ").strip()
            if tx_index.isdigit():
                index = int(tx_index) - 1
                removed = tracker.delete_transaction(index)
                if removed:
                    print(f"  ✅  '{removed.description}' deleted.")
                elif tx_index != "0":
                    print("  ⚠️  Invalid number.")
        elif choice == "7":
            register_account(tracker)
        elif choice == "8":
            tracker.view_users()
        elif choice == "9":
            query = input("  Search term (username, name or email): ").strip()
            matches = tracker.search_users(query)
            print(f"\n  🔎  Search results for '{query or ''}'")
            line()
            if not matches:
                print("  No matching users found.")
            else:
                for index, user in matches:
                    username = user.get("username") or user.get("name") or "Unknown"
                    display_name = user.get("name") or username
                    email = user.get("email") or "No email"
                    print(f"  {index:3}. {username:<20} | {display_name:<20} | {email}")
            line()
        elif choice == "10":
            tracker.view_users()
            if not tracker.users:
                continue
            user_index = input("  User number to edit (0 to cancel): ").strip()
            if user_index.isdigit() and user_index != "0":
                index = int(user_index) - 1
                if not 0 <= index < len(tracker.users):
                    print("  ⚠️  Invalid user number.")
                else:
                    current_user = tracker.users[index]
                    new_name = input(f"  New name ({current_user['name']}): ").strip() or None
                    new_email = input(f"  New email ({current_user['email'] or 'No email'}): ").strip() or None
                    updated = tracker.update_user(index, name=new_name, email=new_email)
                    if updated:
                        print(f"  ✅  User '{updated['name']}' updated!")
                    else:
                        print("  ⚠️  Invalid user number.")
        elif choice == "11":
            tracker.view_users()
            if not tracker.users:
                continue
            user_index = input("  User number to delete (0 to cancel): ").strip()
            if user_index.isdigit() and user_index != "0":
                index = int(user_index) - 1
                if not 0 <= index < len(tracker.users):
                    print("  ⚠️  Invalid user number.")
                else:
                    removed = tracker.delete_user(index)
                    if removed:
                        print(f"  ✅  User '{removed['name']}' deleted.")
                    else:
                        print("  ⚠️  Invalid user number.")
        elif choice == "12":
            print("\n  👋  See you soon! Good money management.\n")
            break
        else:
            print("  ⚠️  Invalid choice. Please enter a number between 1 and 12.")

        input("\n  Press Enter to continue...")


if __name__ == "__main__":
    main()