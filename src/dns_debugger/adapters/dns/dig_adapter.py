"""DNS adapter implementation using the 'dig' command (fallback)."""

import re
import subprocess
from datetime import datetime
from typing import Optional

from dns_debugger.domain.models.dns_record import (
    DNSQuery,
    DNSRecord,
    DNSResponse,
    RecordType,
)
from dns_debugger.domain.ports.dns_port import DNSPort


class DigAdapter(DNSPort):
    """Adapter for the 'dig' DNS client.

    dig is the traditional DNS lookup utility from BIND.
    Used as a fallback when dog is not available.
    """

    def query(
        self, domain: str, record_type: RecordType, resolver: Optional[str] = None
    ) -> DNSResponse:
        """Execute a DNS query using dig."""
        start_time = datetime.now()
        query_obj = DNSQuery(domain=domain, record_type=record_type, resolver=resolver)

        # Build dig command
        cmd = ["dig", "+noall", "+answer", domain, record_type.value]
        if resolver:
            cmd.append(f"@{resolver}")

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=10, check=True
            )

            records = self._parse_dig_output(result.stdout, domain, record_type)
            query_time = (datetime.now() - start_time).total_seconds() * 1000
            resolver_used = resolver or "system"

            return DNSResponse(
                query=query_obj,
                records=records,
                query_time_ms=query_time,
                resolver_used=resolver_used,
                timestamp=datetime.now(),
                has_dnssec=False,
            )

        except subprocess.CalledProcessError as e:
            query_time = (datetime.now() - start_time).total_seconds() * 1000
            return DNSResponse(
                query=query_obj,
                records=[],
                query_time_ms=query_time,
                resolver_used=resolver or "system",
                timestamp=datetime.now(),
                error=f"Query failed: {e.stderr}",
            )
        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds() * 1000
            return DNSResponse(
                query=query_obj,
                records=[],
                query_time_ms=query_time,
                resolver_used=resolver or "system",
                timestamp=datetime.now(),
                error=f"Unexpected error: {str(e)}",
            )

    def _parse_dig_output(
        self, output: str, domain: str, record_type: RecordType
    ) -> list[DNSRecord]:
        """Parse dig output into DNSRecord objects.

        dig output format:
        domain.com.    300    IN    A    93.184.216.34
        """
        records = []

        for line in output.strip().split("\n"):
            if not line or line.startswith(";"):
                continue

            # Parse dig answer line
            # Format: NAME TTL CLASS TYPE RDATA
            parts = line.split(None, 4)
            if len(parts) < 5:
                continue

            name, ttl, record_class, rtype, value = parts

            # Clean up the name (remove trailing dot)
            name = name.rstrip(".")

            record = DNSRecord(
                name=name,
                record_type=record_type,
                value=value.strip(),
                ttl=int(ttl),
                record_class=record_class,
            )
            records.append(record)

        return records

    def query_multiple_types(
        self,
        domain: str,
        record_types: list[RecordType],
        resolver: Optional[str] = None,
    ) -> dict[RecordType, DNSResponse]:
        """Execute multiple DNS queries for different record types."""
        results = {}
        for record_type in record_types:
            results[record_type] = self.query(domain, record_type, resolver)
        return results

    def reverse_lookup(self, ip_address: str) -> DNSResponse:
        """Perform a reverse DNS lookup (PTR record)."""
        # dig has a -x flag for reverse lookups
        start_time = datetime.now()
        query_obj = DNSQuery(domain=ip_address, record_type=RecordType.PTR)

        cmd = ["dig", "+noall", "+answer", "-x", ip_address]

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=10, check=True
            )

            records = self._parse_dig_output(result.stdout, ip_address, RecordType.PTR)
            query_time = (datetime.now() - start_time).total_seconds() * 1000

            return DNSResponse(
                query=query_obj,
                records=records,
                query_time_ms=query_time,
                resolver_used="system",
                timestamp=datetime.now(),
            )

        except Exception as e:
            query_time = (datetime.now() - start_time).total_seconds() * 1000
            return DNSResponse(
                query=query_obj,
                records=[],
                query_time_ms=query_time,
                resolver_used="system",
                timestamp=datetime.now(),
                error=str(e),
            )

    def trace(self, domain: str) -> list[DNSResponse]:
        """Trace the DNS resolution path from root servers."""
        # dig has a +trace flag
        start_time = datetime.now()
        cmd = ["dig", "+trace", domain]

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30, check=True
            )

            # TODO: Parse trace output into multiple DNSResponse objects
            # For now, return a single response with all data
            return []

        except Exception:
            return []

    def is_available(self) -> bool:
        """Check if dig is available on the system."""
        try:
            subprocess.run(["dig", "-v"], capture_output=True, timeout=5, check=True)
            return True
        except (
            subprocess.CalledProcessError,
            FileNotFoundError,
            subprocess.TimeoutExpired,
        ):
            return False

    def get_tool_name(self) -> str:
        """Get the name of the DNS tool."""
        return "dig"

    def get_version(self) -> Optional[str]:
        """Get the version of dig."""
        try:
            result = subprocess.run(
                ["dig", "-v"], capture_output=True, text=True, timeout=5, check=True
            )
            # dig version output is like "DiG 9.10.6"
            match = re.search(r"DiG\s+([\d.]+)", result.stdout)
            return match.group(1) if match else None
        except Exception:
            return None
