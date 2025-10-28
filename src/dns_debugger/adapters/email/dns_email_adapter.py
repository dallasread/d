"""Email configuration adapter using DNS queries."""

import re
from typing import Optional

from dns_debugger.domain.ports.email_port import EmailPort
from dns_debugger.domain.models.email_info import (
    EmailConfiguration,
    MXRecord,
    SPFRecord,
    DKIMRecord,
    DMARCRecord,
    DMARCPolicy,
)
from dns_debugger.domain.ports.dns_port import DNSPort
from dns_debugger.domain.models.dns_record import RecordType
from dns_debugger.adapters.dns.factory import DNSAdapterFactory


class DNSEmailAdapter(EmailPort):
    """Adapter for email configuration using DNS queries."""

    # Common DKIM selectors to check
    COMMON_DKIM_SELECTORS = [
        "default",
        "google",
        "k1",
        "s1",
        "s2",
        "selector1",
        "selector2",
        "dkim",
        "mail",
        "email",
        "mx",
    ]

    def __init__(self, dns_adapter: Optional[DNSPort] = None):
        """Initialize with a DNS adapter.

        Args:
            dns_adapter: DNS adapter to use, or None to create one
        """
        self.dns_adapter = dns_adapter or DNSAdapterFactory.create()

    def get_email_config(self, domain: str) -> EmailConfiguration:
        """Get complete email configuration for a domain."""
        # Query MX records
        mx_records = self._get_mx_records(domain)

        # Query SPF
        spf_record = self._get_spf_record(domain)

        # Query DMARC
        dmarc_record = self._get_dmarc_record(domain)

        # Check common DKIM selectors
        dkim_records = self._check_dkim_selectors(domain)

        return EmailConfiguration(
            domain=domain,
            mx_records=mx_records,
            spf_record=spf_record,
            dmarc_record=dmarc_record,
            dkim_selectors_checked=self.COMMON_DKIM_SELECTORS,
            dkim_records=dkim_records,
        )

    def _get_mx_records(self, domain: str) -> list[MXRecord]:
        """Get and parse MX records."""
        response = self.dns_adapter.query(domain, RecordType.MX)

        mx_records = []
        for record in response.records:
            # MX format: "priority hostname"
            parts = record.value.split(None, 1)
            if len(parts) == 2:
                try:
                    priority = int(parts[0])
                    hostname = parts[1].rstrip(".")

                    # Try to resolve the MX hostname to IPs
                    ip_addresses = []
                    try:
                        a_response = self.dns_adapter.query(hostname, RecordType.A)
                        ip_addresses = [r.value for r in a_response.records]
                    except Exception:
                        pass

                    mx_records.append(
                        MXRecord(
                            priority=priority,
                            hostname=hostname,
                            ip_addresses=ip_addresses,
                        )
                    )
                except ValueError:
                    continue

        # Sort by priority
        mx_records.sort(key=lambda x: x.priority)
        return mx_records

    def _get_spf_record(self, domain: str) -> Optional[SPFRecord]:
        """Get and parse SPF record."""
        response = self.dns_adapter.query(domain, RecordType.TXT)

        for record in response.records:
            value = record.value.strip('"')
            if value.startswith("v=spf1"):
                return self._parse_spf(domain, value)

        return None

    def _parse_spf(self, domain: str, record: str) -> SPFRecord:
        """Parse SPF record."""
        mechanisms = []
        includes = []
        ip4_addresses = []
        ip6_addresses = []
        exists = []
        all_mechanism = None

        # Split on whitespace
        parts = record.split()

        for part in parts[1:]:  # Skip v=spf1
            mechanisms.append(part)

            if part.startswith("include:"):
                includes.append(part[8:])
            elif part.startswith("ip4:"):
                ip4_addresses.append(part[4:])
            elif part.startswith("ip6:"):
                ip6_addresses.append(part[4:])
            elif part.startswith("exists:"):
                exists.append(part[7:])
            elif part in ["-all", "~all", "?all", "+all"]:
                all_mechanism = part

        return SPFRecord(
            domain=domain,
            record=record,
            mechanisms=mechanisms,
            all_mechanism=all_mechanism,
            includes=includes,
            ip4_addresses=ip4_addresses,
            ip6_addresses=ip6_addresses,
            exists=exists,
        )

    def _get_dmarc_record(self, domain: str) -> Optional[DMARCRecord]:
        """Get and parse DMARC record."""
        # DMARC records are at _dmarc.domain.com
        dmarc_domain = f"_dmarc.{domain}"
        response = self.dns_adapter.query(dmarc_domain, RecordType.TXT)

        for record in response.records:
            value = record.value.strip('"')
            if value.startswith("v=DMARC1"):
                return self._parse_dmarc(domain, value)

        return None

    def _parse_dmarc(self, domain: str, record: str) -> DMARCRecord:
        """Parse DMARC record."""
        policy = DMARCPolicy.NONE
        subdomain_policy = None
        percentage = 100
        rua_addresses = []
        ruf_addresses = []
        alignment_spf = "r"
        alignment_dkim = "r"

        # Split on semicolons
        parts = record.split(";")

        for part in parts:
            part = part.strip()
            if not part or part.startswith("v="):
                continue

            if "=" in part:
                key, value = part.split("=", 1)
                key = key.strip()
                value = value.strip()

                if key == "p":
                    try:
                        policy = DMARCPolicy(value)
                    except ValueError:
                        policy = DMARCPolicy.UNKNOWN
                elif key == "sp":
                    try:
                        subdomain_policy = DMARCPolicy(value)
                    except ValueError:
                        subdomain_policy = DMARCPolicy.UNKNOWN
                elif key == "pct":
                    try:
                        percentage = int(value)
                    except ValueError:
                        pass
                elif key == "rua":
                    # Parse mailto: addresses
                    rua_addresses = [
                        addr.strip() for addr in value.replace("mailto:", "").split(",")
                    ]
                elif key == "ruf":
                    ruf_addresses = [
                        addr.strip() for addr in value.replace("mailto:", "").split(",")
                    ]
                elif key == "aspf":
                    alignment_spf = value
                elif key == "adkim":
                    alignment_dkim = value

        return DMARCRecord(
            domain=domain,
            policy=policy,
            subdomain_policy=subdomain_policy,
            percentage=percentage,
            rua_addresses=rua_addresses,
            ruf_addresses=ruf_addresses,
            alignment_spf=alignment_spf,
            alignment_dkim=alignment_dkim,
            raw_record=record,
        )

    def _check_dkim_selectors(self, domain: str) -> list[DKIMRecord]:
        """Check common DKIM selectors."""
        dkim_records = []

        for selector in self.COMMON_DKIM_SELECTORS:
            dkim_record = self._check_dkim_selector(domain, selector)
            dkim_records.append(dkim_record)

        return dkim_records

    def _check_dkim_selector(self, domain: str, selector: str) -> DKIMRecord:
        """Check a specific DKIM selector."""
        # DKIM records are at selector._domainkey.domain.com
        dkim_domain = f"{selector}._domainkey.{domain}"

        try:
            response = self.dns_adapter.query(dkim_domain, RecordType.TXT)

            if response.is_success and response.record_count > 0:
                # Found a DKIM record
                for record in response.records:
                    value = record.value.strip('"')
                    if "p=" in value:  # DKIM public key
                        # Parse the public key
                        public_key = None
                        key_type = "rsa"

                        for part in value.split(";"):
                            part = part.strip()
                            if part.startswith("p="):
                                public_key = part[2:]
                            elif part.startswith("k="):
                                key_type = part[2:]

                        return DKIMRecord(
                            selector=selector,
                            domain=domain,
                            public_key=public_key,
                            key_type=key_type,
                            exists=True,
                            raw_record=value,
                        )
        except Exception:
            pass

        return DKIMRecord(selector=selector, domain=domain, exists=False)

    def check_dkim(self, domain: str, selector: str) -> bool:
        """Check if a specific DKIM selector exists."""
        dkim_record = self._check_dkim_selector(domain, selector)
        return dkim_record.exists

    def get_tool_name(self) -> str:
        """Get the name of the DNS tool."""
        return self.dns_adapter.get_tool_name()
