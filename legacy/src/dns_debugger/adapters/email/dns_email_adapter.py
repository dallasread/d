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
        mx_records, mx_raw = self._get_mx_records(domain)

        # Query SPF
        spf_record, spf_raw = self._get_spf_record(domain)

        # Query DMARC
        dmarc_record, dmarc_raw = self._get_dmarc_record(domain)

        # Check common DKIM selectors
        dkim_records, dkim_raw = self._check_dkim_selectors(domain)

        # Collect raw outputs
        raw_outputs = []
        if mx_raw:
            raw_outputs.append(f"# MX Records\n{mx_raw}")
        if spf_raw:
            raw_outputs.append(f"# SPF Record\n{spf_raw}")
        if dmarc_raw:
            raw_outputs.append(f"# DMARC Record\n{dmarc_raw}")
        if dkim_raw:
            raw_outputs.append(f"# DKIM Records\n{dkim_raw}")

        return EmailConfiguration(
            domain=domain,
            mx_records=mx_records,
            spf_record=spf_record,
            dmarc_record=dmarc_record,
            dkim_selectors_checked=self.COMMON_DKIM_SELECTORS,
            dkim_records=dkim_records,
            raw_data={"raw_output": "\n\n".join(raw_outputs)} if raw_outputs else None,
        )

    def _get_mx_records(self, domain: str) -> tuple[list[MXRecord], str]:
        """Get and parse MX records.

        Returns:
            Tuple of (mx_records, raw_output)
        """
        response = self.dns_adapter.query(domain, RecordType.MX)
        raw_output = (
            response.raw_data.get("raw_output", "") if response.raw_data else ""
        )

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
        return mx_records, raw_output

    def _get_spf_record(self, domain: str) -> tuple[Optional[SPFRecord], str]:
        """Get and parse SPF record.

        Returns:
            Tuple of (spf_record, raw_output)
        """
        response = self.dns_adapter.query(domain, RecordType.TXT)
        raw_output = (
            response.raw_data.get("raw_output", "") if response.raw_data else ""
        )

        for record in response.records:
            value = record.value.strip('"')
            if value.startswith("v=spf1"):
                return self._parse_spf(domain, value), raw_output

        return None, raw_output

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

    def _get_dmarc_record(self, domain: str) -> tuple[Optional[DMARCRecord], str]:
        """Get and parse DMARC record.

        Returns:
            Tuple of (dmarc_record, raw_output)
        """
        # DMARC records are at _dmarc.domain.com
        dmarc_domain = f"_dmarc.{domain}"
        response = self.dns_adapter.query(dmarc_domain, RecordType.TXT)
        raw_output = (
            response.raw_data.get("raw_output", "") if response.raw_data else ""
        )

        for record in response.records:
            value = record.value.strip('"')
            if value.startswith("v=DMARC1"):
                return self._parse_dmarc(domain, value), raw_output

        return None, raw_output

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

    def _check_dkim_selectors(self, domain: str) -> tuple[list[DKIMRecord], str]:
        """Check common DKIM selectors.

        Returns:
            Tuple of (dkim_records, raw_output)
        """
        dkim_records = []
        raw_outputs = []

        for selector in self.COMMON_DKIM_SELECTORS:
            dkim_record, raw = self._check_dkim_selector(domain, selector)
            dkim_records.append(dkim_record)
            if raw:
                raw_outputs.append(raw)

        return dkim_records, "\n\n".join(raw_outputs) if raw_outputs else ""

    def _check_dkim_selector(
        self, domain: str, selector: str
    ) -> tuple[DKIMRecord, str]:
        """Check a specific DKIM selector.

        Returns:
            Tuple of (dkim_record, raw_output)
        """
        # DKIM records are at selector._domainkey.domain.com
        dkim_domain = f"{selector}._domainkey.{domain}"

        try:
            response = self.dns_adapter.query(dkim_domain, RecordType.TXT)
            raw_output = (
                response.raw_data.get("raw_output", "") if response.raw_data else ""
            )

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

                        return (
                            DKIMRecord(
                                selector=selector,
                                domain=domain,
                                public_key=public_key,
                                key_type=key_type,
                                exists=True,
                                raw_record=value,
                            ),
                            f"# DKIM selector: {selector}\n{raw_output}"
                            if raw_output
                            else "",
                        )
        except Exception:
            pass

        return DKIMRecord(selector=selector, domain=domain, exists=False), ""

    def check_dkim(self, domain: str, selector: str) -> bool:
        """Check if a specific DKIM selector exists."""
        dkim_record, _ = self._check_dkim_selector(domain, selector)
        return dkim_record.exists

    def get_tool_name(self) -> str:
        """Get the name of the DNS tool."""
        return self.dns_adapter.get_tool_name()
