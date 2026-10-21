# Calculus (Django)

GST sales and purchase software with login, project areas, several companies, statements and editing.

## Run on your computer
    pip install -r requirements.txt
    python manage.py setup_calculus      # creates the 4 database files + demo logins (first time only)
    python manage.py runserver
Open http://127.0.0.1:8000 and log in as `admin` / `Admin@123` (change every demo password at once).
After updating the code, run `python manage.py setup_calculus` again: it upgrades the databases safely.

## Where things are stored (data/ folder)
| File                    | Holds                                                         |
|-------------------------|---------------------------------------------------------------|
| credentials.sqlite3     | usernames + hashed passwords (nothing else)                   |
| users.sqlite3           | companies, people (name, company, owner flag), allowed areas  |
| invoices.sqlite3        | sales invoices, invoice items, customers                      |
| purchases.sqlite3       | purchase bills, bill items, suppliers                         |
Back up the whole `data/` folder. `core/routers.py` decides which app uses which file.

## Code layout: one file per page
    config/        settings.py (database files, sessions), urls.py, wsgi.py
    core/          shared code: gst.py (tax maths), statement.py, permissions.py, routers.py, middleware.py
    accounts/      views/login.py, views/logout.py            -> credentials.sqlite3
    directory/     views/company_details.py, users_list.py, user_create.py, user_update.py,
                   companies_list.py, company_create.py, company_toggle.py   -> users.sqlite3
    sales/         views/invoice_list|create|detail|edit.py, customer_list|create|edit|delete.py  -> invoices.sqlite3
    purchases/     views/purchase_list|create|detail|edit.py, supplier_list|create|edit|delete.py -> purchases.sqlite3
    statements/    views/sales_statement.py, purchase_statement.py (+ _csv)   (opened from the home page)
    reports/       views/summary.py (sales vs purchases vs net GST)
    templates/ + <app>/templates/    one HTML file per page      static/    css and js

## How it works
- Everyone lands on the home page after login. The Sales statement and Purchase statement are opened from there.
- Edit an invoice or purchase from a statement: **Save** returns to the same statement (filters kept);
  **Save and print** opens the print window, then returns to the statement.
- Invoices and purchases are edited, never cancelled.

## Who can open what
- Sales area: create and edit invoices, manage customers. Purchase area: the same for purchases and suppliers.
- Statements: users with Sales (or Reports) see the sales statement; Purchase (or Reports) the purchase statement.
- Reports area: read-only statements, invoice/purchase pages and the net GST summary (no edit buttons).
- Admin area: company details and users. The owner (`admin`) can also add and disable companies.
- Every user belongs to one company and only ever sees that company's data.

## Putting it online
Set these environment variables: CALCULUS_SECRET_KEY (long random text), CALCULUS_ALLOWED_HOSTS (your domain),
CALCULUS_CSRF_ORIGINS (https://your-domain), CALCULUS_HTTPS=1 (once SSL is on).
cPanel "Setup Python App": startup file `passenger_wsgi.py`, entry point `application`.
No terminal? Also set CALCULUS_AUTO_SETUP=1 and the databases are created when the app starts.
