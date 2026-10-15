"""
PakExpense - Pakistani Expense & Financial Tracker
Consolidates transactions from JazzCash, EasyPaisa, and Commercial Banks (Meezan, HBL, Alfalah, etc.)
Embedded with local persistent SQLite database and packaged for Windows Executable (.exe).
"""
import sys
import os

# Ensure the root project directory is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from ui.main_window import MainWindow

def main():
    try:
        app = MainWindow()
        app.mainloop()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print(f"Error launching application: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
