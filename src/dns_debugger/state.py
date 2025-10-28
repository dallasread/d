"""Global state manager for DNS Debugger application."""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime

from dns_debugger.domain.models.dns_record import DNSResponse
from dns_debugger.domain.models.dnssec_info import DNSSECValidation
from dns_debugger.domain.models.certificate import TLSInfo
from dns_debugger.domain.models.http_info import HTTPResponse
from dns_debugger.domain.models.domain_info import DomainRegistration
from dns_debugger.domain.models.email_info import EmailConfiguration
from dns_debugger.facades.dashboard_facade import (
    HTTPHealthData,
    CertHealthData,
    DNSHealthData,
    RegistryHealthData,
    DNSSECHealthData,
    EmailHealthData,
)


@dataclass
class AppState:
    """Global application state storing all fetched data."""

    domain: str

    # DNS data
    dns_responses: dict = None  # RecordType -> DNSResponse
    dns_last_updated: Optional[datetime] = None

    # DNSSEC data
    dnssec_validation: Optional[DNSSECValidation] = None
    dnssec_last_updated: Optional[datetime] = None

    # Certificate data
    tls_info: Optional[TLSInfo] = None
    tls_last_updated: Optional[datetime] = None

    # HTTP data
    http_response: Optional[HTTPResponse] = None
    http_last_updated: Optional[datetime] = None

    # Registration data
    registration: Optional[DomainRegistration] = None
    registration_last_updated: Optional[datetime] = None

    # Email data
    email_config: Optional[EmailConfiguration] = None
    email_last_updated: Optional[datetime] = None

    # Dashboard health data (simplified for display)
    http_health: Optional[HTTPHealthData] = None
    cert_health: Optional[CertHealthData] = None
    dns_health: Optional[DNSHealthData] = None
    registry_health: Optional[RegistryHealthData] = None
    dnssec_health: Optional[DNSSECHealthData] = None
    email_health: Optional[EmailHealthData] = None

    def __post_init__(self):
        """Initialize mutable defaults."""
        if self.dns_responses is None:
            self.dns_responses = {}


class StateManager:
    """Singleton state manager for the application."""

    _instance: Optional["StateManager"] = None
    _state: Optional[AppState] = None

    def __new__(cls):
        """Ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def initialize(self, domain: str) -> None:
        """Initialize state for a domain."""
        self._state = AppState(domain=domain)

    @property
    def state(self) -> AppState:
        """Get the current state."""
        if self._state is None:
            raise RuntimeError("State not initialized. Call initialize() first.")
        return self._state

    def update_dns(self, responses: dict) -> None:
        """Update DNS responses."""
        self.state.dns_responses = responses
        self.state.dns_last_updated = datetime.now()

    def update_dnssec(self, validation: DNSSECValidation) -> None:
        """Update DNSSEC validation."""
        self.state.dnssec_validation = validation
        self.state.dnssec_last_updated = datetime.now()

    def update_tls(self, tls_info: TLSInfo) -> None:
        """Update TLS/certificate info."""
        self.state.tls_info = tls_info
        self.state.tls_last_updated = datetime.now()

    def update_http(self, response: HTTPResponse) -> None:
        """Update HTTP response."""
        self.state.http_response = response
        self.state.http_last_updated = datetime.now()

    def update_registration(self, registration: DomainRegistration) -> None:
        """Update domain registration."""
        self.state.registration = registration
        self.state.registration_last_updated = datetime.now()

    def update_email(self, email_config: EmailConfiguration) -> None:
        """Update email configuration."""
        self.state.email_config = email_config
        self.state.email_last_updated = datetime.now()

    def update_health_data(
        self,
        http_health: HTTPHealthData,
        cert_health: CertHealthData,
        dns_health: DNSHealthData,
        registry_health: RegistryHealthData,
        dnssec_health: DNSSECHealthData,
        email_health: EmailHealthData,
    ) -> None:
        """Update all dashboard health data."""
        self.state.http_health = http_health
        self.state.cert_health = cert_health
        self.state.dns_health = dns_health
        self.state.registry_health = registry_health
        self.state.dnssec_health = dnssec_health
        self.state.email_health = email_health

    def clear(self) -> None:
        """Clear all state."""
        self._state = None
