"""Calculus - multi-company GST invoicing with login and project-area access, built with Flask.

Every user belongs to ONE company. After login, everything the user sees or saves
(company GSTIN, customers, invoices, users) belongs to that company only.
Two checks protect each page:
  1. AUTHENTICATION - who are you, and is your company active?
  2. AUTHORISATION  - is this project area allowed for you? (user_areas table)
"""
import json
import os
import re
import secrets
import sqlite3
import time
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from functools import wraps

from flask import (Flask, abort, flash, g, redirect, render_template,
                   request, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("CALCULUS_SECRET_KEY", "change-this-secret-before-going-live"),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    PERMANENT_SESSION_LIFETIME=60 * 60 * 8,  # auto logout after 8 hours
)
os.makedirs(app.instance_path, exist_ok=True)
DB_PATH = os.path.join(app.instance_path, "calculus.db")

AREAS = {
    "sales":     {"title": "Sales & invoices", "desc": "Tax invoices, credit notes and customer dues."},
    "purchase":  {"title": "Purchases",        "desc": "Supplier bills, debit notes and input tax credit."},
    "returns":   {"title": "GST returns",      "desc": "GSTR-1, GSTR-3B and reconciliation with GSTR-2B."},
    "inventory": {"title": "Inventory",        "desc": "Items, HSN/SAC codes, stock and rates."},
    "reports":   {"title": "Reports",          "desc": "Tax summaries, ledgers and audit trails."},
    "admin":     {"title": "Admin & company",  "desc": "Company details, users and which areas each person can open."},
}

