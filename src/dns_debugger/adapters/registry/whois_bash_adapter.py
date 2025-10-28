"""WHOIS adapter using bash whois command."""

import re
import subprocess
from datetime import datetime
from typing import Optional

from dns_debugger.domain.models.domain_info import (
    Contact,
    DomainRegistration,
    Nameserver,
    RegistrySource,
)
from dns_debugger.domain.ports.registry_port import RegistryPort


class WHOISBashAdapter(RegistryPort):
    """Adapter for WHOIS lookups using the command-line whois tool."""

    def lookup(self, domain: str) -> DomainRegistration:
        """Look up domain registration information via whois command."""
        try:
            # Run whois command
            result = subprocess.run(
                ["whois", domain],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )

            if result.returncode != 0 and not result.stdout:
                raise RuntimeError(f"whois command failed: {result.stderr}")

            # Parse whois output
            return self._parse_whois_output(domain, result.stdout)

        except FileNotFoundError:
            raise RuntimeError("whois command not found. Please install whois.")
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"whois lookup timed out for {domain}")
        except Exception as e:
            raise RuntimeError(f"whois lookup failed for {domain}: {str(e)}")

    def _parse_whois_output(self, domain: str, output: str) -> DomainRegistration:
        """Parse whois text output into DomainRegistration model."""
        lines = output.split("\n")

        # Extract registrar
        registrar = self._extract_field(
            lines,
            [
                "Registrar:",
                "registrar:",
                "Registrar Name:",
                "organisation:",
                "organization:",
            ],
        )

        # Extract nameservers
        nameservers = []
        ns_patterns = ["Name Server:", "nserver:", "Nameserver:", "nameserver:"]
        for line in lines:
            for pattern in ns_patterns:
                if pattern in line:
                    ns = line.split(pattern, 1)[1].strip().lower()
                    if ns and ns not in [n.hostname for n in nameservers]:
                        nameservers.append(Nameserver(hostname=ns, ip_addresses=[]))

        # Extract dates
        created_date = self._extract_date(
            lines,
            [
                "Creation Date:",
                "created:",
                "Created:",
                "Registered:",
            ],
        )

        updated_date = self._extract_date(
            lines,
            [
                "Updated Date:",
                "changed:",
                "Modified:",
                "Last Updated:",
            ],
        )

        expires_date = self._extract_date(
            lines,
            [
                "Registry Expiry Date:",
                "Expiration Date:",
                "Expiry Date:",
                "expires:",
                "Expires:",
                "paid-till:",
            ],
        )

        # Extract status
        status = []
        status_patterns = ["Domain Status:", "Status:", "domain status:", "status:"]
        for line in lines:
            for pattern in status_patterns:
                if pattern in line:
                    status_value = line.split(pattern, 1)[1].strip()
                    # Remove URLs and extra info from status
                    status_value = re.sub(r"\s+https?://\S+", "", status_value)
                    if status_value and status_value not in status:
                        status.append(status_value)

        # Check DNSSEC
        dnssec = False
        dnssec_line = self._extract_field(lines, ["DNSSEC:", "dnssec:"])
        if dnssec_line:
            dnssec = "signed" in dnssec_line.lower() or "yes" in dnssec_line.lower()

        # Extract registrant organization (limited info due to privacy)
        registrant = None
        org = self._extract_field(
            lines,
            [
                "Registrant Organization:",
                "Registrant:",
                "org:",
                "organization:",
            ],
        )
        if org:
            registrant = Contact(organization=org)

        return DomainRegistration(
            domain=domain,
            registrar=registrar,
            registry_source=RegistrySource.WHOIS,
            status=status,
            nameservers=nameservers,
            registrant=registrant,
            admin_contact=None,
            tech_contact=None,
            created_date=created_date,
            updated_date=updated_date,
            expires_date=expires_date,
            dnssec=dnssec,
            timestamp=datetime.now(),
            raw_data={"raw_output": output},
        )

    def _extract_field(self, lines: list[str], patterns: list[str]) -> Optional[str]:
        """Extract a field value from whois output."""
        for line in lines:
            for pattern in patterns:
                if line.strip().startswith(pattern):
                    value = line.split(pattern, 1)[1].strip()
                    if value:
                        return value
        return None

    def _extract_date(
        self, lines: list[str], patterns: list[str]
    ) -> Optional[datetime]:
        """Extract and parse a date field from whois output."""
        date_str = self._extract_field(lines, patterns)
        if not date_str:
            return None

        # Try various date formats
        date_formats = [
            "%Y-%m-%dT%H:%M:%SZ",  # ISO format with Z
            "%Y-%m-%dT%H:%M:%S.%fZ",  # ISO with microseconds
            "%Y-%m-%d %H:%M:%S",  # Simple datetime
            "%Y-%m-%d",  # Date only
            "%d.%m.%Y",  # DD.MM.YYYY (European)
            "%d-%b-%Y",  # DD-Mon-YYYY
            "%Y/%m/%d",  # YYYY/MM/DD
        ]

        # Clean the date string
        date_str = date_str.split()[0]  # Take first part before any text

        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        # Try with timezone removal
        date_str_clean = re.sub(r"[+-]\d{2}:\d{2}$", "", date_str)
        date_str_clean = re.sub(r"[+-]\d{4}$", "", date_str_clean)

        for fmt in date_formats:
            try:
                return datetime.strptime(date_str_clean.strip(), fmt)
            except ValueError:
                continue

        return None

    def lookup_ip(self, ip_address: str) -> DomainRegistration:
        """Look up IP address registration information via whois."""
        try:
            result = subprocess.run(
                ["whois", ip_address],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )

            if result.returncode != 0 and not result.stdout:
                raise RuntimeError(f"whois command failed: {result.stderr}")

            lines = result.stdout.split("\n")

            # Extract organization/registrar
            registrar = self._extract_field(
                lines,
                [
                    "OrgName:",
                    "org-name:",
                    "organization:",
                    "netname:",
                ],
            )

            return DomainRegistration(
                domain=ip_address,
                registrar=registrar,
                registry_source=RegistrySource.WHOIS,
                status=[],
                nameservers=[],
                registrant=None,
                admin_contact=None,
                tech_contact=None,
                created_date=None,
                updated_date=None,
                expires_date=None,
                dnssec=False,
                timestamp=datetime.now(),
                raw_data={"raw_output": result.stdout},
            )

        except Exception as e:
            raise RuntimeError(f"whois IP lookup failed for {ip_address}: {str(e)}")

    def is_available(self) -> bool:
        """Check if whois command is available."""
        try:
            # Just check if the command exists using which
            result = subprocess.run(
                ["which", "whois"], capture_output=True, timeout=5, check=False
            )
            return result.returncode == 0
        except:
            return False

    def get_source_name(self) -> str:
        """Get the name of the registry source."""
        return "WHOIS (bash)"

    def supports_domain(self, domain: str) -> bool:
        """Check if WHOIS supports the given domain."""
        return True
