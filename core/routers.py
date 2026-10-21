"""Send each app's tables to its own database file."""
APP_DB = {
    "accounts": "credentials",   # data/credentials.sqlite3 - usernames and password hashes
    "directory": "default",      # data/users.sqlite3       - companies, profiles, access areas
    "sales": "invoices",         # data/invoices.sqlite3    - invoices and customers
    "purchases": "purchases",    # data/purchases.sqlite3   - purchase bills and suppliers
}


class AppRouter:
    def db_for_read(self, model, **hints):
        return APP_DB.get(model._meta.app_label)

    db_for_write = db_for_read

    def allow_relation(self, obj1, obj2, **hints):
        a, b = APP_DB.get(obj1._meta.app_label), APP_DB.get(obj2._meta.app_label)
        return (a == b) if (a and b) else None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        target = APP_DB.get(app_label)
        return None if target is None else db == target
