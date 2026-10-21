import re
from decimal import Decimal

AREAS = {
    "sales":     {"title": "Sales & invoices", "desc": "Create and edit tax invoices and manage customers."},
    "purchase":  {"title": "Purchases",        "desc": "Record and edit supplier bills and manage suppliers."},
    "returns":   {"title": "GST returns",      "desc": "GSTR-1, GSTR-3B and reconciliation with GSTR-2B."},
    "inventory": {"title": "Inventory",        "desc": "Items, HSN/SAC codes, stock and rates."},
    "reports":   {"title": "Reports",          "desc": "Sales, purchases and net GST summary. Read-only."},
    "admin":     {"title": "Admin & company",  "desc": "Company details, users and which areas each person can open."},
}

# First-run demo logins: (username, full name, password, areas, is_owner). Change the passwords!
SEED_USERS = [
    ("admin",      "Admin",           "Admin@123",   list(AREAS), True),
    ("accountant", "Asha Accountant", "Account@123", ["sales", "purchase", "returns", "reports"], False),
    ("sales",      "Sam Sales",       "Sales@123",   ["sales", "inventory"], False),
    ("auditor",    "Ira Auditor",     "Audit@123",   ["reports"], False),
]

STATES = {
    "01": "Jammu & Kashmir", "02": "Himachal Pradesh", "03": "Punjab", "04": "Chandigarh",
    "05": "Uttarakhand", "06": "Haryana", "07": "Delhi", "08": "Rajasthan",
    "09": "Uttar Pradesh", "10": "Bihar", "11": "Sikkim", "12": "Arunachal Pradesh",
    "13": "Nagaland", "14": "Manipur", "15": "Mizoram", "16": "Tripura",
    "17": "Meghalaya", "18": "Assam", "19": "West Bengal", "20": "Jharkhand",
    "21": "Odisha", "22": "Chhattisgarh", "23": "Madhya Pradesh", "24": "Gujarat",
    "26": "Dadra & Nagar Haveli and Daman & Diu", "27": "Maharashtra", "29": "Karnataka",
    "30": "Goa", "31": "Lakshadweep", "32": "Kerala", "33": "Tamil Nadu",
    "34": "Puducherry", "35": "Andaman & Nicobar Islands", "36": "Telangana",
    "37": "Andhra Pradesh", "38": "Ladakh",
}

# GST rates offered in the forms. Trim to the rates you use and check the current rates.
GST_RATES = [Decimal(r) for r in ("0", "0.25", "3", "5", "12", "18", "28", "40")]
DEFAULT_GST = "18"

GSTIN_RE = re.compile(r"^\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]$")
COMPANY_FIELDS = ("name", "gstin", "address", "state", "phone", "email", "bank")
