import enum


class OperationType(str, enum.Enum):
    sale = "sale"
    purchase = "purchase"
    expense = "expense"