# (username, full name, password, areas, is_super). Created on first run only - change the passwords!
SEED_USERS = [
    ("admin",      "Admin",           "Admin@123",   list(AREAS), 1),
    ("accountant", "Asha Accountant", "Account@123", ["sales", "purchase", "returns", "reports"], 0),
    ("sales",      "Sam Sales",       "Sales@123",   ["sales", "inventory"], 0),
    ("auditor",    "Ira Auditor",     "Audit@123",   ["reports"], 0),
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

# GST rates offered in the invoice form. Trim to the rates you use and check current rates.
GST_RATES = [Decimal(r) for r in ("0", "0.25", "3", "5", "12", "18", "28", "40")]
DEFAULT_GST = "18"
GSTIN_RE = re.compile(r"^\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]$")
TWO = Decimal("0.01")
MAX_VALUE = Decimal("1000000000")
COMPANY_FIELDS = ("name", "gstin", "address", "state", "phone", "email", "bank")
CUSTOMER_FIELDS = ("name", "gstin", "address", "state", "phone", "email")

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
INVOICE_COLS = ("id, invoice_no, invoice_date, customer_name, customer_gstin, customer_address, "
                "place_of_supply, supply_type, taxable, cgst, sgst, igst, total, status, "
                "created_by, created_at, seller_json")

INVOICES_DDL = """CREATE TABLE {name} (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id       INTEGER NOT NULL DEFAULT 1 REFERENCES companies(id),
    invoice_no       TEXT NOT NULL,
    invoice_date     TEXT NOT NULL,
    customer_name    TEXT NOT NULL,
    customer_gstin   TEXT NOT NULL DEFAULT '',
    customer_address TEXT NOT NULL DEFAULT '',
    place_of_supply  TEXT NOT NULL,
    supply_type      TEXT NOT NULL,
    taxable          TEXT NOT NULL,
    cgst             TEXT NOT NULL,
    sgst             TEXT NOT NULL,
    igst             TEXT NOT NULL,
    total            TEXT NOT NULL,
    status           TEXT NOT NULL DEFAULT 'active',
    created_by       INTEGER REFERENCES users(id),
    created_at       TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    seller_json      TEXT NOT NULL DEFAULT '',
    UNIQUE (company_id, invoice_no)
)"""


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DB_PATH)
    db.execute("PRAGMA foreign_keys = OFF")  # off while creating/upgrading tables
    db.executescript("""
        CREATE TABLE IF NOT EXISTS companies (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            name    TEXT NOT NULL DEFAULT '',
            gstin   TEXT NOT NULL DEFAULT '',
            address TEXT NOT NULL DEFAULT '',
            state   TEXT NOT NULL DEFAULT '09',
            phone   TEXT NOT NULL DEFAULT '',
            email   TEXT NOT NULL DEFAULT '',
            bank    TEXT NOT NULL DEFAULT '',
            active  INTEGER NOT NULL DEFAULT 1
        );
        INSERT OR IGNORE INTO companies (id) VALUES (1);
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT NOT NULL UNIQUE,
            full_name     TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            active        INTEGER NOT NULL DEFAULT 1,
            company_id    INTEGER NOT NULL DEFAULT 1,
            is_super      INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS user_areas (
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            area    TEXT NOT NULL,
            PRIMARY KEY (user_id, area)
        );
        CREATE TABLE IF NOT EXISTS invoice_items (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id  INTEGER NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
            description TEXT NOT NULL,
            hsn         TEXT NOT NULL DEFAULT '',
            qty         TEXT NOT NULL,
            rate        TEXT NOT NULL,
            gst_rate    TEXT NOT NULL,
            taxable     TEXT NOT NULL,
            tax         TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS customers (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER NOT NULL DEFAULT 1,
            name       TEXT NOT NULL,
            gstin      TEXT NOT NULL DEFAULT '',
            address    TEXT NOT NULL DEFAULT '',
            state      TEXT NOT NULL,
            phone      TEXT NOT NULL DEFAULT '',
            email      TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
    """)
    db.execute(INVOICES_DDL.format(name="IF NOT EXISTS invoices"))

    # ---- upgrade databases made by earlier versions of Calculus ----
    def cols(table):
        return [r[1] for r in db.execute(f"PRAGMA table_info({table})")]

    if "company_id" not in cols("users"):
        db.execute("ALTER TABLE users ADD COLUMN company_id INTEGER NOT NULL DEFAULT 1")
    if "is_super" not in cols("users"):
        db.execute("ALTER TABLE users ADD COLUMN is_super INTEGER NOT NULL DEFAULT 0")
        db.execute("UPDATE users SET is_super=1 WHERE id=(SELECT MIN(user_id) FROM user_areas WHERE area='admin')")
    if "company_id" not in cols("customers"):
        db.execute("ALTER TABLE customers ADD COLUMN company_id INTEGER NOT NULL DEFAULT 1")
    if "seller_json" not in cols("invoices"):
        db.execute("ALTER TABLE invoices ADD COLUMN seller_json TEXT NOT NULL DEFAULT ''")
    if "company_id" not in cols("invoices"):
        # invoice numbers must be unique per company, so the table is rebuilt
        db.commit()
        db.executescript(
            INVOICES_DDL.format(name="invoices_new") + ";"
            f"INSERT INTO invoices_new ({INVOICE_COLS}) SELECT {INVOICE_COLS} FROM invoices;"
            "DROP TABLE invoices; ALTER TABLE invoices_new RENAME TO invoices;")
    if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='company'").fetchone():
        db.execute("""UPDATE companies SET
            name=(SELECT name FROM company WHERE id=1), gstin=(SELECT gstin FROM company WHERE id=1),
            address=(SELECT address FROM company WHERE id=1), state=(SELECT state FROM company WHERE id=1),
            phone=(SELECT phone FROM company WHERE id=1), email=(SELECT email FROM company WHERE id=1),
            bank=(SELECT bank FROM company WHERE id=1) WHERE id=1""")
        db.execute("DROP TABLE company")

    if db.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        for username, name, pwd, areas, is_super in SEED_USERS:
            cur = db.execute(
                "INSERT INTO users (username, full_name, password_hash, company_id, is_super) VALUES (?,?,?,1,?)",
                (username, name, generate_password_hash(pwd), is_super))
            db.executemany("INSERT INTO user_areas VALUES (?,?)", [(cur.lastrowid, a) for a in areas])
    db.commit()
    db.close()


def get_company(company_id):
    row = get_db().execute("SELECT * FROM companies WHERE id=?", (company_id,)).fetchone()
    return dict(row) if row else None


def company_ready(company):
    return bool(company["name"] and company["gstin"])


