"""
Accounts, Wallets, and SQLite Database File Management View.
"""
import os
import subprocess
import customtkinter as ctk
from tkinter import filedialog, messagebox
from ui.styles import COLORS, format_pkr
from core.parser import PakistanSMSParser

class AccountsView(ctk.CTkFrame):
    def __init__(self, master, db_manager, on_data_changed_callback=None):
        super().__init__(master, fg_color="transparent")
        self.db = db_manager
        self.on_data_changed = on_data_changed_callback
        self.build_ui()

    def build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 10))

        title = ctk.CTkLabel(
            header,
            text="Wallets & SQLite Database Manager",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=COLORS["text_primary"]
        )
        title.pack(side="left")

        # Scrollable container
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=5)

        # 1. SQLite Database File Card
        db_card = ctk.CTkFrame(scroll, fg_color=COLORS["bg_card"], corner_radius=10, border_width=1, border_color=COLORS["border"])
        db_card.pack(fill="x", pady=10)

        db_top = ctk.CTkFrame(db_card, fg_color="transparent")
        db_top.pack(fill="x", padx=15, pady=(15, 8))

        ctk.CTkLabel(
            db_top,
            text="🗄️ SQLite Database File Status",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(side="left")

        # Database File Details
        db_info_frame = ctk.CTkFrame(db_card, fg_color=COLORS["bg_input"], corner_radius=8)
        db_info_frame.pack(fill="x", padx=15, pady=(0, 15))

        db_path = self.db.db_path
        db_size_kb = 0.0
        if os.path.exists(db_path):
            db_size_kb = os.path.getsize(db_path) / 1024.0

        tx_count = len(self.db.get_transactions(limit=100000))
        acc_count = len(self.db.get_accounts())

        path_lbl = ctk.CTkLabel(
            db_info_frame,
            text=f"Database File: {db_path}\nFile Size: {db_size_kb:.1f} KB  |  Total Transactions: {tx_count}  |  Accounts: {acc_count}",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"],
            justify="left"
        )
        path_lbl.pack(anchor="w", padx=12, pady=10)

        # Database Action Buttons
        db_btns = ctk.CTkFrame(db_card, fg_color="transparent")
        db_btns.pack(fill="x", padx=15, pady=(0, 15))

        open_folder_btn = ctk.CTkButton(
            db_btns,
            text="📂 Open Database Folder",
            fg_color=COLORS["bg_card_hover"],
            hover_color=COLORS["border"],
            height=32,
            command=self.open_db_folder
        )
        open_folder_btn.pack(side="left", padx=(0, 10))

        backup_btn = ctk.CTkButton(
            db_btns,
            text="💾 Backup Database (.db)",
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            height=32,
            command=self.backup_db
        )
        backup_btn.pack(side="left")

        # 2. Add New Custom Account Card
        new_acc_card = ctk.CTkFrame(scroll, fg_color=COLORS["bg_card"], corner_radius=10, border_width=1, border_color=COLORS["border"])
        new_acc_card.pack(fill="x", pady=10)

        ctk.CTkLabel(
            new_acc_card,
            text="➕ Add Custom Wallet / Bank Account",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w", padx=15, pady=(15, 10))

        acc_form = ctk.CTkFrame(new_acc_card, fg_color="transparent")
        acc_form.pack(fill="x", padx=15, pady=(0, 15))

        self.new_acc_name = ctk.CTkEntry(acc_form, placeholder_text="Account Name (e.g. Faysal Bank, USD Card)", width=200, fg_color=COLORS["bg_input"], text_color=COLORS["text_primary"])
        self.new_acc_name.pack(side="left", padx=(0, 10))

        self.new_acc_type = ctk.CTkComboBox(acc_form, values=["Commercial Bank", "Islamic Bank", "Wallet", "Fintech", "Cash"], width=150, fg_color=COLORS["bg_input"], text_color=COLORS["text_primary"])
        self.new_acc_type.set("Commercial Bank")
        self.new_acc_type.pack(side="left", padx=(0, 10))

        self.new_acc_bal = ctk.CTkEntry(acc_form, placeholder_text="Initial Balance (PKR)", width=140, fg_color=COLORS["bg_input"], text_color=COLORS["text_primary"])
        self.new_acc_bal.pack(side="left", padx=(0, 10))

        add_btn = ctk.CTkButton(acc_form, text="Add Account", fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"], command=self.add_custom_account)
        add_btn.pack(side="left")

        # 3. Existing Accounts List & Balance Adjuster
        acc_list_card = ctk.CTkFrame(scroll, fg_color=COLORS["bg_card"], corner_radius=10, border_width=1, border_color=COLORS["border"])
        acc_list_card.pack(fill="x", pady=10)

        ctk.CTkLabel(
            acc_list_card,
            text="💳 Existing Accounts & Balance Adjustment",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w", padx=15, pady=(15, 10))

        self.accounts_container = ctk.CTkFrame(acc_list_card, fg_color="transparent")
        self.accounts_container.pack(fill="x", padx=15, pady=(0, 15))

        self.render_accounts_list()

    def render_accounts_list(self):
        for widget in self.accounts_container.winfo_children():
            widget.destroy()

        accounts = self.db.get_accounts()
        for acc in accounts:
            row = ctk.CTkFrame(self.accounts_container, fg_color=COLORS["bg_input"], corner_radius=6, border_width=1, border_color=COLORS["border"])
            row.pack(fill="x", pady=4)

            name_lbl = ctk.CTkLabel(
                row,
                text=f"{acc['name']} ({acc['account_type']})",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=COLORS["text_primary"]
            )
            name_lbl.pack(side="left", padx=12, pady=10)

            # Right: Current balance & update box
            right_box = ctk.CTkFrame(row, fg_color="transparent")
            right_box.pack(side="right", padx=12, pady=8)

            bal_lbl = ctk.CTkLabel(
                right_box,
                text=format_pkr(acc["balance"]),
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=acc["color"] or COLORS["accent_cyan"]
            )
            bal_lbl.pack(side="left", padx=10)

            edit_entry = ctk.CTkEntry(
                right_box,
                width=100,
                placeholder_text="New Bal",
                fg_color=COLORS["bg_card"],
                text_color=COLORS["text_primary"]
            )
            edit_entry.pack(side="left", padx=5)

            update_btn = ctk.CTkButton(
                right_box,
                text="Update",
                width=60,
                height=28,
                fg_color=COLORS["primary"],
                hover_color=COLORS["primary_hover"],
                command=lambda a_id=acc["id"], a_entry=edit_entry, a_name=acc["name"]: self.update_balance(a_id, a_entry, a_name)
            )
            update_btn.pack(side="left")

    def update_balance(self, acc_id: int, entry_widget: ctk.CTkEntry, acc_name: str):
        val_str = entry_widget.get().strip()
        if not val_str:
            return
        new_val = PakistanSMSParser.clean_amount(val_str)
        self.db.update_account_balance(acc_id, new_val)
        entry_widget.delete(0, "end")
        self.render_accounts_list()
        messagebox.showinfo("Balance Updated", f"Updated {acc_name} balance to {format_pkr(new_val)}!")
        if self.on_data_changed:
            self.on_data_changed()

    def add_custom_account(self):
        name = self.new_acc_name.get().strip()
        acc_type = self.new_acc_type.get().strip()
        bal_str = self.new_acc_bal.get().strip()
        initial_bal = PakistanSMSParser.clean_amount(bal_str) if bal_str else 0.0

        if not name:
            messagebox.showwarning("Missing Name", "Please enter an account name.")
            return

        try:
            self.db.add_custom_account(name=name, code=name[:4].upper(), account_type=acc_type, initial_balance=initial_bal)
            messagebox.showinfo("Account Added", f"Account '{name}' created successfully!")
            self.new_acc_name.delete(0, "end")
            self.new_acc_bal.delete(0, "end")
            self.render_accounts_list()
            if self.on_data_changed:
                self.on_data_changed()
        except Exception as e:
            messagebox.showerror("Error", f"Could not create account: {e}")

    def open_db_folder(self):
        folder = os.path.dirname(os.path.abspath(self.db.db_path))
        if os.name == 'nt':
            os.startfile(folder)
        else:
            subprocess.Popen(['xdg-open', folder])

    def backup_db(self):
        save_path = filedialog.asksaveasfilename(
            defaultextension=".db",
            filetypes=[("SQLite DB", "*.db"), ("All files", "*.*")],
            initialfile="pk_finance_backup.db",
            title="Save SQLite Database Backup"
        )
        if not save_path:
            return

        if self.db.backup_database(save_path):
            messagebox.showinfo("Backup Saved", f"Database successfully backed up to:\n{save_path}")
        else:
            messagebox.showerror("Backup Error", "Failed to backup database.")
