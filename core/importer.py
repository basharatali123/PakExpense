"""
Batch and file importers for SMS logs, raw pasted text, and Android XML/JSON backups.
"""
import re
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Tuple, Dict, Any
from core.parser import PakistanSMSParser
from core.models import ParsedTransaction

class SMSBatchImporter:
    """Handles batch SMS ingestion from clipboard pastes and Android SMS backup files."""

    @staticmethod
    def parse_raw_text_batch(raw_text: str) -> Tuple[List[ParsedTransaction], List[str]]:
        """
        Split user pasted text into individual messages and parse them.
        Splits on double newlines or lines starting with known keywords.
        """
        parsed_items: List[ParsedTransaction] = []
        failed_blocks: List[str] = []

        # Split by multiple newlines first
        blocks = [b.strip() for b in re.split(r"\n\s*\n+", raw_text) if b.strip()]

        for block in blocks:
            # Check if block contains multiple single-line SMS messages
            lines = [l.strip() for l in block.split("\n") if l.strip()]
            
            # If a block has multiple lines, test if the whole block parses, or each line parses
            parsed = PakistanSMSParser.parse_sms(block)
            if parsed:
                parsed_items.append(parsed)
            else:
                # Try parsing line-by-line
                line_matched = False
                for line in lines:
                    sub_parsed = PakistanSMSParser.parse_sms(line)
                    if sub_parsed:
                        parsed_items.append(sub_parsed)
                        line_matched = True
                    else:
                        failed_blocks.append(line)
                if not line_matched and not lines:
                    failed_blocks.append(block)

        return parsed_items, failed_blocks

    @staticmethod
    def parse_android_xml_backup(xml_filepath: str) -> Tuple[List[ParsedTransaction], int]:
        """
        Parse Android 'SMS Backup & Restore' (SyncTech) XML export file.
        Filters for shortcodes: 8558, 3737, 8267, 4250, 8222, etc.
        """
        parsed_items: List[ParsedTransaction] = []
        total_sms_checked = 0

        pak_financial_addresses = {
            "8558", "3737", "8267", "4250", "8222", "8257", "6222", "9672",
            "meezanbank", "meezan", "hbl", "alfalah", "ubl", "mcb", "sadapay", "nayapay"
        }

        try:
            tree = ET.parse(xml_filepath)
            root = tree.getroot()

            # The standard root contains <sms> tags
            for sms in root.iter("sms"):
                total_sms_checked += 1
                address = (sms.attrib.get("address") or "").strip().lower()
                body = (sms.attrib.get("body") or "").strip()
                date_ms = sms.attrib.get("date")

                # Format timestamp
                date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
                if date_ms and date_ms.isdigit():
                    try:
                        date_str = datetime.fromtimestamp(int(date_ms) / 1000.0).strftime("%Y-%m-%d %H:%M")
                    except Exception:
                        pass

                # Match address or financial keywords in body
                is_financial = any(addr in address for addr in pak_financial_addresses) or any(
                    kw in body.lower() for kw in ["jazzcash", "easypaisa", "debited by", "credited to", "trx id", "avail bal"]
                )

                if is_financial and body:
                    parsed = PakistanSMSParser.parse_sms(body, sender_id=address)
                    if parsed:
                        parsed.date_str = date_str
                        parsed_items.append(parsed)

        except Exception as e:
            print(f"Error parsing Android XML backup: {e}")

        return parsed_items, total_sms_checked