# ---------------------------------------------------------------------------
# Per-request: who is logged in (and for which company), CSRF protection
# ---------------------------------------------------------------------------
@app.before_request
def load_user():
    g.user = None
    uid = session.get("uid")
    if uid:
        db = get_db()
        row = db.execute(
            """SELECT u.* FROM users u JOIN companies c ON c.id = u.company_id
               WHERE u.id=? AND u.active=1 AND c.active=1""", (uid,)).fetchone()
        if row:
            areas = {r["area"] for r in db.execute(
                "SELECT area FROM user_areas WHERE user_id=?", (uid,))}
            g.user = {"id": row["id"], "username": row["username"], "full_name": row["full_name"],
                      "areas": areas, "company_id": row["company_id"],
                      "is_super": bool(row["is_super"]), "company": get_company(row["company_id"])}
        else:  # user or company was disabled -> kick out immediately
            session.clear()


@app.before_request
def csrf_protect():
    if request.method == "POST":
        token = session.get("csrf")
        if not token or token != request.form.get("csrf_token"):
            abort(400)


@app.context_processor
def inject_globals():
    if "csrf" not in session:
        session["csrf"] = secrets.token_hex(16)
    return {"csrf_token": session["csrf"], "AREAS": AREAS, "user": g.get("user")}


