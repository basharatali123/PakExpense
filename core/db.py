"""
SQLite Database Manager for Pakistani Financial Tracker.
Designed for standalone Python Executable (.exe) packaging with portable persistence.
"""
import os
import sys
import sqlite3
import shutil
from typing import List, Dict, Any, Optional
from datetime import datetime
from contextlib import contextmanager
from core.models import DEFAULT_PROVIDERS, DEFAULT_CATEGORIES, ParsedTransaction

def get_database_path() -> str:
    """
    Determine the persistent SQLite database path.
    When running as a PyInstaller bundled .exe:
      - sys.frozen is True.
      - sys.executable points to the .exe location.
      - We store the database right next to the .exe so data persists permanently!
      - If that folder is read-only, fallback to %APPDATA%/PakExpenseTracker/
    """
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        # Running from source code
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    # Test if base_dir is writable
    db_file = os.path.join(base_dir, "pk_finance.db")
    try:
        test_file = os.path.join(base_dir, ".write_test")
        with open(test_file, "w") as f:
            f.write("ok")
        os.remove(test_file)
        return db_file
    except (PermissionError, OSError):
        # Fallback to APPDATA on Windows
        appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
        fallback_dir = os.path.join(appdata, "PakExpenseTracker")
        os.makedirs(fallback_dir, exist_ok=True)
        return os.path.join(fallback_dir, "pk_finance.db")

