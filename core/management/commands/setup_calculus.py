from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand

from accounts.models import Credential
from core.constants import SEED_USERS
from directory.models import Company
from directory.services import create_user


class Command(BaseCommand):
    help = "Create/upgrade all four database files and add the demo logins on the first run."

    def handle(self, *args, **options):
        for alias in settings.DATABASES:
            call_command("migrate", database=alias, interactive=False, verbosity=0)
        if not Credential.objects.exists() and not Company.objects.exists():
            company = Company.objects.create()
            for username, name, password, areas, is_owner in SEED_USERS:
                create_user(company, username, name, password, set(areas), is_owner)
            self.stdout.write(self.style.SUCCESS(
                "Demo logins created: admin / Admin@123 (and accountant, sales, auditor). Change these passwords!"))
        self.stdout.write(self.style.SUCCESS("Databases ready in " + str(settings.DATA_DIR)))
