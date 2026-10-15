"""
Transactions Ledger View with filtering, search, deletion, and CSV export.
"""
import csv
import customtkinter as ctk
from tkinter import filedialog, messagebox
from typing import Optional
from ui.styles import COLORS, format_pkr

class LedgerView(ctk.CTkFrame):
    def __init__(self, master, db_manager, on_data_changed_callback=None):
        super().__init__(master, fg_color="transparent")
        self.db = db_manager
        self.on_data_changed = on_data_changed_callback
        
        self.current_account_id: Optional[int] = None
        self.current_type: str = "All"
        self.current_category_id: Optional[int] = None

        self.build_ui()
        self.refresh_ledger()

    def build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 10))

        title = ctk.CTkLabel(
            header,
            text="Transactions Ledger",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=COLORS["text_primary"]
        )
        title.pack(side="left")

        export_btn = ctk.CTkButton(
            header,
            text="📥 Export to CSV",
            width=120,
            height=32,
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            font=ctk.CTkFont(weight="bold"),
            command=self.export_csv
        )
        export_btn.pack(side="right")

        # Filters Toolbar
        toolbar = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=10)
        toolbar.pack(fill="x", padx=20, pady=5)

        # Search box
        self.search_entry = ctk.CTkEntry(
            toolbar,
            placeholder_text="🔍 Search recipient, note, or Ref ID...",
            width=240,
            height=32,
            fg_color=COLORS["bg_input"],
            text_color=COLORS["text_primary"],
            border_color=COLORS["border"]
        )
        self.search_entry.pack(side="left", padx=10, pady=10)
        self.search_entry.bind("<KeyRelease>", lambda event: self.refresh_ledger())

        # Account Filter Dropdown
        accounts = self.db.get_accounts()
        self.account_options = {"All Accounts": None}
        for a in accounts:
            self.account_options[a["name"]] = a["id"]

        self.acc_combo = ctk.CTkComboBox(
            toolbar,
            values=list(self.account_options.keys()),
            width=160,
            height=32,
            fg_color=COLORS["bg_input"],
            text_color=COLORS["text_primary"],
            button_color=COLORS["border"],
            command=self.on_filter_changed
        )
        self.acc_combo.set("All Accounts")
        self.acc_combo.pack(side="left", padx=5, pady=10)

        # Type Filter
        self.type_combo = ctk.CTkComboBox(
            toolbar,
            values=["All Types", "Debit (Expense)", "Credit (Income)"],
            width=140,
            height=32,
            fg_color=COLORS["bg_input"],
            text_color=COLORS["text_primary"],
            button_color=COLORS["border"],
            command=self.on_filter_changed
        )
        self.type_combo.set("All Types")
        self.type_combo.pack(side="left", padx=5, pady=10)

        # Reset button
        reset_btn = ctk.CTkButton(
            toolbar,
            text="Reset",
            width=65,
            height=32,
            fg_color="transparent",
            text_color=COLORS["text_muted"],
            hover_color=COLORS["bg_card_hover"],
            command=self.reset_filters
        )
        reset_btn.pack(side="right", padx=10, pady=10)

        # Scrollable Transactions List
        self.list_container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.list_container.pack(fill="both", expand=True, padx=20, pady=(10, 15))

    def reset_filters(self):
        self.search_entry.delete(0, "end")
        self.acc_combo.set("All Accounts")
        self.type_combo.set("All Types")
        self.refresh_ledger()

    def on_filter_changed(self, choice=None):
        self.refresh_ledger()

    def refresh_ledger(self):
        for widget in self.list_container.winfo_children():
            widget.destroy()

        search_query = self.search_entry.get().strip() or None
        
        acc_choice = self.acc_combo.get()
        acc_id = self.account_options.get(acc_choice)

        type_choice = self.type_combo.get()
        trans_type = None
        if "Debit" in type_choice:
            trans_type = "Debit"
        elif "Credit" in type_choice:
            trans_type = "Credit"

        txs = self.db.get_transactions(
            account_id=acc_id,
            trans_type=trans_type,
            search_query=search_query,
            limit=200
        )

        if not txs:
            empty_lbl = ctk.CTkLabel(
                self.list_container,
                text="No transactions match your filters.\nPaste SMS or add entries to populate.",
                text_color=COLORS["text_muted"],
                justify="center"
            )
            empty_lbl.pack(pady=50)
            return

        for tx in txs:
            self._render_ledger_row(tx)

    def _render_ledger_row(self, tx):
        row = ctk.CTkFrame(self.list_container, fg_color=COLORS["bg_card"], corner_radius=8, border_width=1, border_color=COLORS["border"])
        row.pack(fill="x", pady=4)

        # Left Info: Account Pill & Date
        left_box = ctk.CTkFrame(row, fg_color="transparent", width=160)
        left_box.pack(side="left", padx=12, pady=10)
        left_box.pack_propagate(False)

        acc_badge = ctk.CTkLabel(
            left_box,
            text=f" {tx['account_name']} ",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=tx.get("account_color") or COLORS["primary"],
            text_color="#FFFFFF",
            corner_radius=4
        )
        acc_badge.pack(anchor="w")

        date_lbl = ctk.CTkLabel(
            left_box,
            text=tx["trans_date"][:16],
            font=ctk.CTkFont(size=10),
            text_color=COLORS["text_muted"]
        )
        date_lbl.pack(anchor="w", pady=(3, 0))

        # Center Info: Recipient, Notes & Category
        center_box = ctk.CTkFrame(row, fg_color="transparent")
        center_box.pack(side="left", fill="both", expand=True, padx=10, pady=8)

        rec_name = tx["recipient_or_sender"] or tx["description"] or "Unknown"
        title_lbl = ctk.CTkLabel(
            center_box,
            text=rec_name,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS["text_primary"],
            anchor="w"
        )
        title_lbl.pack(fill="x")

        meta_parts = []
        if tx.get("category_name"):
            meta_parts.append(f"{tx.get('category_icon', '🏷️')} {tx['category_name']}")
        if tx.get("ref_id"):
            meta_parts.append(f"Ref: {tx['ref_id']}")
        if tx.get("source_channel"):
            meta_parts.append(f"via {tx['source_channel']}")

        sub_lbl = ctk.CTkLabel(
            center_box,
            text=" • ".join(meta_parts),
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"],
            anchor="w"
        )
        sub_lbl.pack(fill="x", pady=(2, 0))

        # Right Info: Amount & Delete Button
        right_box = ctk.CTkFrame(row, fg_color="transparent")
        right_box.pack(side="right", padx=12, pady=8)

        is_credit = tx["trans_type"] == "Credit"
        amt_color = COLORS["income_green"] if is_credit else COLORS["expense_red"]
        amt_prefix = "+" if is_credit else "-"

        amt_lbl = ctk.CTkLabel(
            right_box,
            text=f"{amt_prefix}{format_pkr(tx['amount'])}",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=amt_color
        )
        amt_lbl.pack(side="left", padx=10)

        del_btn = ctk.CTkButton(
            right_box,
            text="✕",
            width=28,
            height=28,
            fg_color="transparent",
            hover_color=COLORS["expense_red_bg"],
            text_color=COLORS["expense_red"],
            command=lambda tid=tx["id"]: self.delete_transaction(tid)
        )
        del_btn.pack(side="right")

    def delete_transaction(self, trans_id: int):
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this transaction?\nIts effect on the account balance will be reverted."):
            self.db.delete_transaction(trans_id, revert_balance=True)
            self.refresh_ledger()
            if self.on_data_changed:
                self.on_data_changed()

    def export_csv(self):
        txs = self.db.get_transactions(limit=10000)
        if not txs:
            messagebox.showinfo("Export CSV", "No transactions to export.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Export Transactions as CSV"
        )
        if not file_path:
            return

        try:
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["ID", "Date", "Account", "Type", "Amount (PKR)", "Category", "Recipient/Merchant", "Ref ID", "Fee", "Channel"])
                for t in txs:
                    writer.writerow([
                        t["id"],
                        t["trans_date"],
                        t["account_name"],
                        t["trans_type"],
                        t["amount"],
                        t.get("category_name", ""),
                        t["recipient_or_sender"],
                        t["ref_id"],
                        t["fee"],
                        t["source_channel"]
                    ])
            messagebox.showinfo("Export Successful", f"Exported {len(txs)} transactions to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Export Failed", str(e))
