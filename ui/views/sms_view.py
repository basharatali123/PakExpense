"""
SMS Ingestion and Real-Time Parser View for Pakistani Wallets & Commercial Banks.
"""
import os
import customtkinter as ctk
from tkinter import filedialog, messagebox
from typing import List
from core.models import ParsedTransaction
from core.importer import SMSBatchImporter
from ui.styles import COLORS, format_pkr

class SMSParserView(ctk.CTkFrame):
    def __init__(self, master, db_manager, on_data_changed_callback=None):
        super().__init__(master, fg_color="transparent")
        self.db = db_manager
        self.on_data_changed = on_data_changed_callback
        self.parsed_items: List[ParsedTransaction] = []
        self.build_ui()

    def build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 10))

        title = ctk.CTkLabel(
            header,
            text="Pakistani SMS Ingestion & Regex Engine",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=COLORS["text_primary"]
        )
        title.pack(side="left")

        desc = ctk.CTkLabel(
            self,
            text="Paste raw transaction messages from JazzCash (8558), EasyPaisa (3737), Meezan Bank, HBL, Alfalah, or import Android XML logs.",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"]
        )
        desc.pack(anchor="w", padx=20, pady=(0, 10))

        # Main Split Frame (Left: Input & Controls, Right: Parsed Results)
        split_frame = ctk.CTkFrame(self, fg_color="transparent")
        split_frame.pack(fill="both", expand=True, padx=20, pady=5)
        split_frame.grid_columnconfigure(0, weight=1)
        split_frame.grid_columnconfigure(1, weight=1)

        # Left Column: Input Box & Buttons
        left_box = ctk.CTkFrame(split_frame, fg_color=COLORS["bg_card"], corner_radius=10)
        left_box.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=5)

        lbl_input = ctk.CTkLabel(
            left_box,
            text="📝 Paste SMS Text (Single or Batch)",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text_primary"]
        )
        lbl_input.pack(anchor="w", padx=15, pady=(15, 5))

        self.txt_sms = ctk.CTkTextbox(left_box, height=280, fg_color=COLORS["bg_input"], text_color=COLORS["text_primary"], border_width=1, border_color=COLORS["border"])
        self.txt_sms.pack(fill="both", expand=True, padx=15, pady=5)

        # Action Buttons
        btn_grid = ctk.CTkFrame(left_box, fg_color="transparent")
        btn_grid.pack(fill="x", padx=15, pady=(10, 15))

        parse_btn = ctk.CTkButton(
            btn_grid,
            text="⚡ Parse Messages",
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            font=ctk.CTkFont(weight="bold"),
            height=36,
            command=self.on_parse_clicked
        )
        parse_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))

        sample_btn = ctk.CTkButton(
            btn_grid,
            text="💡 Load Sample SMS",
            fg_color=COLORS["bg_card_hover"],
            hover_color=COLORS["border"],
            height=36,
            command=self.load_sample_sms
        )
        sample_btn.pack(side="left", padx=5)

        clear_btn = ctk.CTkButton(
            btn_grid,
            text="🧹 Clear",
            width=70,
            height=36,
            fg_color="transparent",
            text_color=COLORS["text_muted"],
            hover_color=COLORS["bg_card_hover"],
            command=lambda: self.txt_sms.delete("1.0", "end")
        )
        clear_btn.pack(side="right", padx=(5, 0))

        # Secondary Android Backup Importer
        xml_box = ctk.CTkFrame(left_box, fg_color=COLORS["bg_input"], corner_radius=8, border_width=1, border_color=COLORS["border"])
        xml_box.pack(fill="x", padx=15, pady=(0, 10))

        ctk.CTkLabel(
            xml_box,
            text="📲 Android SMS Backup & Restore (SyncTech XML)",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w", padx=10, pady=(8, 2))

        import_xml_btn = ctk.CTkButton(
            xml_box,
            text="Choose .xml Backup File",
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["bg_card_hover"],
            height=30,
            command=self.import_android_xml
        )
        import_xml_btn.pack(anchor="w", padx=10, pady=(0, 8))

        # Auto Clipboard Watcher Switch
        self.last_clipboard = ""
        self.auto_clipboard_var = ctk.BooleanVar(value=False)
        self.clipboard_switch = ctk.CTkSwitch(
            left_box,
            text="📋 Auto-detect & Parse from Clipboard",
            variable=self.auto_clipboard_var,
            font=ctk.CTkFont(size=12, weight="bold"),
            progress_color=COLORS["primary"],
            command=self.toggle_clipboard_watcher
        )
        self.clipboard_switch.pack(anchor="w", padx=15, pady=(0, 10))

        # Wireless Phone Sync Server Box
        sync_box = ctk.CTkFrame(left_box, fg_color=COLORS["bg_input"], corner_radius=8, border_width=1, border_color=COLORS["border"])
        sync_box.pack(fill="x", padx=15, pady=(0, 15))

        sync_top = ctk.CTkFrame(sync_box, fg_color="transparent")
        sync_top.pack(fill="x", padx=10, pady=(8, 2))

        ctk.CTkLabel(
            sync_top,
            text="📡 Wireless Phone Sync (Auto-Read)",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS["accent_cyan"]
        ).pack(side="left")

        self.server_var = ctk.BooleanVar(value=True)
        self.server_switch = ctk.CTkSwitch(
            sync_top,
            text="Active",
            variable=self.server_var,
            font=ctk.CTkFont(size=11),
            progress_color=COLORS["income_green"],
            command=self.toggle_sync_server
        )
        self.server_switch.pack(side="right")

        local_ip = self.get_local_ip()
        self.server_url = f"http://{local_ip}:8558/api/sms"
        
        self.lbl_server_info = ctk.CTkLabel(
            sync_box,
            text=f"Auto-forward Phone Push/SMS to:\n{self.server_url}",
            font=ctk.CTkFont(size=10),
            text_color=COLORS["text_secondary"],
            justify="left"
        )
        self.lbl_server_info.pack(anchor="w", padx=10, pady=(2, 2))

        setup_btn = ctk.CTkButton(
            sync_box,
            text="📖 Phone Setup Instructions",
            height=24,
            fg_color="transparent",
            text_color=COLORS["accent_cyan"],
            hover_color=COLORS["bg_card"],
            command=self.show_phone_setup_guide
        )
        setup_btn.pack(anchor="w", padx=10, pady=(0, 6))

        # Start the background sync server
        from core.server import LocalSMSReceiver
        self.receiver = LocalSMSReceiver(self.db, port=8558, on_received_callback=self.on_sms_webhook_received)
        self.receiver.start()

        # Right Column: Parsed Results Preview & Import
        right_box = ctk.CTkFrame(split_frame, fg_color=COLORS["bg_card"], corner_radius=10)
        right_box.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=5)

        right_top = ctk.CTkFrame(right_box, fg_color="transparent")
        right_top.pack(fill="x", padx=15, pady=(15, 10))

        self.lbl_parsed_count = ctk.CTkLabel(
            right_top,
            text="Parsed Transactions Preview (0 found)",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text_primary"]
        )
        self.lbl_parsed_count.pack(side="left")

        self.btn_save_all = ctk.CTkButton(
            right_top,
            text="💾 Save to Database",
            fg_color=COLORS["income_green"],
            hover_color=COLORS["income_green_bg"],
            font=ctk.CTkFont(weight="bold"),
            height=32,
            state="disabled",
            command=self.save_parsed_to_db
        )
        self.btn_save_all.pack(side="right")

        self.preview_scroll = ctk.CTkScrollableFrame(right_box, fg_color="transparent")
        self.preview_scroll.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self.show_empty_preview_message()

    def show_empty_preview_message(self):
        for widget in self.preview_scroll.winfo_children():
            widget.destroy()

        empty_lbl = ctk.CTkLabel(
            self.preview_scroll,
            text="No parsed items yet.\n\nType or paste Pakistani banking SMS on the left and click 'Parse Messages' or 'Load Sample SMS'.",
            text_color=COLORS["text_muted"],
            justify="center"
        )
        empty_lbl.pack(pady=60)

    def load_sample_sms(self):
        sample_path = os.path.join(os.path.dirname(__file__), "..", "..", "sample_data", "sample_pak_sms.txt")
        sample_path = os.path.abspath(sample_path)
        if os.path.exists(sample_path):
            with open(sample_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.txt_sms.delete("1.0", "end")
            self.txt_sms.insert("1.0", content)
            self.on_parse_clicked()
        else:
            messagebox.showinfo("Sample SMS", "Sample file not found at " + sample_path)

    def on_parse_clicked(self):
        raw_text = self.txt_sms.get("1.0", "end").strip()
        if not raw_text:
            messagebox.showwarning("Empty", "Please paste some SMS text to parse.")
            return

        parsed, failed = SMSBatchImporter.parse_raw_text_batch(raw_text)
        self.parsed_items = parsed

        for widget in self.preview_scroll.winfo_children():
            widget.destroy()

        self.lbl_parsed_count.configure(text=f"Parsed Transactions ({len(parsed)} valid, {len(failed)} skipped)")

        if not parsed:
            empty_lbl = ctk.CTkLabel(
                self.preview_scroll,
                text="Could not extract financial transactions from the provided text.\nMake sure the text contains Pakistani bank/wallet SMS formats.",
                text_color=COLORS["warning_amber"],
                justify="center"
            )
            empty_lbl.pack(pady=40)
            self.btn_save_all.configure(state="disabled")
            return

        self.btn_save_all.configure(state="normal", text=f"💾 Save All {len(parsed)} to DB")

        for item in parsed:
            self._render_parsed_card(item)

    def _render_parsed_card(self, item: ParsedTransaction):
        card = ctk.CTkFrame(self.preview_scroll, fg_color=COLORS["bg_input"], corner_radius=8, border_width=1, border_color=COLORS["border"])
        card.pack(fill="x", pady=5)

        top_row = ctk.CTkFrame(card, fg_color="transparent")
        top_row.pack(fill="x", padx=10, pady=(8, 2))

        # Provider Tag
        prov_lbl = ctk.CTkLabel(
            top_row,
            text=f"🏦 {item.provider}",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS["accent_cyan"]
        )
        prov_lbl.pack(side="left")

        # Type Badge
        is_credit = item.trans_type == "Credit"
        badge_color = COLORS["income_green_bg"] if is_credit else COLORS["expense_red_bg"]
        badge_text_color = COLORS["income_green"] if is_credit else COLORS["expense_red"]

        type_badge = ctk.CTkLabel(
            top_row,
            text=f" {item.trans_type.upper()} ",
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color=badge_color,
            text_color=badge_text_color,
            corner_radius=4
        )
        type_badge.pack(side="left", padx=8)

        # Amount
        amt_color = COLORS["income_green"] if is_credit else COLORS["expense_red"]
        amt_prefix = "+" if is_credit else "-"
        amt_lbl = ctk.CTkLabel(
            top_row,
            text=f"{amt_prefix}{format_pkr(item.amount)}",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=amt_color
        )
        amt_lbl.pack(side="right")

        # Details Row
        bot_row = ctk.CTkFrame(card, fg_color="transparent")
        bot_row.pack(fill="x", padx=10, pady=(2, 8))

        detail_text = f"👤 {item.recipient_or_sender}  |  🏷️ {item.category}"
        if item.ref_id:
            detail_text += f"  |  #️⃣ {item.ref_id}"
        if item.balance_after is not None:
            detail_text += f"  |  Bal: {format_pkr(item.balance_after)}"

        ctk.CTkLabel(
            bot_row,
            text=detail_text,
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"],
            anchor="w"
        ).pack(fill="x")

    def save_parsed_to_db(self):
        if not self.parsed_items:
            return

        res = self.db.import_parsed_transactions(self.parsed_items)
        msg = f"Successfully imported {res['imported']} transactions into SQLite database!"
        if res["skipped"] > 0:
            msg += f"\n\n({res['skipped']} duplicate transactions were skipped)."

        messagebox.showinfo("Import Complete", msg)

        # Reset preview
        self.parsed_items = []
        self.btn_save_all.configure(state="disabled", text="💾 Save to Database")
        self.show_empty_preview_message()

        # Trigger refresh on dashboard and ledger
        if self.on_data_changed:
            self.on_data_changed()

    def import_android_xml(self):
        file_path = filedialog.askopenfilename(
            title="Select Android SMS Backup XML File",
            filetypes=[("XML files", "*.xml"), ("All files", "*.*")]
        )
        if not file_path:
            return

        parsed, total = SMSBatchImporter.parse_android_xml_backup(file_path)
        if not parsed:
            messagebox.showinfo("XML Import", f"Checked {total} SMS messages, but found no Pakistani financial records.")
            return

        self.parsed_items = parsed
        self.lbl_parsed_count.configure(text=f"Parsed from XML ({len(parsed)} Pakistani financial SMS found from {total} messages)")

        for widget in self.preview_scroll.winfo_children():
            widget.destroy()

        self.btn_save_all.configure(state="normal", text=f"💾 Save All {len(parsed)} to DB")
        for item in parsed:
            self._render_parsed_card(item)

    def toggle_clipboard_watcher(self):
        if self.auto_clipboard_var.get():
            try:
                self.last_clipboard = self.clipboard_get().strip()
            except Exception:
                self.last_clipboard = ""
            self.check_clipboard_loop()

    def check_clipboard_loop(self):
        if not self.auto_clipboard_var.get():
            return
        try:
            current_clip = self.clipboard_get().strip()
            if current_clip and current_clip != self.last_clipboard:
                self.last_clipboard = current_clip
                # Check if it parses as a financial SMS
                parsed = PakistanSMSParser.parse_sms(current_clip)
                if parsed:
                    self.txt_sms.delete("1.0", "end")
                    self.txt_sms.insert("1.0", current_clip)
                    self.on_parse_clicked()
        except Exception:
            pass
        # Poll every 1.5 seconds
        self.after(1500, self.check_clipboard_loop)

    def get_local_ip(self) -> str:
        import socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def toggle_sync_server(self):
        if self.server_var.get():
            self.receiver.start()
            self.lbl_server_info.configure(text=f"Auto-forward Phone Push/SMS to:\n{self.server_url}", text_color=COLORS["text_secondary"])
        else:
            self.receiver.stop()
            self.lbl_server_info.configure(text="Sync Server Stopped.", text_color=COLORS["warning_amber"])

    def on_sms_webhook_received(self):
        self.after(100, self._on_remote_sms_saved)

    def _on_remote_sms_saved(self):
        if self.on_data_changed:
            self.on_data_changed()

    def show_phone_setup_guide(self):
        guide = (
            "📱 AUTOMATIC PHONE SYNC SETUP (Takes 2 Minutes)\n\n"
            "To have EasyPaisa Push Notifications, JazzCash SMS, and Meezan Bank SMS update this dashboard automatically:\n\n"
            "1. Connect your Android phone to the same Wi-Fi as this PC.\n\n"
            "2. Install 'MacroDroid' or 'SMS Forwarder' from the Google Play Store.\n\n"
            "3. Add a Trigger:\n"
            "   • Trigger 1: SMS Received -> Sender: 8558, 8267, 3737\n"
            "   • Trigger 2: Notification Received -> Select EasyPaisa app\n\n"
            "4. Add an Action:\n"
            "   • Action: HTTP Request -> Method: POST\n"
            f"   • URL: {self.server_url}\n"
            "   • Content-Type: application/json\n"
            '   • Content Body: {"body": "{notification_text}", "sender": "{notification_title}"}\n\n'
            "✅ Done! Any new transaction alert on your phone will now immediately appear in your PC Dashboard with zero manual effort!"
        )
        messagebox.showinfo("Automatic Phone Sync Setup", guide)
