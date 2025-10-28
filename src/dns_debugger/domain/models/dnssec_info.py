"""Domain models for DNSSEC information."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class DNSSECStatus(Enum):
    """DNSSEC validation status."""

    SECURE = "secure"
    INSECURE = "insecure"
    BOGUS = "bogus"
    INDETERMINATE = "indeterminate"


class DNSSECAlgorithm(Enum):
    """DNSSEC signature algorithms."""

    RSAMD5 = "RSAMD5 (1)"
    DH = "DH (2)"
    DSA = "DSA (3)"
    RSASHA1 = "RSASHA1 (5)"
    DSA_NSEC3_SHA1 = "DSA-NSEC3-SHA1 (6)"
    RSASHA1_NSEC3_SHA1 = "RSASHA1-NSEC3-SHA1 (7)"
    RSASHA256 = "RSASHA256 (8)"
    RSASHA512 = "RSASHA512 (10)"
    ECC_GOST = "ECC-GOST (12)"
    ECDSAP256SHA256 = "ECDSAP256SHA256 (13)"
    ECDSAP384SHA384 = "ECDSAP384SHA384 (14)"
    ED25519 = "ED25519 (15)"
    ED448 = "ED448 (16)"
    UNKNOWN = "Unknown"


class DigestType(Enum):
    """DS record digest types."""

    SHA1 = "SHA-1 (1)"
    SHA256 = "SHA-256 (2)"
    GOST = "GOST R 34.11-94 (3)"
    SHA384 = "SHA-384 (4)"
    UNKNOWN = "Unknown"


@dataclass
class DNSKEYRecord:
    """Represents a DNSKEY record."""

    flags: int  # 256=ZSK, 257=KSK
    protocol: int  # Always 3
    algorithm: DNSSECAlgorithm
    key_tag: int
    public_key: str
    ttl: int

    @property
    def is_key_signing_key(self) -> bool:
        """Check if this is a Key Signing Key (KSK)."""
        return self.flags == 257

    @property
    def is_zone_signing_key(self) -> bool:
        """Check if this is a Zone Signing Key (ZSK)."""
        return self.flags == 256


@dataclass
class DSRecord:
    """Represents a DS (Delegation Signer) record."""

    key_tag: int
    algorithm: DNSSECAlgorithm
    digest_type: DigestType
    digest: str
    ttl: int


@dataclass
class RRSIGRecord:
    """Represents a RRSIG (Resource Record Signature) record."""

    type_covered: str  # e.g., "A", "AAAA"
    algorithm: DNSSECAlgorithm
    labels: int
    original_ttl: int
    signature_expiration: datetime
    signature_inception: datetime
    key_tag: int
    signer_name: str
    signature: str
    ttl: int

    @property
    def is_expired(self) -> bool:
        """Check if the signature has expired."""
        return datetime.now() > self.signature_expiration

    @property
    def is_not_yet_valid(self) -> bool:
        """Check if the signature is not yet valid."""
        return datetime.now() < self.signature_inception

    @property
    def days_until_expiry(self) -> int:
        """Calculate days until signature expires."""
        if self.is_expired:
            return 0
        delta = self.signature_expiration - datetime.now()
        return delta.days


@dataclass
class DNSSECChain:
    """Represents the DNSSEC chain of trust."""

    domain: str
    has_ds_record: bool
    has_dnskey_record: bool
    has_rrsig_record: bool
    ds_records: list[DSRecord]
    dnskey_records: list[DNSKEYRecord]
    rrsig_records: list[RRSIGRecord]

    @property
    def is_signed(self) -> bool:
        """Check if the domain is DNSSEC signed."""
        return self.has_dnskey_record and self.has_rrsig_record

    @property
    def has_chain_of_trust(self) -> bool:
        """Check if there is a complete chain of trust to parent."""
        return self.has_ds_record and self.is_signed

    @property
    def ksk_count(self) -> int:
        """Count Key Signing Keys."""
        return sum(1 for key in self.dnskey_records if key.is_key_signing_key)

    @property
    def zsk_count(self) -> int:
        """Count Zone Signing Keys."""
        return sum(1 for key in self.dnskey_records if key.is_zone_signing_key)


@dataclass
class DNSSECValidation:
    """Represents DNSSEC validation results."""

    domain: str
    status: DNSSECStatus
    validation_time_ms: float
    timestamp: datetime
    chain: Optional[DNSSECChain] = None
    error_message: Optional[str] = None
    warnings: list[str] = None
    raw_data: Optional[dict] = None

    def __post_init__(self) -> None:
        """Initialize mutable defaults."""
        if self.warnings is None:
            self.warnings = []

    @property
    def is_secure(self) -> bool:
        """Check if DNSSEC validation passed."""
        return self.status == DNSSECStatus.SECURE

    @property
    def is_bogus(self) -> bool:
        """Check if DNSSEC validation failed (bogus)."""
        return self.status == DNSSECStatus.BOGUS

    @property
    def is_insecure(self) -> bool:
        """Check if the domain is not signed."""
        return self.status == DNSSECStatus.INSECURE

    @property
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0
