"""
Constants for Synthetic Data Generation
========================================

Comprehensive constants including countries, currencies, languages, time zones,
tax havens, suspicious keywords, and other reference data.

Author: IBM Bob
Date: 2026-01-28
"""

from typing import Dict, List, Tuple

# ============================================================================
# COUNTRIES & REGIONS
# ============================================================================

# ISO 3166-1 alpha-2 country codes with names
COUNTRIES: Dict[str, str] = {
    # Major Financial Centers
    "US": "United States",
    "GB": "United Kingdom",
    "CH": "Switzerland",
    "SG": "Singapore",
    "HK": "Hong Kong",
    "JP": "Japan",
    "DE": "Germany",
    "FR": "France",
    "LU": "Luxembourg",
    "NL": "Netherlands",
    
    # Tax Havens & Offshore Centers
    "KY": "Cayman Islands",
    "BM": "Bermuda",
    "VG": "British Virgin Islands",
    "PA": "Panama",
    "LI": "Liechtenstein",
    "MC": "Monaco",
    "AD": "Andorra",
    "BS": "Bahamas",
    "BB": "Barbados",
    "MU": "Mauritius",
    "SC": "Seychelles",
    "MT": "Malta",
    "CY": "Cyprus",
    "IE": "Ireland",
    
    # High-Risk Jurisdictions
    "RU": "Russia",
    "CN": "China",
    "IR": "Iran",
    "KP": "North Korea",
    "SY": "Syria",
    "VE": "Venezuela",
    "MM": "Myanmar",
    "AF": "Afghanistan",
    
    # Other Major Economies
    "CA": "Canada",
    "AU": "Australia",
    "BR": "Brazil",
    "IN": "India",
    "MX": "Mexico",
    "IT": "Italy",
    "ES": "Spain",
    "KR": "South Korea",
    "SA": "Saudi Arabia",
    "AE": "United Arab Emirates",
    "TR": "Turkey",
    "ZA": "South Africa",
    "AR": "Argentina",
    "CL": "Chile",
    "CO": "Colombia",
    "PE": "Peru",
    "TH": "Thailand",
    "MY": "Malaysia",
    "ID": "Indonesia",
    "PH": "Philippines",
    "VN": "Vietnam",
    "EG": "Egypt",
    "NG": "Nigeria",
    "KE": "Kenya",
    "PL": "Poland",
    "SE": "Sweden",
    "NO": "Norway",
    "DK": "Denmark",
    "FI": "Finland",
    "AT": "Austria",
    "BE": "Belgium",
    "PT": "Portugal",
    "GR": "Greece",
    "CZ": "Czech Republic",
    "RO": "Romania",
    "HU": "Hungary",
    "NZ": "New Zealand",
    "IL": "Israel",
    "QA": "Qatar",
    "KW": "Kuwait",
    "OM": "Oman",
    "BH": "Bahrain",
}

# Tax havens and offshore financial centers
TAX_HAVENS: List[str] = [
    "KY", "BM", "VG", "PA", "LI", "MC", "AD", "BS", "BB", "MU", "SC", "MT", "CY", "IE", "LU"
]

# High-risk countries for AML/CFT
HIGH_RISK_COUNTRIES: List[str] = [
    "RU", "CN", "IR", "KP", "SY", "VE", "MM", "AF", "YE", "SO", "SD", "LY"
]

# Major financial centers
FINANCIAL_CENTERS: List[str] = [
    "US", "GB", "CH", "SG", "HK", "JP", "DE", "FR", "LU", "NL"
]


# ============================================================================
# CURRENCIES
# ============================================================================

