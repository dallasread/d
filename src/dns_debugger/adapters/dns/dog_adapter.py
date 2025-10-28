"""DNS adapter implementation using the 'dog' command."""

import json
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


class DogAdapter(DNSPort):
    """Adapter for the 'dog' DNS client.

    dog is a modern DNS client with colorful output and JSON support.
    https://dns.lookup.dog/
    """

    def query(
        self, domain: str, record_type: RecordType, resolver: Optional[str] = None
    ) -> DNSResponse:
        """Execute a DNS query using dog."""
        start_time = datetime.now()
        query_obj = DNSQuery(domain=domain, record_type=record_type, resolver=resolver)

        # Build dog command
        cmd = ["dog", domain, record_type.value, "--json"]
        if resolver:
            cmd.extend(["@", resolver])

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=10, check=True
            )

            # Parse JSON output from dog
            data = json.loads(result.stdout)
            records = self._parse_dog_output(data, domain, record_type)

            query_time = (datetime.now() - start_time).total_seconds() * 1000
            resolver_used = resolver or "system"

            return DNSResponse(
                query=query_obj,
                records=records,
                query_time_ms=query_time,
                resolver_used=resolver_used,
                timestamp=datetime.now(),
                has_dnssec=False,  # TODO: Parse DNSSEC info from dog output
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
        except json.JSONDecodeError as e:
            query_time = (datetime.now() - start_time).total_seconds() * 1000
            return DNSResponse(
                query=query_obj,
                records=[],
                query_time_ms=query_time,
                resolver_used=resolver or "system",
                timestamp=datetime.now(),
                error=f"Failed to parse dog output: {str(e)}",
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

    def _parse_dog_output(
        self, data: dict, domain: str, record_type: RecordType
    ) -> list[DNSRecord]:
        """Parse dog JSON output into DNSRecord objects."""
        records = []

        # dog JSON format has an "answers" section
        answers = data.get("answers", [])

        for answer in answers:
            record = DNSRecord(
                name=answer.get("name", domain),
                record_type=record_type,
                value=answer.get("data", ""),
                ttl=answer.get("ttl", 0),
                record_class=answer.get("class", "IN"),
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
        return self.query(ip_address, RecordType.PTR)

    def trace(self, domain: str) -> list[DNSResponse]:
        """Trace the DNS resolution path from root servers."""
        # TODO: Implement DNS tracing
        # This requires iterative queries starting from root servers
        raise NotImplementedError("DNS tracing not yet implemented")

    def is_available(self) -> bool:
        """Check if dog is available on the system."""
        try:
            subprocess.run(
                ["dog", "--version"], capture_output=True, timeout=5, check=True
            )
            return True
        except (
            subprocess.CalledProcessError,
            FileNotFoundError,
            subprocess.TimeoutExpired,
        ):
            return False

    def get_tool_name(self) -> str:
        """Get the name of the DNS tool."""
        return "dog"

    def get_version(self) -> Optional[str]:
        """Get the version of dog."""
        try:
            result = subprocess.run(
                ["dog", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
                check=True,
            )
            # dog version output is like "dog 0.1.0"
            return result.stdout.strip().split()[-1]
        except Exception:
            return None
