# Calculus

Login-protected web app with per-user project areas (modules), built with Flask.

## Run
    pip install -r requirements.txt
    set CALCULUS_SECRET_KEY=any-long-random-string     (Windows)
    export CALCULUS_SECRET_KEY=any-long-random-string  (Linux/Mac)
    python app.py
Open http://127.0.0.1:5000

## First-run demo users (change these immediately in User management)
| username   | password     | project areas                          |
|------------|--------------|----------------------------------------|
| admin      | Admin@123    | all, including User management         |
| accountant | Account@123  | Sales, Purchases, GST returns, Reports |
| sales      | Sales@123    | Sales, Inventory                       |
| auditor    | Audit@123    | Reports                                |

To reset everything, delete instance/calculus.db and start again.

## Invoices (Sales area)
- Edit `COMPANY` near the top of the Sales section in `app.py` with your company name, GSTIN, address and state code.
- Same state as your business -> CGST + SGST. Other state -> IGST.
- Invoice numbers run per financial year: INV/2026-27/0001, 0002, ...
- Invoices are cancelled, not deleted, so the number sequence stays intact.

## Company details and customers
- Admin > Company details: name, GSTIN, state, address, phone, email, bank details. Required before the first invoice.
- Sales > Customers: save customers once; the invoice form fills name, GSTIN, address and state automatically.
- Each invoice keeps a copy of the company and customer details it was made with, so later edits never change old invoices.

## Multiple companies
- Every user belongs to one company. After login they see only that company's GSTIN, customers, invoices and users.
- Invoice numbers run separately per company and financial year.
- The `admin` user is the owner: Admin > All companies lets it add a company with its first login, and disable or enable companies.
- Usernames are unique across all companies, so use something like `acme.accounts`.
