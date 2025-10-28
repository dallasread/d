"""Facade for dashboard health checks - separates data fetching from display."""

from dataclasses import dataclass
from typing import Optional

from dns_debugger.adapters.dns.factory import DNSAdapterFactory
from dns_debugger.adapters.cert.factory import CertificateAdapterFactory
from dns_debugger.adapters.http.factory import HTTPAdapterFactory
from dns_debugger.adapters.registry.factory import RegistryAdapterFactory
from dns_debugger.adapters.email.factory import EmailAdapterFactory
from dns_debugger.domain.models.dns_record import RecordType


@dataclass
class HTTPHealthData:
    """HTTP/HTTPS health check data."""

    is_success: bool
    is_redirect: bool
    status_code: Optional[int]
    response_time_ms: Optional[float]
    redirect_count: int
    error: Optional[str]


@dataclass
class CertHealthData:
    """Certificate health check data."""

    is_valid: bool
    is_expired: bool
    days_until_expiry: Optional[int]
    issuer_cn: Optional[str]
    expiry_date: Optional[str]
    chain_valid: bool
    error: Optional[str]


@dataclass
class DNSHealthData:
    """DNS health check data."""

    a_count: int
    aaaa_count: int
    mx_count: int
    ns_count: int
    has_error: bool
    error: Optional[str]


@dataclass
class RegistryHealthData:
    """Domain registration health check data."""

    is_expired: bool
    is_expiring_soon: bool
    days_until_expiry: Optional[int]
    expiry_date: Optional[str]
    registrar: Optional[str]
    dnssec_enabled: bool
    nameserver_count: int
    error: Optional[str]


@dataclass
class DNSSECHealthData:
    """DNSSEC health check data."""

    is_secure: bool
    is_insecure: bool
    is_bogus: bool
    has_dnskey: bool
    has_ds: bool
    ksk_count: int
    zsk_count: int
    warning_count: int
    error: Optional[str]


@dataclass
class EmailHealthData:
    """Email configuration health check data."""

    has_mx: bool
    mx_count: int
    has_spf: bool
    spf_policy: Optional[str]
    has_dkim: bool
    dkim_count: int
    has_dmarc: bool
    dmarc_policy: Optional[str]
    email_provider: Optional[str]
    security_score: int
    error: Optional[str]