# ISO 4217 currency codes with names and symbols
CURRENCIES: Dict[str, Tuple[str, str]] = {
    # Major Currencies
    "USD": ("US Dollar", "$"),
    "EUR": ("Euro", "€"),
    "GBP": ("British Pound", "£"),
    "JPY": ("Japanese Yen", "¥"),
    "CHF": ("Swiss Franc", "CHF"),
    "CAD": ("Canadian Dollar", "C$"),
    "AUD": ("Australian Dollar", "A$"),
    "NZD": ("New Zealand Dollar", "NZ$"),
    "SGD": ("Singapore Dollar", "S$"),
    "HKD": ("Hong Kong Dollar", "HK$"),
    
    # Asian Currencies
    "CNY": ("Chinese Yuan", "¥"),
    "INR": ("Indian Rupee", "₹"),
    "KRW": ("South Korean Won", "₩"),
    "THB": ("Thai Baht", "฿"),
    "MYR": ("Malaysian Ringgit", "RM"),
    "IDR": ("Indonesian Rupiah", "Rp"),
    "PHP": ("Philippine Peso", "₱"),
    "VND": ("Vietnamese Dong", "₫"),
    
    # Middle Eastern Currencies
    "SAR": ("Saudi Riyal", "﷼"),
    "AED": ("UAE Dirham", "د.إ"),
    "QAR": ("Qatari Riyal", "﷼"),
    "KWD": ("Kuwaiti Dinar", "د.ك"),
    "BHD": ("Bahraini Dinar", "د.ب"),
    "OMR": ("Omani Rial", "﷼"),
    "ILS": ("Israeli Shekel", "₪"),
    "TRY": ("Turkish Lira", "₺"),
    
    # Latin American Currencies
    "BRL": ("Brazilian Real", "R$"),
    "MXN": ("Mexican Peso", "$"),
    "ARS": ("Argentine Peso", "$"),
    "CLP": ("Chilean Peso", "$"),
    "COP": ("Colombian Peso", "$"),
    "PEN": ("Peruvian Sol", "S/"),
    
    # European Currencies (non-Euro)
    "SEK": ("Swedish Krona", "kr"),
    "NOK": ("Norwegian Krone", "kr"),
    "DKK": ("Danish Krone", "kr"),
    "PLN": ("Polish Zloty", "zł"),
    "CZK": ("Czech Koruna", "Kč"),
    "HUF": ("Hungarian Forint", "Ft"),
    "RON": ("Romanian Leu", "lei"),
    "RUB": ("Russian Ruble", "₽"),
    
    # African Currencies
    "ZAR": ("South African Rand", "R"),
    "EGP": ("Egyptian Pound", "£"),
    "NGN": ("Nigerian Naira", "₦"),
    "KES": ("Kenyan Shilling", "KSh"),
    
    # Cryptocurrencies
    "BTC": ("Bitcoin", "₿"),
    "ETH": ("Ethereum", "Ξ"),
    "USDT": ("Tether", "₮"),
    "USDC": ("USD Coin", "$"),
    "XRP": ("Ripple", "XRP"),
}

# Major reserve currencies
RESERVE_CURRENCIES: List[str] = ["USD", "EUR", "GBP", "JPY", "CHF"]

# Cryptocurrencies
CRYPTOCURRENCIES: List[str] = ["BTC", "ETH", "USDT", "USDC", "XRP"]


# ============================================================================
# LANGUAGES
# ============================================================================

# ISO 639-1 language codes with names
LANGUAGES: Dict[str, str] = {
    # Major Languages
    "en": "English",
    "zh": "Chinese",
    "es": "Spanish",
    "hi": "Hindi",
    "ar": "Arabic",
    "pt": "Portuguese",
    "bn": "Bengali",
    "ru": "Russian",
    "ja": "Japanese",
    "de": "German",
    "fr": "French",
    "it": "Italian",
    "ko": "Korean",
    "tr": "Turkish",
    "vi": "Vietnamese",
    "pl": "Polish",
    "uk": "Ukrainian",
    "nl": "Dutch",
    "th": "Thai",
    "id": "Indonesian",
    "fa": "Persian",
    "ro": "Romanian",
    "el": "Greek",
    "cs": "Czech",
    "sv": "Swedish",
    "hu": "Hungarian",
    "he": "Hebrew",
    "da": "Danish",
    "fi": "Finnish",
    "no": "Norwegian",
    "sk": "Slovak",
    "bg": "Bulgarian",
    "hr": "Croatian",
    "ms": "Malay",
    "sr": "Serbian",
    "lt": "Lithuanian",
    "lv": "Latvian",
    "et": "Estonian",
    "sl": "Slovenian",
    "ca": "Catalan",
    "tl": "Tagalog",
    "ur": "Urdu",
    "ta": "Tamil",
    "te": "Telugu",
    "mr": "Marathi",
    "kn": "Kannada",
    "ml": "Malayalam",
    "gu": "Gujarati",
}


# ============================================================================
# TIME ZONES
# ============================================================================