# ---------------------------------------------------------------------------
# Access-control decorators
# ---------------------------------------------------------------------------
def area_required(area):
    """Allow only logged-in users who have been granted this project area."""
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not g.user:
                return redirect(url_for("login"))
            if area not in g.user["areas"]:
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorator


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not g.user:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def super_required(view):
    """Admin area AND the owner flag - used for creating/disabling companies."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not g.user:
            return redirect(url_for("login"))
        if "admin" not in g.user["areas"] or not g.user["is_super"]:
            abort(403)
        return view(*args, **kwargs)
    return wrapped


# ---------------------------------------------------------------------------
# Login throttling (in memory): 5 wrong tries -> 5 minute lock
# ---------------------------------------------------------------------------
FAILED = {}
MAX_TRIES, LOCK_SECONDS = 5, 300


def is_locked(key):
    count, last = FAILED.get(key, (0, 0))
    if count >= MAX_TRIES:
        if time.time() - last < LOCK_SECONDS:
            return True
        FAILED.pop(key, None)
    return False


def record_failure(key):
    count, _ = FAILED.get(key, (0, 0))
    FAILED[key] = (count + 1, time.time())


# ---------------------------------------------------------------------------
# Login / logout / dashboard
# ---------------------------------------------------------------------------
def landing_url(areas):
    """Where to send a user right after login."""
    return url_for("sales") if "sales" in areas else url_for("dashboard")


@app.route("/")
def home():
    if g.user:
        return redirect(landing_url(g.user["areas"]))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if g.user:
        return redirect(landing_url(g.user["areas"]))
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        key = (username, request.remote_addr)
        if is_locked(key):
            flash("Too many failed attempts. Try again in 5 minutes.", "error")
            return render_template("login.html"), 429
        db = get_db()
        row = db.execute(
            """SELECT u.* FROM users u JOIN companies c ON c.id = u.company_id
               WHERE u.username=? AND u.active=1 AND c.active=1""", (username,)).fetchone()
        if row and check_password_hash(row["password_hash"], password):
            FAILED.pop(key, None)
            session.clear()              # new session on login
            session.permanent = True
            session["uid"] = row["id"]
            areas = {r["area"] for r in db.execute(
                "SELECT area FROM user_areas WHERE user_id=?", (row["id"],))}
            return redirect(landing_url(areas))
        record_failure(key)
        flash("Username or password is incorrect, or the account is disabled.", "error")
    return render_template("login.html")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")


# ---------------------------------------------------------------------------
# Other project areas (placeholders) - each route is locked with @area_required
# ---------------------------------------------------------------------------
def render_area(key):
    return render_template("area.html", key=key, area=AREAS[key])


@app.route("/purchase")
@area_required("purchase")
def purchase():
    return render_area("purchase")


@app.route("/returns")
@area_required("returns")
def returns():
    return render_area("returns")


@app.route("/inventory")
@area_required("inventory")
def inventory():
    return render_area("inventory")


@app.route("/reports")
@area_required("reports")
def reports():
    return render_area("reports")


# ===========================================================================
# SALES & INVOICES  (everything below is limited to the user's own company)
# ===========================================================================
def money(x):
    return Decimal(x).quantize(TWO, rounding=ROUND_HALF_UP)


def financial_year(d):
    start = d.year if d.month >= 4 else d.year - 1
    return f"{start}-{str(start + 1)[-2:]}"


def next_invoice_no(db, company_id, inv_date):
    """Numbers run separately for each company and financial year."""
    prefix = f"INV/{financial_year(inv_date)}/"
    last = db.execute(
        """SELECT MAX(CAST(SUBSTR(invoice_no, ?) AS INTEGER)) FROM invoices
           WHERE company_id=? AND invoice_no LIKE ?""",
        (len(prefix) + 1, company_id, prefix + "%")).fetchone()[0] or 0
    return f"{prefix}{last + 1:04d}"


@app.template_filter("inr")
def inr(value):
    v = money(Decimal(str(value)))
    sign = "-" if v < 0 else ""
    whole, frac = f"{abs(v):.2f}".split(".")
    if len(whole) > 3:
        head, tail, parts = whole[:-3], whole[-3:], []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        whole = ",".join(parts + [tail])
    return f"{sign}\u20b9{whole}.{frac}"


@app.template_filter("num")
def num(value):
    return format(Decimal(str(value)).normalize(), "f")


@app.template_filter("dmy")
def dmy(value):
    return date.fromisoformat(value).strftime("%d-%m-%Y")


def customer_choices(company_id):
    """This company's saved customers, shaped for the invoice form's auto-fill."""
    out = []
    for c in get_db().execute(
            "SELECT * FROM customers WHERE company_id=? ORDER BY name COLLATE NOCASE", (company_id,)):
        label = f'{c["name"]} ({c["gstin"]})' if c["gstin"] else f'{c["name"]} (unregistered)'
        out.append({"label": label, "name": c["name"], "gstin": c["gstin"],
                    "address": c["address"], "state": c["state"]})
    return out


def save_customer_if_new(db, company_id, d):
    if db.execute("SELECT 1 FROM customers WHERE company_id=? AND lower(name)=lower(?) AND gstin=?",
                  (company_id, d["name"], d["gstin"])).fetchone():
        return
    db.execute("INSERT INTO customers (company_id, name, gstin, address, state) VALUES (?,?,?,?,?)",
               (company_id, d["name"], d["gstin"], d["address"], d["pos"]))


def form_rows(form):
    """Item rows exactly as typed, so the form can be shown again after an error."""
    cols = [form.getlist(k) for k in ("desc", "hsn", "qty", "rate", "gst")]
    rows = [dict(desc=d, hsn=h, qty=q, rate=r, gst=g_) for d, h, q, r, g_ in zip(*cols)]
    return rows or [dict(desc="", hsn="", qty="", rate="", gst=DEFAULT_GST)]


def parse_invoice_form(form, company_state):
    """Validate the form and calculate GST on the server (never trust browser maths)."""
    errors = []
    name = form.get("customer_name", "").strip()
    gstin = form.get("customer_gstin", "").strip().upper()
    address = form.get("customer_address", "").strip()
    pos = form.get("place_of_supply", "")
    try:
        inv_date = date.fromisoformat(form.get("invoice_date", ""))
    except ValueError:
        inv_date = None
        errors.append("Enter a valid invoice date.")
    if not name:
        errors.append("Enter the customer name.")
    if pos not in STATES:
        errors.append("Choose the place of supply.")
    if gstin:
        if not GSTIN_RE.match(gstin):
            errors.append("Customer GSTIN is not in a valid format.")
        elif pos in STATES and gstin[:2] != pos:
            errors.append("Customer GSTIN state code does not match the place of supply.")

    items = []
    cols = [form.getlist(k) for k in ("desc", "hsn", "qty", "rate", "gst")]
    for desc, hsn, qty_s, rate_s, gst_s in zip(*cols):
        desc, hsn = desc.strip(), hsn.strip()
        if not (desc or qty_s.strip() or rate_s.strip()):
            continue  # ignore completely blank rows
        try:
            qty, rate, gst = Decimal(qty_s), Decimal(rate_s), Decimal(gst_s)
            ok = (desc and qty.is_finite() and rate.is_finite() and 0 < qty <= MAX_VALUE
                  and 0 <= rate <= MAX_VALUE and gst in GST_RATES)
        except InvalidOperation:
            ok = False
        if not ok:
            errors.append("Each item needs a description, a quantity above 0, a rate and a GST %.")
            break
        if hsn and not re.fullmatch(r"\d{4,8}", hsn):
            errors.append("HSN/SAC must be 4 to 8 digits.")
            break
        taxable = money(qty * rate)
        items.append({"description": desc, "hsn": hsn, "qty": qty, "rate": rate,
                      "gst_rate": gst, "taxable": taxable, "tax": money(taxable * gst / 100)})
    if not items and not errors:
        errors.append("Add at least one item.")
    if errors:
        return None, errors

    taxable_total = sum((i["taxable"] for i in items), Decimal("0"))
    tax_total = sum((i["tax"] for i in items), Decimal("0"))
    intra = pos == company_state          # same state -> CGST + SGST, else IGST
    cgst = money(tax_total / 2) if intra else Decimal("0")
    sgst = tax_total - cgst if intra else Decimal("0")
    igst = Decimal("0") if intra else tax_total
    return {
        "date": inv_date, "name": name, "gstin": gstin, "address": address, "pos": pos,
        "supply_type": "intra" if intra else "inter", "items": items,
        "taxable": taxable_total, "cgst": cgst, "sgst": sgst, "igst": igst,
        "total": taxable_total + tax_total,
    }, []


@app.route("/sales")
@area_required("sales")
def sales():
    cid = g.user["company_id"]
    q = request.args.get("q", "").strip()
    sql, params = "SELECT * FROM invoices WHERE company_id=?", [cid]
    if q:
        sql += " AND (invoice_no LIKE ? OR customer_name LIKE ? OR customer_gstin LIKE ?)"
        params += [f"%{q}%"] * 3
    sql += " ORDER BY invoice_date DESC, id DESC LIMIT 200"
    rows, sums = [], {"taxable": Decimal("0"), "gst": Decimal("0"), "total": Decimal("0")}
    for inv in get_db().execute(sql, params):
        d = dict(inv)
        d["gst"] = money(Decimal(inv["cgst"]) + Decimal(inv["sgst"]) + Decimal(inv["igst"]))
        rows.append(d)
        if inv["status"] == "active":
            sums["taxable"] += Decimal(inv["taxable"])
            sums["gst"] += d["gst"]
            sums["total"] += Decimal(inv["total"])
    return render_template("sales.html", invoices=rows, sums=sums, q=q,
                           company_ready=company_ready(g.user["company"]))


@app.route("/sales/new", methods=["GET", "POST"])
@area_required("sales")
def sales_new():
    company = g.user["company"]
    if not company_ready(company):
        flash("Add your company name and GSTIN before creating invoices.", "error")
        return redirect(url_for("sales"))
    blank = [dict(desc="", hsn="", qty="", rate="", gst=DEFAULT_GST)]
    rows = form_rows(request.form) if request.method == "POST" else blank
    if request.method == "POST":
        data, errors = parse_invoice_form(request.form, company["state"])
        if not errors:
            db = get_db()
            seller = json.dumps({k: company[k] for k in COMPANY_FIELDS})
            try:
                inv_no = next_invoice_no(db, company["id"], data["date"])
                cur = db.execute(
                    """INSERT INTO invoices (company_id, invoice_no, invoice_date, customer_name,
                       customer_gstin, customer_address, place_of_supply, supply_type, taxable, cgst,
                       sgst, igst, total, created_by, seller_json)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (company["id"], inv_no, data["date"].isoformat(), data["name"], data["gstin"],
                     data["address"], data["pos"], data["supply_type"], str(data["taxable"]),
                     str(data["cgst"]), str(data["sgst"]), str(data["igst"]), str(data["total"]),
                     g.user["id"], seller))
                db.executemany(
                    """INSERT INTO invoice_items (invoice_id, description, hsn, qty, rate, gst_rate,
                       taxable, tax) VALUES (?,?,?,?,?,?,?,?)""",
                    [(cur.lastrowid, i["description"], i["hsn"], str(i["qty"]), str(i["rate"]),
                      str(i["gst_rate"]), str(i["taxable"]), str(i["tax"])) for i in data["items"]])
                if request.form.get("save_customer"):
                    save_customer_if_new(db, company["id"], data)
                db.commit()
            except sqlite3.IntegrityError:
                db.rollback()
                errors = ["Another invoice was saved at the same moment. Click Save invoice again."]
            else:
                flash(f"Invoice {inv_no} saved.", "ok")
                return redirect(url_for("sales_view", inv_id=cur.lastrowid))
        for e in errors:
            flash(e, "error")
    return render_template("invoice_new.html", rows=rows, today=date.today().isoformat(),
                           states=STATES, gst_rates=GST_RATES, company=company,
                           customers=customer_choices(company["id"]), form=request.form)