class DashboardFacade:
    """Facade for fetching dashboard health check data."""

    def __init__(self):
        self.dns_adapter = DNSAdapterFactory.create()
        self.cert_adapter = CertificateAdapterFactory.create()
        self.http_adapter = HTTPAdapterFactory.create()
        self.registry_adapter = RegistryAdapterFactory.create()
        self.email_adapter = EmailAdapterFactory.create()

    def get_http_health(self, domain: str) -> HTTPHealthData:
        """Get HTTP/HTTPS health data."""
        try:
            response = self.http_adapter.check_url(f"https://{domain}")

            return HTTPHealthData(
                is_success=response.is_success,
                is_redirect=response.is_redirect,
                status_code=response.status_code,
                response_time_ms=response.response_time_ms,
                redirect_count=response.redirect_count,
                error=response.error,
            )
        except Exception as e:
            return HTTPHealthData(
                is_success=False,
                is_redirect=False,
                status_code=None,
                response_time_ms=None,
                redirect_count=0,
                error=str(e),
            )

    def get_cert_health(self, domain: str) -> CertHealthData:
        """Get certificate health data."""
        try:
            tls_info = self.cert_adapter.get_certificate_info(domain)

            if tls_info.certificate_chain.leaf_certificate:
                cert = tls_info.certificate_chain.leaf_certificate
                return CertHealthData(
                    is_valid=not cert.is_expired,
                    is_expired=cert.is_expired,
                    days_until_expiry=cert.days_until_expiry,
                    issuer_cn=cert.issuer.common_name,
                    expiry_date=cert.not_after.strftime("%Y-%m-%d"),
                    chain_valid=tls_info.certificate_chain.is_valid,
                    error=None,
                )
            else:
                return CertHealthData(
                    is_valid=False,
                    is_expired=False,
                    days_until_expiry=None,
                    issuer_cn=None,
                    expiry_date=None,
                    chain_valid=False,
                    error="No certificate found",
                )
        except Exception as e:
            return CertHealthData(
                is_valid=False,
                is_expired=False,
                days_until_expiry=None,
                issuer_cn=None,
                expiry_date=None,
                chain_valid=False,
                error=str(e),
            )

    def get_dns_health(self, domain: str) -> DNSHealthData:
        """Get DNS health data."""
        try:
            a_response = self.dns_adapter.query(domain, RecordType.A)
            aaaa_response = self.dns_adapter.query(domain, RecordType.AAAA)
            mx_response = self.dns_adapter.query(domain, RecordType.MX)
            ns_response = self.dns_adapter.query(domain, RecordType.NS)

            return DNSHealthData(
                a_count=a_response.record_count if a_response.is_success else 0,
                aaaa_count=aaaa_response.record_count
                if aaaa_response.is_success
                else 0,
                mx_count=mx_response.record_count if mx_response.is_success else 0,
                ns_count=ns_response.record_count if ns_response.is_success else 0,
                has_error=False,
                error=None,
            )
        except Exception as e:
            return DNSHealthData(
                a_count=0,
                aaaa_count=0,
                mx_count=0,
                ns_count=0,
                has_error=True,
                error=str(e),
            )

    def get_registry_health(self, domain: str) -> RegistryHealthData:
        """Get domain registration health data."""
        try:
            registration = self.registry_adapter.lookup(domain)

            return RegistryHealthData(
                is_expired=registration.is_expired,
                is_expiring_soon=registration.is_expiring_soon(),
                days_until_expiry=registration.days_until_expiry,
                expiry_date=registration.expires_date.strftime("%Y-%m-%d")
                if registration.expires_date
                else None,
                registrar=registration.registrar,
                dnssec_enabled=registration.dnssec,
                nameserver_count=len(registration.nameservers)
                if registration.nameservers
                else 0,
                error=None,
            )
        except Exception as e:
            return RegistryHealthData(
                is_expired=False,
                is_expiring_soon=False,
                days_until_expiry=None,
                expiry_date=None,
                registrar=None,
                dnssec_enabled=False,
                nameserver_count=0,
                error=str(e),
            )

    def get_dnssec_health(self, domain: str) -> DNSSECHealthData:
        """Get DNSSEC health data."""
        try:
            validation = self.dns_adapter.validate_dnssec(domain)

            has_dnskey = (
                validation.chain.has_dnskey_record if validation.chain else False
            )
            has_ds = validation.chain.has_ds_record if validation.chain else False
            ksk_count = validation.chain.ksk_count if validation.chain else 0
            zsk_count = validation.chain.zsk_count if validation.chain else 0

            return DNSSECHealthData(
                is_secure=validation.is_secure,
                is_insecure=validation.is_insecure,
                is_bogus=validation.is_bogus,
                has_dnskey=has_dnskey,
                has_ds=has_ds,
                ksk_count=ksk_count,
                zsk_count=zsk_count,
                warning_count=len(validation.warnings) if validation.warnings else 0,
                error=None,
            )
        except Exception as e:
            return DNSSECHealthData(
                is_secure=False,
                is_insecure=False,
                is_bogus=False,
                has_dnskey=False,
                has_ds=False,
                ksk_count=0,
                zsk_count=0,
                warning_count=0,
                error=str(e),
            )

    def get_email_health(self, domain: str) -> EmailHealthData:
        """Get email configuration health data."""
        try:
            email_config = self.email_adapter.get_email_config(domain)

            spf_policy = None
            if email_config.spf_record:
                spf_policy = email_config.spf_record.all_mechanism or "present"

            dmarc_policy = None
            if email_config.dmarc_record:
                dmarc_policy = email_config.dmarc_record.policy.value

            dkim_count = (
                sum(1 for d in email_config.dkim_records if d.exists)
                if email_config.dkim_records
                else 0
            )

            return EmailHealthData(
                has_mx=email_config.has_mx,
                mx_count=len(email_config.mx_records) if email_config.mx_records else 0,
                has_spf=email_config.has_spf,
                spf_policy=spf_policy,
                has_dkim=email_config.has_dkim,
                dkim_count=dkim_count,
                has_dmarc=email_config.has_dmarc,
                dmarc_policy=dmarc_policy,
                email_provider=email_config.email_provider,
                security_score=email_config.security_score,
                error=None,
            )
        except Exception as e:
            return EmailHealthData(
                has_mx=False,
                mx_count=0,
                has_spf=False,
                spf_policy=None,
                has_dkim=False,
                dkim_count=0,
                has_dmarc=False,
                dmarc_policy=None,
                email_provider=None,
                security_score=0,
                error=str(e),
            )