# Major time zones with UTC offsets
TIME_ZONES: Dict[str, str] = {
    "America/New_York": "UTC-5",
    "America/Chicago": "UTC-6",
    "America/Denver": "UTC-7",
    "America/Los_Angeles": "UTC-8",
    "America/Toronto": "UTC-5",
    "America/Mexico_City": "UTC-6",
    "America/Sao_Paulo": "UTC-3",
    "America/Buenos_Aires": "UTC-3",
    "Europe/London": "UTC+0",
    "Europe/Paris": "UTC+1",
    "Europe/Berlin": "UTC+1",
    "Europe/Rome": "UTC+1",
    "Europe/Madrid": "UTC+1",
    "Europe/Amsterdam": "UTC+1",
    "Europe/Zurich": "UTC+1",
    "Europe/Stockholm": "UTC+1",
    "Europe/Moscow": "UTC+3",
    "Asia/Dubai": "UTC+4",
    "Asia/Karachi": "UTC+5",
    "Asia/Kolkata": "UTC+5:30",
    "Asia/Bangkok": "UTC+7",
    "Asia/Singapore": "UTC+8",
    "Asia/Hong_Kong": "UTC+8",
    "Asia/Shanghai": "UTC+8",
    "Asia/Tokyo": "UTC+9",
    "Asia/Seoul": "UTC+9",
    "Australia/Sydney": "UTC+10",
    "Pacific/Auckland": "UTC+12",
}


# ============================================================================
# SUSPICIOUS KEYWORDS & PATTERNS
# ============================================================================

# Suspicious keywords for communication analysis
SUSPICIOUS_KEYWORDS: Dict[str, List[str]] = {
    "insider_trading": [
        "inside information", "material non-public", "mnpi", "confidential earnings",
        "merger talks", "acquisition target", "buyout", "takeover", "stock tip",
        "before announcement", "ahead of news", "pre-release", "embargo",
        "don't tell anyone", "keep quiet", "between us", "off the record",
        "buy before", "sell before", "load up", "dump shares", "unload position"
    ],
    
    "money_laundering": [
        "cash business", "structuring", "smurfing", "layering", "integration",
        "shell company", "nominee", "beneficial owner", "offshore account",
        "wire transfer", "bulk cash", "trade-based", "invoice manipulation",
        "over-invoice", "under-invoice", "round-tripping", "back-to-back",
        "clean money", "dirty money", "wash", "launder", "placement"
    ],
    
    "fraud": [
        "fake invoice", "phantom", "ghost employee", "kickback", "bribe",
        "under the table", "off the books", "slush fund", "secret account",
        "falsify", "forge", "fabricate", "manipulate records", "cook the books",
        "ponzi", "pyramid scheme", "advance fee", "419 scam", "phishing"
    ],
    
    "sanctions_evasion": [
        "sanctions", "embargo", "restricted party", "blocked person", "sdn list",
        "ofac", "designated national", "prohibited transaction", "unlicensed",
        "circumvent", "evade", "bypass", "front company", "cutout",
        "third country", "transshipment", "re-export", "dual-use"
    ],
    
    "tax_evasion": [
        "tax haven", "offshore", "undeclared", "unreported income", "hidden assets",
        "bearer shares", "nominee director", "trust structure", "foundation",
        "avoid tax", "evade tax", "minimize tax", "aggressive planning",
        "transfer pricing", "profit shifting", "base erosion"
    ],
    
    "market_manipulation": [
        "pump and dump", "wash trade", "spoofing", "layering", "front running",
        "painting the tape", "marking the close", "ramping", "cornering",
        "squeeze", "manipulate price", "artificial demand", "false market"
    ],
    
    "bribery_corruption": [
        "bribe", "kickback", "payoff", "grease payment", "facilitation payment",
        "commission", "consulting fee", "success fee", "finder's fee",
        "political contribution", "donation", "gift", "hospitality",
        "foreign official", "government contract", "procurement"
    ]
}

# Financial crime indicators
FINANCIAL_CRIME_INDICATORS: List[str] = [
    "unusual_transaction_pattern",
    "rapid_movement_of_funds",
    "round_dollar_amounts",
    "just_below_reporting_threshold",
    "multiple_transactions_same_day",
    "inconsistent_with_profile",
    "high_risk_jurisdiction",
    "shell_company_involvement",
    "complex_ownership_structure",
    "nominee_arrangements",
    "cash_intensive_business",
    "trade_anomalies",
    "invoice_discrepancies",
    "related_party_transactions",
    "circular_transactions",
    "back_to_back_transactions",
    "unexplained_wealth",
    "lifestyle_inconsistent_with_income",
    "pep_involvement",
    "sanctioned_entity_connection"
]


# ============================================================================
# INDUSTRY CLASSIFICATIONS
# ============================================================================

# High-risk industries for AML
HIGH_RISK_INDUSTRIES: List[str] = [
    "money_services_business",
    "cryptocurrency_exchange",
    "casino_gaming",
    "precious_metals_dealer",
    "art_dealer",
    "real_estate",
    "used_car_dealer",
    "pawn_shop",
    "check_cashing",
    "money_transmitter",
    "foreign_exchange",
    "trade_finance",
    "private_banking",
    "correspondent_banking",
    "shell_bank"
]

