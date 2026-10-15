"""
Styling tokens, color palette, and helper formatters for CustomTkinter UI.
"""

# Color Palette (Dark Mode Premium FinTech Theme)
COLORS = {
    "bg_dark": "#0F172A",          # Slate 900
    "bg_sidebar": "#1E293B",       # Slate 800
    "bg_card": "#1E293B",          # Slate 800
    "bg_card_hover": "#334155",    # Slate 700
    "bg_input": "#0F172A",         # Slate 900
    
    # Brand Accents
    "primary": "#0D9488",          # Teal 600
    "primary_hover": "#0F766E",    # Teal 700
    "accent_cyan": "#06B6D4",      # Cyan 500
    
    # Financial Status Colors
    "income_green": "#10B981",     # Emerald 500
    "income_green_bg": "#064E3B",  # Deep emerald
    "expense_red": "#F43F5E",      # Rose 500
    "expense_red_bg": "#881337",   # Deep rose
    "warning_amber": "#F59E0B",    # Amber 500
    
    # Text
    "text_primary": "#F8FAFC",     # Slate 50
    "text_secondary": "#94A3B8",   # Slate 400
    "text_muted": "#64748B",       # Slate 500
    
    # Borders
    "border": "#334155",
}

def format_pkr(amount: float) -> str:
    """Format numeric float as Pakistani Rupee string (e.g. Rs. 45,250.00)."""
    if amount is None:
        amount = 0.0
    return f"Rs. {amount:,.2f}"

def format_pkr_short(amount: float) -> str:
    """Format large Pakistani Rupee amount compactly (e.g. 1.5 Lakh, 2.5 Crore, or 45K)."""
    if amount is None:
        return "Rs. 0"
    abs_amt = abs(amount)
    sign = "-" if amount < 0 else ""
    if abs_amt >= 10000000:  # 1 Crore
        return f"{sign}Rs. {abs_amt/10000000:.2f} Cr"
    elif abs_amt >= 100000:  # 1 Lakh
        return f"{sign}Rs. {abs_amt/100000:.2f} Lac"
    elif abs_amt >= 1000:
        return f"{sign}Rs. {abs_amt/1000:.1f}k"
    else:
        return f"{sign}Rs. {abs_amt:,.0f}"
