"""
💰 Personal Finance Manager
PARTIE 3 — Gestionnaire de base : FinanceManager
Membre : ___________________________

Contenu :
  - Classe FinanceManager (logique métier principale)
    · Propriétés : transactions, users, credentials, monthly_budget, alert_threshold
    · Méthodes   : load(), save(), add_transaction(), add_user(), update_user(),
                   delete_user(), delete_transaction(), authenticate(),
                   calculate_monthly_stats(), view_transactions(), view_users(),
                   search_users(), monthly_summary()

Dépendances :
  - partie1_config_persistance.py  →  load_data(), save_data(), FILE_PATH
  - partie2_modeles_transaction.py →  IncomeTransaction, ExpenseTransaction
  - partie4_budget_affichage.py    →  line()  (utilisée dans view_transactions, etc.)
"""

from datetime import datetime

# Ces imports viennent des autres parties du projet
from partie1_config_persistance import load_data, save_data, FILE_PATH
from partie2_modeles_transaction import IncomeTransaction, ExpenseTransaction


# ── FinanceManager ────────────────────────────────────────────────────────────


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
        from partie4_budget_affichage import line
        print(f"\n  📋  All transactions ({len(self._transactions)} total)")
        line()

        if not self._transactions:
            print("  No transactions recorded.")
            return

        for index, transaction in enumerate(self._transactions, start=1):
            print(f"  {index:3}. {transaction.render()}")
        line()

    def view_users(self):
        from partie4_budget_affichage import line
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
        from partie4_budget_affichage import line
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
