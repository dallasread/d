"""Domain models for domain registration information."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class RegistrySource(Enum):
    """Source of registry information."""

    RDAP = "rdap"
    WHOIS = "whois"


class DomainStatus(Enum):
    """Domain registration status."""

    ACTIVE = "active"
    LOCKED = "locked"
    PENDING_DELETE = "pending_delete"
    EXPIRED = "expired"
    AVAILABLE = "available"
    UNKNOWN = "unknown"


@dataclass
class Contact:
    """Contact information."""

    name: Optional[str] = None
    organization: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None


@dataclass
class Nameserver:
    """Nameserver information."""

    hostname: str
    ip_addresses: list[str]


@dataclass
class DomainRegistration:
    """Domain registration information."""

    domain: str
    registrar: Optional[str]
    registry_source: RegistrySource
    status: list[str]
    nameservers: list[Nameserver]
    registrant: Optional[Contact]
    admin_contact: Optional[Contact]
    tech_contact: Optional[Contact]
    created_date: Optional[datetime]
    updated_date: Optional[datetime]
    expires_date: Optional[datetime]
    dnssec: bool
    timestamp: datetime
    raw_data: Optional[dict] = None

    @property
    def days_until_expiry(self) -> Optional[int]:
        """Calculate days until expiry."""
        if not self.expires_date:
            return None
        delta = self.expires_date - datetime.utcnow()
        return delta.days

    @property
    def is_expired(self) -> bool:
        """Check if the domain is expired."""
        if not self.expires_date:
            return False
        return datetime.utcnow() > self.expires_date

    @property
    def is_expiring_soon(self, days: int = 30) -> bool:
        """Check if the domain is expiring soon."""
        days_left = self.days_until_expiry
        if days_left is None:
            return False
        return 0 < days_left <= days