# Cash-intensive businesses
CASH_INTENSIVE_BUSINESSES: List[str] = [
    "restaurant",
    "bar_nightclub",
    "retail_store",
    "convenience_store",
    "gas_station",
    "car_wash",
    "laundromat",
    "vending_machine",
    "parking_lot",
    "taxi_service",
    "beauty_salon",
    "barbershop",
    "massage_parlor",
    "arcade",
    "amusement_park"
]


# ============================================================================
# TRANSACTION PATTERNS
# ============================================================================

# Structuring thresholds by country (in local currency)
STRUCTURING_THRESHOLDS: Dict[str, float] = {
    "US": 10000.0,  # USD
    "GB": 10000.0,  # GBP
    "EU": 10000.0,  # EUR
    "CA": 10000.0,  # CAD
    "AU": 10000.0,  # AUD
    "SG": 20000.0,  # SGD
    "HK": 120000.0,  # HKD
    "JP": 1000000.0,  # JPY
    "CH": 15000.0,  # CHF
}

# Round amount thresholds
ROUND_AMOUNTS: List[float] = [
    1000, 2000, 5000, 10000, 15000, 20000, 25000, 50000,
    75000, 100000, 150000, 200000, 250000, 500000, 1000000
]

# Suspicious transaction patterns
SUSPICIOUS_PATTERNS: List[str] = [
    "rapid_succession",
    "just_below_threshold",
    "round_amounts",
    "multiple_locations",
    "unusual_hours",
    "inconsistent_with_business",
    "no_apparent_purpose",
    "complex_routing",
    "multiple_intermediaries",
    "high_risk_countries",
    "shell_companies",
    "related_parties",
    "circular_flow",
    "back_to_back"
]


# ============================================================================
# STOCK EXCHANGES & MARKETS
# ============================================================================

STOCK_EXCHANGES: Dict[str, str] = {
    "NYSE": "New York Stock Exchange",
    "NASDAQ": "NASDAQ",
    "LSE": "London Stock Exchange",
    "TSE": "Tokyo Stock Exchange",
    "HKEX": "Hong Kong Stock Exchange",
    "SSE": "Shanghai Stock Exchange",
    "SZSE": "Shenzhen Stock Exchange",
    "Euronext": "Euronext",
    "TSX": "Toronto Stock Exchange",
    "ASX": "Australian Securities Exchange",
    "BSE": "Bombay Stock Exchange",
    "NSE": "National Stock Exchange of India",
    "KRX": "Korea Exchange",
    "SIX": "SIX Swiss Exchange",
    "BME": "Bolsa de Madrid",
    "B3": "B3 (Brazil)",
}


# ============================================================================
# REGULATORY LISTS
# ============================================================================

# Sanctions lists
SANCTIONS_LISTS: List[str] = [
    "OFAC_SDN",  # US Treasury OFAC Specially Designated Nationals
    "UN_SANCTIONS",  # United Nations Security Council
    "EU_SANCTIONS",  # European Union
    "UK_SANCTIONS",  # UK HM Treasury
    "DFAT_SANCTIONS",  # Australian DFAT
    "SECO_SANCTIONS",  # Swiss SECO
    "CONSOLIDATED_LIST",  # UN Consolidated List
]

# PEP categories
PEP_CATEGORIES: List[str] = [
    "head_of_state",
    "head_of_government",
    "government_minister",
    "senior_politician",
    "senior_government_official",
    "judicial_official",
    "military_official",
    "senior_executive_soe",  # State-Owned Enterprise
    "political_party_official",
    "member_of_parliament",
    "ambassador",
    "central_bank_official",
    "international_organization_official",
    "family_member_pep",
    "close_associate_pep"
]


# ============================================================================
# EXPORT ALL CONSTANTS
# ============================================================================

__all__ = [
    'COUNTRIES', 'TAX_HAVENS', 'HIGH_RISK_COUNTRIES', 'FINANCIAL_CENTERS',
    'CURRENCIES', 'RESERVE_CURRENCIES', 'CRYPTOCURRENCIES',
    'LANGUAGES', 'TIME_ZONES',
    'SUSPICIOUS_KEYWORDS', 'FINANCIAL_CRIME_INDICATORS',
    'HIGH_RISK_INDUSTRIES', 'CASH_INTENSIVE_BUSINESSES',
    'STRUCTURING_THRESHOLDS', 'ROUND_AMOUNTS', 'SUSPICIOUS_PATTERNS',
    'STOCK_EXCHANGES', 'SANCTIONS_LISTS', 'PEP_CATEGORIES'
]

