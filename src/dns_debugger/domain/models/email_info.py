"""Domain models for email configuration."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class DMARCPolicy(Enum):
    """DMARC policy actions."""

    NONE = "none"
    QUARANTINE = "quarantine"
    REJECT = "reject"
    UNKNOWN = "unknown"


class SPFResult(Enum):
    """SPF validation result."""

    PASS = "pass"
    FAIL = "fail"
    SOFTFAIL = "softfail"
    NEUTRAL = "neutral"
    NONE = "none"
    TEMPERROR = "temperror"
    PERMERROR = "permerror"


@dataclass
class SPFRecord:
    """Represents an SPF record."""

    domain: str
    record: str
    mechanisms: list[str]
    all_mechanism: Optional[str] = None  # ~all, -all, ?all, +all
    includes: list[str] = None
    ip4_addresses: list[str] = None
    ip6_addresses: list[str] = None
    exists: list[str] = None

    def __post_init__(self) -> None:
        """Initialize mutable defaults."""
        if self.includes is None:
            self.includes = []
        if self.ip4_addresses is None:
            self.ip4_addresses = []
        if self.ip6_addresses is None:
            self.ip6_addresses = []
        if self.exists is None:
            self.exists = []

    @property
    def is_strict(self) -> bool:
        """Check if SPF uses strict policy (-all)."""
        return self.all_mechanism == "-all"

    @property
    def is_softfail(self) -> bool:
        """Check if SPF uses softfail (~all)."""
        return self.all_mechanism == "~all"


@dataclass
class DKIMRecord:
    """Represents a DKIM record."""

    selector: str
    domain: str
    public_key: Optional[str] = None
    key_type: str = "rsa"
    exists: bool = False
    raw_record: Optional[str] = None


@dataclass
class DMARCRecord:
    """Represents a DMARC record."""

    domain: str
    policy: DMARCPolicy
    subdomain_policy: Optional[DMARCPolicy] = None
    percentage: int = 100
    rua_addresses: list[str] = None  # Aggregate reports
    ruf_addresses: list[str] = None  # Forensic reports
    alignment_spf: str = "r"  # r=relaxed, s=strict
    alignment_dkim: str = "r"
    raw_record: Optional[str] = None

    def __post_init__(self) -> None:
        """Initialize mutable defaults."""
        if self.rua_addresses is None:
            self.rua_addresses = []
        if self.ruf_addresses is None:
            self.ruf_addresses = []

    @property
    def is_enforcing(self) -> bool:
        """Check if DMARC policy is enforcing (quarantine or reject)."""
        return self.policy in [DMARCPolicy.QUARANTINE, DMARCPolicy.REJECT]

    @property
    def has_reporting(self) -> bool:
        """Check if DMARC has reporting configured."""
        return len(self.rua_addresses) > 0 or len(self.ruf_addresses) > 0


@dataclass
class MXRecord:
    """Represents an MX record."""

    priority: int
    hostname: str
    ip_addresses: list[str] = None

    def __post_init__(self) -> None:
        """Initialize mutable defaults."""
        if self.ip_addresses is None:
            self.ip_addresses = []


@dataclass
class EmailConfiguration:
    """Complete email configuration for a domain."""

    domain: str
    mx_records: list[MXRecord]
    spf_record: Optional[SPFRecord] = None
    dmarc_record: Optional[DMARCRecord] = None
    dkim_selectors_checked: list[str] = None
    dkim_records: list[DKIMRecord] = None
    timestamp: datetime = None

    def __post_init__(self) -> None:
        """Initialize mutable defaults."""
        if self.dkim_selectors_checked is None:
            self.dkim_selectors_checked = []
        if self.dkim_records is None:
            self.dkim_records = []
        if self.timestamp is None:
            self.timestamp = datetime.now()

    @property
    def has_mx(self) -> bool:
        """Check if domain has MX records."""
        return len(self.mx_records) > 0

    @property
    def has_spf(self) -> bool:
        """Check if domain has SPF record."""
        return self.spf_record is not None

    @property
    def has_dmarc(self) -> bool:
        """Check if domain has DMARC record."""
        return self.dmarc_record is not None

    @property
    def has_dkim(self) -> bool:
        """Check if any DKIM records were found."""
        return any(dkim.exists for dkim in self.dkim_records)

    @property
    def email_provider(self) -> Optional[str]:
        """Attempt to identify email provider from MX records."""
        if not self.mx_records:
            return None

        primary_mx = self.mx_records[0].hostname.lower()

        if "google" in primary_mx or "googlemail" in primary_mx:
            return "Google Workspace"
        elif "outlook" in primary_mx or "microsoft" in primary_mx:
            return "Microsoft 365"
        elif "mail.protection.outlook" in primary_mx:
            return "Microsoft 365"
        elif "amazonses" in primary_mx:
            return "Amazon SES"
        elif "sendgrid" in primary_mx:
            return "SendGrid"
        elif "mailgun" in primary_mx:
            return "Mailgun"
        elif "proofpoint" in primary_mx:
            return "Proofpoint"
        elif "mimecast" in primary_mx:
            return "Mimecast"
        elif "postmark" in primary_mx:
            return "Postmark"

        return "Unknown / Self-hosted"

    @property
    def security_score(self) -> int:
        """Calculate a basic email security score out of 100."""
        score = 0

        # MX records (20 points)
        if self.has_mx:
            score += 20

        # SPF (25 points)
        if self.has_spf:
            score += 15
            if self.spf_record.is_strict:
                score += 10  # Bonus for -all

        # DKIM (25 points)
        if self.has_dkim:
            score += 25

        # DMARC (30 points)
        if self.has_dmarc:
            score += 15
            if self.dmarc_record.is_enforcing:
                score += 10  # Bonus for quarantine/reject
            if self.dmarc_record.has_reporting:
                score += 5  # Bonus for reporting

        return score