@app.route("/sales/<int:inv_id>")
@area_required("sales")
def sales_view(inv_id):
    db = get_db()
    inv = db.execute(
        """SELECT i.*, u.full_name AS creator FROM invoices i
           LEFT JOIN users u ON u.id = i.created_by
           WHERE i.id=? AND i.company_id=?""", (inv_id, g.user["company_id"])).fetchone()
    if inv is None:
        abort(404)
    items = db.execute("SELECT * FROM invoice_items WHERE invoice_id=? ORDER BY id", (inv_id,)).fetchall()
    # show the company details as they were when the invoice was made
    seller = json.loads(inv["seller_json"]) if inv["seller_json"] else get_company(inv["company_id"])
    return render_template("invoice.html", inv=inv, items=items, company=seller,
                           state_name=STATES.get(inv["place_of_supply"], ""))


@app.route("/sales/<int:inv_id>/cancel", methods=["POST"])
@area_required("sales")
def sales_cancel(inv_id):
    db = get_db()
    db.execute("UPDATE invoices SET status='cancelled' WHERE id=? AND company_id=? AND status='active'",
               (inv_id, g.user["company_id"]))
    db.commit()
    flash("Invoice cancelled.", "ok")
    return redirect(url_for("sales_view", inv_id=inv_id))


