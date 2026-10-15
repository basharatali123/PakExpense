"""
Pakistani Financial SMS & Text Parsing Engine.
Supports JazzCash (8558), EasyPaisa (3737), Raast, and Pakistani Commercial Banks
(Meezan, HBL, Bank Alfalah, UBL, MCB, Faysal, Standard Chartered, SadaPay, NayaPay).
"""
import re
from datetime import datetime
from typing import Optional, Dict, Any, List
from core.models import ParsedTransaction

class PakistanSMSParser:
    """High-accuracy regex and rule-based parser for Pakistani banking & wallet SMS."""

    @staticmethod
    def clean_amount(val_str: str) -> float:
        """Strip currency prefixes, commas, trailing periods, and whitespace to extract numeric float."""
        if not val_str:
            return 0.0
        val_str = val_str.rstrip(".,;: ")
        cleaned = re.sub(r"[^\d.]", "", val_str)
        parts = cleaned.split(".")
        if len(parts) > 2:
            cleaned = "".join(parts[:-1]) + "." + parts[-1]
        try:
            return float(cleaned)
        except ValueError:
            return 0.0

    @staticmethod
    def extract_datetime(text: str, default_date: str) -> str:
        """Extract explicit timestamp from Pakistani SMS text if present, else fallback."""
        m = re.search(r"on\s+(\d{2,4}[-/]\d{2}[-/]\d{2,4})\s+at\s+(\d{1,2}:\d{2}(?::\d{2})?)", text, re.IGNORECASE)
        if m:
            d_part = m.group(1)
            t_part = m.group(2)[:5]
            parts = re.split(r"[-/]", d_part)
            if len(parts) == 3:
                if len(parts[0]) == 4:
                    return f"{parts[0]}-{parts[1]}-{parts[2]} {t_part}"
                elif len(parts[2]) == 4:
                    return f"{parts[2]}-{parts[1]}-{parts[0]} {t_part}"
            return f"{d_part} {t_part}"

        m2 = re.search(r"on\s+(\d{1,2}-[A-Za-z]+-\d{4})\s+at\s+(\d{1,2}:\d{2})", text, re.IGNORECASE)
        if m2:
            return f"{m2.group(1)} {m2.group(2)}"

        return default_date

    @staticmethod
    def detect_category(text: str, trans_type: str) -> str:
        """Auto-categorize transaction based on Pakistani merchant/vendor keywords."""
        lower = text.lower()
        
        # Salary / Income
        if any(w in lower for w in ["salary", "payroll", "dividend", "profit credit"]):
            return "Salary / Income"
        
        # Utilities & Bills
        if any(w in lower for w in [
            "k-electric", "kelectric", "lesco", "iesco", "gepco", "fesco", "mepco", "pesco", "qesco",
            "ssgc", "sngpl", "ptcl", "stormfiber", "nayatel", "bill payment", "electricity bill",
            "gas bill", "water board", "bill paid"
        ]):
            return "Bills & Utilities (KE/LESCO/SNGPL/PTCL)"
        
        # Mobile Load
        if any(w in lower for w in ["easyload", "prepaid load", "mobile load", "super card", "bundle", "loaded to mobile"]):
            return "Mobile Load & Packages"
        
        # ATM Cash Withdrawal
        if any(w in lower for w in ["atm", "cash withdrawal", "cash withdrawn", "1link atm", "withdrawn from atm"]):
            return "Cash Withdrawal (ATM)"
        
        # Fuel & Transport
        if any(w in lower for w in ["shell", "pso", "total parco", "attock", "bykea", "careem", "indrive", "uber", "petrol", "daewoo", "niazi", "faisal movers"]):
            return "Fuel & Transport (Careem/Bykea/Shell/PSO)"
            
        # Food & Dining
        if any(w in lower for w in [
            "foodpanda", "kfc", "mcdonald", "subway", "cheezious", "chaye khana", "hardees", 
            "burger lab", "optp", "domino", "broadway", "howdy", "ginsoy", "cafe", "restaurant"
        ]):
            return "Food & Dining"
            
        # Groceries & Supermarkets
        if any(w in lower for w in ["imtiaz", "carrefour", "al-fatah", "al fatah", "metro", "chase up", "naheed", "greenvalley", "supermarket", "mart"]):
            return "Groceries & Supermarket"
            
        # Medical / Health
        if any(w in lower for w in ["pharmacy", "jinnah pharmacy", "chughtai", "shaukat khanum", "hospital", "clinic", "medical", "d-watson", "fazal din"]):
            return "Health & Medical"
            
        # General Sent / Received
        if trans_type == "Credit":
            return "Money Transfer Received"
        else:
            return "Money Transfer Sent"

    @classmethod
    def parse_sms(cls, text: str, sender_id: str = "") -> Optional[ParsedTransaction]:
        """
        Parse a single SMS or notification string from Pakistani financial providers.
        Returns a ParsedTransaction dataclass or None if not recognized.
        """
        text = text.strip()
        if not text:
            return None

        sender_id_lower = sender_id.strip().lower()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

        # ----------------------------------------------------
        # 1. JAZZCASH (8558 or keywords)
        # ----------------------------------------------------
        if any(w in sender_id_lower for w in ["8558", "jazzcash", "mobilink"]) or "jazzcash" in text.lower():
            return cls._parse_jazzcash(text, now_str)

        # ----------------------------------------------------
        # 2. EASYPAISA (3737, easypaisa push notification)
        # ----------------------------------------------------
        if any(w in sender_id_lower for w in ["3737", "easypaisa", "telenor"]) or "easypaisa" in text.lower():
            return cls._parse_easypaisa(text, now_str)

        # ----------------------------------------------------
        # 3. MEEZAN BANK (8079, 8267 or 'meezan')
        # ----------------------------------------------------
        if any(w in sender_id_lower for w in ["8079", "8267", "meezan", "meezanbank"]) or "meezan" in text.lower():
            return cls._parse_meezan(text, now_str)

        # ----------------------------------------------------
        # 4. HBL (4250 or 'hbl')
        # ----------------------------------------------------
        if sender_id_lower == "4250" or "hbl" in text.lower() or "habib bank" in text.lower():
            return cls._parse_hbl(text, now_str)

        # ----------------------------------------------------
        # 5. BANK ALFALAH (8222 or 'alfalah')
        # ----------------------------------------------------
        if sender_id_lower == "8222" or "alfalah" in text.lower():
            return cls._parse_alfalah(text, now_str)

        # ----------------------------------------------------
        # 6. SADAPAY & NAYAPAY
        # ----------------------------------------------------
        if "sadapay" in text.lower() or "nayapay" in text.lower():
            return cls._parse_fintech(text, now_str)

        # ----------------------------------------------------
        # 7. GENERIC PAKISTANI BANK / RAAST FALLBACK
        # ----------------------------------------------------
        generic_res = cls._parse_generic_bank(text, now_str)
        if generic_res:
            return generic_res

        # If sender_id was provided (e.g. 8558 or 3737) but didn't have provider name in body
        if sender_id_lower in ["8558"]:
            return cls._parse_jazzcash(text, now_str)
        elif sender_id_lower in ["3737"]:
            return cls._parse_easypaisa(text, now_str)
        elif sender_id_lower in ["8079", "8267"]:
            return cls._parse_meezan(text, now_str)

        return None

    @classmethod
    def _parse_jazzcash(cls, text: str, default_date: str) -> Optional[ParsedTransaction]:
        """Parse JazzCash 8558 patterns."""
        lower = text.lower()
        trans_type = "Debit"
        amount = 0.0
        ref_id = ""
        recipient = "JazzCash Service"
        balance_after = None
        fee = 0.0
        trans_date = cls.extract_datetime(text, default_date)

        # Ref / Trx ID / TID
        trx_match = re.search(r"(?:Trx\s*ID|TID|T\.ID|Trx)\s*[:#]?\s*(\d+)", text, re.IGNORECASE)
        if trx_match:
            ref_id = trx_match.group(1)

        # Fee
        fee_match = re.search(r"Fee\s*[:#]?\s*(?:Rs\.?|PKR)?\s*([\d,.]+)", text, re.IGNORECASE)
        if fee_match:
            fee = cls.clean_amount(fee_match.group(1))

        # Balance
        bal_match = re.search(r"(?:Balance|Bal|New Bal|New Balance)\s*[:#]?\s*(?:Rs\.?|PKR)?\s*([\d,.]+)", text, re.IGNORECASE)
        if bal_match:
            balance_after = cls.clean_amount(bal_match.group(1))

        # Amount extraction (handles Rs 1,610.00, Rs. 1, amount of Rs. 1)
        amt_match = re.search(r"(?:amount of\s+)?(?:Rs\.?|PKR)\s*([\d,.]+)", text, re.IGNORECASE)
        if amt_match:
            amount = cls.clean_amount(amt_match.group(1))

        # 1. Received Money
        if "received" in lower:
            trans_type = "Credit"
            m = re.search(r"received\s+(?:Rs\.?|PKR)?\s*[\d,.]*\s+from\s+([^.]+?)(?:\s+in|\s+on|\.|$)", text, re.IGNORECASE)
            if m:
                recipient = m.group(1).strip()
            elif "via raast" in lower:
                recipient = "Received via Raast"

        # 2. Sent Money / Transferred / Paid To
        elif any(k in lower for k in ["sent to", "transferred to", "paid to"]):
            trans_type = "Debit"
            m = re.search(r"(?:sent to|transferred to|paid to)\s+([^.]+?)(?:\s+of\s+iban|\s+from|\s+on\s+\d|\s+at\s+\d|\s+fee|\.|$)", text, re.IGNORECASE)
            if m:
                recipient = m.group(1).strip()

        # 3. Bill payment / Load / Merchant
        elif any(k in lower for k in ["bill payment", "payment of", "paid rs", "prepaid load"]):
            trans_type = "Debit"
            for_m = re.search(r"(?:to|for)\s+([A-Za-z0-9\s-]+?)(?:\s+successful|\s+Fee|\s+was|\.|$)", text, re.IGNORECASE)
            if for_m:
                recipient = for_m.group(1).strip()

        if amount <= 0:
            return None

        category = cls.detect_category(text, trans_type)

        return ParsedTransaction(
            provider="JazzCash",
            trans_type=trans_type,
            amount=amount,
            date_str=trans_date,
            recipient_or_sender=recipient,
            ref_id=ref_id,
            fee=fee,
            balance_after=balance_after,
            category=category,
            raw_text=text,
            source_channel="SMS",
            account_name="JazzCash"
        )

    @classmethod
    def _parse_easypaisa(cls, text: str, default_date: str) -> Optional[ParsedTransaction]:
        """Parse EasyPaisa 3737 patterns."""
        lower = text.lower()
        trans_type = "Debit"
        amount = 0.0
        ref_id = ""
        recipient = "EasyPaisa Service"
        balance_after = None
        fee = 0.0

        # Ref / Trx ID
        trx_match = re.search(r"(?:Trx\s*ID|Trans\s*ID|TR\s*ID|TID)\s*[:#]?\s*(\d+)", text, re.IGNORECASE)
        if trx_match:
            ref_id = trx_match.group(1)

        # Balance
        bal_match = re.search(r"(?:new\s+balance\s+is|bal(?:ance)?\s*[:#]?)\s*(?:Rs\.?|PKR)?\s*([\d,.]+)", text, re.IGNORECASE)
        if bal_match:
            balance_after = cls.clean_amount(bal_match.group(1))

        # Fee
        fee_match = re.search(r"Fee\s*[:#]?\s*(?:Rs\.?|PKR)?\s*([\d,.]+)", text, re.IGNORECASE)
        if fee_match:
            fee = cls.clean_amount(fee_match.group(1))

        # 1. Received Money
        if "received" in lower:
            trans_type = "Credit"
            m = re.search(r"(?:received\s+(?:Rs\.?|PKR)?\s*([\d,.]+)\s+from\s+([^.]+?)(?:\.|$)|(?:Rs\.?|PKR)?\s*([\d,.]+)\s+received\s+from\s+([^.]+?)(?:\.|$))", text, re.IGNORECASE)
            if m:
                amount_str = m.group(1) or m.group(3)
                recipient = (m.group(2) or m.group(4) or "Sender").strip()
                amount = cls.clean_amount(amount_str)
            else:
                amt_m = re.search(r"(?:Rs\.?|PKR)\s*([\d,.]+)", text, re.IGNORECASE)
                if amt_m:
                    amount = cls.clean_amount(amt_m.group(1))

        # 2. Sent / Transferred
        elif "transferred" in lower or "sent" in lower:
            trans_type = "Debit"
            m = re.search(r"(?:transferred|sent)\s+(?:Rs\.?|PKR)?\s*([\d,.]+)\s+to\s+([^.]+?)(?:\.|\s+Fee|\s+New balance|$)", text, re.IGNORECASE)
            if m:
                amount = cls.clean_amount(m.group(1))
                recipient = m.group(2).strip()
            else:
                amt_m = re.search(r"(?:Rs\.?|PKR)\s*([\d,.]+)", text, re.IGNORECASE)
                if amt_m:
                    amount = cls.clean_amount(amt_m.group(1))

        # 3. Bill / Load / Paid
        elif "paid" in lower or "loaded" in lower:
            trans_type = "Debit"
            amt_m = re.search(r"(?:Rs\.?|PKR)\s*([\d,.]+)", text, re.IGNORECASE)
            if amt_m:
                amount = cls.clean_amount(amt_m.group(1))
            
            for_m = re.search(r"(?:paid\s+(?:Rs\.?|PKR)?\s*[\d,.]+\s+(?:to|for)\s+([^.]+?)(?:\.|\s+via|\s+Trx|$)|loaded\s+to\s+([^.]+?)(?:\.|$))", text, re.IGNORECASE)
            if for_m:
                recipient = (for_m.group(1) or for_m.group(2) or "EasyPaisa Service").strip()

        else:
            amt_m = re.search(r"(?:Rs\.?|PKR)\s*([\d,.]+)", text, re.IGNORECASE)
            if amt_m:
                amount = cls.clean_amount(amt_m.group(1))

        if amount <= 0:
            return None

        category = cls.detect_category(text, trans_type)

        return ParsedTransaction(
            provider="EasyPaisa",
            trans_type=trans_type,
            amount=amount,
            date_str=default_date,
            recipient_or_sender=recipient,
            ref_id=ref_id,
            fee=fee,
            balance_after=balance_after,
            category=category,
            raw_text=text,
            source_channel="SMS",
            account_name="EasyPaisa"
        )

    @classmethod
    def _parse_meezan(cls, text: str, default_date: str) -> Optional[ParsedTransaction]:
        """Parse Meezan Bank 8079 / 8267 SMS."""
        lower = text.lower()
        trans_type = "Debit"
        if "credited" in lower:
            trans_type = "Credit"

        # Amount extraction
        amt_match = re.search(r"(?:PKR|Rs\.?)\s*([\d,.]+)", text, re.IGNORECASE)
        if not amt_match:
            return None
        amount = cls.clean_amount(amt_match.group(1))

        # Available Balance
        bal_match = re.search(r"(?:Available\s+Bal(?:ance)?\s+is\s+(?:PKR|Rs\.?)|Avail\s+Bal\s+(?:PKR|Rs\.?))\s*([\d,.]+)", text, re.IGNORECASE)
        balance_after = cls.clean_amount(bal_match.group(1)) if bal_match else None

        # Reference / TID
        ref_match = re.search(r"(?:Ref\s*[:#]?|Reference\s*[:#]?|TID\s*[:#]?)\s*([A-Za-z0-9]+)", text, re.IGNORECASE)
        ref_id = ref_match.group(1) if ref_match else ""

        # Fee
        fee = 0.0
        fee_match = re.search(r"Fee\s*[:#]?\s*(?:Rs\.?|PKR)?\s*([\d,.]+)", text, re.IGNORECASE)
        if fee_match:
            fee = cls.clean_amount(fee_match.group(1))

        # Timestamp
        trans_date = cls.extract_datetime(text, default_date)

        # Merchant / Recipient
        recipient = "Meezan Bank"
        if "charged at" in lower:
            m = re.search(r"charged\s+at\s+([^.]+?)\s+for\s+card\s+used", text, re.IGNORECASE)
            if m:
                recipient = m.group(1).strip()
        elif "cash withdrawn" in lower:
            m = re.search(r"cash\s+withdrawn\s+from\s+([^.]+?)\s+from\s+A/C", text, re.IGNORECASE)
            if m:
                recipient = m.group(1).strip()
            else:
                recipient = "1Link ATM"
        elif "sent to" in lower:
            m = re.search(r"sent\s+to\s+([^.]+?)\s+from\s+your\s+A/C", text, re.IGNORECASE)
            if m:
                recipient = m.group(1).strip()
        elif " at " in text:
            m = re.search(r"\sat\s+([^.]+?)(?:\.|\s+Available|\s+Avail|$)", text, re.IGNORECASE)
            if m:
                recipient = m.group(1).strip()
        elif "to " in text:
            m = re.search(r"\sto\s+([^.]+?)(?:\.|\s+Available|\s+successful|$)", text, re.IGNORECASE)
            if m:
                recipient = m.group(1).strip()
        elif "from " in text and trans_type == "Credit":
            m = re.search(r"\sfrom\s+([^.]+?)(?:\.|\s+Available|\s+Avail|$)", text, re.IGNORECASE)
            if m:
                recipient = m.group(1).strip()

        category = cls.detect_category(text, trans_type)

        return ParsedTransaction(
            provider="Meezan Bank",
            trans_type=trans_type,
            amount=amount,
            date_str=trans_date,
            recipient_or_sender=recipient,
            ref_id=ref_id,
            fee=fee,
            balance_after=balance_after,
            category=category,
            raw_text=text,
            source_channel="SMS",
            account_name="Meezan Bank"
        )

    @classmethod
    def _parse_hbl(cls, text: str, default_date: str) -> Optional[ParsedTransaction]:
        """Parse HBL 4250 SMS."""
        lower = text.lower()
        trans_type = "Debit"
        if "credited" in lower:
            trans_type = "Credit"

        amt_match = re.search(r"(?:PKR|Rs\.?)\s*([\d,.]+)", text, re.IGNORECASE)
        if not amt_match:
            return None
        amount = cls.clean_amount(amt_match.group(1))

        # Balance
        bal_match = re.search(r"(?:Bal(?:ance)?|Avail\s+Bal)\s*[:#]?\s*(?:PKR|Rs\.?)\s*([\d,.]+)", text, re.IGNORECASE)
        balance_after = cls.clean_amount(bal_match.group(1)) if bal_match else None

        # Reference
        ref_match = re.search(r"Ref\s*[:#]?\s*([A-Za-z0-9]+)", text, re.IGNORECASE)
        ref_id = ref_match.group(1) if ref_match else ""

        recipient = "HBL"
        if " at " in text:
            m = re.search(r"\sat\s+([^.]+?)(?:\.|\s+Bal|$)", text, re.IGNORECASE)
            if m:
                recipient = m.group(1).strip()

        category = cls.detect_category(text, trans_type)

        return ParsedTransaction(
            provider="HBL",
            trans_type=trans_type,
            amount=amount,
            date_str=default_date,
            recipient_or_sender=recipient,
            ref_id=ref_id,
            balance_after=balance_after,
            category=category,
            raw_text=text,
            source_channel="SMS",
            account_name="HBL"
        )

    @classmethod
    def _parse_alfalah(cls, text: str, default_date: str) -> Optional[ParsedTransaction]:
        """Parse Bank Alfalah 8222 SMS."""
        lower = text.lower()
        trans_type = "Credit" if "credited" in lower else "Debit"

        amt_match = re.search(r"(?:PKR|Rs\.?)\s*([\d,.]+)", text, re.IGNORECASE)
        if not amt_match:
            return None
        amount = cls.clean_amount(amt_match.group(1))

        bal_match = re.search(r"Avail\s+Bal\s+(?:PKR|Rs\.?)\s*([\d,.]+)", text, re.IGNORECASE)
        balance_after = cls.clean_amount(bal_match.group(1)) if bal_match else None

        ref_match = re.search(r"Ref\s*#?\s*([A-Za-z0-9]+)", text, re.IGNORECASE)
        ref_id = ref_match.group(1) if ref_match else ""

        recipient = "Bank Alfalah"
        if " at " in text:
            m = re.search(r"\sat\s+([^.]+?)(?:\.|\s+Avail|$)", text, re.IGNORECASE)
            if m:
                recipient = m.group(1).strip()

        category = cls.detect_category(text, trans_type)

        return ParsedTransaction(
            provider="Bank Alfalah",
            trans_type=trans_type,
            amount=amount,
            date_str=default_date,
            recipient_or_sender=recipient,
            ref_id=ref_id,
            balance_after=balance_after,
            category=category,
            raw_text=text,
            source_channel="SMS",
            account_name="Bank Alfalah"
        )

    @classmethod
    def _parse_fintech(cls, text: str, default_date: str) -> Optional[ParsedTransaction]:
        """Parse SadaPay and NayaPay transaction alerts."""
        lower = text.lower()
        provider = "SadaPay" if "sadapay" in lower else "NayaPay"
        trans_type = "Credit" if any(w in lower for w in ["received", "credited", "added"]) else "Debit"

        amt_match = re.search(r"(?:Rs\.?|PKR)\s*([\d,.]+)", text, re.IGNORECASE)
        if not amt_match:
            return None
        amount = cls.clean_amount(amt_match.group(1))

        recipient = provider
        if " at " in text:
            m = re.search(r"\sat\s+([^.]+?)(?:\s+using|\.|$)", text, re.IGNORECASE)
            if m:
                recipient = m.group(1).strip()
        elif "from " in text:
            m = re.search(r"\sfrom\s+([^.]+?)(?:\s+on|\.|$)", text, re.IGNORECASE)
            if m:
                recipient = m.group(1).strip()

        category = cls.detect_category(text, trans_type)

        return ParsedTransaction(
            provider=provider,
            trans_type=trans_type,
            amount=amount,
            date_str=default_date,
            recipient_or_sender=recipient,
            ref_id="",
            category=category,
            raw_text=text,
            source_channel="SMS",
            account_name=provider
        )

    @classmethod
    def _parse_generic_bank(cls, text: str, default_date: str) -> Optional[ParsedTransaction]:
        """Generic Pakistani bank SMS fallback looking for standard Pakistani banking terms."""
        lower = text.lower()
        has_debit = any(w in lower for w in ["debited", "debit", "withdrawn", "paid", "spent"])
        has_credit = any(w in lower for w in ["credited", "credit", "received", "deposit"])
        
        if not (has_debit or has_credit):
            return None

        amt_match = re.search(r"(?:PKR|Rs\.?)\s*([\d,.]+)", text, re.IGNORECASE)
        if not amt_match:
            return None
        amount = cls.clean_amount(amt_match.group(1))
        if amount <= 0:
            return None

        trans_type = "Credit" if (has_credit and not has_debit) else "Debit"

        # Determine Provider
        provider = "Commercial Bank"
        account_name = "Commercial Bank"
        if "ubl" in lower:
            provider = account_name = "UBL"
        elif "mcb" in lower:
            provider = account_name = "MCB"
        elif "faysal" in lower:
            provider = account_name = "Faysal Bank"
        elif "standard chartered" in lower or "scb" in lower:
            provider = account_name = "Standard Chartered"
        elif "allied" in lower or "abl" in lower:
            provider = account_name = "Allied Bank"
        elif "raast" in lower:
            provider = account_name = "Raast Transfer"

        # Ref
        ref_match = re.search(r"(?:Ref(?:erence)?|Trx|Txn|TID)\s*[:#]?\s*([A-Za-z0-9]+)", text, re.IGNORECASE)
        ref_id = ref_match.group(1) if ref_match else ""

        recipient = provider
        if " at " in text:
            m = re.search(r"\sat\s+([^.]+?)(?:\.|\s+Avail|$)", text, re.IGNORECASE)
            if m:
                recipient = m.group(1).strip()
        elif " to " in text:
            m = re.search(r"\sto\s+([^.]+?)(?:\.|\s+Avail|$)", text, re.IGNORECASE)
            if m:
                recipient = m.group(1).strip()

        category = cls.detect_category(text, trans_type)

        return ParsedTransaction(
            provider=provider,
            trans_type=trans_type,
            amount=amount,
            date_str=default_date,
            recipient_or_sender=recipient,
            ref_id=ref_id,
            category=category,
            raw_text=text,
            source_channel="SMS",
            account_name=account_name
        )
