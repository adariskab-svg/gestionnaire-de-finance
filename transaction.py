

from abc import ABC, abstractmethod
from datetime import datetime
# ── POO models ───────────────────────────────────────────────────────────────


class Transaction(ABC):
    def _init_(self, description, amount, category, date=None):
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