# ---------------------------------------------------------------------------
# Customers (saved once per company, filled into invoices automatically)
# ---------------------------------------------------------------------------
def valid_phone(p):
    return len(p) <= 20 and all(ch in "0123456789+-() " for ch in p)


def parse_customer_form(form):
    v = {k: form.get(k, "").strip() for k in CUSTOMER_FIELDS}
    v["gstin"] = v["gstin"].upper()
    errors = []
    if not v["name"]:
        errors.append("Enter the customer name.")
    if v["state"] not in STATES:
        errors.append("Choose the customer's state.")
    if v["gstin"]:
        if not GSTIN_RE.match(v["gstin"]):
            errors.append("GSTIN is not in a valid format.")
        elif v["state"] in STATES and v["gstin"][:2] != v["state"]:
            errors.append("GSTIN state code does not match the selected state.")
    if v["phone"] and not valid_phone(v["phone"]):
        errors.append("Phone number can contain only digits, spaces, + - ( ).")
    if v["email"] and ("@" not in v["email"] or " " in v["email"]):
        errors.append("Enter a valid email address.")
    return v, errors


@app.route("/sales/customers")
@area_required("sales")
def customers():
    q = request.args.get("q", "").strip()
    sql, params = "SELECT * FROM customers WHERE company_id=?", [g.user["company_id"]]
    if q:
        sql += " AND (name LIKE ? OR gstin LIKE ? OR phone LIKE ?)"
        params += [f"%{q}%"] * 3
    sql += " ORDER BY name COLLATE NOCASE LIMIT 500"
    return render_template("customers.html", rows=get_db().execute(sql, params).fetchall(),
                           q=q, states=STATES)


@app.route("/sales/customers/new", methods=["GET", "POST"], defaults={"cid": None})
@app.route("/sales/customers/<int:cid>", methods=["GET", "POST"])
@area_required("sales")
def customer_edit(cid):
    db, company = get_db(), g.user["company"]
    existing = None
    if cid is not None:
        existing = db.execute("SELECT * FROM customers WHERE id=? AND company_id=?",
                              (cid, company["id"])).fetchone()
        if existing is None:
            abort(404)
    v = dict(existing) if existing else {
        "name": "", "gstin": "", "address": "", "state": company["state"], "phone": "", "email": ""}
    if request.method == "POST":
        v, errors = parse_customer_form(request.form)
        if not errors and db.execute(
                "SELECT 1 FROM customers WHERE company_id=? AND lower(name)=lower(?) AND gstin=? AND id IS NOT ?",
                (company["id"], v["name"], v["gstin"], cid)).fetchone():
            errors.append("A customer with this name and GSTIN already exists.")
        if errors:
            for e in errors:
                flash(e, "error")
        else:
            vals = [v[k] for k in CUSTOMER_FIELDS]
            if existing:
                db.execute("""UPDATE customers SET name=?, gstin=?, address=?, state=?, phone=?, email=?
                              WHERE id=? AND company_id=?""", vals + [cid, company["id"]])
            else:
                db.execute("""INSERT INTO customers (name, gstin, address, state, phone, email, company_id)
                              VALUES (?,?,?,?,?,?,?)""", vals + [company["id"]])
            db.commit()
            flash("Customer saved.", "ok")
            return redirect(url_for("customers"))
    return render_template("customer_form.html", v=v, cid=cid, states=STATES)


