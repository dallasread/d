"""WHOIS adapter for domain registration lookups (fallback)."""

from datetime import datetime
from typing import Optional
import whois

from dns_debugger.domain.models.domain_info import (
    Contact,
    DomainRegistration,
    Nameserver,
    RegistrySource,
)
from dns_debugger.domain.ports.registry_port import RegistryPort


class WHOISAdapter(RegistryPort):
    """Adapter for WHOIS lookups (fallback when RDAP is not available)."""

    def lookup(self, domain: str) -> DomainRegistration:
        """Look up domain registration information via WHOIS."""
        try:
            # Perform WHOIS query
            result = whois.whois(domain)

            # Parse WHOIS response
            return self._parse_whois_response(domain, result)

        except Exception as e:
            raise RuntimeError(f"WHOIS lookup failed for {domain}: {str(e)}")

    def _parse_whois_response(self, domain: str, result) -> DomainRegistration:
        """Parse WHOIS response into DomainRegistration model."""
        # Extract registrar
        registrar = result.registrar if hasattr(result, "registrar") else None
        if isinstance(registrar, list):
            registrar = registrar[0] if registrar else None

        # Extract status
        status = result.status if hasattr(result, "status") else []
        if not isinstance(status, list):
            status = [status] if status else []

        # Extract nameservers
        nameservers = []
        ns_list = result.name_servers if hasattr(result, "name_servers") else []
        if not isinstance(ns_list, list):
            ns_list = [ns_list] if ns_list else []

        for ns in ns_list:
            if ns:
                nameservers.append(Nameserver(hostname=ns.lower(), ip_addresses=[]))

        # Extract dates
        created_date = self._parse_date(
            result.creation_date if hasattr(result, "creation_date") else None
        )
        updated_date = self._parse_date(
            result.updated_date if hasattr(result, "updated_date") else None
        )
        expires_date = self._parse_date(
            result.expiration_date if hasattr(result, "expiration_date") else None
        )

        # Extract contacts
        registrant = self._extract_contact(result, "registrant")
        admin_contact = self._extract_contact(result, "admin")
        tech_contact = self._extract_contact(result, "tech")

        # Check DNSSEC (basic check)
        dnssec = False
        if hasattr(result, "dnssec"):
            dnssec_value = result.dnssec
            if isinstance(dnssec_value, str):
                dnssec = (
                    "signed" in dnssec_value.lower() or "yes" in dnssec_value.lower()
                )
            elif isinstance(dnssec_value, bool):
                dnssec = dnssec_value

        return DomainRegistration(
            domain=domain,
            registrar=registrar,
            registry_source=RegistrySource.WHOIS,
            status=status,
            nameservers=nameservers,
            registrant=registrant,
            admin_contact=admin_contact,
            tech_contact=tech_contact,
            created_date=created_date,
            updated_date=updated_date,
            expires_date=expires_date,
            dnssec=dnssec,
            timestamp=datetime.now(),
            raw_data=result.__dict__ if hasattr(result, "__dict__") else {},
        )

    def _parse_date(self, date_value) -> Optional[datetime]:
        """Parse various date formats from WHOIS."""
        if not date_value:
            return None

        # Handle list of dates (take the first one)
        if isinstance(date_value, list):
            date_value = date_value[0] if date_value else None

        # If already a datetime, return it
        if isinstance(date_value, datetime):
            return date_value

        # Try to parse string
        if isinstance(date_value, str):
            try:
                return datetime.fromisoformat(date_value)
            except ValueError:
                pass

        return None

    def _extract_contact(self, result, prefix: str) -> Optional[Contact]:
        """Extract contact information from WHOIS result."""
        contact = Contact()
        found_any = False

        # Try to extract common fields
        fields = {
            "name": f"{prefix}_name",
            "organization": f"{prefix}_organization",
            "email": f"{prefix}_email",
            "phone": f"{prefix}_phone",
            "address": f"{prefix}_address",
            "city": f"{prefix}_city",
            "state": f"{prefix}_state",
            "postal_code": f"{prefix}_postal_code",
            "country": f"{prefix}_country",
        }

        for attr, field_name in fields.items():
            if hasattr(result, field_name):
                value = getattr(result, field_name)
                if value:
                    setattr(contact, attr, value)
                    found_any = True

        return contact if found_any else None

    def lookup_ip(self, ip_address: str) -> DomainRegistration:
        """Look up IP address registration information via WHOIS."""
        try:
            # WHOIS can query IP addresses too
            result = whois.whois(ip_address)

            return DomainRegistration(
                domain=ip_address,
                registrar=result.registrar if hasattr(result, "registrar") else None,
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
                raw_data=result.__dict__ if hasattr(result, "__dict__") else {},
            )

        except Exception as e:
            raise RuntimeError(f"WHOIS IP lookup failed for {ip_address}: {str(e)}")

    def is_available(self) -> bool:
        """Check if WHOIS is available."""
        try:
            import whois

            return True
        except ImportError:
            return False

    def get_source_name(self) -> str:
        """Get the name of the registry source."""
        return "WHOIS"

    def supports_domain(self, domain: str) -> bool:
        """Check if WHOIS supports the given domain."""
        # WHOIS supports almost all domains
        return True
