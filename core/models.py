"""
Data models and constants for Pakistani Financial Tracker.
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

# Default Supported Financial Providers in Pakistan
DEFAULT_PROVIDERS = [
    {"name": "JazzCash", "code": "8558", "type": "Wallet", "color": "#E53935"},
    {"name": "EasyPaisa", "code": "3737", "type": "Wallet", "color": "#43A047"},
    {"name": "SadaPay", "code": "SadaPay", "type": "Fintech", "color": "#00E5FF"},
    {"name": "NayaPay", "code": "NayaPay", "type": "Fintech", "color": "#FF6D00"},
    {"name": "Meezan Bank", "code": "8267", "type": "Islamic Bank", "color": "#1B5E20"},
    {"name": "HBL", "code": "4250", "type": "Commercial Bank", "color": "#004D40"},
    {"name": "Bank Alfalah", "code": "8222", "type": "Commercial Bank", "color": "#C2185B"},
    {"name": "UBL", "code": "8257", "type": "Commercial Bank", "color": "#1565C0"},
    {"name": "MCB", "code": "6222", "type": "Commercial Bank", "color": "#F57C00"},
    {"name": "Faysal Bank", "code": "9672", "type": "Islamic Bank", "color": "#4E342E"},
    {"name": "Standard Chartered", "code": "SCB", "type": "Commercial Bank", "color": "#0277BD"},
    {"name": "Cash Wallet", "code": "CASH", "type": "Cash", "color": "#7CB342"},
]

# Default Categories tailored to Pakistani household and business spending
DEFAULT_CATEGORIES = [
    # Expenses
    {"name": "Bills & Utilities (KE/LESCO/SNGPL/PTCL)", "type": "Expense", "icon": "💡"},
    {"name": "Groceries & Supermarket", "type": "Expense", "icon": "🛒"},
    {"name": "Fuel & Transport (Careem/Bykea/Shell/PSO)", "type": "Expense", "icon": "⛽"},
    {"name": "Food & Dining", "type": "Expense", "icon": "🍔"},
    {"name": "Mobile Load & Packages", "type": "Expense", "icon": "📱"},
    {"name": "Shopping & Retail", "type": "Expense", "icon": "🛍️"},
    {"name": "Health & Medical", "type": "Expense", "icon": "💊"},
    {"name": "Education & Fees", "type": "Expense", "icon": "📚"},
    {"name": "Cash Withdrawal (ATM)", "type": "Expense", "icon": "🏧"},
    {"name": "Bank & Transfer Fees", "type": "Expense", "icon": "💳"},
    {"name": "Money Transfer Sent", "type": "Expense", "icon": "📤"},
    {"name": "Other Expenses", "type": "Expense", "icon": "📦"},
    # Incomes
    {"name": "Salary / Income", "type": "Income", "icon": "💰"},
    {"name": "Money Transfer Received", "type": "Income", "icon": "📥"},
    {"name": "Business / Freelance", "type": "Income", "icon": "💻"},
    {"name": "Cash Deposit", "type": "Income", "icon": "🏦"},
    {"name": "Other Income", "type": "Income", "icon": "💵"},
]

@dataclass
class ParsedTransaction:
    provider: str
    trans_type: str  # "Debit" or "Credit"
    amount: float
    date_str: str
    recipient_or_sender: str
    ref_id: str
    fee: float = 0.0
    balance_after: Optional[float] = None
    category: str = "Other Expenses"
    raw_text: str = ""
    source_channel: str = "SMS"
    account_name: str = ""