@app.route("/sales/customers/<int:cid>/delete", methods=["POST"])
@area_required("sales")
def customer_delete(cid):
    db = get_db()
    db.execute("DELETE FROM customers WHERE id=? AND company_id=?", (cid, g.user["company_id"]))
    db.commit()
    flash("Customer deleted. Existing invoices are not affected.", "ok")
    return redirect(url_for("customers"))


# ---------------------------------------------------------------------------
# Admin: company details, users, and (owner only) companies
# ---------------------------------------------------------------------------
@app.route("/admin/company", methods=["GET", "POST"])
@area_required("admin")
def admin_company():
    v = g.user["company"]
    if request.method == "POST":
        v = {k: request.form.get(k, "").strip() for k in COMPANY_FIELDS}
        v["gstin"] = v["gstin"].upper()
        errors = []
        if not v["name"]:
            errors.append("Enter your company name.")
        if not GSTIN_RE.match(v["gstin"]):
            errors.append("Enter a valid 15-character GSTIN.")
        if v["state"] not in STATES:
            errors.append("Choose your state.")
        elif GSTIN_RE.match(v["gstin"]) and v["gstin"][:2] != v["state"]:
            errors.append("GSTIN state code does not match the selected state.")
        if v["phone"] and not valid_phone(v["phone"]):
            errors.append("Phone number can contain only digits, spaces, + - ( ).")
        if v["email"] and ("@" not in v["email"] or " " in v["email"]):
            errors.append("Enter a valid email address.")
        if errors:
            for e in errors:
                flash(e, "error")
        else:
            db = get_db()
            db.execute("""UPDATE companies SET name=?, gstin=?, address=?, state=?, phone=?,
                          email=?, bank=? WHERE id=?""",
                       [v[k] for k in COMPANY_FIELDS] + [g.user["company_id"]])
            db.commit()
            flash("Company details saved. New invoices will use them.", "ok")
            return redirect(url_for("admin_company"))
    return render_template("company.html", v=v, states=STATES)


@app.route("/admin")
@area_required("admin")
def admin():
    db = get_db()
    rows = []
    for u in db.execute("SELECT * FROM users WHERE company_id=? ORDER BY username", (g.user["company_id"],)):
        areas = {r["area"] for r in db.execute(
            "SELECT area FROM user_areas WHERE user_id=?", (u["id"],))}
        rows.append({"id": u["id"], "username": u["username"], "full_name": u["full_name"],
                     "active": u["active"], "areas": areas, "is_super": u["is_super"]})
    return render_template("admin.html", rows=rows)


def chosen_areas():
    return {a for a in request.form.getlist("areas") if a in AREAS}


@app.route("/admin/users", methods=["POST"])
@area_required("admin")
def admin_create_user():
    username = request.form.get("username", "").strip().lower()
    full_name = request.form.get("full_name", "").strip()
    password = request.form.get("password", "")
    if not username or not full_name or len(password) < 8:
        flash("Enter a username, full name and a password of at least 8 characters.", "error")
        return redirect(url_for("admin"))
    db = get_db()
    try:
        cur = db.execute(
            "INSERT INTO users (username, full_name, password_hash, company_id) VALUES (?,?,?,?)",
            (username, full_name, generate_password_hash(password), g.user["company_id"]))
    except sqlite3.IntegrityError:
        flash(f"The username '{username}' is already taken. Usernames are unique across all companies.", "error")
        return redirect(url_for("admin"))
    db.executemany("INSERT INTO user_areas VALUES (?,?)", [(cur.lastrowid, a) for a in chosen_areas()])
    db.commit()
    flash(f"User '{username}' created.", "ok")
    return redirect(url_for("admin"))


