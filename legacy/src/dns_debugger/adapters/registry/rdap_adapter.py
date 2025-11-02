"""RDAP adapter for domain registration lookups (primary)."""

from datetime import datetime
from typing import Optional
import whodap

from dns_debugger.domain.models.domain_info import (
    Contact,
    DomainRegistration,
    Nameserver,
    RegistrySource,
)
from dns_debugger.domain.ports.registry_port import RegistryPort


class RDAPAdapter(RegistryPort):
    """Adapter for RDAP (Registration Data Access Protocol).

    RDAP is the modern replacement for WHOIS, providing structured JSON data.
    """

    def lookup(self, domain: str) -> DomainRegistration:
        """Look up domain registration information via RDAP."""
        try:
            # Use whodap to perform RDAP query
            result = whodap.lookup_domain(domain)

            # Parse RDAP response
            return self._parse_rdap_response(domain, result)

        except Exception as e:
            raise RuntimeError(f"RDAP lookup failed for {domain}: {str(e)}")

    def _parse_rdap_response(self, domain: str, result: dict) -> DomainRegistration:
        """Parse RDAP JSON response into DomainRegistration model."""
        # Extract registrar
        registrar = None
        if "entities" in result:
            for entity in result.get("entities", []):
                if "registrar" in entity.get("roles", []):
                    registrar = (
                        entity.get("vcardArray", [[]])[1][0][3]
                        if entity.get("vcardArray")
                        else None
                    )
                    break

        # Extract status
        status = result.get("status", [])

        # Extract nameservers
        nameservers = []
        if "nameservers" in result:
            for ns in result.get("nameservers", []):
                ns_name = ns.get("ldhName", "")
                ns_ips = []
                if "ipAddresses" in ns:
                    ns_ips.extend(ns.get("ipAddresses", {}).get("v4", []))
                    ns_ips.extend(ns.get("ipAddresses", {}).get("v6", []))
                nameservers.append(Nameserver(hostname=ns_name, ip_addresses=ns_ips))

        # Extract dates
        events = result.get("events", [])
        created_date = None
        updated_date = None
        expires_date = None

        for event in events:
            event_action = event.get("eventAction", "")
            event_date_str = event.get("eventDate", "")

            if event_date_str:
                try:
                    event_date = datetime.fromisoformat(
                        event_date_str.replace("Z", "+00:00")
                    )

                    if event_action == "registration":
                        created_date = event_date
                    elif event_action == "last changed":
                        updated_date = event_date
                    elif event_action == "expiration":
                        expires_date = event_date
                except ValueError:
                    pass

        # Extract contacts (registrant, admin, tech)
        registrant = None
        admin_contact = None
        tech_contact = None

        if "entities" in result:
            for entity in result.get("entities", []):
                roles = entity.get("roles", [])
                contact = self._parse_entity_contact(entity)

                if "registrant" in roles and not registrant:
                    registrant = contact
                elif "administrative" in roles and not admin_contact:
                    admin_contact = contact
                elif "technical" in roles and not tech_contact:
                    tech_contact = contact

        # Check DNSSEC
        dnssec = "signedDelegation" in status

        return DomainRegistration(
            domain=domain,
            registrar=registrar,
            registry_source=RegistrySource.RDAP,
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
            raw_data=result,
        )

    def _parse_entity_contact(self, entity: dict) -> Contact:
        """Parse entity vCard data into Contact model."""
        contact = Contact()

        vcard_array = entity.get("vcardArray", [])
        if len(vcard_array) > 1:
            for vcard_item in vcard_array[1]:
                if not isinstance(vcard_item, list) or len(vcard_item) < 4:
                    continue

                field_name = vcard_item[0].lower()
                field_value = vcard_item[3]

                if field_name == "fn":  # Full name
                    contact.name = field_value
                elif field_name == "org":  # Organization
                    contact.organization = field_value
                elif field_name == "email":
                    contact.email = field_value
                elif field_name == "tel":
                    contact.phone = field_value
                elif field_name == "adr":  # Address
                    if isinstance(field_value, list) and len(field_value) >= 7:
                        contact.address = field_value[2] if field_value[2] else None
                        contact.city = field_value[3] if field_value[3] else None
                        contact.state = field_value[4] if field_value[4] else None
                        contact.postal_code = field_value[5] if field_value[5] else None
                        contact.country = field_value[6] if field_value[6] else None

        return contact

    def lookup_ip(self, ip_address: str) -> DomainRegistration:
        """Look up IP address registration information via RDAP."""
        try:
            result = (
                whodap.lookup_ipv4(ip_address)
                if "." in ip_address
                else whodap.lookup_ipv6(ip_address)
            )

            # For IP lookups, we create a simplified DomainRegistration
            # Extract relevant information
            registrar = None
            if "entities" in result:
                for entity in result.get("entities", []):
                    if entity.get("vcardArray"):
                        registrar = entity.get("vcardArray", [[]])[1][0][3]
                        break

            return DomainRegistration(
                domain=ip_address,
                registrar=registrar,
                registry_source=RegistrySource.RDAP,
                status=result.get("status", []),
                nameservers=[],
                registrant=None,
                admin_contact=None,
                tech_contact=None,
                created_date=None,
                updated_date=None,
                expires_date=None,
                dnssec=False,
                timestamp=datetime.now(),
                raw_data=result,
            )

        except Exception as e:
            raise RuntimeError(f"RDAP IP lookup failed for {ip_address}: {str(e)}")

    def is_available(self) -> bool:
        """Check if RDAP is available (whodap library)."""
        try:
            import whodap

            return True
        except ImportError:
            return False

    def get_source_name(self) -> str:
        """Get the name of the registry source."""
        return "RDAP"

    def supports_domain(self, domain: str) -> bool:
        """Check if RDAP supports the given domain.

        RDAP support varies by TLD, but whodap handles the bootstrap process.
        """
        # whodap handles TLD detection automatically
        return True
