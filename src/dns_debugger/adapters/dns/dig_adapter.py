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
from dns_debugger.domain.models.dnssec_info import (
    DNSSECValidation,
    DNSSECStatus,
    DNSSECChain,
    DNSKEYRecord,
    DSRecord,
    RRSIGRecord,
    DNSSECAlgorithm,
    DigestType,
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

    def validate_dnssec(self, domain: str) -> DNSSECValidation:
        """Validate DNSSEC for a domain using dig.

        Args:
            domain: The domain to validate

        Returns:
            DNSSECValidation with validation results
        """
        start_time = datetime.now()

        try:
            # Query for DNSSEC-related records
            ds_response = self.query(domain, RecordType.DS)
            dnskey_response = self.query(domain, RecordType.DNSKEY)

            has_ds = ds_response.is_success and ds_response.record_count > 0
            has_dnskey = dnskey_response.is_success and dnskey_response.record_count > 0

            # Parse DNSSEC records
            ds_records = self._parse_ds_records(ds_response)
            dnskey_records = self._parse_dnskey_records(dnskey_response)

            # Try to check for DNSSEC validation using dig +dnssec
            rrsig_records = []
            has_rrsig = False
            try:
                cmd = ["dig", "+dnssec", "+noall", "+answer", domain, "A"]
                result = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=10, check=True
                )
                # Check if RRSIG records are present in output
                has_rrsig = "RRSIG" in result.stdout
            except Exception:
                has_rrsig = False

            # Build DNSSEC chain
            chain = DNSSECChain(
                domain=domain,
                has_ds_record=has_ds,
                has_dnskey_record=has_dnskey,
                has_rrsig_record=has_rrsig,
                ds_records=ds_records,
                dnskey_records=dnskey_records,
                rrsig_records=rrsig_records,
            )

            # Determine validation status
            if not has_dnskey:
                status = DNSSECStatus.INSECURE
            elif chain.has_chain_of_trust:
                status = DNSSECStatus.SECURE
            else:
                status = DNSSECStatus.INDETERMINATE

            validation_time = (datetime.now() - start_time).total_seconds() * 1000

            warnings = []
            if has_dnskey and not has_ds:
                warnings.append("Domain has DNSKEY but no DS record in parent zone")
            if chain.ksk_count == 0 and has_dnskey:
                warnings.append("No Key Signing Key (KSK) found")
            if chain.zsk_count == 0 and has_dnskey:
                warnings.append("No Zone Signing Key (ZSK) found")

            return DNSSECValidation(
                domain=domain,
                status=status,
                validation_time_ms=validation_time,
                timestamp=datetime.now(),
                chain=chain,
                warnings=warnings,
            )

        except Exception as e:
            validation_time = (datetime.now() - start_time).total_seconds() * 1000
            return DNSSECValidation(
                domain=domain,
                status=DNSSECStatus.INDETERMINATE,
                validation_time_ms=validation_time,
                timestamp=datetime.now(),
                error_message=f"DNSSEC validation failed: {str(e)}",
            )

    def _parse_ds_records(self, response: DNSResponse) -> list[DSRecord]:
        """Parse DS records from DNS response."""
        ds_records = []
        for record in response.records:
            try:
                # DS record format: key_tag algorithm digest_type digest
                parts = record.value.split(None, 3)
                if len(parts) == 4:
                    key_tag = int(parts[0])
                    algorithm = self._parse_algorithm(int(parts[1]))
                    digest_type = self._parse_digest_type(int(parts[2]))
                    digest = parts[3]

                    ds_records.append(
                        DSRecord(
                            key_tag=key_tag,
                            algorithm=algorithm,
                            digest_type=digest_type,
                            digest=digest,
                            ttl=record.ttl,
                        )
                    )
            except (ValueError, IndexError):
                continue

        return ds_records

    def _parse_dnskey_records(self, response: DNSResponse) -> list[DNSKEYRecord]:
        """Parse DNSKEY records from DNS response."""
        dnskey_records = []
        for record in response.records:
            try:
                # DNSKEY format: flags protocol algorithm public_key
                parts = record.value.split(None, 3)
                if len(parts) == 4:
                    flags = int(parts[0])
                    protocol = int(parts[1])
                    algorithm = self._parse_algorithm(int(parts[2]))
                    public_key = parts[3]

                    # Calculate key tag (simplified)
                    key_tag = self._calculate_key_tag(flags, protocol, int(parts[2]))

                    dnskey_records.append(
                        DNSKEYRecord(
                            flags=flags,
                            protocol=protocol,
                            algorithm=algorithm,
                            key_tag=key_tag,
                            public_key=public_key,
                            ttl=record.ttl,
                        )
                    )
            except (ValueError, IndexError):
                continue

        return dnskey_records

    def _parse_algorithm(self, alg_num: int) -> DNSSECAlgorithm:
        """Parse DNSSEC algorithm number to enum."""
        algorithm_map = {
            1: DNSSECAlgorithm.RSAMD5,
            2: DNSSECAlgorithm.DH,
            3: DNSSECAlgorithm.DSA,
            5: DNSSECAlgorithm.RSASHA1,
            6: DNSSECAlgorithm.DSA_NSEC3_SHA1,
            7: DNSSECAlgorithm.RSASHA1_NSEC3_SHA1,
            8: DNSSECAlgorithm.RSASHA256,
            10: DNSSECAlgorithm.RSASHA512,
            12: DNSSECAlgorithm.ECC_GOST,
            13: DNSSECAlgorithm.ECDSAP256SHA256,
            14: DNSSECAlgorithm.ECDSAP384SHA384,
            15: DNSSECAlgorithm.ED25519,
            16: DNSSECAlgorithm.ED448,
        }
        return algorithm_map.get(alg_num, DNSSECAlgorithm.UNKNOWN)

    def _parse_digest_type(self, digest_num: int) -> DigestType:
        """Parse DS digest type number to enum."""
        digest_map = {
            1: DigestType.SHA1,
            2: DigestType.SHA256,
            3: DigestType.GOST,
            4: DigestType.SHA384,
        }
        return digest_map.get(digest_num, DigestType.UNKNOWN)

    def _calculate_key_tag(self, flags: int, protocol: int, algorithm: int) -> int:
        """Calculate a simplified key tag (for display purposes)."""
        # This is a simplified calculation
        # Real key tag calculation involves the entire RDATA
        return (flags + protocol + algorithm) % 65536
