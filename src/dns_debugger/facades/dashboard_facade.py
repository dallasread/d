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
    created_date: Optional[str]
    updated_date: Optional[str]
    registrar: Optional[str]
    dnssec_enabled: bool
    nameserver_count: int
    status: list[str]
    error: Optional[str]


@dataclass
class DNSSECHealthData:
    """DNSSEC health check data."""

    is_secure: bool
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


@dataclass
class OverallHealthData:
    """Overall domain health summary."""

    domain_status: str  # "healthy", "warning", "critical"
    total_issues: int
    http_status: str  # "pass", "warn", "fail"
    cert_status: str
    dns_status: str
    registry_status: str
    dnssec_status: str
    email_status: str
    summary_message: str


class DashboardFacade:
    """Facade for fetching dashboard health check data."""

    def __init__(self):
        """Initialize the facade."""
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
                    days_until_expiry=cert.days_until_expiry,
                    issuer_cn=cert.issuer.common_name,
                    expiry_date=cert.not_after.strftime("%Y-%m-%d"),
                    chain_valid=tls_info.certificate_chain.is_valid,
                    error=None,
                )
            else:
                return CertHealthData(
                    is_valid=False,
                    days_until_expiry=None,
                    issuer_cn=None,
                    expiry_date=None,
                    chain_valid=False,
                    error="No certificate found",
                )
        except Exception as e:
            return CertHealthData(
                is_valid=False,
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
                is_expiring_soon=registration.is_expiring_soon,
                days_until_expiry=registration.days_until_expiry,
                expiry_date=registration.expires_date.strftime("%Y-%m-%d")
                if registration.expires_date
                else None,
                created_date=registration.created_date.strftime("%Y-%m-%d")
                if registration.created_date
                else None,
                updated_date=registration.updated_date.strftime("%Y-%m-%d")
                if registration.updated_date
                else None,
                registrar=registration.registrar,
                dnssec_enabled=registration.dnssec,
                nameserver_count=len(registration.nameservers)
                if registration.nameservers
                else 0,
                status=registration.status if registration.status else [],
                error=None,
            )
        except Exception as e:
            return RegistryHealthData(
                is_expired=False,
                is_expiring_soon=False,
                days_until_expiry=None,
                expiry_date=None,
                created_date=None,
                updated_date=None,
                registrar=None,
                dnssec_enabled=False,
                nameserver_count=0,
                status=[],
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

    def get_overall_health(
        self,
        http_health: HTTPHealthData,
        cert_health: CertHealthData,
        dns_health: DNSHealthData,
        registry_health: RegistryHealthData,
        dnssec_health: DNSSECHealthData,
        email_health: EmailHealthData,
    ) -> OverallHealthData:
        """Calculate overall domain health from individual components."""

        # Evaluate each component
        http_status = "fail"
        if http_health.error:
            http_status = "fail"  # Connection error
        elif http_health.is_success:
            http_status = "pass"  # 2xx status code (may have gone through redirects)
        elif http_health.is_redirect:
            http_status = "warn"  # Final status is still a redirect (3xx)
        elif http_health.status_code and http_health.status_code < 500:
            http_status = "warn"  # 4xx client error
        else:
            http_status = "fail"  # 5xx or no response

        cert_status = "fail"
        if not cert_health.error:
            if cert_health.is_valid and cert_health.chain_valid:
                if cert_health.days_until_expiry and cert_health.days_until_expiry > 30:
                    cert_status = "pass"
                else:
                    cert_status = "warn"

        dns_status = "fail"
        if not dns_health.has_error:
            if dns_health.a_count > 0 or dns_health.aaaa_count > 0:
                dns_status = "pass"

        registry_status = "fail"
        if not registry_health.error:
            if registry_health.is_expired:
                registry_status = "fail"
            elif registry_health.is_expiring_soon:
                registry_status = "warn"
            else:
                registry_status = "pass"

        dnssec_status = "neutral"  # DNSSEC is optional, so default to neutral
        if dnssec_health.error:
            dnssec_status = "warn"  # Error checking DNSSEC
        elif dnssec_health.is_bogus:
            dnssec_status = "fail"  # DNSSEC is broken
        elif dnssec_health.is_secure:
            dnssec_status = "pass"  # DNSSEC is enabled and valid
        elif dnssec_health.has_dnskey or dnssec_health.has_ds:
            dnssec_status = "warn"  # Partially configured
        else:
            dnssec_status = "neutral"  # Not enabled (optional, neutral state)

        email_status = "fail"
        if not email_health.error:
            if email_health.has_mx:
                if email_health.security_score >= 75:
                    email_status = "pass"
                elif email_health.security_score >= 50:
                    email_status = "warn"
                else:
                    email_status = "warn"

        # Count issues
        statuses = [
            http_status,
            cert_status,
            dns_status,
            registry_status,
            dnssec_status,
            email_status,
        ]
        fail_count = statuses.count("fail")
        warn_count = statuses.count("warn")
        total_issues = fail_count + warn_count

        # Determine overall status
        if fail_count > 0:
            domain_status = "critical"
            summary_message = f"{fail_count} critical issue{'s' if fail_count != 1 else ''}, {warn_count} warning{'s' if warn_count != 1 else ''}"
        elif warn_count > 0:
            domain_status = "warning"
            summary_message = f"{warn_count} warning{'s' if warn_count != 1 else ''}"
        else:
            domain_status = "healthy"
            summary_message = "All systems operational"

        return OverallHealthData(
            domain_status=domain_status,
            total_issues=total_issues,
            http_status=http_status,
            cert_status=cert_status,
            dns_status=dns_status,
            registry_status=registry_status,
            dnssec_status=dnssec_status,
            email_status=email_status,
            summary_message=summary_message,
        )
