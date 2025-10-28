"""Domain models for SSL/TLS certificates."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class CertificateStatus(Enum):
    """Certificate validation status."""

    VALID = "valid"
    EXPIRED = "expired"
    NOT_YET_VALID = "not_yet_valid"
    REVOKED = "revoked"
    SELF_SIGNED = "self_signed"
    INVALID_CHAIN = "invalid_chain"


class TLSVersion(Enum):
    """TLS/SSL protocol versions."""

    SSL_3_0 = "SSLv3"
    TLS_1_0 = "TLSv1.0"
    TLS_1_1 = "TLSv1.1"
    TLS_1_2 = "TLSv1.2"
    TLS_1_3 = "TLSv1.3"


@dataclass
class CertificateSubject:
    """Certificate subject information."""

    common_name: str
    organization: Optional[str] = None
    organizational_unit: Optional[str] = None
    locality: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None

    def __str__(self) -> str:
        """String representation of the subject."""
        parts = [f"CN={self.common_name}"]
        if self.organization:
            parts.append(f"O={self.organization}")
        if self.organizational_unit:
            parts.append(f"OU={self.organizational_unit}")
        if self.locality:
            parts.append(f"L={self.locality}")
        if self.state:
            parts.append(f"ST={self.state}")
        if self.country:
            parts.append(f"C={self.country}")
        return ", ".join(parts)


@dataclass
class Certificate:
    """Represents an SSL/TLS certificate."""

    subject: CertificateSubject
    issuer: CertificateSubject
    serial_number: str
    version: int
    not_before: datetime
    not_after: datetime
    signature_algorithm: str
    public_key_algorithm: str
    public_key_size: int
    subject_alternative_names: list[str]
    fingerprint_sha256: str

    @property
    def is_expired(self) -> bool:
        """Check if the certificate is expired."""
        return datetime.utcnow() > self.not_after

    @property
    def is_valid_now(self) -> bool:
        """Check if the certificate is currently valid."""
        now = datetime.utcnow()
        return self.not_before <= now <= self.not_after

    @property
    def days_until_expiry(self) -> int:
        """Calculate days until expiry (negative if expired)."""
        delta = self.not_after - datetime.utcnow()
        return delta.days

    @property
    def is_self_signed(self) -> bool:
        """Check if the certificate is self-signed."""
        return str(self.subject) == str(self.issuer)


@dataclass
class CertificateChain:
    """Represents a certificate chain."""

    certificates: list[Certificate]
    is_valid: bool
    validation_errors: list[str]

    @property
    def leaf_certificate(self) -> Optional[Certificate]:
        """Get the leaf (end-entity) certificate."""
        return self.certificates[0] if self.certificates else None

    @property
    def root_certificate(self) -> Optional[Certificate]:
        """Get the root certificate."""
        return self.certificates[-1] if self.certificates else None

    @property
    def chain_length(self) -> int:
        """Get the length of the certificate chain."""
        return len(self.certificates)


@dataclass
class TLSInfo:
    """TLS connection information."""

    host: str
    port: int
    certificate_chain: CertificateChain
    supported_versions: list[TLSVersion]
    cipher_suites: list[str]
    has_ocsp_stapling: bool
    supports_sni: bool
    connection_time_ms: float
    timestamp: datetime
