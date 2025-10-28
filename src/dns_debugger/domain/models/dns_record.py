"""Domain models for DNS records."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class RecordType(Enum):
    """DNS record types."""

    A = "A"
    AAAA = "AAAA"
    CNAME = "CNAME"
    MX = "MX"
    NS = "NS"
    TXT = "TXT"
    SOA = "SOA"
    PTR = "PTR"
    SRV = "SRV"
    CAA = "CAA"
    DNSKEY = "DNSKEY"
    DS = "DS"
    NSEC = "NSEC"
    NSEC3 = "NSEC3"
    RRSIG = "RRSIG"


@dataclass
class DNSRecord:
    """Represents a single DNS record."""

    name: str
    record_type: RecordType
    value: str
    ttl: int
    record_class: str = "IN"

    def __str__(self) -> str:
        """String representation of the DNS record."""
        return f"{self.name} {self.ttl} {self.record_class} {self.record_type.value} {self.value}"


@dataclass
class DNSQuery:
    """Represents a DNS query request."""

    domain: str
    record_type: RecordType
    resolver: Optional[str] = None
    dnssec: bool = False

    def __post_init__(self) -> None:
        """Validate the query parameters."""
        if not self.domain:
            raise ValueError("Domain cannot be empty")


@dataclass
class DNSResponse:
    """Represents a DNS query response."""

    query: DNSQuery
    records: list[DNSRecord]
    query_time_ms: float
    resolver_used: str
    timestamp: datetime
    has_dnssec: bool = False
    error: Optional[str] = None
    raw_data: Optional[dict] = None

    @property
    def is_success(self) -> bool:
        """Check if the query was successful."""
        return self.error is None

    @property
    def record_count(self) -> int:
        """Get the number of records returned."""
        return len(self.records)

    def get_records_by_type(self, record_type: RecordType) -> list[DNSRecord]:
        """Filter records by type."""
        return [r for r in self.records if r.record_type == record_type]
