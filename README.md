# 🇵🇰 PakExpense - Pakistani Financial & SMS Tracker

A desktop expense and financial tracker specifically tailored for Pakistani financial services:
- **JazzCash** (Shortcode `8558`)
- **EasyPaisa** (Shortcode `3737`)
- **Commercial & Islamic Banks** (Meezan Bank `8267`, HBL `4250`, Bank Alfalah `8222`, UBL `8257`, MCB `6222`, etc.)
- **Fintechs & Instant Raast** (SadaPay, NayaPay, SBP Raast)
- **Cash Wallet & Manual Entries**

Built using **Python 3.14**, **CustomTkinter** (modern dark-theme FinTech GUI), **SQLite3** for secure local encrypted/offline storage, and packaged into a standalone **Windows Executable (`.exe`)**.

---

## 🏗️ Architecture & SQLite Persistence in `.exe`

### The "SQLite Inside EXE" Solution
When packaging a Python app into a single `.exe` using PyInstaller (`--onefile`):
- Any file embedded directly inside the `.exe` bundle is extracted to a temporary folder (`sys._MEIPASS`) each time the app runs and **deleted when the app closes**.
- **The Production Solution Implemented**:
  The application detects if it is running as a compiled `.exe` or from source code:
  - If compiled (`sys.frozen` is True), it stores `pk_finance.db` **right next to the `.exe` in portable mode**.
  - If that folder is protected (e.g. `Program Files`), it automatically falls back to `%APPDATA%/PakExpenseTracker/pk_finance.db`.
  - Default Pakistani accounts and categories are automatically seeded on first launch.
  - **Your transaction data persists permanently across restarts and computer reboots.**

---

## 🚀 How to Run

### Option 1: Standalone Windows Executable (No Python Required)
You can directly run the pre-compiled executable:
```
c:\Python Setup\Mobile App\dist\PakExpenseTracker.exe
```
*(Or double-click `dist\PakExpenseTracker.exe` in Windows Explorer)*

### Option 2: Run via Python Source
```bash
# 1. Install dependencies (if not already installed)
pip install -r requirements.txt

# 2. Run the application
python app.py
# Or double-click run.bat
```

### Option 3: Re-compile the Executable
To build a fresh `.exe` at any time:
```bash
python build_exe.py
# Or double-click build.bat
```

---

## 📱 Features

1. **📊 Financial Dashboard**:
   - Total Net Worth in PKR across all Pakistani banks and wallets.
   - Monthly Income, Monthly Expense, and Net Savings Rate (%).
   - Live Wallet Badges (JazzCash, EasyPaisa, Meezan, HBL, Cash).
   - Category Expense Breakdown with visual progress bars.
   - Recent transaction feed with Debit (Red) / Credit (Green) indicators.

2. **⚡ Pakistani SMS Regex Parser**:
   - **Bulk SMS Paste**: Paste multiple messages copied from phone/WhatsApp/SMS threads.
   - **1-Click Sample Loader**: Test with pre-loaded Pakistani SMS variations.
   - **Live Parsed Cards**: Automatically detects Provider, Type, Amount (PKR), Recipient/Merchant, Reference ID, and Auto-Categorization.
   - **Android XML Backup Importer**: Directly imports XML backup files created by the popular Android *SMS Backup & Restore* app (filtering shortcodes 8558, 3737, 8267, 4250, etc.).
   - **Duplicate Detection**: Prevents double-counting by tracking Trx/Ref IDs and timestamps.

3. **📋 Transactions Ledger**:
   - Real-time search by Recipient, Note, or Reference ID.
   - Filter by Account (All, JazzCash, EasyPaisa, Banks, Cash) and Type (Debit/Credit).
   - Delete transactions with automatic balance reversion.
   - Export all transaction logs to CSV.

4. **➕ Quick Add Manual Entry**:
   - Fast logging for cash spending or un-alerted bank transactions.
   - Presets for Pakistani categories (Bills & Utilities, Groceries, Fuel, Foodpanda, etc.).

5. **🗄️ Database & Wallets Manager**:
   - Live SQLite database path display and file size.
   - One-click "Open Database Folder in Windows Explorer".
   - One-click "Backup Database (.db)" to save copies.
   - Add custom bank accounts (Faysal, SadaBiz, USD card) or adjust current balances.

---

## 🧪 Unit Tests
The regex parsing engine and database operations are verified by unit tests:
```bash
python -m unittest tests/test_parser.py
```
*(9/9 tests pass with 100% precision for JazzCash, EasyPaisa, Meezan, HBL, and duplicate prevention).*