class DatabaseManager:
    """Encapsulates all SQLite operations, migrations, and seed logic."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or get_database_path()
        self.init_db()

    @contextmanager
    def session(self):
        """Context manager that auto-commits and guarantees connection closure."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        try:
            yield conn
        finally:
            conn.close()

    def init_db(self):
        """Create tables if they don't exist and seed default Pakistani data."""
        with self.session() as conn:
            cursor = conn.cursor()

            # Accounts Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                code TEXT,
                account_type TEXT NOT NULL,
                color TEXT DEFAULT '#1976D2',
                balance REAL DEFAULT 0.0,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # Categories Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                category_type TEXT NOT NULL, -- 'Expense' or 'Income'
                icon TEXT DEFAULT '💵',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # Transactions Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                category_id INTEGER,
                trans_date TEXT NOT NULL,
                amount REAL NOT NULL,
                trans_type TEXT NOT NULL, -- 'Debit' or 'Credit'
                recipient_or_sender TEXT,
                description TEXT,
                ref_id TEXT,
                fee REAL DEFAULT 0.0,
                raw_sms TEXT,
                source_channel TEXT DEFAULT 'Manual',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE,
                FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
            );
            """)

            # Budgets Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                monthly_limit REAL NOT NULL,
                month_year TEXT NOT NULL, -- YYYY-MM
                FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE,
                UNIQUE(category_id, month_year)
            );
            """)

            # Indexes for ultra-fast queries
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_trans_date ON transactions(trans_date);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_trans_ref ON transactions(ref_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_trans_account ON transactions(account_id);")

            # Seed default accounts if empty
            cursor.execute("SELECT COUNT(*) FROM accounts;")
            if cursor.fetchone()[0] == 0:
                for prov in DEFAULT_PROVIDERS:
                    cursor.execute("""
                    INSERT INTO accounts (name, code, account_type, color, balance)
                    VALUES (?, ?, ?, ?, 0.0);
                    """, (prov["name"], prov["code"], prov["type"], prov["color"]))

            # Seed default categories if empty
            cursor.execute("SELECT COUNT(*) FROM categories;")
            if cursor.fetchone()[0] == 0:
                for cat in DEFAULT_CATEGORIES:
                    cursor.execute("""
                    INSERT INTO categories (name, category_type, icon)
                    VALUES (?, ?, ?);
                    """, (cat["name"], cat["type"], cat["icon"]))

            conn.commit()

    def backup_database(self, destination_path: str) -> bool:
        """Create a full copy backup of the SQLite database file."""
        try:
            shutil.copy2(self.db_path, destination_path)
            return True
        except Exception as e:
            print(f"Backup error: {e}")
            return False

    # ----------------------------------------------------
    # Accounts Operations
    # ----------------------------------------------------
    def get_accounts(self) -> List[Dict[str, Any]]:
        with self.session() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM accounts WHERE is_active = 1 ORDER BY id ASC;")
            return [dict(r) for r in cursor.fetchall()]

    def get_account_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        with self.session() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM accounts WHERE LOWER(name) = LOWER(?);", (name,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_account_balance(self, account_id: int, new_balance: float):
        with self.session() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE accounts SET balance = ? WHERE id = ?;", (new_balance, account_id))
            conn.commit()

    def add_custom_account(self, name: str, code: str, account_type: str, initial_balance: float = 0.0) -> int:
        with self.session() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO accounts (name, code, account_type, balance)
            VALUES (?, ?, ?, ?);
            """, (name, code, account_type, initial_balance))
            conn.commit()
            return cursor.lastrowid

    # ----------------------------------------------------
    # Categories Operations
    # ----------------------------------------------------
    def get_categories(self, category_type: Optional[str] = None) -> List[Dict[str, Any]]:
        with self.session() as conn:
            cursor = conn.cursor()
            if category_type:
                cursor.execute("SELECT * FROM categories WHERE category_type = ? ORDER BY name ASC;", (category_type,))
            else:
                cursor.execute("SELECT * FROM categories ORDER BY category_type ASC, name ASC;")
            return [dict(r) for r in cursor.fetchall()]

    def get_category_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        with self.session() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM categories WHERE LOWER(name) = LOWER(?);", (name,))
            row = cursor.fetchone()
            return dict(row) if row else None

    # ----------------------------------------------------
    # Transactions Operations
    # ----------------------------------------------------
    def check_duplicate_transaction(self, ref_id: str, amount: float, trans_date: str) -> bool:
        if not ref_id and not amount:
            return False
        with self.session() as conn:
            cursor = conn.cursor()
            if ref_id:
                cursor.execute("SELECT COUNT(*) FROM transactions WHERE ref_id = ?;", (ref_id,))
                if cursor.fetchone()[0] > 0:
                    return True
            cursor.execute("""
            SELECT COUNT(*) FROM transactions 
            WHERE amount = ? AND trans_date LIKE ?;
            """, (amount, f"{trans_date[:10]}%"))
            return cursor.fetchone()[0] > 0

    def add_transaction(
        self,
        account_id: int,
        category_id: Optional[int],
        trans_date: str,
        amount: float,
        trans_type: str,
        recipient_or_sender: str = "",
        description: str = "",
        ref_id: str = "",
        fee: float = 0.0,
        raw_sms: str = "",
        source_channel: str = "Manual",
        sync_account_balance: bool = True
    ) -> int:
        with self.session() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO transactions (
                account_id, category_id, trans_date, amount, trans_type,
                recipient_or_sender, description, ref_id, fee, raw_sms, source_channel
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                account_id, category_id, trans_date, amount, trans_type,
                recipient_or_sender, description, ref_id, fee, raw_sms, source_channel
            ))
            trans_id = cursor.lastrowid

            if sync_account_balance:
                delta = -amount if trans_type == "Debit" else amount
                if fee > 0 and trans_type == "Debit":
                    delta -= fee
                cursor.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?;", (delta, account_id))

            conn.commit()
            return trans_id

    def delete_transaction(self, trans_id: int, revert_balance: bool = True) -> bool:
        with self.session() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM transactions WHERE id = ?;", (trans_id,))
            row = cursor.fetchone()
            if not row:
                return False

            if revert_balance:
                account_id = row["account_id"]
                amount = row["amount"]
                trans_type = row["trans_type"]
                fee = row["fee"] or 0.0
                
                revert_delta = amount if trans_type == "Debit" else -amount
                if fee > 0 and trans_type == "Debit":
                    revert_delta += fee
                cursor.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?;", (revert_delta, account_id))

            cursor.execute("DELETE FROM transactions WHERE id = ?;", (trans_id,))
            conn.commit()
            return True

    def get_transactions(
        self,
        account_id: Optional[int] = None,
        trans_type: Optional[str] = None,
        category_id: Optional[int] = None,
        search_query: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        with self.session() as conn:
            cursor = conn.cursor()
            query = """
            SELECT 
                t.*,
                a.name AS account_name,
                a.color AS account_color,
                c.name AS category_name,
                c.icon AS category_icon
            FROM transactions t
            JOIN accounts a ON t.account_id = a.id
            LEFT JOIN categories c ON t.category_id = c.id
            WHERE 1=1
            """
            params: List[Any] = []

            if account_id:
                query += " AND t.account_id = ?"
                params.append(account_id)
            if trans_type and trans_type != "All":
                query += " AND t.trans_type = ?"
                params.append(trans_type)
            if category_id:
                query += " AND t.category_id = ?"
                params.append(category_id)
            if search_query:
                query += " AND (t.recipient_or_sender LIKE ? OR t.description LIKE ? OR t.ref_id LIKE ?)"
                like_term = f"%{search_query}%"
                params.extend([like_term, like_term, like_term])

            query += " ORDER BY t.trans_date DESC, t.id DESC LIMIT ? OFFSET ?;"
            params.extend([limit, offset])

            cursor.execute(query, params)
            return [dict(r) for r in cursor.fetchall()]

    def import_parsed_transactions(self, parsed_list: List[ParsedTransaction]) -> Dict[str, int]:
        imported_count = 0
        skipped_count = 0

        accounts_map = {acc["name"].lower(): acc["id"] for acc in self.get_accounts()}
        categories_map = {cat["name"].lower(): cat["id"] for cat in self.get_categories()}

        default_acc_id = accounts_map.get("cash wallet", list(accounts_map.values())[0])
        default_exp_id = categories_map.get("other expenses")
        default_inc_id = categories_map.get("other income")

        for item in parsed_list:
            if item.ref_id and self.check_duplicate_transaction(item.ref_id, item.amount, item.date_str):
                skipped_count += 1
                continue

            acc_name_lower = (item.account_name or item.provider).lower()
            acc_id = None
            for key, val in accounts_map.items():
                if key in acc_name_lower or acc_name_lower in key:
                    acc_id = val
                    break
            if not acc_id:
                acc_id = default_acc_id

            cat_name_lower = item.category.lower()
            cat_id = None
            for key, val in categories_map.items():
                if key in cat_name_lower or cat_name_lower in key:
                    cat_id = val
                    break
            if not cat_id:
                cat_id = default_inc_id if item.trans_type == "Credit" else default_exp_id

            self.add_transaction(
                account_id=acc_id,
                category_id=cat_id,
                trans_date=item.date_str,
                amount=item.amount,
                trans_type=item.trans_type,
                recipient_or_sender=item.recipient_or_sender,
                description=f"{item.provider} via SMS",
                ref_id=item.ref_id,
                fee=item.fee,
                raw_sms=item.raw_text,
                source_channel="SMS"
            )

            if item.balance_after is not None and item.balance_after >= 0:
                self.update_account_balance(acc_id, item.balance_after)

            imported_count += 1

        return {"imported": imported_count, "skipped": skipped_count}

    def get_dashboard_summary(self, month_str: Optional[str] = None) -> Dict[str, Any]:
        if not month_str:
            month_str = datetime.now().strftime("%Y-%m")

        with self.session() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT SUM(balance) FROM accounts WHERE is_active = 1;")
            total_net_worth = cursor.fetchone()[0] or 0.0

            cursor.execute("""
            SELECT SUM(amount) FROM transactions
            WHERE trans_type = 'Credit' AND trans_date LIKE ?;
            """, (f"{month_str}%",))
            monthly_income = cursor.fetchone()[0] or 0.0

            cursor.execute("""
            SELECT SUM(amount + COALESCE(fee, 0)) FROM transactions
            WHERE trans_type = 'Debit' AND trans_date LIKE ?;
            """, (f"{month_str}%",))
            monthly_expense = cursor.fetchone()[0] or 0.0

            net_savings = monthly_income - monthly_expense
            savings_rate = (net_savings / monthly_income * 100) if monthly_income > 0 else 0.0

            cursor.execute("""
            SELECT 
                COALESCE(c.name, 'Uncategorized') as category_name,
                COALESCE(c.icon, '📦') as icon,
                SUM(t.amount) as total_amount
            FROM transactions t
            LEFT JOIN categories c ON t.category_id = c.id
            WHERE t.trans_type = 'Debit' AND t.trans_date LIKE ?
            GROUP BY c.name
            ORDER BY total_amount DESC;
            """, (f"{month_str}%",))
            category_breakdown = [dict(r) for r in cursor.fetchall()]

            cursor.execute("SELECT name, balance, color, account_type FROM accounts WHERE is_active = 1 ORDER BY balance DESC;")
            accounts_summary = [dict(r) for r in cursor.fetchall()]

            return {
                "month": month_str,
                "net_worth": total_net_worth,
                "monthly_income": monthly_income,
                "monthly_expense": monthly_expense,
                "net_savings": net_savings,
                "savings_rate": savings_rate,
                "category_breakdown": category_breakdown,
                "accounts": accounts_summary
            }
