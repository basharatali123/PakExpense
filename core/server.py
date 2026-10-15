"""
Lightweight Local HTTP Webhook Server for Real-Time Android SMS Auto-Sync.
Allows phone automation tools (MacroDroid, Tasker, SMS Forwarder) on the same Wi-Fi
to push incoming SMS alerts directly to PakExpense automatically in real time.
"""
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional, Callable
from core.parser import PakistanSMSParser
from core.db import DatabaseManager

class SMSWebhookHandler(BaseHTTPRequestHandler):
    db: Optional[DatabaseManager] = None
    on_transaction_received: Optional[Callable] = None

    def log_message(self, format, *args):
        # Suppress default stdout server logging
        return

    def do_POST(self):
        if self.path == "/api/sms":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode("utf-8"))
                body = data.get("body") or data.get("message") or data.get("text") or ""
                sender = data.get("sender") or data.get("address") or data.get("from") or ""

                if not body:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(b'{"error": "No body provided"}')
                    return

                parsed = PakistanSMSParser.parse_sms(body, sender_id=sender)
                if not parsed:
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b'{"status": "ignored", "reason": "Not a recognized financial SMS"}')
                    return

                # Save directly into SQLite Database
                if self.db:
                    res = self.db.import_parsed_transactions([parsed])
                    if self.on_transaction_received:
                        self.on_transaction_received()

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                resp = {
                    "status": "success",
                    "provider": parsed.provider,
                    "type": parsed.trans_type,
                    "amount": parsed.amount,
                    "category": parsed.category
                }
                self.wfile.write(json.dumps(resp).encode("utf-8"))

            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

class LocalSMSReceiver:
    """Manages the background HTTP server for wireless SMS ingestion."""

    def __init__(self, db_manager: DatabaseManager, port: int = 8558, on_received_callback=None):
        self.db = db_manager
        self.port = port
        self.on_received = on_received_callback
        self.server: Optional[HTTPServer] = None
        self.thread: Optional[threading.Thread] = None
        self.is_running = False

    def start(self) -> bool:
        if self.is_running:
            return True
        try:
            SMSWebhookHandler.db = self.db
            SMSWebhookHandler.on_transaction_received = self.on_received
            self.server = HTTPServer(("0.0.0.0", self.port), SMSWebhookHandler)
            self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.thread.start()
            self.is_running = True
            return True
        except Exception as e:
            print(f"Could not start SMS webhook server on port {self.port}: {e}")
            self.is_running = False
            return False

    def stop(self):
        if self.server and self.is_running:
            self.server.shutdown()
            self.server.server_close()
            self.is_running = False
