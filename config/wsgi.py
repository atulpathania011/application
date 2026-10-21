import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
application = get_wsgi_application()

# For hosts without a terminal: set CALCULUS_AUTO_SETUP=1 and the databases are
# created/upgraded automatically when the app starts (safe to run every time).
if os.environ.get("CALCULUS_AUTO_SETUP") == "1":
    from django.core.management import call_command
    call_command("setup_calculus", verbosity=0)
