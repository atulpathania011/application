from dataclasses import dataclass

from directory.models import Company


@dataclass
class CurrentUser:
    id: int            # directory.Profile id
    username: str
    full_name: str
    company: Company
    is_owner: bool
    areas: frozenset

    @property
    def company_id(self):
        return self.company.id
