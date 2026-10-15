"""
Dashboard View displaying Pakistani Net Worth, Monthly Flow, and Account Balances.
"""
import customtkinter as ctk
from datetime import datetime
from ui.styles import COLORS, format_pkr, format_pkr_short

class DashboardView(ctk.CTkFrame):
    def __init__(self, master, db_manager, on_navigate_callback=None):
        super().__init__(master, fg_color="transparent")
        self.db = db_manager
        self.on_navigate = on_navigate_callback
        self.build_ui()
        self.refresh_data()

    def build_ui(self):
        # Top Header Bar
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(15, 10))

        title = ctk.CTkLabel(
            header_frame,
            text="Financial Overview",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=COLORS["text_primary"]
        )
        title.pack(side="left")

        self.month_label = ctk.CTkLabel(
            header_frame,
            text=datetime.now().strftime("%B %Y"),
            font=ctk.CTkFont(size=14),
            text_color=COLORS["accent_cyan"]
        )
        self.month_label.pack(side="left", padx=15)

        refresh_btn = ctk.CTkButton(
            header_frame,
            text="🔄 Refresh",
            width=100,
            height=32,
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["bg_card_hover"],
            command=self.refresh_data
        )
        refresh_btn.pack(side="right")

        # Scrollable container for dashboard contents
        self.scroll_container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_container.pack(fill="both", expand=True, padx=15, pady=5)

        # 1. KPI Cards Row (4 Cards)
        self.cards_row = ctk.CTkFrame(self.scroll_container, fg_color="transparent")
        self.cards_row.pack(fill="x", pady=10)
        self.cards_row.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="kpi")

        self.card_net_worth = self._create_kpi_card(self.cards_row, 0, "💎 Total Net Worth", "Rs. 0.00", COLORS["primary"])
        self.card_income = self._create_kpi_card(self.cards_row, 1, "📥 Monthly Income", "Rs. 0.00", COLORS["income_green"])
        self.card_expense = self._create_kpi_card(self.cards_row, 2, "📤 Monthly Expense", "Rs. 0.00", COLORS["expense_red"])
        self.card_savings = self._create_kpi_card(self.cards_row, 3, "💰 Net Savings", "Rs. 0.00", COLORS["accent_cyan"])

        # 2. Wallets & Accounts Section
        acc_header = ctk.CTkLabel(
            self.scroll_container,
            text="Pakistani Wallets & Bank Balances",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text_primary"]
        )
        acc_header.pack(anchor="w", padx=5, pady=(15, 8))

        self.accounts_frame = ctk.CTkScrollableFrame(self.scroll_container, height=110, orientation="horizontal", fg_color="transparent")
        self.accounts_frame.pack(fill="x", pady=5)

        # 3. Two Columns: Categories Breakdown & Recent Transactions
        bottom_frame = ctk.CTkFrame(self.scroll_container, fg_color="transparent")
        bottom_frame.pack(fill="both", expand=True, pady=15)
        bottom_frame.grid_columnconfigure(0, weight=1)
        bottom_frame.grid_columnconfigure(1, weight=1)

        # Left Column: Category Spending Breakdown
        self.cat_frame = ctk.CTkFrame(bottom_frame, fg_color=COLORS["bg_card"], corner_radius=10)
        self.cat_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=5)

        cat_title = ctk.CTkLabel(
            self.cat_frame,
            text="📊 Expense Breakdown by Category",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=COLORS["text_primary"]
        )
        cat_title.pack(anchor="w", padx=15, pady=(15, 10))

        self.cat_items_frame = ctk.CTkFrame(self.cat_frame, fg_color="transparent")
        self.cat_items_frame.pack(fill="both", expand=True, padx=15, pady=5)

        # Right Column: Recent Transactions
        self.recent_frame = ctk.CTkFrame(bottom_frame, fg_color=COLORS["bg_card"], corner_radius=10)
        self.recent_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=5)

        rec_header_box = ctk.CTkFrame(self.recent_frame, fg_color="transparent")
        rec_header_box.pack(fill="x", padx=15, pady=(15, 10))

        rec_title = ctk.CTkLabel(
            rec_header_box,
            text="🕒 Recent Activity",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=COLORS["text_primary"]
        )
        rec_title.pack(side="left")

        view_all_btn = ctk.CTkButton(
            rec_header_box,
            text="View Ledger →",
            width=90,
            height=26,
            fg_color="transparent",
            text_color=COLORS["accent_cyan"],
            hover_color=COLORS["bg_card_hover"],
            command=lambda: self.on_navigate("ledger") if self.on_navigate else None
        )
        view_all_btn.pack(side="right")

        self.recent_items_frame = ctk.CTkFrame(self.recent_frame, fg_color="transparent")
        self.recent_items_frame.pack(fill="both", expand=True, padx=15, pady=5)

    def _create_kpi_card(self, parent, col, title, initial_val, accent_color):
        card = ctk.CTkFrame(parent, fg_color=COLORS["bg_card"], corner_radius=10, border_width=1, border_color=COLORS["border"])
        card.grid(row=0, column=col, padx=6, pady=5, sticky="nsew")

        lbl_title = ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=12, weight="bold"), text_color=COLORS["text_secondary"])
        lbl_title.pack(anchor="w", padx=15, pady=(12, 4))

        lbl_val = ctk.CTkLabel(card, text=initial_val, font=ctk.CTkFont(size=18, weight="bold"), text_color=accent_color)
        lbl_val.pack(anchor="w", padx=15, pady=(0, 12))
        return lbl_val

    def refresh_data(self):
        summary = self.db.get_dashboard_summary()

        # Update KPI values
        self.card_net_worth.configure(text=format_pkr(summary["net_worth"]))
        self.card_income.configure(text=format_pkr(summary["monthly_income"]))
        self.card_expense.configure(text=format_pkr(summary["monthly_expense"]))
        
        savings_text = f"{format_pkr(summary['net_savings'])} ({summary['savings_rate']:.1f}%)"
        self.card_savings.configure(text=savings_text)

        # Update Accounts Row
        for widget in self.accounts_frame.winfo_children():
            widget.destroy()

        for acc in summary["accounts"]:
            # Card for each account
            acc_card = ctk.CTkFrame(self.accounts_frame, fg_color=COLORS["bg_card"], corner_radius=8, width=170, height=90, border_width=1, border_color=COLORS["border"])
            acc_card.pack(side="left", padx=6, pady=4)
            acc_card.pack_propagate(False)

            top_row = ctk.CTkFrame(acc_card, fg_color="transparent")
            top_row.pack(fill="x", padx=10, pady=(8, 2))

            name_lbl = ctk.CTkLabel(top_row, text=acc["name"], font=ctk.CTkFont(size=13, weight="bold"), text_color=COLORS["text_primary"])
            name_lbl.pack(side="left")

            type_lbl = ctk.CTkLabel(top_row, text=acc["account_type"][:8], font=ctk.CTkFont(size=10), text_color=COLORS["text_muted"])
            type_lbl.pack(side="right")

            bal_lbl = ctk.CTkLabel(acc_card, text=format_pkr(acc["balance"]), font=ctk.CTkFont(size=14, weight="bold"), text_color=acc["color"] or COLORS["accent_cyan"])
            bal_lbl.pack(anchor="w", padx=10, pady=(2, 6))

        # Update Category Spending Breakdown
        for widget in self.cat_items_frame.winfo_children():
            widget.destroy()

        categories = summary["category_breakdown"]
        total_exp = summary["monthly_expense"] or 1.0

        if not categories:
            no_cat = ctk.CTkLabel(self.cat_items_frame, text="No expenses recorded for this month yet.\nImport SMS or add transactions to see insights.", text_color=COLORS["text_muted"], justify="center")
            no_cat.pack(pady=30)
        else:
            for item in categories[:6]:  # Show top 6
                pct = min(1.0, max(0.0, item["total_amount"] / total_exp))
                
                row = ctk.CTkFrame(self.cat_items_frame, fg_color="transparent")
                row.pack(fill="x", pady=4)

                lbl_box = ctk.CTkFrame(row, fg_color="transparent")
                lbl_box.pack(fill="x")

                cat_name = f"{item['icon']} {item['category_name']}"
                ctk.CTkLabel(lbl_box, text=cat_name, font=ctk.CTkFont(size=12), text_color=COLORS["text_primary"]).pack(side="left")
                ctk.CTkLabel(lbl_box, text=f"{format_pkr(item['total_amount'])} ({pct*100:.1f}%)", font=ctk.CTkFont(size=11, weight="bold"), text_color=COLORS["text_secondary"]).pack(side="right")

                pbar = ctk.CTkProgressBar(row, height=8, progress_color=COLORS["primary"], fg_color=COLORS["border"])
                pbar.pack(fill="x", pady=(2, 6))
                pbar.set(pct)

        # Update Recent Transactions
        for widget in self.recent_items_frame.winfo_children():
            widget.destroy()

        recent_txs = self.db.get_transactions(limit=6)
        if not recent_txs:
            no_tx = ctk.CTkLabel(self.recent_items_frame, text="No transactions logged yet.\nPaste your bank/wallet SMS in the SMS Parser tab!", text_color=COLORS["text_muted"], justify="center")
            no_tx.pack(pady=30)
        else:
            for tx in recent_txs:
                tx_box = ctk.CTkFrame(self.recent_items_frame, fg_color="transparent")
                tx_box.pack(fill="x", pady=4)

                left_info = ctk.CTkFrame(tx_box, fg_color="transparent")
                left_info.pack(side="left", fill="x", expand=True)

                title_text = f"{tx.get('category_icon', '💵')} {tx['recipient_or_sender'] or tx['account_name']}"
                sub_text = f"{tx['account_name']} • {tx['trans_date'][:16]}"

                ctk.CTkLabel(left_info, text=title_text, font=ctk.CTkFont(size=12, weight="bold"), text_color=COLORS["text_primary"], anchor="w").pack(anchor="w")
                ctk.CTkLabel(left_info, text=sub_text, font=ctk.CTkFont(size=10), text_color=COLORS["text_muted"], anchor="w").pack(anchor="w")

                is_credit = tx["trans_type"] == "Credit"
                amt_prefix = "+" if is_credit else "-"
                amt_color = COLORS["income_green"] if is_credit else COLORS["expense_red"]

                amt_lbl = ctk.CTkLabel(
                    tx_box,
                    text=f"{amt_prefix}{format_pkr(tx['amount'])}",
                    font=ctk.CTkFont(size=13, weight="bold"),
                    text_color=amt_color
                )
                amt_lbl.pack(side="right", padx=5)
