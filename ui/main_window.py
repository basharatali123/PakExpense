"""
Main Window for Pakistani Expense & Financial Tracker Desktop App.
"""
import customtkinter as ctk
from core.db import DatabaseManager
from ui.styles import COLORS
from ui.views.dashboard_view import DashboardView
from ui.views.sms_view import SMSParserView
from ui.views.ledger_view import LedgerView
from ui.views.add_trans_view import AddTransactionView
from ui.views.accounts_view import AccountsView

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Window configuration
        self.title("PakExpense - Pakistani Finance & SMS Tracker")
        self.geometry("1120x720")
        self.minsize(980, 620)
        
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.configure(fg_color=COLORS["bg_dark"])

        # Initialize SQLite Database
        self.db = DatabaseManager()

        # Build Main Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.build_sidebar()
        self.build_content_area()

        # Select default view
        self.select_view("dashboard")

    def build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=COLORS["bg_sidebar"])
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(6, weight=1)

        # App Brand Header
        brand_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand_frame.pack(fill="x", padx=15, pady=(20, 25))

        logo_lbl = ctk.CTkLabel(
            brand_frame,
            text="🇵🇰 PakExpense",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COLORS["primary"]
        )
        logo_lbl.pack(anchor="w")

        tag_lbl = ctk.CTkLabel(
            brand_frame,
            text="JazzCash • EasyPaisa • Banks",
            font=ctk.CTkFont(size=10),
            text_color=COLORS["text_secondary"]
        )
        tag_lbl.pack(anchor="w", pady=(2, 0))

        # Nav Buttons
        self.nav_buttons = {}
        nav_items = [
            ("dashboard", "📊 Dashboard"),
            ("sms", "⚡ SMS Parser"),
            ("ledger", "📋 Ledger"),
            ("add", "➕ Quick Add"),
            ("accounts", "🗄️ Database & Wallets"),
        ]

        for key, text in nav_items:
            btn = ctk.CTkButton(
                self.sidebar,
                text=text,
                anchor="w",
                height=40,
                font=ctk.CTkFont(size=13, weight="bold"),
                fg_color="transparent",
                text_color=COLORS["text_secondary"],
                hover_color=COLORS["bg_card_hover"],
                corner_radius=8,
                command=lambda k=key: self.select_view(k)
            )
            btn.pack(fill="x", padx=12, pady=4)
            self.nav_buttons[key] = btn

        # Spacer to push DB status to bottom
        spacer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        spacer.pack(fill="both", expand=True)

        # Database Status Badge at bottom
        db_badge = ctk.CTkFrame(self.sidebar, fg_color=COLORS["bg_card"], corner_radius=8, border_width=1, border_color=COLORS["border"])
        db_badge.pack(fill="x", padx=12, pady=(10, 15))

        status_top = ctk.CTkFrame(db_badge, fg_color="transparent")
        status_top.pack(fill="x", padx=10, pady=(8, 2))

        ctk.CTkLabel(
            status_top,
            text="● SQLite Engine",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLORS["income_green"]
        ).pack(side="left")

        ctk.CTkLabel(
            db_badge,
            text="Local Persistent DB (.db)",
            font=ctk.CTkFont(size=10),
            text_color=COLORS["text_muted"]
        ).pack(anchor="w", padx=10, pady=(0, 8))

    def build_content_area(self):
        self.content_area = ctk.CTkFrame(self, fg_color=COLORS["bg_dark"], corner_radius=0)
        self.content_area.grid(row=0, column=1, sticky="nsew")

        # Instantiate Views
        self.views = {
            "dashboard": DashboardView(self.content_area, self.db, on_navigate_callback=self.select_view),
            "sms": SMSParserView(self.content_area, self.db, on_data_changed_callback=self.on_data_updated),
            "ledger": LedgerView(self.content_area, self.db, on_data_changed_callback=self.on_data_updated),
            "add": AddTransactionView(self.content_area, self.db, on_data_changed_callback=self.on_data_updated),
            "accounts": AccountsView(self.content_area, self.db, on_data_changed_callback=self.on_data_updated),
        }

    def select_view(self, view_key: str):
        # Update Nav buttons styling
        for key, btn in self.nav_buttons.items():
            if key == view_key:
                btn.configure(fg_color=COLORS["primary"], text_color="#FFFFFF")
            else:
                btn.configure(fg_color="transparent", text_color=COLORS["text_secondary"])

        # Hide all views and show active view
        for key, view in self.views.items():
            if key == view_key:
                view.pack(fill="both", expand=True)
            else:
                view.pack_forget()

    def on_data_updated(self):
        """Called whenever transactions, balances, or accounts change."""
        self.views["dashboard"].refresh_data()
        self.views["ledger"].refresh_ledger()
        self.views["accounts"].render_accounts_list()