@app.route("/admin/users/<int:uid>", methods=["POST"])
@area_required("admin")
def admin_update_user(uid):
    db = get_db()
    target = db.execute("SELECT id, is_super FROM users WHERE id=? AND company_id=?",
                        (uid, g.user["company_id"])).fetchone()
    if target is None:
        abort(404)                      # users of other companies cannot be touched
    if target["is_super"] and not g.user["is_super"]:
        abort(403)
    areas = chosen_areas()
    active = 1 if "active" in request.form else 0
    if uid == g.user["id"]:             # an admin cannot lock themselves out
        active = 1
        areas.add("admin")
    db.execute("UPDATE users SET active=? WHERE id=?", (active, uid))
    new_pwd = request.form.get("new_password", "")
    if new_pwd:
        if len(new_pwd) < 8:
            flash("New password must be at least 8 characters.", "error")
            return redirect(url_for("admin"))
        db.execute("UPDATE users SET password_hash=? WHERE id=?", (generate_password_hash(new_pwd), uid))
    db.execute("DELETE FROM user_areas WHERE user_id=?", (uid,))
    db.executemany("INSERT INTO user_areas VALUES (?,?)", [(uid, a) for a in areas])
    db.commit()
    flash("User updated.", "ok")
    return redirect(url_for("admin"))


@app.route("/admin/companies")
@super_required
def admin_companies():
    rows = get_db().execute(
        """SELECT c.*,
             (SELECT COUNT(*) FROM users u WHERE u.company_id = c.id) AS n_users,
             (SELECT COUNT(*) FROM invoices i WHERE i.company_id = c.id) AS n_invoices
           FROM companies c ORDER BY c.id""").fetchall()
    return render_template("companies.html", rows=rows, states=STATES, form=request.form)


@app.route("/admin/companies/new", methods=["POST"])
@super_required
def admin_company_create():
    f = {k: request.form.get(k, "").strip() for k in
         ("name", "gstin", "state", "address", "admin_username", "admin_name")}
    f["gstin"] = f["gstin"].upper()
    f["admin_username"] = f["admin_username"].lower()
    password = request.form.get("admin_password", "")
    errors = []
    if not f["name"]:
        errors.append("Enter the company name.")
    if not GSTIN_RE.match(f["gstin"]):
        errors.append("Enter a valid 15-character GSTIN.")
    elif f["state"] not in STATES or f["gstin"][:2] != f["state"]:
        errors.append("GSTIN state code does not match the selected state.")
    if not f["admin_username"] or not f["admin_name"] or len(password) < 8:
        errors.append("Enter the company admin's username, name and a password of at least 8 characters.")
    if not errors:
        db = get_db()
        try:
            cur = db.execute("INSERT INTO companies (name, gstin, address, state) VALUES (?,?,?,?)",
                             (f["name"], f["gstin"], f["address"], f["state"]))
            ucur = db.execute(
                "INSERT INTO users (username, full_name, password_hash, company_id) VALUES (?,?,?,?)",
                (f["admin_username"], f["admin_name"], generate_password_hash(password), cur.lastrowid))
            db.executemany("INSERT INTO user_areas VALUES (?,?)", [(ucur.lastrowid, a) for a in AREAS])
            db.commit()
            flash(f"Company '{f['name']}' created. Its admin can now log in as '{f['admin_username']}'.", "ok")
            return redirect(url_for("admin_companies"))
        except sqlite3.IntegrityError:
            db.rollback()
            errors.append(f"The username '{f['admin_username']}' is already taken.")
    for e in errors:
        flash(e, "error")
    return redirect(url_for("admin_companies"))


@app.route("/admin/companies/<int:cid>/toggle", methods=["POST"])
@super_required
def admin_company_toggle(cid):
    if cid == g.user["company_id"]:
        flash("You cannot deactivate your own company.", "error")
    else:
        db = get_db()
        db.execute("UPDATE companies SET active = 1 - active WHERE id=?", (cid,))
        db.commit()
        flash("Company status changed. Its users are logged out or allowed back in immediately.", "ok")
    return redirect(url_for("admin_companies"))


# ---------------------------------------------------------------------------
@app.errorhandler(400)
@app.errorhandler(403)
@app.errorhandler(404)
def error_page(err):
    msgs = {
        400: ("Request could not be verified", "Reload the page and try again."),
        403: ("You don't have access to this area", "Ask your administrator to add it to your account."),
        404: ("Page not found", "Check the address or go back to your dashboard."),
    }
    title, text = msgs[err.code]
    return render_template("error.html", code=err.code, title=title, text=text), err.code


init_db()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
