"""
Quick Add Manual Transaction View for cash, non-SMS transactions, or adjustments.
"""
import customtkinter as ctk
from datetime import datetime
from tkinter import messagebox
from ui.styles import COLORS
from core.parser import PakistanSMSParser

class AddTransactionView(ctk.CTkFrame):
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
            text="Quick Add Transaction",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=COLORS["text_primary"]
        )
        title.pack(side="left")

        desc = ctk.CTkLabel(
            self,
            text="Manually record cash spending, income, or transactions that did not send an SMS alert.",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"]
        )
        desc.pack(anchor="w", padx=20, pady=(0, 15))

        # Center Container Form
        center_card = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=12, border_width=1, border_color=COLORS["border"])
        center_card.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        form_scroll = ctk.CTkScrollableFrame(center_card, fg_color="transparent")
        form_scroll.pack(fill="both", expand=True, padx=30, pady=20)

        # 1. Transaction Type (Debit / Credit)
        lbl_type = ctk.CTkLabel(form_scroll, text="Transaction Type", font=ctk.CTkFont(size=13, weight="bold"), text_color=COLORS["text_secondary"])
        lbl_type.pack(anchor="w", pady=(5, 5))

        self.type_segmented = ctk.CTkSegmentedButton(
            form_scroll,
            values=["Expense (Debit)", "Income (Credit)"],
            selected_color=COLORS["primary"],
            selected_hover_color=COLORS["primary_hover"],
            height=36,
            command=self.on_type_switched
        )
        self.type_segmented.set("Expense (Debit)")
        self.type_segmented.pack(fill="x", pady=(0, 15))

        # 2. Amount in PKR
        lbl_amt = ctk.CTkLabel(form_scroll, text="Amount (PKR) *", font=ctk.CTkFont(size=13, weight="bold"), text_color=COLORS["text_secondary"])
        lbl_amt.pack(anchor="w", pady=(5, 5))

        self.amt_entry = ctk.CTkEntry(
            form_scroll,
            placeholder_text="e.g. 2,500",
            height=38,
            font=ctk.CTkFont(size=15),
            fg_color=COLORS["bg_input"],
            text_color=COLORS["text_primary"],
            border_color=COLORS["border"]
        )
        self.amt_entry.pack(fill="x", pady=(0, 15))

        # 3. Account Dropdown
        lbl_acc = ctk.CTkLabel(form_scroll, text="Account / Wallet *", font=ctk.CTkFont(size=13, weight="bold"), text_color=COLORS["text_secondary"])
        lbl_acc.pack(anchor="w", pady=(5, 5))

        self.accounts = self.db.get_accounts()
        self.acc_map = {a["name"]: a["id"] for a in self.accounts}
        default_acc = "Cash Wallet" if "Cash Wallet" in self.acc_map else list(self.acc_map.keys())[0]

        self.acc_combo = ctk.CTkComboBox(
            form_scroll,
            values=list(self.acc_map.keys()),
            height=36,
            fg_color=COLORS["bg_input"],
            text_color=COLORS["text_primary"],
            button_color=COLORS["border"]
        )
        self.acc_combo.set(default_acc)
        self.acc_combo.pack(fill="x", pady=(0, 15))

        # 4. Category Dropdown
        lbl_cat = ctk.CTkLabel(form_scroll, text="Category *", font=ctk.CTkFont(size=13, weight="bold"), text_color=COLORS["text_secondary"])
        lbl_cat.pack(anchor="w", pady=(5, 5))

        self.cat_combo = ctk.CTkComboBox(
            form_scroll,
            values=[],
            height=36,
            fg_color=COLORS["bg_input"],
            text_color=COLORS["text_primary"],
            button_color=COLORS["border"]
        )
        self.cat_combo.pack(fill="x", pady=(0, 15))
        self.update_categories_dropdown("Expense")

        # 5. Recipient / Vendor / Note
        lbl_note = ctk.CTkLabel(form_scroll, text="Recipient, Merchant or Note", font=ctk.CTkFont(size=13, weight="bold"), text_color=COLORS["text_secondary"])
        lbl_note.pack(anchor="w", pady=(5, 5))

        self.note_entry = ctk.CTkEntry(
            form_scroll,
            placeholder_text="e.g. Grocery at Imtiaz, Biryani with friends, Freelance payment",
            height=36,
            fg_color=COLORS["bg_input"],
            text_color=COLORS["text_primary"],
            border_color=COLORS["border"]
        )
        self.note_entry.pack(fill="x", pady=(0, 15))

        # 6. Date & Time
        lbl_date = ctk.CTkLabel(form_scroll, text="Date & Time (YYYY-MM-DD HH:MM)", font=ctk.CTkFont(size=13, weight="bold"), text_color=COLORS["text_secondary"])
        lbl_date.pack(anchor="w", pady=(5, 5))

        self.date_entry = ctk.CTkEntry(
            form_scroll,
            height=36,
            fg_color=COLORS["bg_input"],
            text_color=COLORS["text_primary"],
            border_color=COLORS["border"]
        )
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d %H:%M"))
        self.date_entry.pack(fill="x", pady=(0, 15))

        # 7. Reference Number (Optional)
        lbl_ref = ctk.CTkLabel(form_scroll, text="Reference / Receipt ID (Optional)", font=ctk.CTkFont(size=13, weight="bold"), text_color=COLORS["text_secondary"])
        lbl_ref.pack(anchor="w", pady=(5, 5))

        self.ref_entry = ctk.CTkEntry(
            form_scroll,
            placeholder_text="e.g. TRX1092837",
            height=36,
            fg_color=COLORS["bg_input"],
            text_color=COLORS["text_primary"],
            border_color=COLORS["border"]
        )
        self.ref_entry.pack(fill="x", pady=(0, 20))

        # Submit Button
        submit_btn = ctk.CTkButton(
            form_scroll,
            text="✅ Save Transaction",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            height=40,
            command=self.submit_form
        )
        submit_btn.pack(fill="x", pady=(10, 15))

    def on_type_switched(self, value):
        cat_type = "Income" if "Income" in value else "Expense"
        self.update_categories_dropdown(cat_type)

    def update_categories_dropdown(self, cat_type: str):
        cats = self.db.get_categories(category_type=cat_type)
        self.cat_map = {f"{c['icon']} {c['name']}": c["id"] for c in cats}
        values = list(self.cat_map.keys())
        self.cat_combo.configure(values=values)
        if values:
            self.cat_combo.set(values[0])

    def submit_form(self):
        amt_str = self.amt_entry.get().strip()
        amount = PakistanSMSParser.clean_amount(amt_str)
        if amount <= 0:
            messagebox.showwarning("Invalid Amount", "Please enter a valid numeric amount greater than zero.")
            return

        acc_name = self.acc_combo.get()
        acc_id = self.acc_map.get(acc_name)
        if not acc_id:
            messagebox.showwarning("Account Missing", "Please select an account.")
            return

        cat_choice = self.cat_combo.get()
        cat_id = self.cat_map.get(cat_choice)

        trans_type = "Credit" if "Income" in self.type_segmented.get() else "Debit"
        recipient = self.note_entry.get().strip() or "Manual Entry"
        trans_date = self.date_entry.get().strip() or datetime.now().strftime("%Y-%m-%d %H:%M")
        ref_id = self.ref_entry.get().strip()

        # Add to database
        self.db.add_transaction(
            account_id=acc_id,
            category_id=cat_id,
            trans_date=trans_date,
            amount=amount,
            trans_type=trans_type,
            recipient_or_sender=recipient,
            description="Manual Quick Add",
            ref_id=ref_id,
            source_channel="Manual",
            sync_account_balance=True
        )

        messagebox.showinfo("Success", f"Recorded {trans_type} of Rs. {amount:,.2f} for {acc_name}!")

        # Reset form fields
        self.amt_entry.delete(0, "end")
        self.note_entry.delete(0, "end")
        self.ref_entry.delete(0, "end")
        self.date_entry.delete(0, "end")
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d %H:%M"))

        if self.on_data_changed:
            self.on_data_changed()
